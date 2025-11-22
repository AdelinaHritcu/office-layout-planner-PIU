# file: office_layout/graphics/scene.py

import os
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QBrush, QPen, QTransform
from PyQt5.QtCore import Qt, QRectF

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
            "Table": ObjectType.MEETING_TABLE,
            "Table 3 Persons": ObjectType.MEETING_TABLE,
            "Coffee Table": ObjectType.MEETING_TABLE,
            "Dining Table": ObjectType.MEETING_TABLE,
            "Meeting Room": ObjectType.MEETING_TABLE,
            "Chair": ObjectType.CHAIR,
            "Armchair": ObjectType.ARMCHAIR,
            "Sofa": ObjectType.ARMCHAIR,
            "Wall": ObjectType.WALL,
            # other UI types (Door, Sink, Toilet etc.) will use default
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

        # snap to grid if enabled
        if self.show_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)

        clicked_item = self.itemAt(pos, QTransform())

        # if there is a selection and user clicks on empty space,
        # only clear selection; do not add a new item yet
        if event.button() == Qt.LeftButton and clicked_item is None:
            if self.selectedItems():
                for s in self.selectedItems():
                    s.setSelected(False)
                return

        # right click: delete movable item
        if event.button() == Qt.RightButton:
            if clicked_item and (clicked_item.flags() & QGraphicsItem.ItemIsMovable):
                # if linked to model, remove from model too
                logical_id = getattr(clicked_item, "logical_id", None)
                if logical_id is not None:
                    self.layout_model.remove_object(logical_id)
                self.removeItem(clicked_item)
                del clicked_item
                return

        # left click: either start wall drawing or place normal item
        if event.button() == Qt.LeftButton:
            if self.current_type == "Wall":
                # start wall drawing from this point
                self.is_drawing_wall = True
                self.wall_start_pos = pos

                thickness = self.wall_thickness
                # initial tiny horizontal wall; rect is local (0,0,length,thickness)
                self.current_wall_item = WallItem(pos.x(), pos.y(), 1.0, thickness)
                self.current_wall_item.orientation = "horizontal"
                self.addItem(self.current_wall_item)
                # also register in model
                self._register_item_in_model(self.current_wall_item, "Wall")
                return
            else:
                # add new item only if empty space (and no selection to clear)
                if clicked_item is None:
                    self.add_item_at(pos)
                    return
                # if clicked on item, base class will handle selection/drag

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

    def get_scene_data(self) -> dict:
        """
        Export the logical layout (via LayoutModel) as a serializable dict.
        We rebuild the model from current graphics items to ensure sync.
        """
        # rebuild model from current scene items
        self.layout_model = LayoutModel(
            room_width=self.sceneRect().width(),
            room_height=self.sceneRect().height(),
            grid_size=self.grid_size,
        )

        for item in self.items():
            if item.flags() & QGraphicsItem.ItemIsMovable:
                if hasattr(item, "to_dict"):
                    d = item.to_dict()
                    ui_type = d.get("type", "Desk")
                    x = float(d.get("x", 0.0))
                    y = float(d.get("y", 0.0))
                    width = float(d.get("width", 50.0))
                    height = float(d.get("height", 50.0))
                    rotation = float(d.get("rotation", 0.0))

                    object_type = self._map_ui_type_to_object_type(ui_type)
                    metadata = {"ui_type": ui_type}

                    layout_obj = self.layout_model.add_object(
                        object_type=object_type,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        rotation=rotation,
                        metadata=metadata,
                    )
                    setattr(item, "logical_id", layout_obj.id)

        return self.layout_model.to_dict()

    def clear_scene(self):
        """Remove all movable items from the scene."""
        items_to_remove = []
        for item in self.items():
            if item.flags() & QGraphicsItem.ItemIsMovable:
                items_to_remove.append(item)

        for item in items_to_remove:
            self.removeItem(item)
            del item

    def load_scene_data(self, data: dict):
        """
        Populate the scene from a LayoutModel dictionary.
        """
        self.clear_scene()

        # rebuild model from dict
        self.layout_model = LayoutModel.from_dict(data)

        for obj in self.layout_model.all_objects():
            ui_type = obj.metadata.get("ui_type", obj.type.name.title())
            item = self._create_item_for_ui_type(ui_type, obj.x, obj.y)
            if item:
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