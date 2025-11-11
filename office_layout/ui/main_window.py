from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QGraphicsView
)
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
from office_layout.graphics.scene import OfficeScene


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Office Layout Planner")
        self.resize(1200, 700)

        central = QWidget()
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        left_layout = QVBoxLayout()
        self.object_list = QListWidget()
        self.object_list.addItems([
            "Desk", "Chair", "PC", "Printer", "Wall", "Meeting Room"
        ])

        self.btn_save = QPushButton("Save Plan")
        self.btn_load = QPushButton("Load Plan")

        left_layout.addWidget(self.object_list)
        left_layout.addWidget(self.btn_save)
        left_layout.addWidget(self.btn_load)
        left_layout.addStretch()

        self.scene = OfficeScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.view, 4)

        self.object_list.currentTextChanged.connect(self.scene.set_object_type)
        self.btn_save.clicked.connect(self.save_plan)
        self.btn_load.clicked.connect(self.load_plan)

        if self.object_list.count() > 0:
            self.object_list.setCurrentRow(0)

    def save_plan(self):
        print("Save button clicked (to be implemented)")

    def load_plan(self):
        print("Load button clicked (to be implemented)")
