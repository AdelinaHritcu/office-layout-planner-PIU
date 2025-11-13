from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt5.QtGui import QPixmap, QBrush, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF


class WallItem(QGraphicsRectItem):
    """
    A resizable wall item.
    - Click-to-add a default size.
    - Click-and-drag to move.
    - Click-and-drag resize handle (bottom-right) when selected.
    """

    def __init__(self, x: float, y: float, w: float = 100.0, h: float = 20.0):
        # --- CHANGE 1: Initialize the rectangle at (0, 0) ---
        super().__init__(QRectF(0, 0, w, h))

        # --- And set the item's position in the scene ---
        self.setPos(x, y)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.item_type = "Wall"
        self.is_resizing = False
        self.handle_size = 15.0

        try:
            image_path = "resources/icons/wall.png"
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.setBrush(QBrush(pixmap))
            else:
                self.setBrush(QBrush(Qt.darkGray))
        except Exception as e:
            print(f"Error loading wall texture: {e}")
            self.setBrush(QBrush(Qt.darkGray))

        self.setPen(Qt.NoPen)

    # --- CHANGE 2: to_dict() must now get the scene position ---
    def to_dict(self):
        """Serialize wall data to a dictionary."""
        rect = self.rect()  # This gets the local rect (0, 0, w, h)
        pos = self.pos()  # This gets the scene position (x, y)
        return {
            "type": self.item_type,
            "x": pos.x(),  # Use the item's X position
            "y": pos.y(),  # Use the item's Y position
            "width": rect.width(),
            "height": rect.height(),
            "rotation": self.rotation(),
        }

    # --- NO CHANGES NEEDED BELOW THIS LINE ---
    # (All other methods work in local coordinates, so they are correct)

    def get_handle_rect(self) -> QRectF:
        """Returns the bounding rect of the resize handle."""
        rect = self.rect()  # This is (0, 0, w, h), which is correct
        return QRectF(
            rect.right() - self.handle_size / 2,
            rect.bottom() - self.handle_size / 2,
            self.handle_size,
            self.handle_size
        )

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget: QWidget):
        super().paint(painter, option, widget)
        if self.isSelected():
            handle_rect = self.get_handle_rect()
            handle_pen = QPen(Qt.blue, 2)
            handle_brush = QBrush(Qt.white)
            painter.setPen(handle_pen)
            painter.setBrush(handle_brush)
            painter.drawRect(handle_rect)

    def hoverMoveEvent(self, event):
        if self.isSelected() and self.get_handle_rect().contains(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        pos = event.pos()
        if self.isSelected() and self.get_handle_rect().contains(pos):
            self.is_resizing = True
            self.resize_anchor = self.rect().topLeft()  # This is (0, 0), which is correct
        else:
            self.is_resizing = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            # event.pos() is local, so this is correct
            new_rect = QRectF(self.resize_anchor, event.pos()).normalized()
            if new_rect.width() > 10 and new_rect.height() > 10:
                self.setRect(new_rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.update()
        return super().itemChange(change, value)