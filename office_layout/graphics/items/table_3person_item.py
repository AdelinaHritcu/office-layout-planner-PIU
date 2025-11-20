from .base_item import ImageItem


class Table3PersonsItem(ImageItem):
    """Table for 3 persons image item."""
    def __init__(self, x: float, y: float):
        image_path = "resources/icons/table-3persons.png"
        super().__init__(x, y, image_path, item_type="Table 3 Persons")
        self.setScale(1.5)
