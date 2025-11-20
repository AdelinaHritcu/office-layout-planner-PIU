from .base_item import ImageItem

class SinkItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/sink.png"
        super().__init__(x, y, image_path, item_type="Sink")
        self.setScale(1.5)