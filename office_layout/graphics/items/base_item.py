from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImageItem(QGraphicsPixmapItem):
    """Generic item that displays an image (icon) in the scene."""

    def __init__(self, x: float, y: float, image_path: str):
        pixmap = QPixmap(image_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(pixmap)
        self.setPos(x, y)
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable, True)
