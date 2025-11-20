from .base_item import ImageItem


class RightItem(ImageItem):
    """Generic item for right.png."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/right.png"
        super().__init__(x, y, image_path, item_type="Right")
        self.setScale(1.5)
