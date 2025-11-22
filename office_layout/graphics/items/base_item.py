# file: office_layout/graphics/items/base_item.py

from math import hypot
from typing import Optional

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt5.QtGui import QPixmap, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QPointF


class ImageItem(QGraphicsPixmapItem):
    """
    Generic image item with resize from selection frame corners.
    """
    def __init__(self, x: float, y: float, image_path: str, item_type: str = "Generic"):
        self.original_pixmap = QPixmap(image_path)
        scaled_pixmap = self.original_pixmap.scaled(
            50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        super().__init__(scaled_pixmap)

        self.setPos(x, y)
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)

        # rotate and scale around visual center
        self.setTransformOriginPoint(self.boundingRect().center())

        self.item_type = item_type
        self.image_path = image_path

        # resize state
        self._resize_active: bool = False
        self._resize_start_scale: float = 1.0
        self._resize_start_len: float = 0.0
        self._resize_corner: Optional[str] = None

        # how far from the corner the mouse can be to start resize
        self.resize_margin: float = 10.0

    def to_dict(self):
        pos = self.pos()
        rect = self.boundingRect()
        width = rect.width() * self.scale()
        height = rect.height() * self.scale()
        return {
            "type": self.item_type,
            "x": pos.x(),
            "y": pos.y(),
            "rotation": self.rotation(),
            "scale": self.scale(),
            "width": width,
            "height": height,
        }

    # ----- geometry / shape -----

    def shape(self) -> QPainterPath:
        """
        Override shape so mouse events are received on the whole bounding rect,
        including transparent parts of the pixmap. This makes corner hit tests
        match the Qt selection rectangle.
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    # ----- resize helpers -----

    def _corner_hit_test(self, pos: QPointF) -> Optional[str]:
        """
        Return which corner is hit by local pos: 'tl', 'tr', 'bl', 'br' or None.
        The hit region is a square around each corner, slightly outside
        the selection frame so it matches the Qt selection rectangle feeling.
        """
        m = self.resize_margin

        # expand rect so corners include a bit outside the bounding box
        rect = self.boundingRect().adjusted(-m, -m, m, m)
        size = m * 2.0

        tl = QRectF(rect.left(), rect.top(), size, size)
        tr = QRectF(rect.right() - size, rect.top(), size, size)
        bl = QRectF(rect.left(), rect.bottom() - size, size, size)
        br = QRectF(rect.right() - size, rect.bottom() - size, size, size)

        if tl.contains(pos):
            return "tl"
        if tr.contains(pos):
            return "tr"
        if bl.contains(pos):
            return "bl"
        if br.contains(pos):
            return "br"
        return None

    # ----- painting -----

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget: QWidget):
        # let Qt draw the pixmap and its default selection frame (dotted box)
        super().paint(painter, option, widget)

    # ----- hover and mouse events -----

    def hoverMoveEvent(self, event):
        """
        Change cursor when hovering near a corner of the selection frame,
        but only if the item is selected.
        """
        if self.isSelected():
            corner = self._corner_hit_test(event.pos())
            if corner in ("tl", "br"):
                self.setCursor(Qt.SizeFDiagCursor)
                super().hoverMoveEvent(event)
                return
            elif corner in ("tr", "bl"):
                self.setCursor(Qt.SizeBDiagCursor)
                super().hoverMoveEvent(event)
                return

        self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        """
        Start resize if mouse is pressed near a corner while item is selected.
        Otherwise behave like a normal movable/selectable item.
        """
        if self.isSelected():
            corner = self._corner_hit_test(event.pos())
            if corner is not None:
                self._resize_active = True
                self._resize_corner = corner
                self._resize_start_scale = self.scale()

                center = self.boundingRect().center()
                vec = event.pos() - center
                self._resize_start_len = max(hypot(vec.x(), vec.y()), 1.0)

                event.accept()
                return

        self._resize_active = False
        self._resize_corner = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_active:
            center = self.boundingRect().center()
            vec = event.pos() - center
            cur_len = hypot(vec.x(), vec.y())

            if self._resize_start_len > 0.0 and cur_len > 0.0:
                ratio = cur_len / self._resize_start_len
                new_scale = self._resize_start_scale * ratio

                # clamp scale to a reasonable range
                if new_scale < 0.2:
                    new_scale = 0.2

                self.setScale(new_scale)
                self.update()

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resize_active = False
        self._resize_corner = None
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change in (
            QGraphicsItem.ItemSelectedChange,
            QGraphicsItem.ItemTransformHasChanged,
            QGraphicsItem.ItemPositionHasChanged,
        ):
            self.update()
        return super().itemChange(change, value)
