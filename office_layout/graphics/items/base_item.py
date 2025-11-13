from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImageItem(QGraphicsPixmapItem):
    """Generic item that displays an image (icon) in the scene."""

    def __init__(self, x: float, y: float, image_path: str, item_type: str = "Generic"):
        pixmap = QPixmap(image_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(pixmap)

        self.setPos(x, y)
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable, True)

        self.item_type = item_type
        self.image_path = image_path

    def to_dict(self):
        """Serialize item data to a dictionary."""
        pos = self.pos()
        return {
            "type": self.item_type,
            "x": pos.x(),
            "y": pos.y(),
            "rotation": self.rotation(),
            "scale": self.scale()
        }