from .base_item import ImageItem

class DoorItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/door.png"
        super().__init__(x, y, image_path, item_type="Door")
        self.setScale(1.5)