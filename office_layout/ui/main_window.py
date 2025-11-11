from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QGraphicsView
)
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

from office_layout.graphics.scene import OfficeScene
from office_layout.ui.toolbar import MainToolBar
from office_layout.ui.statusbar import MainStatusBar


class MainWindow(QMainWindow):
    """Main application window – defines the general UI layout."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Office Layout Planner")
        self.resize(1200, 700)

        # === CENTRAL WIDGET & MAIN LAYOUT ===
        central = QWidget(self)
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        # === SIDEBAR (LEFT PANEL) ===
        left_layout = QVBoxLayout()

        self.object_list = QListWidget()
        self.object_list.addItems([
            "Desk",
            "Chair",
            "PC",
            "Printer",
            "Wall",
            "Meeting Room",
        ])

        self.btn_save = QPushButton("Save Plan")
        self.btn_load = QPushButton("Load Plan")

        left_layout.addWidget(self.object_list)
        left_layout.addWidget(self.btn_save)
        left_layout.addWidget(self.btn_load)
        left_layout.addStretch()

        # === SCENE + VIEW (RIGHT PANEL) ===
        self.scene = OfficeScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # add sidebar + view to main layout
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.view, 4)

        # === TOOLBAR ===
        self.toolbar = MainToolBar(self)
        self.addToolBar(self.toolbar)

        # === STATUS BAR ===
        self.status_bar = MainStatusBar(self)
        self.setStatusBar(self.status_bar)

        # === SIGNAL CONNECTIONS ===

        # sidebar -> scene / actions
        self.object_list.currentTextChanged.connect(self.scene.set_object_type)
        self.btn_save.clicked.connect(self.save_plan)
        self.btn_load.clicked.connect(self.load_plan)

        # toolbar -> actions
        self.toolbar.zoom_in_action.triggered.connect(self.zoom_in)
        self.toolbar.zoom_out_action.triggered.connect(self.zoom_out)
        self.toolbar.toggle_grid_action.triggered.connect(self.toggle_grid)
        self.toolbar.validate_action.triggered.connect(self.validate_layout)

        # default selection
        if self.object_list.count() > 0:
            self.object_list.setCurrentRow(0)

    # === ACTION METHODS ===

    def zoom_in(self):
        self.view.scale(1.2, 1.2)
        self.status_bar.info("Zoom In")

    def zoom_out(self):
        self.view.scale(1 / 1.2, 1 / 1.2)
        self.status_bar.info("Zoom Out")

    def toggle_grid(self):
        self.scene.toggle_grid()
        state = "ON" if self.scene.show_grid else "OFF"
        self.status_bar.info(f"Grid {state}")

    def validate_layout(self):
        # will be connected to algorithms later
        self.status_bar.info("Layout validation not implemented yet")

    def save_plan(self):
        # will be connected to JSON storage later
        self.status_bar.info("Save Plan clicked (not implemented)")

    def load_plan(self):
        # will be connected to JSON storage later
        self.status_bar.info("Load Plan clicked (not implemented)")
