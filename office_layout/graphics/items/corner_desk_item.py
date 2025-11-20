from .base_item import ImageItem

class CornerDeskItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/corner-desk.png"
        super().__init__(x, y, image_path, item_type="Corner Desk")
        self.setScale(1.5)