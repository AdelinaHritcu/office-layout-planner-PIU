from .base_item import ImageItem


class DeskItem(ImageItem):
    """A desk item with a wider scaled image."""

    def __init__(self, x, y):
        image_path = "resources/icons/desk.png"
        super().__init__(x, y, image_path, item_type="Desk")

        # default larger size for desks
        self.base_scale = 1.5
        self.setScale(self.base_scale)

        # make sure rotation and scaling use the visual center
        self.setTransformOriginPoint(self.boundingRect().center())
