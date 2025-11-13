from .base_item import ImageItem

class ToiletItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/toilet.png"
        super().__init__(x, y, image_path, item_type="Toilet")
        self.setScale(2)