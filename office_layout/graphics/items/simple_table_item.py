from .base_item import ImageItem


class SimpleTableItem(ImageItem):
    """Simple Table image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/simple_table.png"
        super().__init__(x, y, image_path, item_type="Simple Table")
        self.setScale(1.5)
