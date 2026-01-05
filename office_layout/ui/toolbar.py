# file: office_layout/ui/toolbar.py

from PyQt5.QtWidgets import QToolBar, QAction


class MainToolBar(QToolBar):
    """Top toolbar with main layout actions."""

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)

        self.setMovable(False)
        self.setFloatable(False)

        self.zoom_in_action = self.addAction("Zoom In")
        self.zoom_out_action = self.addAction("Zoom Out")

        self.addSeparator()

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.addAction(self.redo_action)

        self.addSeparator()

        # === SELECT TOOL (CURSOR MODE) ===
        # When checked, clicks only select/move items
        self.select_action = QAction("Select", self)
        self.select_action.setCheckable(True)
        self.addAction(self.select_action)

        self.addSeparator()

        # === GRID TOGGLE ===
        self.toggle_grid_action = self.addAction("Toggle Grid")

        self.addSeparator()

        # === VALIDATION ===
        self.validate_action = self.addAction("Validate Layout")

        self.setStyleSheet("""
            QToolBar {
                background-color: #e0e0e0;
                spacing: 6px;
                padding: 4px;
                border: none;
            }
            QToolButton {
                background-color: #ffffff;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #cfd8dc;
            }
        """)
