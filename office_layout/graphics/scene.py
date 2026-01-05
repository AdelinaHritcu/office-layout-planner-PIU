# file: office_layout/graphics/scene.py

import os
from typing import Optional, Dict, Any, List

from PyQt5.QtWidgets import (
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsItem,
)
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
from office_layout.graphics.items.exit_item import ExitItem

from office_layout.models.layout_model import LayoutModel
from office_layout.models.object_types import ObjectType

from office_layout.algorithms.placement import move_object


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

        # --- Undo/Redo history (snapshot-based) ---
        self._undo_stack: List[dict] = []
        self._redo_stack: List[dict] = []
        self._history_limit: int = 80
        self._history_suspended: bool = False

        # rebuild exit markers if model already has them
        self._rebuild_exit_markers_from_model()

        # initial snapshot (so first undo works)
        self._push_undo_state()

    # ------------------------------------------------------------------
    # general helpers
    # ------------------------------------------------------------------

    def set_object_type(self, object_type: str):
        self.current_type = object_type

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.update()

    def snap_to_grid(self, x: float, y: float) -> tuple[float, float]:
        grid = self.grid_size
        snapped_x = round(x / grid) * grid
        snapped_y = round(y / grid) * grid
        return snapped_x, snapped_y

    # ------------------------------------------------------------------
    # Undo / Redo helpers
    # ------------------------------------------------------------------

    def _push_undo_state(self) -> None:
        """Save a snapshot of current scene/model state."""
        if self._history_suspended:
            return
        snap = self.get_scene_data()  # includes exit_points
        self._undo_stack.append(snap)
        if len(self._undo_stack) > self._history_limit:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 1

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo(self) -> None:
        """Undo last change (restore previous snapshot)."""
        if not self.can_undo():
            return

        current = self.get_scene_data()
        self._redo_stack.append(current)

        # drop current, restore previous
        self._undo_stack.pop()
        target = self._undo_stack[-1]

        self._history_suspended = True
        self.load_scene_data(target)
        self._history_suspended = False

    def redo(self) -> None:
        """Redo last undone change (restore next snapshot)."""
        if not self.can_redo():
            return

        target = self._redo_stack.pop()

        self._history_suspended = True
        self.load_scene_data(target)
        self._history_suspended = False

        # redone state becomes current
        self._undo_stack.append(self.get_scene_data())

    # ------------------------------------------------------------------
    # Exit marker support (NOT a LayoutObject)
    # ------------------------------------------------------------------

    def _create_exit_marker(self, x: float, y: float) -> QGraphicsItem:
        """Create an ExitItem centered at (x, y)."""
        it = ExitItem(0.0, 0.0)

        # center the pixmap on requested point
        br = it.boundingRect()
        it.setPos(x - br.width() * it.scale() / 2.0, y - br.height() * it.scale() / 2.0)

        # mark as exit marker so we do not register it as LayoutObject
        setattr(it, "is_exit_marker", True)
        return it

    def _is_exit_marker(self, item: QGraphicsItem) -> bool:
        if isinstance(item, ExitItem):
            return True
        return bool(getattr(item, "is_exit_marker", False))

    def _sync_exit_points_from_markers(self) -> None:
        pts: List[Dict[str, float]] = []
        for it in self.items():
            if self._is_exit_marker(it):
                c = it.sceneBoundingRect().center()
                pts.append({"x": float(c.x()), "y": float(c.y())})
        self.layout_model.exit_points = pts

    def _remove_all_exit_markers(self) -> None:
        to_remove = []
        for it in self.items():
            if self._is_exit_marker(it):
                to_remove.append(it)
        for it in to_remove:
            self.removeItem(it)
            del it

    def _rebuild_exit_markers_from_model(self) -> None:
        self._remove_all_exit_markers()
        for p in getattr(self.layout_model, "exit_points", []) or []:
            if isinstance(p, dict):
                x = float(p.get("x", 0.0))
                y = float(p.get("y", 0.0))
            else:
                x = float(p[0])
                y = float(p[1])

            m = self._create_exit_marker(x, y)
            self.addItem(m)

    # ------------------------------------------------------------------
    # mapping helpers: UI type <-> ObjectType
    # ------------------------------------------------------------------

    def _map_ui_type_to_object_type(self, ui_type: str) -> ObjectType:
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
            length = 200.0
            thickness = self.wall_thickness
            return WallItem(x, y, length, thickness)

        # Exit is not created here for normal placement; it is handled as a marker tool.
        if ui_type == "Exit":
            it = ExitItem(x, y)
            setattr(it, "is_exit_marker", True)
            return it

        size = 50
        image_name = f"{ui_type.lower().replace(' ', '')}.png"
        image_path = os.path.join("resources", "icons", image_name)

        if os.path.exists(image_path):
            return ImageItem(x, y, image_path, item_type=ui_type)

        rect_item = QGraphicsRectItem(0, 0, size, size)
        rect_item.setPos(x, y)
        rect_item.setBrush(QBrush(Qt.lightGray))
        rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        return rect_item

    def _register_item_in_model(self, item: QGraphicsItem, ui_type: str):
        if not hasattr(self, "layout_model") or self.layout_model is None:
            return None

        # Exit markers are not LayoutObjects
        if ui_type == "Exit" or self._is_exit_marker(item):
            return None

        try:
            pos = item.pos()
            rect = item.boundingRect()

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

        except Exception:
            return None

    # ------------------------------------------------------------------
    # item creation
    # ------------------------------------------------------------------

    def add_item_at(self, pos: QPointF):
        ui_type = self.current_type

        # Select tool should never place
        if ui_type == "Select":
            return

        # Exit tool: place a marker and store in layout_model.exit_points
        if ui_type == "Exit":
            # undo snapshot before change
            self._push_undo_state()

            x, y = float(pos.x()), float(pos.y())
            if self.show_grid:
                x, y = self.snap_to_grid(x, y)

            marker = self._create_exit_marker(x, y)
            self.addItem(marker)
            self._sync_exit_points_from_markers()

            for s in self.selectedItems():
                s.setSelected(False)
            marker.setSelected(True)
            try:
                marker.setFocus()
            except Exception:
                pass
            return

        size = 50
        x = pos.x() - size / 2
        y = pos.y() - size / 2

        if self.show_grid:
            x, y = self.snap_to_grid(x, y)

        item = self._create_item_for_ui_type(ui_type, x, y)

        if item:
            self._register_item_in_model(item, ui_type)

            for s in self.selectedItems():
                s.setSelected(False)

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

        # --- Select tool: cursor only, no placement ---
        if self.current_type == "Select":
            if event.button() == Qt.LeftButton and clicked_item is None and self.selectedItems():
                # click empty -> deselect
                for s in self.selectedItems():
                    s.setSelected(False)
            super().mousePressEvent(event)
            return

        # deselect on empty click, but do not return (allow new placement)
        if event.button() == Qt.LeftButton and clicked_item is None and self.selectedItems():
            for s in self.selectedItems():
                s.setSelected(False)

        # right click delete
        if event.button() == Qt.RightButton:
            if clicked_item and (clicked_item.flags() & QGraphicsItem.ItemIsMovable):
                # undo snapshot before delete
                self._push_undo_state()

                # exit marker delete
                if self._is_exit_marker(clicked_item):
                    self.removeItem(clicked_item)
                    del clicked_item
                    self._sync_exit_points_from_markers()
                    return

                # normal object delete
                logical_id = getattr(clicked_item, "logical_id", None)
                if logical_id is not None:
                    self.layout_model.remove_object(logical_id)
                self.removeItem(clicked_item)
                del clicked_item
                return

        if event.button() == Qt.LeftButton:
            # Wall placement (drag to size)
            if self.current_type == "Wall":
                if isinstance(clicked_item, WallItem):
                    super().mousePressEvent(event)
                    return

                if clicked_item is None:
                    # undo snapshot before starting wall
                    self._push_undo_state()

                    self.is_drawing_wall = True
                    self.wall_start_pos = pos

                    thickness = self.wall_thickness
                    min_len = 40.0
                    self.current_wall_item = WallItem(pos.x(), pos.y(), min_len, thickness)
                    self.current_wall_item.orientation = "horizontal"
                    self.addItem(self.current_wall_item)
                    self._register_item_in_model(self.current_wall_item, "Wall")
                    return

                super().mousePressEvent(event)
                return

            # Exit placement
            if self.current_type == "Exit":
                # allow selecting/moving existing marker
                if clicked_item is not None and self._is_exit_marker(clicked_item):
                    super().mousePressEvent(event)
                    return
                # place on empty
                if clicked_item is None:
                    self.add_item_at(pos)
                    return
                super().mousePressEvent(event)
                return

            # Normal objects: place only on empty
            if clicked_item is None:
                # undo snapshot before placement
                self._push_undo_state()
                self.add_item_at(pos)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # live wall drawing
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

            if abs(dx) >= abs(dy):
                self.current_wall_item.orientation = "horizontal"
                length = max(abs(dx), min_length)
                left_x = start.x() if dx >= 0 else start.x() - length
                top_y = start.y() - thickness / 2.0

                self.current_wall_item.setRect(0, 0, length, thickness)
                self.current_wall_item.setPos(left_x, top_y)
            else:
                self.current_wall_item.orientation = "vertical"
                length = max(abs(dy), min_length)
                top_y = start.y() if dy >= 0 else start.y() - length
                left_x = start.x() - thickness / 2.0

                self.current_wall_item.setRect(0, 0, thickness, length)
                self.current_wall_item.setPos(left_x, top_y)

            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # stop wall drawing
        if self.is_drawing_wall and event.button() == Qt.LeftButton:
            self.is_drawing_wall = False

            wall = self.current_wall_item
            self.current_wall_item = None
            self.wall_start_pos = None

            if wall is not None:
                self._snap_wall_endpoints(wall, snap_dist=12.0)
                self._sync_single_item_to_model(wall)

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

        # If an exit marker was moved, update model exit points
        if self._is_exit_marker(item):
            # snapshot only if actually moved is hard to detect; safe to snapshot on release
            self._push_undo_state()
            self._sync_exit_points_from_markers()
            return

        logical_id = getattr(item, "logical_id", None)
        if logical_id is None:
            return

        # detect meaningful change before snapshot (avoid no-op history)
        model_obj = self.layout_model.get_object(logical_id)
        if model_obj is None:
            return

        old_x, old_y, old_rot = float(model_obj.x), float(model_obj.y), float(model_obj.rotation)
        new_pos = item.pos()
        new_rot = float(item.rotation()) if hasattr(item, "rotation") else 0.0

        changed = (abs(new_pos.x() - old_x) > 0.01) or (abs(new_pos.y() - old_y) > 0.01) or (abs(new_rot - old_rot) > 0.01)
        if changed:
            self._push_undo_state()

        # keep model in sync for all items
        self._sync_single_item_to_model(item)

        pos = item.pos()
        ok, msg = move_object(
            self.layout_model,
            logical_id,
            pos.x(),
            pos.y()
        )

        if not ok:
            # Move rejected -> revert graphics to model position
            model_obj = self.layout_model.get_object(logical_id)
            if model_obj is not None:
                if isinstance(item, WallItem):
                    orient = getattr(item, "orientation", "horizontal")
                    t = float(getattr(item, "thickness", self.wall_thickness))
                    if orient == "horizontal":
                        item.setPos(model_obj.x, model_obj.y - t / 2.0)
                    else:
                        item.setPos(model_obj.x - t / 2.0, model_obj.y)
                else:
                    item.setPos(model_obj.x, model_obj.y)

    # ------------------------------------------------------------------
    # KEYBOARD EVENTS (rotate)
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        selected = self.selectedItems()
        if not selected:
            super().keyPressEvent(event)
            return

        # no rotation in Select mode? (optional) - keep allowed
        if event.key() in (Qt.Key_R, Qt.Key_Left, Qt.Key_Right):
            self._push_undo_state()

        if event.key() == Qt.Key_R:
            for item in selected:
                if self._is_exit_marker(item):
                    continue
                item.setRotation(item.rotation() + 90)
        elif event.key() == Qt.Key_Left:
            for item in selected:
                if self._is_exit_marker(item):
                    continue
                item.setRotation(item.rotation() - 15)
        elif event.key() == Qt.Key_Right:
            for item in selected:
                if self._is_exit_marker(item):
                    continue
                item.setRotation(item.rotation() + 15)
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # SAVE / LOAD HELPERS
    # ------------------------------------------------------------------

    def sync_model_from_items(self) -> None:
        # Update LayoutObjects from graphics items (except exit markers)
        for item in self.items():
            if self._is_exit_marker(item):
                continue

            logical_id = getattr(item, "logical_id", None)
            if logical_id is None:
                continue

            obj = self.layout_model.get_object(logical_id)
            if obj is None:
                continue

            pos = item.pos()

            if hasattr(item, "rect") and callable(getattr(item, "rect")):
                r = item.rect()
                w = float(r.width())
                h = float(r.height())
            else:
                br = item.boundingRect()
                w = float(br.width())
                h = float(br.height())

            rotation = float(item.rotation()) if hasattr(item, "rotation") else 0.0

            x = float(pos.x())
            y = float(pos.y())

            if isinstance(item, WallItem):
                thickness = float(getattr(item, "thickness", 0.0))
                orient = getattr(item, "orientation", "horizontal")
                if orient == "horizontal":
                    y = float(pos.y() + thickness / 2.0)
                else:
                    x = float(pos.x() + thickness / 2.0)

            obj.x = x
            obj.y = y
            obj.width = w
            obj.height = h
            obj.rotation = rotation

        # Update exit_points from markers
        self._sync_exit_points_from_markers()

    def get_scene_data(self) -> dict:
        self.sync_model_from_items()
        return self.layout_model.to_dict()

    def clear_scene(self):
        items_to_remove = []
        for item in self.items():
            if self._is_exit_marker(item):
                items_to_remove.append(item)
                continue
            if (item.flags() & QGraphicsItem.ItemIsMovable) or isinstance(item, WallItem):
                items_to_remove.append(item)

        for item in items_to_remove:
            self.removeItem(item)
            del item

    def _sync_single_item_to_model(self, item: QGraphicsItem) -> None:
        logical_id = getattr(item, "logical_id", None)
        if logical_id is None:
            return

        obj = self.layout_model.get_object(logical_id)
        if obj is None:
            return

        pos = item.pos()

        if hasattr(item, "rect") and callable(getattr(item, "rect")):
            r = item.rect()
            w = float(r.width())
            h = float(r.height())
        else:
            br = item.boundingRect()
            w = float(br.width())
            h = float(br.height())

        x = float(pos.x())
        y = float(pos.y())
        rot = float(item.rotation()) if hasattr(item, "rotation") else 0.0

        if isinstance(item, WallItem):
            thickness = float(getattr(item, "thickness", 0.0))
            orient = getattr(item, "orientation", "horizontal")
            if orient == "horizontal":
                y = float(pos.y() + thickness / 2.0)
            else:
                x = float(pos.x() + thickness / 2.0)

        obj.x = x
        obj.y = y
        obj.width = w
        obj.height = h
        obj.rotation = rot

    def load_scene_data(self, data: dict):
        self.clear_scene()

        self.layout_model = LayoutModel.from_dict(data)

        for obj in self.layout_model.all_objects():
            ui_type = obj.metadata.get("ui_type", obj.type.name.title())
            item = self._create_item_for_ui_type(ui_type, obj.x, obj.y)
            if item:
                if ui_type == "Wall" and isinstance(item, WallItem):
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

        self._rebuild_exit_markers_from_model()

    def _snap_wall_endpoints(self, wall: WallItem, snap_dist: float = 12.0) -> None:
        if wall is None:
            return

        w_points = wall.get_snap_points_scene()

        best_d = float("inf")
        best = None

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
        self.layout_model = model

        self.setSceneRect(0, 0, model.room_width, model.room_height)
        self.grid_size = int(model.grid_size)

        self.rebuild_from_model()

    def rebuild_from_model(self) -> None:
        self.clear_scene()

        for obj in self.layout_model.all_objects():
            ui_type = obj.metadata.get("ui_type", obj.type.name.title())
            item = self._create_item_for_ui_type(ui_type, obj.x, obj.y)
            if item:
                if ui_type == "Wall" and isinstance(item, WallItem):
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

        self._rebuild_exit_markers_from_model()

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
