from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize


class Sidebar(QWidget):
    """
    Left-side panel with:
      - object list
      - Save / Load buttons
    Styled in a warm beige/brown palette.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # === OBJECT LIST ===
        self.object_list = QListWidget()
        self.object_list.setIconSize(QSize(32, 32))  # iconițe mai mari
        self.object_list.setMinimumHeight(400)

        # lățime minimă ca să nu fie claustrofob
        self.setMinimumWidth(260)

        objects = [
            ("Desk", "resources/icons/desk.png"),
            ("Chair", "resources/icons/chair.png"),
            ("PC", "resources/icons/pc.png"),
            ("Printer", "resources/icons/printer.png"),
            ("Wall", "resources/icons/wall.png"),
            ("Meeting Room", "resources/icons/meetingroom.png"),
        ]

        for name, icon_path in objects:
            item = QListWidgetItem(name)
            item.setIcon(QIcon(icon_path))
            # înălțime mai mare pentru fiecare rând
            item.setSizeHint(QSize(240, 50))
            self.object_list.addItem(item)

        # === BUTTONS ===
        self.btn_save = QPushButton("Save Plan")
        self.btn_load = QPushButton("Load Plan")

        # === STYLES ===
        self.setStyleSheet("""
            QWidget {
                background-color: #F7F1E8;
                font-size: 40px;                     /* font mai mare global pe sidebar */
            }

            QListWidget {
                background-color: #FFF7EE;
                border: 1px solid #C8AD90;
                padding: 4px;
                color: #3E2723;
            }

            QListWidget::item {
                padding: 6px 4px;
            }

            QListWidget::item:selected {
                background-color: #D7B899;
                color: #2C1810;
            }

            QPushButton {
                background-color: #8D6E63;
                color: #FDF8F1;
                border: none;
                border-radius: 6px;
                padding: 10px 12px;                  /* butoane mai înalte */
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #A1887F;
            }

            QPushButton:pressed {
                background-color: #6D4C41;
            }
        """)

        # === ADD WIDGETS TO LAYOUT ===
        layout.addWidget(self.object_list)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_load)
        layout.addStretch()
