from .base_item import ImageItem


class CoffeeTableItem(ImageItem):
    """Coffee table image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/coffee-table.png"
        super().__init__(x, y, image_path, item_type="Coffee Table")
        self.setScale(1.5)
