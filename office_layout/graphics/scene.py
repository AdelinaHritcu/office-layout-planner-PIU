from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtCore import Qt, QRectF


class OfficeScene(QGraphicsScene):
    """Main 2D canvas for placing office elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 600)
        self.current_type = "Desk"
        self.show_grid = False
        self.grid_size = 40

    def set_object_type(self, object_type: str):
        self.current_type = object_type

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.add_item_at(event.scenePos())
        super().mousePressEvent(event)

    def add_item_at(self, pos):
        size = 50
        item = QGraphicsRectItem(0, 0, size, size)
        item.setPos(pos.x() - size / 2, pos.y() - size / 2)
        item.setBrush(QBrush(Qt.lightGray))
        item.setFlag(item.ItemIsMovable, True)
        item.setFlag(item.ItemIsSelectable, True)
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

        # align start positions to grid
        left = int(rect.left()) - (int(rect.left()) % grid)
        top = int(rect.top()) - (int(rect.top()) % grid)

        x = left
        right = int(rect.right())
        bottom = int(rect.bottom())

        while x <= right:
            painter.drawLine(int(x), int(rect.top()), int(x), bottom)
            x += grid

        y = top
        while y <= bottom:
            painter.drawLine(int(rect.left()), int(y), right, int(y))
            y += grid

        painter.restore()
