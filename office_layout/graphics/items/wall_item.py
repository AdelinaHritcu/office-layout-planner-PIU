from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt5.QtGui import QPixmap, QBrush, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF
from enum import Enum


# --- NOU: Definim cele 4 colțuri + starea de repaus ---
class Handle(Enum):
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class WallItem(QGraphicsRectItem):
    """
    Un item "zid" redimensionabil folosind 4 mânere de colț.
    """

    def __init__(self, x: float, y: float, w: float = 200.0, h: float = 450.0):
        # Inițializăm dreptunghiul la (0, 0)
        super().__init__(QRectF(0, 0, w, h))
        # Setăm poziția item-ului în scenă
        self.setPos(x, y)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)  # Notifică la schimbări

        self.item_type = "Wall"

        # --- Stare pentru redimensionare ---
        self.is_resizing = False
        self.handle_size = 12.0  # Mărimea mânerelor roșii
        self.current_handle = Handle.NONE

        # Vom salva geometria originală în timpul redimensionării
        self.original_geometry = QRectF()

        # --- Setare textură ---
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

        self.setPen(Qt.NoPen)  # Fără contur

    def to_dict(self):
        """Serialize wall data to a dictionary."""
        rect = self.rect()  # Dreptunghiul local (0, 0, w, h)
        pos = self.pos()  # Poziția în scenă (x, y)
        return {
            "type": self.item_type,
            "x": pos.x(),
            "y": pos.y(),
            "width": rect.width(),
            "height": rect.height(),
            "rotation": self.rotation(),
        }

    # --- NOU: Metodă care returnează toate cele 4 mânere ---
    def get_handle_rects(self) -> dict:
        """Returnează un dicționar cu dreptunghiurile celor 4 mânere în coordonate locale."""
        rect = self.rect()  # Acesta este (0, 0, w, h)
        s = self.handle_size
        s2 = s / 2  # Jumătate din mărime

        return {
            Handle.TOP_LEFT: QRectF(rect.left() - s2, rect.top() - s2, s, s),
            Handle.TOP_RIGHT: QRectF(rect.right() - s2, rect.top() - s2, s, s),
            Handle.BOTTOM_LEFT: QRectF(rect.left() - s2, rect.bottom() - s2, s, s),
            Handle.BOTTOM_RIGHT: QRectF(rect.right() - s2, rect.bottom() - s2, s, s),
        }

    # --- MODIFICAT: Desenează toate cele 4 mânere ---
    def paint(self, painter, option: QStyleOptionGraphicsItem, widget: QWidget):
        super().paint(painter, option, widget)

        # Desenează mânerele ("butoanele") DOAR dacă e selectat
        if self.isSelected():
            painter.setPen(QPen(Qt.darkRed))
            painter.setBrush(QBrush(Qt.red))

            for handle_rect in self.get_handle_rects().values():
                painter.drawRect(handle_rect)

    # --- MODIFICAT: Verifică toate cele 4 mânere ---
    def hoverMoveEvent(self, event):
        """Schimbă cursorul în funcție de mânerul peste care e mouse-ul."""
        if self.isSelected():
            for handle, rect in self.get_handle_rects().items():
                if rect.contains(event.pos()):
                    # Setează cursorul corect (diagonală)
                    if handle in [Handle.TOP_LEFT, Handle.BOTTOM_RIGHT]:
                        self.setCursor(Qt.SizeFDiagCursor)
                    else:
                        self.setCursor(Qt.SizeBDiagCursor)
                    return

        # Dacă nu e peste un mâner, cursorul e normal
        self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    # --- MODIFICAT: Detectează care mâner a fost apăsat ---
    def mousePressEvent(self, event):
        """Verifică dacă începem o redimensionare și salvează starea inițială."""
        self.current_handle = Handle.NONE
        self.is_resizing = False

        if self.isSelected():
            for handle, rect in self.get_handle_rects().items():
                if rect.contains(event.pos()):
                    self.current_handle = handle
                    self.is_resizing = True
                    # Salvăm geometria (poziția și rect-ul) așa cum e în scenă
                    self.original_geometry = self.mapToScene(self.rect()).boundingRect()
                    self.prepareGeometryChange()
                    return

        # Dacă nu am dat click pe un mâner, lasă item-ul să fie mutat
        super().mousePressEvent(event)

    # --- MODIFICAT: Logica centrală de redimensionare ---
    def mouseMoveEvent(self, event):
        """Calculează noua poziție și dimensiune a zidului."""
        if self.is_resizing:
            # Luăm poziția curentă a mouse-ului în coordonatele scenei
            mouse_pos_scene = event.scenePos()

            # Începem cu geometria originală
            new_rect_scene = QRectF(self.original_geometry)

            # Modificăm dreptunghiul scenei în funcție de mânerul tras
            if self.current_handle == Handle.TOP_LEFT:
                new_rect_scene.setTopLeft(mouse_pos_scene)
            elif self.current_handle == Handle.TOP_RIGHT:
                new_rect_scene.setTopRight(mouse_pos_scene)
            elif self.current_handle == Handle.BOTTOM_LEFT:
                new_rect_scene.setBottomLeft(mouse_pos_scene)
            elif self.current_handle == Handle.BOTTOM_RIGHT:
                new_rect_scene.setBottomRight(mouse_pos_scene)

            # Normalizăm (să meargă și dacă tragem de jos în sus)
            new_rect_scene = new_rect_scene.normalized()

            # Prevenim dimensiuni prea mici
            if new_rect_scene.width() < self.handle_size or new_rect_scene.height() < self.handle_size:
                return

            # --- Aceasta este magia ---
            # 1. Mutăm POZIȚIA item-ului la noul colț stânga-sus
            self.setPos(new_rect_scene.topLeft())
            # 2. Setăm DREPTUNGHIUL item-ului să fie de la (0,0) la noua lățime/înălțime
            local_rect = self.mapRectFromScene(new_rect_scene)
            self.setRect(0, 0, local_rect.width(), local_rect.height())

            self.prepareGeometryChange()
        else:
            # Dacă nu redimensionăm, mutăm normal item-ul
            super().mouseMoveEvent(event)

    # --- MODIFICAT: Oprește redimensionarea ---
    def mouseReleaseEvent(self, event):
        """Oprește redimensionarea."""
        self.is_resizing = False
        self.current_handle = Handle.NONE
        super().mouseReleaseEvent(event)

    # --- MODIFICAT: Pentru a redesena la schimbarea selecției ---
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            # Forțează o redesenare pentru a arăta/ascunde mânerele
            self.update()
        return super().itemChange(change, value)