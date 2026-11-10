import os
from PySide6.QtGui import QIcon

from core.branding import RESOURCES_DIR

class ThemeManager:
    def __init__(self, app, window):
        self.app = app
        self.window = window
        self.current_theme = "dark"

    def get_qss_path(self, name: str) -> str:
        if not name.endswith(".qss"):
            name += ".qss"
        path = os.path.join(os.path.dirname(__file__), name)
        if not os.path.isfile(path):
            print(f"[ERROR] Theme file not found: {path}")
            return None
        return path

    def load_theme(self, theme_name: str):
        qss_file = self.get_qss_path(f"{theme_name}.qss")
        with open(qss_file, "r") as f:
            self.app.setStyleSheet(f.read())
        self.current_theme = theme_name
        self.update_theme_icon()

    def toggle_theme(self):
        next_theme = "light" if self.current_theme == "dark" else "dark"
        self.load_theme(next_theme)

    def update_theme_icon(self):
        icon_name = "sun.ico" if self.current_theme == "light" else "moon.ico"
        icon_path = self.get_icon_path(icon_name)
        self.window.update_toggle_icon()

    def get_icon_path(self, icon_name):
        if not icon_name.endswith(".ico") and not icon_name.endswith(".png"):
            icon_name += ".png"  # default to .png if no extension provided

        return os.path.join(RESOURCES_DIR, icon_name)


