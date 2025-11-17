# python
# file: `office_layout/graphics/items/base_item.py`
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt5.QtGui import QPixmap, QPen, QBrush
from PyQt5.QtCore import Qt, QRectF

class ImageItem(QGraphicsPixmapItem):
    """
    Generic image item with a round white resize handle or optionally no handle.
    """
    def __init__(self, x: float, y: float, image_path: str, item_type: str = "Generic"):
        self.original_pixmap = QPixmap(image_path)
        scaled_pixmap = self.original_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        super().__init__(scaled_pixmap)

        self.setPos(x, y)
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)

        self.setTransformOriginPoint(self.boundingRect().center())

        self.item_type = item_type
        self.image_path = image_path

        self.is_resizing = False
        self.handle_size = 12.0        # set to 0 to effectively hide handle
        self.handle_visible = True    # set to False to hide handle
        self.base_scale = 1.0

    def to_dict(self):
        pos = self.pos()
        return {
            "type": self.item_type,
            "x": pos.x(),
            "y": pos.y(),
            "rotation": self.rotation(),
            "scale": self.scale()
        }

    def get_handle_rect(self) -> QRectF:
        """Return the handle rect (square used for hit test), centered on bottom-right corner (local coords)."""
        if self.handle_size <= 0 or not self.handle_visible:
            return QRectF()  # empty rect -> no hit
        rect = self.pixmap().rect()
        size = self.handle_size
        cx = rect.right() - size / 2
        cy = rect.bottom() - size / 2
        return QRectF(cx - size / 2, cy - size / 2, size, size)

    def _handle_scene_rect(self) -> QRectF:
        """Return handle rect in scene coordinates (normalized)."""
        local = self.get_handle_rect()
        if local.isNull():
            return QRectF()
        tl_scene = self.mapToScene(local.topLeft())
        br_scene = self.mapToScene(local.bottomRight())
        return QRectF(tl_scene, br_scene).normalized()

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget: QWidget):
        super().paint(painter, option, widget)

        # draw round white handle if selected and visible
        if self.isSelected() and self.handle_visible and self.handle_size > 0:
            handle_rect = self.get_handle_rect()
            if not handle_rect.isNull():
                pen = QPen(Qt.darkGray)
                pen.setWidthF(1.0)
                brush = QBrush(Qt.white)
                painter.setPen(pen)
                painter.setBrush(brush)
                painter.drawEllipse(handle_rect)

    def hoverMoveEvent(self, event):
        """Change cursor when over the round handle (use local item coords for hit test)."""
        handle_local = self.get_handle_rect()
        if self.isSelected() and not handle_local.isNull() and handle_local.contains(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        # detect handle hit using local item coordinates (reliable when item is transformed)
        handle_local = self.get_handle_rect()
        if self.isSelected() and not handle_local.isNull() and handle_local.contains(event.pos()):
            self.is_resizing = True
            self.base_scale = self.scale()
            event.accept()
        else:
            self.is_resizing = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            # use event.pos() (local item coords) for resizing math
            local_pos = event.pos()
            original_width = self.pixmap().rect().width()
            original_height = self.pixmap().rect().height()
            if original_width > 0 and original_height > 0:
                new_scale_x = local_pos.x() / original_width
                new_scale_y = local_pos.y() / original_height
                new_scale = (new_scale_x + new_scale_y) / 2.0
                # clamp to a reasonable minimum
                if new_scale > 0.2:
                    self.setScale(new_scale)
                    self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.update()
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        # ensure handle repaints when selection or transform changes
        if change == QGraphicsItem.ItemSelectedChange or change == QGraphicsItem.ItemTransformHasChanged:
            self.update()
        return super().itemChange(change, value)
