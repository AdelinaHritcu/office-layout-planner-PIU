# file: office_layout/graphics/scene.py

import os

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


class OfficeScene(QGraphicsScene):
    """Main 2D canvas for placing office elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 600)

        self.current_type = "Desk"
        self.show_grid = False
        self.grid_size = 40

        # wall drawing state
        self.is_drawing_wall = False
        self.wall_start_pos = None
        self.current_wall_item: WallItem | None = None
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
    # item creation
    # ------------------------------------------------------------------

    def add_item_at(self, pos):
        size = 50
        x = pos.x() - size / 2
        y = pos.y() - size / 2

        if self.show_grid:
            x, y = self.snap_to_grid(x, y)

        item = None

        if self.current_type == "Desk":
            item = DeskItem(x, y)
        elif self.current_type == "Chair":
            item = ChairItem(x, y)
        elif self.current_type == "Corner Desk":
            item = CornerDeskItem(x, y)
        elif self.current_type == "Door":
            item = DoorItem(x, y)
        elif self.current_type == "Meeting Room":
            item = MeetingRoomItem(x, y)
        elif self.current_type == "Sink":
            item = SinkItem(x, y)
        elif self.current_type == "Toilet":
            item = ToiletItem(x, y)
        elif self.current_type == "Washbasin":
            item = WashbasinItem(x, y)
        elif self.current_type == "Wall":
            # default wall placed without dragging
            length = 100.0
            thickness = self.wall_thickness
            item = WallItem(x, y, length, thickness)
        else:
            image_name = f"{self.current_type.lower().replace(' ', '')}.png"
            image_path = os.path.join("resources", "icons", image_name)

            if os.path.exists(image_path):
                item = ImageItem(x, y, image_path, item_type=self.current_type)
            else:
                # fallback simple rect item
                item = QGraphicsRectItem(0, 0, size, size)
                item.setPos(x, y)
                item.setBrush(QBrush(Qt.lightGray))
                item.setFlag(QGraphicsItem.ItemIsMovable, True)
                item.setFlag(QGraphicsItem.ItemIsSelectable, True)

        if item:
            self.addItem(item)

    # ------------------------------------------------------------------
    # MOUSE EVENTS (TOT CE TINE DE MOUSE)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        pos = event.scenePos()

        # snap to grid if enabled
        if self.show_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)

        clicked_item = self.itemAt(pos, QTransform())

        # right click: delete movable item
        if event.button() == Qt.RightButton:
            if clicked_item and (clicked_item.flags() & QGraphicsItem.ItemIsMovable):
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
                return
            else:
                # add new item only if empty space
                if clicked_item is None:
                    self.add_item_at(pos)
                    return
                # if clicked on item, base class will handle selection/dragging

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
            self.current_wall_item = None
            self.wall_start_pos = None
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
    # SAVE / LOAD HELPERS
    # ------------------------------------------------------------------

    def get_scene_data(self) -> dict:
        """Get all serializable items from the scene."""
        layout = {
            "layout_name": "My Plan",
            "canvas_size": {
                "width": self.sceneRect().width(),
                "height": self.sceneRect().height(),
            },
            "objects": [],
        }

        for item in self.items():
            if item.flags() & QGraphicsItem.ItemIsMovable:
                if hasattr(item, "to_dict"):
                    layout["objects"].append(item.to_dict())

        return layout

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
        """Populate the scene from a dictionary."""
        self.clear_scene()

        for obj in data.get("objects", []):
            x = obj.get("x", 0)
            y = obj.get("y", 0)
            obj_type = obj.get("type", "Desk")
            rotation = obj.get("rotation", 0)
            scale = obj.get("scale", 1.0)

            item = None
            if obj_type == "Wall":
                w = obj.get("width", 200)
                h = obj.get("height", self.wall_thickness)
                item = WallItem(x, y, w if w >= h else h, self.wall_thickness)
            elif obj_type == "Desk":
                item = DeskItem(x, y)
            elif obj_type == "Chair":
                item = ChairItem(x, y)
            elif obj_type == "Corner Desk":
                item = CornerDeskItem(x, y)
            elif obj_type == "Door":
                item = DoorItem(x, y)
            elif obj_type == "Meeting Room":
                item = MeetingRoomItem(x, y)
            elif obj_type == "Sink":
                item = SinkItem(x, y)
            elif obj_type == "Toilet":
                item = ToiletItem(x, y)
            elif obj_type == "Washbasin":
                item = WashbasinItem(x, y)
            else:
                image_name = f"{obj_type.lower().replace(' ', '')}.png"
                image_path = os.path.join("resources", "icons", image_name)
                if not os.path.exists(image_path):
                    image_path = "resources/icons/desk.png"
                item = ImageItem(x, y, image_path, item_type=obj_type)

            if item:
                item.setRotation(rotation)
                item.setScale(scale)
                self.addItem(item)

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
