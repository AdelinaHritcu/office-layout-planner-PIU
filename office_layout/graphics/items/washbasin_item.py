from .base_item import ImageItem

class WashbasinItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/washbasin.png"
        super().__init__(x, y, image_path, item_type="Washbasin")
        self.setScale(3)