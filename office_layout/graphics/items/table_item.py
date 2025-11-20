from .base_item import ImageItem


class TableItem(ImageItem):
    """Generic table image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/table.png"
        super().__init__(x, y, image_path, item_type="Table")
        self.setScale(1.5)
