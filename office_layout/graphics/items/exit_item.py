# python
from .base_item import ImageItem

class ExitItem(ImageItem):
    """Exit image item."""
    def __init__(self, x: float, y: float, image_path: str = "resources/icons/exit.png"):
        super().__init__(x, y, image_path, item_type="Exit")
        self.base_scale = 1.0
        self.setScale(self.base_scale)
        self.setTransformOriginPoint(self.boundingRect().center())
