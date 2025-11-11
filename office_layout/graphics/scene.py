import os
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt5.QtGui import QBrush, QPen, QTransform
from PyQt5.QtCore import Qt, QRectF

from office_layout.graphics.items.base_item import ImageItem
from office_layout.graphics.items.desk_item import DeskItem



class OfficeScene(QGraphicsScene):
    """Main 2D canvas for placing office elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 600)
        self.current_type = "Desk"
        self.show_grid = False
        self.grid_size = 40

    def set_object_type(self, object_type: str):
        """Update the currently selected object type from the sidebar."""
        self.current_type = object_type

    def toggle_grid(self):
        """Toggle grid visibility and refresh the scene."""
        self.show_grid = not self.show_grid
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.scenePos()
            clicked_item = self.itemAt(pos, QTransform())

            if clicked_item is None:
                self.add_item_at(pos)
                return

        super().mousePressEvent(event)

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

        # dacă tipul este Desk -> folosește DeskItem
        if self.current_type == "Desk":
            item = DeskItem(x, y)

        else:
            image_name = f"{self.current_type.lower().replace(' ', '')}.png"
            image_path = os.path.join("resources", "icons", image_name)

            if os.path.exists(image_path):
                item = ImageItem(x, y, image_path)
            else:
                item = QGraphicsRectItem(0, 0, size, size)
                item.setPos(x, y)
                item.setBrush(QBrush(Qt.lightGray))
                item.setFlag(QGraphicsRectItem.ItemIsMovable, True)
                item.setFlag(QGraphicsRectItem.ItemIsSelectable, True)

        self.addItem(item)

    def drawBackground(self, painter, rect: QRectF):
        """Draw grid if enabled."""
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
