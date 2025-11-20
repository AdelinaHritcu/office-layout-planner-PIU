from .base_item import ImageItem


class PoolTableItem(ImageItem):
    """Pool table image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/pool-table.png"
        super().__init__(x, y, image_path, item_type="Pool Table")
        self.setScale(1.5)
