from PyQt5.QtWidgets import QStatusBar


class MainStatusBar(QStatusBar):
    """Status bar used to display feedback messages to the user."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.showMessage("Ready")

    def info(self, message: str, timeout: int = 2000):
        """Show an informational message for a short time."""
        self.showMessage(message, timeout)
