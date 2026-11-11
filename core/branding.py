import os

from PySide6.QtGui import QFont, QIcon

def get_inter_font(size=10, bold=False):
    font = QFont("Inter", size)
    font.setBold(bold)
    return font

def get_theme_stylesheet():
    return """
    QWidget {
        background-color: #101014;
        color: white;
        font-family: Inter, sans-serif;
        font-size: 10pt;
    }
    QPushButton {
        background-color: #1a1a1a;
        border: 1px solid gray;
        border-radius: 6px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #2a2a2a;
    }
    """

# Single source of truth for where icons live.
RESOURCES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "resources_Local")
)

def get_icon_path(name: str) -> str:
    return os.path.join(RESOURCES_DIR, name)

def get_icon(name: str) -> QIcon:
    return QIcon(get_icon_path(name))
