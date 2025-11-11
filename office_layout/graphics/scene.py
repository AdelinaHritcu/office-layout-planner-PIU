from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt5.QtGui import QBrush
from PyQt5.QtCore import Qt


class OfficeScene(QGraphicsScene):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 600)
        self.current_type = "Desk"

    def set_object_type(self, object_type: str):
        self.current_type = object_type

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
