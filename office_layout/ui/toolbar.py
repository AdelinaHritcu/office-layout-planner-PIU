from PyQt5.QtWidgets import QToolBar


class MainToolBar(QToolBar):
    """Top toolbar with main layout actions."""

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)

        self.setMovable(False)
        self.setFloatable(False)

        self.zoom_in_action = self.addAction("Zoom In")
        self.zoom_out_action = self.addAction("Zoom Out")

        self.addSeparator()

        self.toggle_grid_action = self.addAction("Toggle Grid")

        self.addSeparator()

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
