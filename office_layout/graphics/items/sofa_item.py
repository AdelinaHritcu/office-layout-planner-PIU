from .base_item import ImageItem


class SofaItem(ImageItem):
    """Sofa image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/sofa.png"
        super().__init__(x, y, image_path, item_type="Sofa")
        self.setScale(1.7)
