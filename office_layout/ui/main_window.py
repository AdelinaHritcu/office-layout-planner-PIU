# file: office_layout/ui/main_window.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QGraphicsView
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

from office_layout.graphics.scene import OfficeScene
from office_layout.ui.toolbar import MainToolBar
from office_layout.ui.statusbar import MainStatusBar
from office_layout.ui.sidebar import Sidebar
from office_layout.models.layout_model import LayoutModel
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from office_layout.storage.json_io import save_layout, load_layout
from office_layout.algorithms.validation import validate_layout as run_validation



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
        # Create the logical model of the room
        self.layout_model = LayoutModel(
            room_width=900,       # should match sceneRect width
            room_height=600,      # should match sceneRect height
            grid_size=40.0,
        )
        self.layout_model.exit_points = [{"x": 899.0, "y": 300.0}]

        # Pass the model to the scene (and this window as Qt parent)
        self.scene = OfficeScene(layout_model=self.layout_model, parent=self)

        # Graphics view that displays the scene
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
        try:
            self.scene.sync_model_from_items()
            errors = run_validation(self.layout_model)
        except Exception as e:
            QMessageBox.critical(self, "Validation error", str(e))
            self.status_bar.info("Validation failed")
            return

        if not errors:
            QMessageBox.information(self, "Validation", "Layout is valid.")
            self.status_bar.info("Layout valid")
            return

        lines = []
        for idx, err in enumerate(errors[:25], start=1):
            lines.append(f"{idx}. [{err.code}] {err.message}")
        if len(errors) > 25:
            lines.append(f"... and {len(errors) - 25} more.")

        QMessageBox.warning(self, "Validation issues", "\n".join(lines))
        self.status_bar.info(f"Validation: {len(errors)} issue(s)")

    def save_plan(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save layout", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            self.status_bar.info("Save cancelled")
            return

        try:
            self.scene.sync_model_from_items()
            save_layout(path, self.layout_model)
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))
            self.status_bar.info("Save failed")
            return

        self.status_bar.info(f"Saved: {path}")

    def load_plan(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open layout",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            self.status_bar.info("Open cancelled")
            return

        try:
            model = load_layout(path)
        except Exception as e:
            QMessageBox.critical(self, "Open error", str(e))
            self.status_bar.info("Open failed")
            return

        self._apply_loaded_model(model)
        self.status_bar.info(f"Loaded: {path}")

    def _apply_loaded_model(self, model: LayoutModel) -> None:
        """
        Replace current model with the loaded one and rebuild the scene from it.
        """
        self.layout_model = model

        # Prefer set_model (single authoritative rebuild path)
        if hasattr(self.scene, "set_model") and callable(getattr(self.scene, "set_model")):
            self.scene.set_model(model)
            return

        # Fallback: recreate scene if set_model does not exist
        self._recreate_scene(model)

    def _recreate_scene(self, model: LayoutModel) -> None:
        """
        Fallback robust: recreeaza scene + reconecteaza view-ul.
        """
        old_scene = self.scene
        self.scene = OfficeScene(layout_model=model, parent=self)

        self.view.setScene(self.scene)

        # reconectare signal sidebar -> scene
        try:
            self.sidebar.object_list.currentTextChanged.disconnect()
        except Exception:
            pass
        self.sidebar.object_list.currentTextChanged.connect(self.scene.set_object_type)

        # pastreaza setarile de grid (daca vrei)
        if hasattr(old_scene, "show_grid") and hasattr(self.scene, "show_grid"):
            self.scene.show_grid = getattr(old_scene, "show_grid")

        # optional: elibereaza vechiul scene
        old_scene.deleteLater()

