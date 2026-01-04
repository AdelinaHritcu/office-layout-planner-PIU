# file: office_layout/graphics/scene.py

import os
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QBrush, QPen, QTransform
from PyQt5.QtCore import Qt, QRectF, QPointF

from office_layout.graphics.items.base_item import ImageItem
from office_layout.graphics.items.desk_item import DeskItem
from office_layout.graphics.items.chair_item import ChairItem
from office_layout.graphics.items.corner_desk_item import CornerDeskItem
from office_layout.graphics.items.door_item import DoorItem
from office_layout.graphics.items.meeting_room_item import MeetingRoomItem
from office_layout.graphics.items.sink_item import SinkItem
from office_layout.graphics.items.toilet_item import ToiletItem
from office_layout.graphics.items.washbasin_item import WashbasinItem
from office_layout.graphics.items.wall_item import WallItem

from office_layout.graphics.items.armchair_item import ArmchairItem
from office_layout.graphics.items.simple_table_item import SimpleTableItem
from office_layout.graphics.items.coffee_table_item import CoffeeTableItem
from office_layout.graphics.items.dining_table_item import DiningTableItem
from office_layout.graphics.items.pool_table_item import PoolTableItem
from office_layout.graphics.items.right_item import RightItem
from office_layout.graphics.items.sofa_item import SofaItem
from office_layout.graphics.items.table_item import TableItem
from office_layout.graphics.items.table_3person_item import Table3PersonsItem
from office_layout.models.layout_model import LayoutModel, LayoutObject
from office_layout.models.object_types import ObjectType

from office_layout.algorithms.placement import can_place_object, move_object
from office_layout.algorithms.validation import validate_layout

class OfficeScene(QGraphicsScene):
    """Main 2D canvas for placing office elements."""

    def __init__(self, layout_model: Optional[LayoutModel] = None, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 600)

        # logical model (data)
        if layout_model is None:
            self.layout_model = LayoutModel(
                room_width=self.sceneRect().width(),
                room_height=self.sceneRect().height(),
                grid_size=40.0,
            )
        else:
            self.layout_model = layout_model

        self.current_type = "Desk"
        self.show_grid = False
        self.grid_size = 40

        # wall drawing state
        self.is_drawing_wall = False
        self.wall_start_pos = None
        self.current_wall_item: Optional[WallItem] = None
        self.wall_thickness = 10.0  # fixed wall thickness

    # ------------------------------------------------------------------
    # general helpers
    # ------------------------------------------------------------------

    def set_object_type(self, object_type: str):
        """Update the currently selected object type from the sidebar."""
        self.current_type = object_type

    def toggle_grid(self):
        """Toggle grid visibility and refresh the scene."""
        self.show_grid = not self.show_grid
        self.update()

    def snap_to_grid(self, x: float, y: float) -> tuple[float, float]:
        """Return the nearest grid-aligned position for (x, y)."""
        grid = self.grid_size
        snapped_x = round(x / grid) * grid
        snapped_y = round(y / grid) * grid
        return snapped_x, snapped_y

    # ------------------------------------------------------------------
    # mapping helpers: UI type <-> ObjectType
    # ------------------------------------------------------------------

    def _map_ui_type_to_object_type(self, ui_type: str) -> ObjectType:
        """
        Map the UI label (e.g. 'Desk', 'Armchair') to a logical ObjectType.
        Unknown types fallback to DESK for now.
        """
        mapping: Dict[str, ObjectType] = {
            "Desk": ObjectType.DESK,
            "Corner Desk": ObjectType.DESK,
            "Simple Table": ObjectType.DESK,

            "Chair": ObjectType.CHAIR,

            "Armchair": ObjectType.ARMCHAIR,
            "Sofa": ObjectType.ARMCHAIR,

            "Wall": ObjectType.WALL,
            "Door": ObjectType.DOOR,

            "Table": ObjectType.MEETING_TABLE,
            "Table 3 Persons": ObjectType.MEETING_TABLE,
            "Coffee Table": ObjectType.MEETING_TABLE,
            "Dining Table": ObjectType.MEETING_TABLE,
            "Pool Table": ObjectType.MEETING_TABLE,
            "Meeting Room": ObjectType.MEETING_TABLE,

            "Sink": ObjectType.SINK,
            "Toilet": ObjectType.TOILET,
            "Washbasin": ObjectType.WASHBASIN,
        }

        return mapping.get(ui_type, ObjectType.DESK)

    def _create_item_for_ui_type(self, ui_type: str, x: float, y: float) -> QGraphicsItem:
        """
        Create a graphics item instance for a given UI type and position.
        This is used both when adding new items and when loading from model.
        """
        if ui_type == "Desk":
            return DeskItem(x, y)
        if ui_type == "Chair":
            return ChairItem(x, y)
        if ui_type == "Corner Desk":
            return CornerDeskItem(x, y)
        if ui_type == "Sofa":
            return SofaItem(x, y)
        if ui_type == "Armchair":
            return ArmchairItem(x, y)
        if ui_type == "Coffee Table":
            return CoffeeTableItem(x, y)
        if ui_type == "Dining Table":
            return DiningTableItem(x, y)
        if ui_type == "Table":
            return TableItem(x, y)
        if ui_type == "Table 3 Persons":
            return Table3PersonsItem(x, y)
        if ui_type == "Pool Table":
            return PoolTableItem(x, y)
        if ui_type == "Simple Table":
            return SimpleTableItem(x, y)
        if ui_type == "Right":
            return RightItem(x, y)
        if ui_type == "Door":
            return DoorItem(x, y)
        if ui_type == "Meeting Room":
            return MeetingRoomItem(x, y)
        if ui_type == "Sink":
            return SinkItem(x, y)
        if ui_type == "Toilet":
            return ToiletItem(x, y)
        if ui_type == "Washbasin":
            return WashbasinItem(x, y)
        if ui_type == "Wall":
            # default wall placed without dragging
            length = 200.0
            thickness = self.wall_thickness
            return WallItem(x, y, length, thickness)

        # fallback generic image item
        size = 50
        image_name = f"{ui_type.lower().replace(' ', '')}.png"
        image_path = os.path.join("resources", "icons", image_name)

        if os.path.exists(image_path):
            return ImageItem(x, y, image_path, item_type=ui_type)

        # fallback simple rect item
        rect_item = QGraphicsRectItem(0, 0, size, size)
        rect_item.setPos(x, y)
        rect_item.setBrush(QBrush(Qt.lightGray))
        rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        return rect_item

    def _register_item_in_model(self, item: QGraphicsItem, ui_type: str):
        """
        Create a LayoutObject in the model corresponding to this graphics item.
        Store the model id on the item as 'logical_id' for later sync.
        If something goes wrong, do not crash the app – just log and return None.
        """
        # extra safety: layout_model must exist
        if not hasattr(self, "layout_model") or self.layout_model is None:
            print("[DEBUG] No layout_model attached to scene, skipping registration.")
            return None

        try:
            pos = item.pos()
            rect = item.boundingRect()

            # some items might not implement scale()/rotation the same way
            scale = item.scale() if hasattr(item, "scale") else 1.0
            rotation = item.rotation() if hasattr(item, "rotation") else 0.0

            width = rect.width() * scale
            height = rect.height() * scale

            object_type = self._map_ui_type_to_object_type(ui_type)
            metadata: Dict[str, Any] = {"ui_type": ui_type}

            layout_obj = self.layout_model.add_object(
                object_type=object_type,
                x=pos.x(),
                y=pos.y(),
                width=width,
                height=height,
                rotation=rotation,
                metadata=metadata,
            )

            setattr(item, "logical_id", layout_obj.id)
            return layout_obj

        except Exception as e:
            # VERY IMPORTANT: do not kill the app, just log to console
            print("[ERROR] _register_item_in_model failed:", repr(e))
            return None

    # ------------------------------------------------------------------
    # item creation
    # ------------------------------------------------------------------

    def add_item_at(self, pos):
        size = 50
        x = pos.x() - size / 2
        y = pos.y() - size / 2

        if self.show_grid:
            x, y = self.snap_to_grid(x, y)

        ui_type = self.current_type
        item = self._create_item_for_ui_type(ui_type, x, y)

        if item:
            # link to model
            self._register_item_in_model(item, ui_type)

            # clear existing selection
            for s in self.selectedItems():
                s.setSelected(False)

            # add and select the new item
            self.addItem(item)
            item.setSelected(True)
            try:
                item.setFocus()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # MOUSE EVENTS
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        pos = event.scenePos()

        if self.show_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)

        clicked_item = self.itemAt(pos, QTransform())

        # daca e selectat ceva si dai click pe gol, doar deselecteaza
        if event.button() == Qt.LeftButton and clicked_item is None and self.selectedItems():
            for s in self.selectedItems():
                s.setSelected(False)
            # nu return

        # right click delete
        if event.button() == Qt.RightButton:
            if clicked_item and (clicked_item.flags() & QGraphicsItem.ItemIsMovable):
                logical_id = getattr(clicked_item, "logical_id", None)
                if logical_id is not None:
                    self.layout_model.remove_object(logical_id)
                self.removeItem(clicked_item)
                del clicked_item
                return

        if event.button() == Qt.LeftButton:
            if self.current_type == "Wall":
                # IMPORTANT: daca ai dat click pe un perete existent, NU crea altul
                if isinstance(clicked_item, WallItem):
                    super().mousePressEvent(event)
                    return

                # creezi perete nou doar pe spatiu liber
                if clicked_item is None:
                    self.is_drawing_wall = True
                    self.wall_start_pos = pos

                    thickness = self.wall_thickness
                    min_len = 40.0  # ca sa nu fie punct mic
                    self.current_wall_item = WallItem(pos.x(), pos.y(), min_len, thickness)
                    self.current_wall_item.orientation = "horizontal"
                    self.addItem(self.current_wall_item)
                    self._register_item_in_model(self.current_wall_item, "Wall")
                    return

                # daca ai dat click pe alt obiect (desk/chair etc), lasa selectia normala
                super().mousePressEvent(event)
                return

            else:
                if clicked_item is None:
                    self.add_item_at(pos)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # handle live wall drawing
        if self.is_drawing_wall and self.current_wall_item is not None:
            pos = event.scenePos()

            if self.show_grid:
                pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
                pos.setY(round(pos.y() / self.grid_size) * self.grid_size)

            start = self.wall_start_pos
            thickness = self.wall_thickness
            min_length = 40.0

            dx = pos.x() - start.x()
            dy = pos.y() - start.y()

            # choose orientation by dominant axis
            if abs(dx) >= abs(dy):
                # horizontal wall
                self.current_wall_item.orientation = "horizontal"
                length = max(abs(dx), min_length)
                left_x = start.x() if dx >= 0 else start.x() - length
                top_y = start.y() - thickness / 2.0

                # local rect is (0, 0, length, thickness)
                self.current_wall_item.setRect(0, 0, length, thickness)
                self.current_wall_item.setPos(left_x, top_y)
            else:
                # vertical wall
                self.current_wall_item.orientation = "vertical"
                length = max(abs(dy), min_length)
                top_y = start.y() if dy >= 0 else start.y() - length
                left_x = start.x() - thickness / 2.0

                # local rect is (0, 0, thickness, length)
                self.current_wall_item.setRect(0, 0, thickness, length)
                self.current_wall_item.setPos(left_x, top_y)

            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # stop wall drawing on left button release
        if self.is_drawing_wall and event.button() == Qt.LeftButton:
            self.is_drawing_wall = False

            wall = self.current_wall_item
            self.current_wall_item = None
            self.wall_start_pos = None

            if wall is not None:
                # snap endpoints to nearby wall endpoints
                self._snap_wall_endpoints(wall, snap_dist=12.0)
                self._sync_single_item_to_model(wall)

                # clear previous selection and select the new wall
                for s in self.selectedItems():
                    s.setSelected(False)
                wall.setSelected(True)
                try:
                    wall.setFocus()
                except Exception:
                    pass

            return

        super().mouseReleaseEvent(event)

        selected = self.selectedItems()
        if not selected:
            return

        item = selected[0]
        logical_id = getattr(item, "logical_id", None)
        if logical_id is None:
            return

        # IMPORTANT: for walls, sync directly to model (avoid move_object pos convention mismatch)
        if isinstance(item, WallItem):
            self._sync_single_item_to_model(item)
            return

        pos = item.pos()
        ok, msg = move_object(
            self.layout_model,
            logical_id,
            pos.x(),
            pos.y()
        )

        if not ok:
            print("[VALIDATION] Move rejected:", msg)
            model_obj = self.layout_model.get_object(logical_id)
            if model_obj is not None:
                item.setPos(model_obj.x, model_obj.y)

    # ------------------------------------------------------------------
    # KEYBOARD EVENTS (rotate)
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        """Handle key presses for rotating selected items."""
        selected = self.selectedItems()
        if not selected:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_R:
            for item in selected:
                item.setRotation(item.rotation() + 90)
        elif event.key() == Qt.Key_Left:
            for item in selected:
                item.setRotation(item.rotation() - 15)
        elif event.key() == Qt.Key_Right:
            for item in selected:
                item.setRotation(item.rotation() + 15)
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # SAVE / LOAD HELPERS (via LayoutModel)
    # ------------------------------------------------------------------

    def sync_model_from_items(self) -> None:
        for item in self.items():
            logical_id = getattr(item, "logical_id", None)
            if logical_id is None:
                continue

            obj = self.layout_model.get_object(logical_id)
            if obj is None:
                continue

            rotation = float(item.rotation()) if hasattr(item, "rotation") else 0.0

            if isinstance(item, WallItem):
                pts = item.get_snap_points_scene()
                xs = [p.x() for p in pts]
                ys = [p.y() for p in pts]

                left, right = min(xs), max(xs)
                top, bottom = min(ys), max(ys)

                w = float(right - left)
                h = float(bottom - top)

                orient = "horizontal" if w >= h else "vertical"
                item.orientation = orient

                if orient == "horizontal":
                    x = float(left)  # colț stânga real
                    y = float((top + bottom) / 2.0)  # centerline y
                else:
                    x = float((left + right) / 2.0)  # centerline x
                    y = float(top)  # sus real

                obj.x = x
                obj.y = y
                obj.width = w
                obj.height = h
                obj.rotation = rotation
                continue

            # --- default items ---
            pos = item.pos()
            rect = item.rect() if hasattr(item, "rect") else item.boundingRect()

            obj.x = float(pos.x())
            obj.y = float(pos.y())
            obj.width = float(rect.width())
            obj.height = float(rect.height())
            obj.rotation = rotation

    def get_scene_data(self) -> dict:
        self.sync_model_from_items()
        return self.layout_model.to_dict()

    def clear_scene(self):
        """Remove all placed items from the scene (movable + walls)."""
        items_to_remove = []
        for item in self.items():
            if (item.flags() & QGraphicsItem.ItemIsMovable) or isinstance(item, WallItem):
                items_to_remove.append(item)

        for item in items_to_remove:
            self.removeItem(item)
            del item

    def _sync_single_item_to_model(self, item):
        logical_id = getattr(item, "logical_id", None)
        if logical_id is None:
            return

        obj = self.layout_model.get_object(logical_id)
        if obj is None:
            return

        rotation = float(item.rotation()) if hasattr(item, "rotation") else 0.0

        if isinstance(item, WallItem):
            pts = item.get_snap_points_scene()
            xs = [p.x() for p in pts]
            ys = [p.y() for p in pts]

            left, right = min(xs), max(xs)
            top, bottom = min(ys), max(ys)

            w = float(right - left)
            h = float(bottom - top)

            orient = "horizontal" if w >= h else "vertical"
            item.orientation = orient

            if orient == "horizontal":
                obj.x = float(left)
                obj.y = float((top + bottom) / 2.0)
            else:
                obj.x = float((left + right) / 2.0)
                obj.y = float(top)

            obj.width = w
            obj.height = h
            obj.rotation = rotation
            return

        pos = item.pos()
        rect = item.rect() if hasattr(item, "rect") else item.boundingRect()

        obj.x = float(pos.x())
        obj.y = float(pos.y())
        obj.width = float(rect.width())
        obj.height = float(rect.height())
        obj.rotation = rotation

    def load_scene_data(self, data: dict):
        self.clear_scene()
        self.layout_model = LayoutModel.from_dict(data)

        for obj in self.layout_model.all_objects():
            ui_type = obj.metadata.get("ui_type", obj.type.name.title())

            if ui_type == "Wall":
                t = float(self.wall_thickness)
                item = WallItem(0.0, 0.0, 1.0, t)

                item.setRect(0, 0, obj.width, obj.height)
                item.orientation = "horizontal" if obj.width >= obj.height else "vertical"

                t = float(getattr(item, "thickness", self.wall_thickness))
                if item.orientation == "horizontal":
                    item.setPos(obj.x, obj.y - t / 2.0)
                else:
                    item.setPos(obj.x - t / 2.0, obj.y)



            else:
                item = self._create_item_for_ui_type(ui_type, obj.x, obj.y)

            if item:
                item.setRotation(obj.rotation)
                self.addItem(item)
                setattr(item, "logical_id", obj.id)

    def _snap_wall_endpoints(self, wall: WallItem, snap_dist: float = 12.0) -> None:
        """
        Snap wall corners (rectangle corner-to-corner) so walls visually touch without gaps.
        """
        if wall is None:
            return

        w_points = wall.get_snap_points_scene()

        best_d = float("inf")
        best = None  # (wall_point, target_point)

        for item in self.items():
            if item is wall:
                continue
            if not isinstance(item, WallItem):
                continue

            o_points = item.get_snap_points_scene()

            for wp in w_points:
                for op in o_points:
                    d = WallItem.distance(wp, op)
                    if d < best_d:
                        best_d = d
                        best = (wp, op)

        if best is None or best_d > snap_dist:
            return

        w_pt, target_pt = best
        delta = target_pt - w_pt
        wall.setPos(wall.pos() + delta)

    def set_model(self, model: LayoutModel) -> None:
        """
        Attach a new LayoutModel to the scene and rebuild graphics items from it.
        """
        self.layout_model = model

        # keep sceneRect consistent with loaded room size
        self.setSceneRect(0, 0, model.room_width, model.room_height)

        # optional: keep grid size from model if you want
        self.grid_size = int(model.grid_size)

        self.rebuild_from_model()

    def rebuild_from_model(self) -> None:
        self.clear_scene()

        for obj in self.layout_model.all_objects():
            ui_type = obj.metadata.get("ui_type", obj.type.name.title())
            item = self._create_item_for_ui_type(ui_type, obj.x, obj.y)
            if item:
                if ui_type == "Wall" and isinstance(item, WallItem):
                    t = float(self.wall_thickness)
                    item = WallItem(0.0, 0.0, 1.0, t)

                    item.setRect(0, 0, obj.width, obj.height)
                    item.orientation = "horizontal" if obj.width >= obj.height else "vertical"

                    t = float(getattr(item, "thickness", self.wall_thickness))
                    if item.orientation == "horizontal":
                        item.setPos(obj.x, obj.y - t / 2.0)
                    else:
                        item.setPos(obj.x - t / 2.0, obj.y)

                item.setRotation(obj.rotation)
                self.addItem(item)
                setattr(item, "logical_id", obj.id)

    # ------------------------------------------------------------------
    # GRID DRAWING
    # ------------------------------------------------------------------

    def drawBackground(self, painter, rect: QRectF):
        super().drawBackground(painter, rect)

        if not self.show_grid:
            return

        painter.save()
        pen = QPen(Qt.gray)
        pen.setWidth(0)
        painter.setPen(pen)
        grid = self.grid_size

        left = int(rect.left()) - (int(rect.left()) % grid)
        top = int(rect.top()) - (int(rect.top()) % grid)
        right = int(rect.right())
        bottom = int(rect.bottom())

        x = left
        while x <= right:
            painter.drawLine(int(x), int(rect.top()), int(x), bottom)
            x += grid

        y = top
        while y <= bottom:
            painter.drawLine(int(rect.left()), int(y), right, int(y))
            y += grid

        painter.restore()

