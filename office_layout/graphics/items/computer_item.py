from PyQt5.QtCore import Qt
from .base_item import ImageItem


class ComputerItem(ImageItem):
    """A desk item with a wider scaled image."""

    def __init__(self, x, y):
        image_path = "resources/icons/computer.png"
        super().__init__(x, y, image_path)
        self.setScale(2)
