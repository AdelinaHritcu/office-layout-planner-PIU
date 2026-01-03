from typing import Optional

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QBrush, QPen, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF


class WallItem(QGraphicsRectItem):
    """
    Wall item with fixed thickness and resizable length.
    """

    def __init__(self, x: float, y: float, length: float, thickness: float):
        # local rect starts horizontal: length x thickness
        super().__init__(0, 0, max(length, 1.0), thickness)

        # position in scene
        self.setPos(x, y - thickness / 2.0)

        # visual: black wall
        self.setBrush(QBrush(Qt.black))
        self.setPen(QPen(Qt.black, 1))

        # interactive
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)

        # wall params
        self.thickness: float = thickness
        self.orientation: str = "horizontal"  # "horizontal" or "vertical"

        # resize state
        self.resize_margin: float = 10.0
        self._resize_active: bool = False
        self._resize_corner: Optional[str] = None
        self._start_rect: QRectF = QRectF()

        self.item_type = "Wall"

    # ----------------- shape -----------------

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    # ----------------- helpers -----------------

    def _corner_hit_test(self, pos: QPointF) -> Optional[str]:
        m = self.resize_margin
        r = self.boundingRect()

        tl = QRectF(r.left(), r.top(), m, m)
        tr = QRectF(r.right() - m, r.top(), m, m)
        bl = QRectF(r.left(), r.bottom() - m, m, m)
        br = QRectF(r.right() - m, r.bottom() - m, m, m)

        if tl.contains(pos):
            return "tl"
        if tr.contains(pos):
            return "tr"
        if bl.contains(pos):
            return "bl"
        if br.contains(pos):
            return "br"
        return None

    def get_endpoints_scene(self) -> tuple[QPointF, QPointF]:
        """
        Return centerline endpoints in scene coordinates.
        This exists to stay compatible with older snapping code.
        """
        r = self.rect()
        p = self.pos()

        if self.orientation == "horizontal":
            y = p.y() + r.height() / 2.0
            start = QPointF(p.x(), y)
            end = QPointF(p.x() + r.width(), y)
            return start, end

        x = p.x() + r.width() / 2.0
        start = QPointF(x, p.y())
        end = QPointF(x, p.y() + r.height())
        return start, end

    def get_snap_points_scene(self) -> list[QPointF]:
        """
        Return rectangle corner points in scene coordinates.
        Use these for corner-to-corner snapping so walls visually touch.
        """
        r = self.rect()
        p = self.pos()

        left = p.x()
        right = p.x() + r.width()
        top = p.y()
        bottom = p.y() + r.height()

        return [
            QPointF(left, top),
            QPointF(left, bottom),
            QPointF(right, top),
            QPointF(right, bottom),
        ]

    @staticmethod
    def distance(a: QPointF, b: QPointF) -> float:
        return QLineF(a, b).length()

    # ----------------- hover -----------------

    def hoverMoveEvent(self, event):
        if self.isSelected():
            c = self._corner_hit_test(event.pos())
            if c in ("tl", "br"):
                self.setCursor(Qt.SizeFDiagCursor)
                return
            if c in ("tr", "bl"):
                self.setCursor(Qt.SizeBDiagCursor)
                return
        self.setCursor(Qt.ArrowCursor)

    # ----------------- mouse press -----------------

    def mousePressEvent(self, event):
        if self.isSelected():
            corner = self._corner_hit_test(event.pos())
            if corner is not None:
                self._resize_active = True
                self._resize_corner = corner
                self._start_rect = QRectF(self.rect())
                event.accept()
                return

        self._resize_active = False
        self._resize_corner = None
        super().mousePressEvent(event)

    # ----------------- resize only length -----------------

    def mouseMoveEvent(self, event):
        if self._resize_active:
            r = QRectF(self._start_rect)
            pos = event.pos()

            min_len = 20.0

            if self.orientation == "horizontal":
                # change only width, keep thickness constant
                if self._resize_corner in ("tl", "bl"):
                    new_left = pos.x()
                    if self._start_rect.right() - new_left < min_len:
                        new_left = self._start_rect.right() - min_len
                    r.setLeft(new_left)
                elif self._resize_corner in ("tr", "br"):
                    new_right = pos.x()
                    if new_right - self._start_rect.left() < min_len:
                        new_right = self._start_rect.left() + min_len
                    r.setRight(new_right)

                # lock height to thickness and keep center Y
                cy = self._start_rect.center().y()
                r.setHeight(self.thickness)
                r.moveCenter(QPointF(r.center().x(), cy))

            else:
                # change only height, keep thickness constant
                if self._resize_corner in ("tl", "tr"):
                    new_top = pos.y()
                    if self._start_rect.bottom() - new_top < min_len:
                        new_top = self._start_rect.bottom() - min_len
                    r.setTop(new_top)
                elif self._resize_corner in ("bl", "br"):
                    new_bottom = pos.y()
                    if new_bottom - self._start_rect.top() < min_len:
                        new_bottom = self._start_rect.top() + min_len
                    r.setBottom(new_bottom)

                # lock width to thickness and keep center X
                cx = self._start_rect.center().x()
                r.setWidth(self.thickness)
                r.moveCenter(QPointF(cx, r.center().y()))

            self.setRect(r.normalized())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resize_active = False
        self._resize_corner = None
        super().mouseReleaseEvent(event)

    # ----------------- save -----------------

    def to_dict(self):
        p = self.pos()
        r = self.rect()
        return {
            "type": "Wall",
            "x": p.x(),
            "y": p.y() + self.thickness / 2.0,
            "width": r.width(),
            "height": r.height(),
            "rotation": self.rotation(),
            "scale": self.scale(),
        }
