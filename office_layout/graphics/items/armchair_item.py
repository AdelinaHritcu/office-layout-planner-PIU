from .base_item import ImageItem


class ArmchairItem(ImageItem):
    """Armchair image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/armchair.png"
        super().__init__(x, y, image_path, item_type="Armchair")
        self.setScale(1)
