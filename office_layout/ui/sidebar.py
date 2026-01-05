from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QGraphicsEllipseItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize



class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        self.object_list = QListWidget()
        self.object_list.setIconSize(QSize(32, 32))
        self.object_list.setMinimumHeight(400)
        self.setMinimumWidth(260)

        objects = [
            ("Desk", "resources/icons/desk.png"),
            ("Corner Desk", "resources/icons/corner-desk.png"),
            ("Chair", "resources/icons/chair.png"),
            ("Sofa", "resources/icons/sofa.png"),
            ("Armchair", "resources/icons/armchair.png"),
            ("Coffee Table", "resources/icons/coffee-table.png"),
            ("Dining Table", "resources/icons/dining-table.png"),
            ("Table", "resources/icons/table.png"),
            ("Table 3 Persons", "resources/icons/table-3persons.png"),
            ("Pool Table", "resources/icons/pool-table.png"),
            ("Simple Table", "resources/icons/simple_table.png"),
            ("Right", "resources/icons/right.png"),
            ("Wall", "resources/icons/wall.png"),
            ("Door", "resources/icons/door.png"),
            ("Meeting Room", "resources/icons/meeting.png"),
            ("Toilet", "resources/icons/toilet.png"),
            ("Sink", "resources/icons/sink.png"),
            ("Washbasin", "resources/icons/washbasin.png"),
            ("Exit", "resources/icons/exit.png")
        ]


        for name, icon_path in objects:
            item = QListWidgetItem(name)
            item.setIcon(QIcon(icon_path))
            item.setSizeHint(QSize(240, 50))
            self.object_list.addItem(item)

        self.btn_save = QPushButton("Save Plan")
        self.btn_load = QPushButton("Load Plan")

        self.setStyleSheet("""
            QWidget {
                background-color: #F7F1E8;
                font-size: 16px;
            }
            QListWidget {
                background-color: #FFF7EE;
                border: 1px solid #C8AD90;
                padding: 4px; color: #3E2723;
            }
            QListWidget::item { padding: 6px 4px; }
            QListWidget::item:selected {
                background-color: #D7B899;
                color: #2C1810;
            }
            QPushButton {
                background-color: #8D6E63;
                color: #FDF8F1;
                border: none;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #A1887F; }
            QPushButton:pressed { background-color: #6D4C41; }
        """)

        layout.addWidget(self.object_list)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_load)
        layout.addStretch()