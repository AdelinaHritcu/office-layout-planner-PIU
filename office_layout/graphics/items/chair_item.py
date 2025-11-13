from .base_item import ImageItem

class ChairItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/chair.png"
        super().__init__(x, y, image_path, item_type="Chair")
        self.setScale(2)