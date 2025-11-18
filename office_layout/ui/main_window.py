from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QGraphicsView
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

from office_layout.graphics.scene import OfficeScene
from office_layout.ui.toolbar import MainToolBar
from office_layout.ui.statusbar import MainStatusBar
from office_layout.ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    """Main application window – defines the general UI layout."""

    def __init__(self):
        super().__init__()

        # === WINDOW SETUP ===
        self.setWindowTitle("Office Layout Planner")
        self.resize(1400, 800)

        # === CENTRAL WIDGET & MAIN LAYOUT ===
        central = QWidget(self)
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        # === SIDEBAR (LEFT PANEL) ===
        self.sidebar = Sidebar(self)

        # === SCENE + VIEW (RIGHT PANEL) ===
        self.scene = OfficeScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Add sidebar + view to main layout
        main_layout.addWidget(self.sidebar, 1)
        main_layout.addWidget(self.view, 4)

        # === TOOLBAR ===
        self.toolbar = MainToolBar(self)
        self.addToolBar(self.toolbar)

        # === STATUS BAR ===
        self.status_bar = MainStatusBar(self)
        self.setStatusBar(self.status_bar)

        # === SIGNAL CONNECTIONS ===
        # Sidebar → scene / actions
        self.sidebar.object_list.currentTextChanged.connect(self.scene.set_object_type)
        self.sidebar.btn_save.clicked.connect(self.save_plan)
        self.sidebar.btn_load.clicked.connect(self.load_plan)

        # Toolbar → actions
        self.toolbar.zoom_in_action.triggered.connect(self.zoom_in)
        self.toolbar.zoom_out_action.triggered.connect(self.zoom_out)
        self.toolbar.toggle_grid_action.triggered.connect(self.toggle_grid)
        self.toolbar.validate_action.triggered.connect(self.validate_layout)

        # Default selection
        if self.sidebar.object_list.count() > 0:
            self.sidebar.object_list.setCurrentRow(0)

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
        self.status_bar.info("Layout validation not implemented yet")

    def save_plan(self):
        self.status_bar.info("Save Plan clicked (not implemented)")

    def load_plan(self):
        self.status_bar.info("Load Plan clicked (not implemented)")
