import os
import json
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsItem, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QPen, QTransform
from PyQt5.QtCore import Qt, QRectF  # Qt is needed for key codes

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

        self.is_drawing_wall = False
        self.wall_start_pos = None
        self.current_wall_item = None


    def set_object_type(self, object_type: str):
        """Update the currently selected object type from the sidebar."""
        self.current_type = object_type

    def toggle_grid(self):
        """Toggle grid visibility and refresh the scene."""
        self.show_grid = not self.show_grid
        self.update()

    def mousePressEvent(self, event):
        pos = event.scenePos()

        # Snap to grid if enabled
        if self.show_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)

        clicked_item = self.itemAt(pos, QTransform())

        # --- Handle Wall Drawing ---
        if self.current_type == "Wall" and event.button() == Qt.LeftButton:
            self.is_drawing_wall = True
            self.wall_start_pos = pos
            # Create a new wall item with zero size
            self.current_wall_item = WallItem(pos.x(), pos.y(), 0, 0)
            self.addItem(self.current_wall_item)
            return

        # --- Handle Deletion ---
        if event.button() == Qt.RightButton:
            if clicked_item and (clicked_item.flags() & QGraphicsItem.ItemIsMovable):
                self.removeItem(clicked_item)
                del clicked_item
                return

        # --- Handle Adding Other Items ---
        if event.button() == Qt.LeftButton:
            if clicked_item is None:
                self.add_item_at(pos)  # Add normal item
                return

        # Call base class for item selection/moving
        super().mousePressEvent(event)

    # --- NEW: Handles resizing the wall during draw ---
    def mouseMoveEvent(self, event):
        if self.is_drawing_wall and self.current_wall_item:
            pos = event.scenePos()

            # Snap to grid if enabled
            if self.show_grid:
                pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
                pos.setY(round(pos.y() / self.grid_size) * self.grid_size)

            # Create a normalized rectangle
            rect = QRectF(self.wall_start_pos, pos).normalized()
            self.current_wall_item.setRect(rect)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing_wall and event.button() == Qt.LeftButton:
            self.is_drawing_wall = False

            # Optional: Set a minimum wall thickness
            if self.current_wall_item:
                rect = self.current_wall_item.rect()
                if rect.width() < self.grid_size and rect.height() < self.grid_size:
                    # If it's too small, make it a standard "block"
                    rect.setWidth(self.grid_size)
                    rect.setHeight(self.grid_size)
                    self.current_wall_item.setRect(rect)
                elif rect.width() < 10:  # Min thickness
                    rect.setWidth(10)
                    self.current_wall_item.setRect(rect)
                elif rect.height() < 10:  # Min thickness
                    rect.setHeight(10)
                    self.current_wall_item.setRect(rect)

            self.current_wall_item = None
            self.wall_start_pos = None
            return

        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        pos = event.scenePos()
        clicked_item = self.itemAt(pos, QTransform())

        if event.button() == Qt.LeftButton:
            if clicked_item is None:
                self.add_item_at(pos)
                return
            # Let the base class handle selection/drag start

        elif event.button() == Qt.RightButton:
            # Check if we clicked a movable item
            if clicked_item and (clicked_item.flags() & QGraphicsItem.ItemIsMovable):
                self.removeItem(clicked_item)
                del clicked_item
                return

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """Handle key presses for rotating selected items."""

        # Get all selected items
        selected = self.selectedItems()

        if not selected:
            super().keyPressEvent(event)
            return

        # Rotate 90 degrees with 'R'
        if event.key() == Qt.Key_R:
            for item in selected:
                current_rotation = item.rotation()
                item.setRotation(current_rotation + 90)

        elif event.key() == Qt.Key_Left:
            for item in selected:
                item.setRotation(item.rotation() - 15)

        elif event.key() == Qt.Key_Right:
            for item in selected:
                item.setRotation(item.rotation() + 15)

        else:
            super().keyPressEvent(event)

    def snap_to_grid(self, x: float, y: float) -> tuple[float, float]:
        """Return the nearest grid-aligned position for (x, y)."""
        grid = self.grid_size
        snapped_x = round(x / grid) * grid
        snapped_y = round(y / grid) * grid
        return snapped_x, snapped_y

    def add_item_at(self, pos):
        size = 50
        x = pos.x() - size / 2
        y = pos.y() - size / 2

        if self.show_grid:
            x, y = self.snap_to_grid(x, y)

        item = None

        # Use if/elif/else to correctly create items
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
        else:
            # Fallback for any other types
            image_name = f"{self.current_type.lower().replace(' ', '')}.png"
            image_path = os.path.join("resources", "icons", image_name)

            if os.path.exists(image_path):
                item = ImageItem(x, y, image_path, item_type=self.current_type)
            else:
                print(f"Warning: Could not find icon for {self.current_type}")
                item = QGraphicsRectItem(0, 0, size, size)
                item.setPos(x, y)
                item.setBrush(QBrush(Qt.lightGray))
                item.setFlag(QGraphicsRectItem.ItemIsMovable, True)
                item.setFlag(QGraphicsRectItem.ItemIsSelectable, True)

        if item:
            self.addItem(item)


    def get_scene_data(self) -> dict:
        """Get all serializable items from the scene."""
        layout = {
            "layout_name": "My Plan",
            "canvas_size": {"width": self.width(), "height": self.height()},
            "objects": []
        }

        for item in self.items():
            if item.flags() & QGraphicsItem.ItemIsMovable:
                if hasattr(item, 'to_dict'):
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
            scale = obj.get("scale", 2)

            item = None
            if obj_type == "Wall":
                w = obj.get("width", 300)  # Default width
                h = obj.get("height", 300)  # Default height
                item = WallItem(x, y, w, h)
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
                    image_path = "resources/icons/desk.png"  # default
                item = ImageItem(x, y, image_path, item_type=obj_type)

            if item:
                item.setRotation(rotation)
                item.setScale(scale)
                self.addItem(item)

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

        # --- AICI ESTE LINIA CORECTATĂ ---
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


# python
# file: office_layout/graphics/scene_utils.py

# python
# file: office_layout/graphics/scene.py (add these methods / replace the existing add_item_at)

def _add_and_select_item(self, item, x: float = None, y: float = None, clear_selection: bool = True, select: bool = True):
    """
    Internal helper: set position, ensure flags for focus/hover, add to scene,
    bring to front and optionally select+focus the item so resizing works immediately.
    """
    if x is not None or y is not None:
        cur = item.pos()
        nx = x if x is not None else cur.x()
        ny = y if y is not None else cur.y()
        item.setPos(nx, ny)

    if clear_selection:
        for s in self.selectedItems():
            s.setSelected(False)

    # Ensure the item can accept focus and hover events (works for ImageItem and QGraphicsRectItem)
    try:
        item.setFlag(QGraphicsItem.ItemIsFocusable, True)
        item.setAcceptHoverEvents(True)
    except Exception:
        pass

    # Add, bring to front and optionally select/focus
    self.addItem(item)
    max_z = max((it.zValue() for it in self.items()), default=0)
    item.setZValue(max_z + 1)

    if select:
        item.setSelected(True)
        item.setFocus()


def _add_and_select_item(self, item, x: float = None, y: float = None, clear_selection: bool = True, select: bool = True):
    """
    Internal helper: set position, ensure flags for focus/hover, add to scene,
    bring to front and optionally select+focus the item so resizing works immediately.
    Must be a method of OfficeScene.
    """
    if x is not None or y is not None:
        cur = item.pos()
        nx = x if x is not None else cur.x()
        ny = y if y is not None else cur.y()
        item.setPos(nx, ny)

    if clear_selection:
        for s in self.selectedItems():
            s.setSelected(False)

    # Ensure the item is movable/selectable/focusable and accepts hover events
    try:
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.ItemIsFocusable, True)
        item.setAcceptHoverEvents(True)
    except Exception:
        # Some items might not implement these methods; ignore safely
        pass

    # Add, bring to front and optionally select/focus
    self.addItem(item)
    max_z = max((it.zValue() for it in self.items()), default=0)
    item.setZValue(max_z + 1)

    if select:
        item.setSelected(True)
        try:
            item.setFocus()
        except Exception:
            pass


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
    else:
        image_name = f"{self.current_type.lower().replace(' ', '')}.png"
        image_path = os.path.join("resources", "icons", image_name)

        if os.path.exists(image_path):
            item = ImageItem(x, y, image_path, item_type=self.current_type)
        else:
            item = QGraphicsRectItem(0, 0, size, size)
            item.setPos(x, y)
            item.setBrush(QBrush(Qt.lightGray))
            # set basic flags so fallback rect is interactable
            try:
                item.setFlag(QGraphicsItem.ItemIsMovable, True)
                item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                item.setFlag(QGraphicsItem.ItemIsFocusable, True)
                item.setAcceptHoverEvents(True)
            except Exception:
                pass

    if item:
        # Use the helper so every item is selected/focused consistently
        self._add_and_select_item(item, x, y)
