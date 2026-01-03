from .base_item import ImageItem

class MeetingRoomItem(ImageItem):
    def __init__(self, x, y):
        image_path = "resources/icons/meeting.png"
        super().__init__(x, y, image_path, item_type="Meeting Room")
        self.setScale(1.5)