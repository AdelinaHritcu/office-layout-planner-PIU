from .base_item import ImageItem


class DiningTableItem(ImageItem):
    """Dining table image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/dining-table.png"
        super().__init__(x, y, image_path, item_type="Dining Table")
        self.setScale(1.5)
