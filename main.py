import sys
import json
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

from core import window_manager
from core.get_data_path import get_data_path
from core.branding import get_inter_font, get_theme_stylesheet
from core.branding import get_icon
from core.theme_manager import ThemeManager
# type: ignore
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QToolTip
from PySide6.QtWidgets import QGridLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout
from PySide6.QtWidgets import QMenu, QFileDialog, QFileIconProvider, QMessageBox
from PySide6.QtCore import Qt, QRect, QTimer, QSize, QFileInfo, QSettings
from PySide6.QtGui import QIcon, QFont, QColor, QPalette

DEFAULT_LAYOUT = "WEN_Palette_runtime_layout_default.json"
MODE_TIMEOUT_MS = 15000  # add/remove mode cancels itself after this long

class WENPalette(QWidget):

    def set_branding_icon(self, icon_name="WEN_square.ico"):
        if self.theme_mgr:
            icon_path = self.theme_mgr.get_icon_path(icon_name)
            print(f"[DEBUG] Setting branding icon: {icon_path}")

    def __init__(self, json_path, theme_mgr=None):
        super().__init__()

        print("[WEN INIT] Starting init sequence...")

# Apply WEN branding
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1C1F26"))  # vapor_slate
        palette.setColor(QPalette.Button, QColor("#C2C7CC"))  # window_silver
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.WindowText, QColor("#00D1FF"))  # accent_cyan
        palette.setColor(QPalette.Text, Qt.white)
        QApplication.instance().setPalette(palette)
        QApplication.instance().setFont(QFont("Inter", 10))

        self.setWindowFlags(
            Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint
        )
        self.setWindowTitle("WEN")
        title_font = QFont("Poppins", 20, QFont.Bold)
        self.setStyleSheet("QWidget { color: #00D1FF; }")  # Apply window text color
#        self.setWindowIcon(QIcon(get_data_path("gimp.ico")))  # Stubbed WEN logo path

        #        icon_path = RESOURCES / "moon.ico"  # Use paths module



        main_layout = QGridLayout()
        self.setLayout(main_layout)
        self.setContentsMargins(0, 0, 0, 0)  # Window margins
        main_layout.setContentsMargins(4, 0, 0, 0)  # 4 pixels left margin for all widgets
        main_layout.setSpacing(0)  # No default spacing, handled by nested layouts
        self.buttons = []
        self.theme_mgr = theme_mgr
        self.current_theme = "dark"  # or "light", depending on default

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.layout_data = data
        self.layout_path = json_path
        self.assignments = {}  # slot_id -> {"title", "exe_path", "class_name", "hwnd"}
        self.default_icons = {}  # slot_id -> icon file shown while unassigned
        self.current_layout_label = None
        self._icon_provider = QFileIconProvider()

        # Create control layout (row 0) with 2px spacing
        control_layout = QGridLayout()
        control_layout.setSpacing(2)  # 2 pixels between control widgets
        main_layout.addLayout(control_layout, 0, 0, 1, 6)  # Span all 6 columns

        # Create grid layout (rows 1-4) with 10px spacing
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(12,0,0,0)
        grid_layout.setSpacing(12)  # 12 pixels between grid buttons
        main_layout.addLayout(grid_layout, 1, 0, 4, 4)  # 4x4 grid area

        # Create and position all widgets based on JSON data
        # Row 0 using QHBoxLayout
        row0_layout = QHBoxLayout()
        row0_layout.setSpacing(0)  # No default spacing, controlled by spacers
        main_layout.addLayout(row0_layout, 0, 0, 1, 6)  # Span all 6 columns in Row 0

        # Grid rows using QHBoxLayout
        row_layouts = []  # List to hold QHBoxLayout for each grid row
        for i in range(4):  # 4 rows for the grid
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)  # 10px horizontal spacing between grid buttons
            # Add 12px spacer to push buttons right
            spacer = QSpacerItem(10, 40, QSizePolicy.Fixed, QSizePolicy.Expanding)
            row_layout.addItem(spacer)
            row_layouts.append(row_layout)
            grid_layout.addLayout(row_layout, i + 1, 0, 1, 4)  # Grid rows start at 1
            row5_layout = QHBoxLayout()
            row5_layout.setSpacing(0)  # No default spacing, controlled by spacers
            main_layout.addLayout(row5_layout, 5, 0, 1, 6)  # Span all 6 columns in Row 5

        for cell in data["root"]["cells"]:
            w = cell.get("width", 40)
            h = cell.get("height", 40)
            label = cell.get("label", "*")
            tooltip = cell.get("tooltip", "")
            icon_path = cell.get("icon", "WEN_square.ico")  # Default icon if none provided
            slot_id = cell.get("slot_id", "")
            style_class = cell.get("style_class", "unassigned")
            cell_type = cell.get("type", "grid")
#            print(f"Processing cell: slot_id={slot_id}, type={cell_type}")
            # Create widget
            if slot_id == "Current_Layout":
                btn = QLabel(label, self)  # Use QLabel for read-only text
                btn.setFixedSize(130, 20)  # Set desired size
                btn.setStyleSheet("border: 1px solid gray;")  # Add border
                self.current_layout_label = btn  # text is set by _set_current_layout
            else:
                btn = QPushButton(self)
            btn.setProperty("slot_id", slot_id)
            # Override style_class for specific widgets
            if slot_id == "Current_Layout":
                style_class = "info"  # Informational, read-only style
            elif slot_id == "Theme_Toggle":
                style_class = "toggle"  # Binary toggle style
            btn.setProperty("class", style_class)
            btn.slot_id = slot_id
            # Use the 'label' from the layout file for labeling
            if cell_type == "grid" and slot_id.startswith("Button_"):
                btn.setFixedSize(40, 40)  # Grid buttons at 40x40
                self.default_icons[slot_id] = icon_path
                btn.setIcon(QIcon(get_icon(icon_path)))  # Keep icon setup
                btn.setIconSize(QSize(20, 20))  # Smaller icon
                btn.setText("")  # No label for grid buttons
            elif slot_id in ["Load_Layout", "Save_Layout", "Toggle_Layout"]:
                btn.setFixedSize(40, 20)  # 30x20px for these widgets
                btn.setIcon(QIcon(get_icon(icon_path)))  # Keep icon setup (optional until wired)
                btn.setIconSize(QSize(16, 16))  # Adjust icon size to fit
                btn.setText(f"{label.replace('_', ' ')}")  # Temporary label (e.g., "Load Layout")
            elif slot_id in ["Add_window_assignment", "Remove_window_assignment"]:
                btn.setFixedSize(20, 20)  # 15x15px for + and -
                btn.setIcon(QIcon(get_icon(icon_path)))  # Keep icon setup (optional until wired)
                btn.setIconSize(QSize(20, 20))  # Adjust icon size to fit
                btn.setText(f"{label.replace('_', ' ').split()[-1]}")  # Temporary label (e.g., "+")
            elif slot_id == "Theme_Toggle":
                btn.setFixedSize(30, 30)

                print(f"[DEBUG] Theme_Toggle searching at: {icon_path}")
                icon = QIcon(icon_path)



                btn.setIcon(icon)
                if not icon.isNull():
                    print("[DEBUG] Icon loaded")
                else:
                    print("[DEBUG] Icon failed to load")
                btn.setIconSize(QSize(28, 28))
                btn.setText("")
                btn.setStyleSheet("background-color: #1C1F26; qproperty-iconSize: 28px;")
                btn.setIcon(icon)  # Reapply to ensure default
                current_icon = btn.icon()
                print(f"[DEBUG] Post-setup icon: {current_icon.cacheKey() if not current_icon.isNull() else 'null'}")
                btn.clicked.connect(self.update_toggle_icon)
                print(f"[DEBUG] Theme_Toggle connected for {slot_id}")

            # Position in appropriate layout
            if cell_type == "grid" and slot_id.startswith("Button_"):
                button_num = int(slot_id.replace("Button_", ""))
                row = (button_num - 1) // 4
                col = (button_num - 1) % 4
                row_layouts[row].addWidget(btn)  # Add to the corresponding row's HBox
                if col <3:
                    spacer = QSpacerItem(6, 40, QSizePolicy.Fixed, QSizePolicy.Minimum)  # 12px horizontal spacer
                    row_layouts[row].addItem(spacer)
            else:  # Control widgets (Row 0 and Row 5)
                if slot_id == "Load_Layout":
                    row0_layout.addWidget(btn)
                elif slot_id == "Save_Layout":
                    # Add 4px spacer between Load and Save
                    spacer = QSpacerItem(4, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
                    row0_layout.addItem(spacer)
                    row0_layout.addWidget(btn)
                elif slot_id == "Add_window_assignment":
                    spacer = QSpacerItem(4, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
#                    print(f"Processing widget : slot_id={slot_id}")
                    row0_layout.addItem(spacer)
                    row0_layout.addWidget(btn)
                elif slot_id == "Remove_window_assignment":
                    # Add 4px spacer between + and -
#                    print(f"Processing widget : slot_id={slot_id}")
                    spacer = QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
                    row0_layout.addItem(spacer)
                    row0_layout.addWidget(btn)
                elif slot_id == "Toggle_Layout":
                    # Add 10px spacer between - and Toggle
                    spacer = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
                    row0_layout.addItem(spacer)
                    row0_layout.addWidget(btn)
                elif slot_id == "Current_Layout":
                    btn.setFixedWidth(150)  # Keep current width
                    row5_layout.addWidget(btn)  # Add to Row 5 layout
                    spacer_right = QSpacerItem(25, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)  # Spacer to push Theme_Toggle
                    row5_layout.addItem(spacer_right)
                elif slot_id == "Theme_Toggle":
                    spacer_left = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)  # Optional left spacer
                    row5_layout.addItem(spacer_left)
                    row5_layout.addWidget(btn)  # Add to Row 5 layout
#                   Apply specific properties
            if slot_id == "Border":
                btn.setEnabled(False)
                btn.setFocusPolicy(Qt.NoFocus)
            elif slot_id.startswith("Button_"):
                btn.setFocusPolicy(Qt.NoFocus)
            elif slot_id == "Theme_Toggle" and self.theme_mgr:     #    < -----
                btn.clicked.connect(self.theme_mgr.toggle_theme)
            elif slot_id == "Add_window_assignment":
                btn.clicked.connect(self.toggle_window_assignment_mode)
            elif slot_id == "Remove_window_assignment":
                btn.clicked.connect(self.toggle_remove_assignment_mode)
            elif slot_id == "Load_Layout":
                btn.clicked.connect(self.load_layout)
            elif slot_id == "Save_Layout":
                btn.clicked.connect(self.save_layout)
            if tooltip:
                btn.setToolTip(tooltip)

            self.buttons.append(btn)

        # Every grid button shares one handler; what a click does depends on
        # the current mode and on whether the slot has a window assigned.
        for btn in self._grid_buttons():
            btn.clicked.connect(lambda _, b=btn: self._on_grid_button(b))

        # Set layout constraints with 10px vertical spacing
        main_layout.setVerticalSpacing(10)  # 10px between rows
        for i in range(6):  # 6 rows
            main_layout.setRowMinimumHeight(i, 1)  # Default minimum height
        for i in range(6):  # 6 columns
            main_layout.setColumnMinimumWidth(i, 1)  # Default minimum width

        # Fix grid rows (1-4) to 40px height each, accounting for spacing
        for i in range(1, 5):  # Rows 1 to 4 for the 4x4 grid
            main_layout.setRowMinimumHeight(i, 40)
            main_layout.setRowStretch(i, 0)  # No stretching for grid rows

        # Allow grid_layout to adapt
        for i in range(4):  # Columns 0 to 3
            grid_layout.setColumnStretch(i, 1)

        # Allow remaining space to stretch for controls and bottom row
        main_layout.setRowStretch(0, 1)  # Row 0 (controls) can stretch
        main_layout.setRowStretch(5, 1)  # Row 5 (bottom row) can stretch
        main_layout.setColumnStretch(5, 1)  # Column 5 (for L/D) can stretch

#        self.adjustSize()  # Let the layout determine the minimum size
        self.setFixedSize(255, 275)

#  This is the boundary

        # "add" (after '+') and "remove" (after '-') are mutually exclusive
        # modes that end on the next grid click or after MODE_TIMEOUT_MS.
        self.mode = None
        self.mode_timer = QTimer(self)
        self.mode_timer.setSingleShot(True)
        self.mode_timer.timeout.connect(self._end_mode)

        self._apply_assignments(data)
        self._set_current_layout(json_path, remember=False)

        print("[WEN INIT] Layout setup complete.")

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _grid_buttons(self):
        return [b for b in self.buttons if b.slot_id.startswith("Button_")]

    def _button(self, slot_id):
        return next((b for b in self.buttons if b.slot_id == slot_id), None)

    def _set_class(self, btn, cls):
        """Change the QSS class of a button and force a restyle."""
        btn.setProperty("class", cls)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()

    def _hint(self, btn, text):
        if btn is not None:
            QToolTip.showText(btn.mapToGlobal(btn.rect().center()), text, btn)

    def _exe_icon(self, exe_path):
        """The program's own icon, or the WEN logo if it can't be read."""
        if exe_path and os.path.isfile(exe_path):
            icon = self._icon_provider.icon(QFileInfo(exe_path))
            if not icon.isNull():
                return icon
        return get_icon("WEN_square.ico")

    # ------------------------------------------------------------------
    # Add / remove modes
    # ------------------------------------------------------------------
    def toggle_window_assignment_mode(self):
        self._toggle_mode("add")

    def toggle_remove_assignment_mode(self):
        self._toggle_mode("remove")

    def _toggle_mode(self, mode):
        previous = self.mode
        self._end_mode()
        if previous != mode:
            self._begin_mode(mode)

    def _begin_mode(self, mode):
        removing = mode == "remove"
        targets = [b for b in self._grid_buttons()
                   if (b.slot_id in self.assignments) == removing]
        if not targets:
            if removing:
                self._hint(self._button("Remove_window_assignment"), "No buttons are assigned yet")
            else:
                self._hint(self._button("Add_window_assignment"), "Every button is already assigned")
            return
        self.mode = mode
        for btn in targets:
            self._set_class(btn, "assigned highlight" if removing else "unassigned highlight")
        self.mode_timer.start(MODE_TIMEOUT_MS)

    def _end_mode(self):
        self.mode = None
        self.mode_timer.stop()
        for btn in self._grid_buttons():
            self._set_class(btn, "assigned" if btn.slot_id in self.assignments else "unassigned")

    def _on_grid_button(self, btn):
        assigned = btn.slot_id in self.assignments
        if self.mode == "add":
            if assigned:
                self._hint(btn, "Already assigned - pick a highlighted button")
                return
            self._end_mode()
            self.assign_window(btn)
        elif self.mode == "remove":
            if not assigned:
                self._hint(btn, "Nothing assigned here - pick a highlighted button")
                return
            self._end_mode()
            self._clear_assignment(btn)
        elif assigned:
            self.focus_assigned_window(btn)
        else:
            self._hint(btn, "Click '+', then this button, to assign a window")

    # ------------------------------------------------------------------
    # Window assignment and focus
    # ------------------------------------------------------------------
    def assign_window(self, btn):
        """Let the user pick one of the open windows for this button."""
        windows = [w for w in window_manager.list_windows() if w.exe_path]
        if not windows:
            self._hint(btn, "No open windows found")
            return

        menu = QMenu(self)
        for w in windows:
            title = w.title if len(w.title) <= 60 else w.title[:57] + "..."
            menu.addAction(self._exe_icon(w.exe_path), title).setData(w)
        chosen = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        if chosen is None:
            return

        w = chosen.data()
        self._set_assignment(btn, {
            "title": w.title,
            "exe_path": w.exe_path,
            "class_name": w.class_name,
            "hwnd": w.hwnd,  # this session only; never saved
        })

    def _set_assignment(self, btn, assignment):
        self.assignments[btn.slot_id] = assignment
        btn.setToolTip(assignment["title"])
        btn.setIcon(self._exe_icon(assignment["exe_path"]))
        btn.setIconSize(QSize(28, 28))
        self._set_class(btn, "assigned")

    def _clear_assignment(self, btn):
        self.assignments.pop(btn.slot_id, None)
        btn.setToolTip("Unassigned")
        btn.setIcon(get_icon(self.default_icons.get(btn.slot_id, "Default.ico")))
        btn.setIconSize(QSize(20, 20))
        self._set_class(btn, "unassigned")

    def focus_assigned_window(self, btn):
        assignment = self.assignments[btn.slot_id]
        name = Path(assignment["exe_path"]).stem
        hwnd = window_manager.find_window(assignment)
        if hwnd is None:
            self._hint(btn, f"{name} is not open")
            return
        assignment["hwnd"] = hwnd
        if not window_manager.focus_window(hwnd):
            self._hint(btn, f"Could not switch to {name}")

    # ------------------------------------------------------------------
    # Layout save / load
    # ------------------------------------------------------------------
    def _apply_assignments(self, data):
        """Set every grid button from the 'window' entries in a layout."""
        cells = {c.get("slot_id"): c for c in data["root"]["cells"] if isinstance(c, dict)}
        for btn in self._grid_buttons():
            window = cells.get(btn.slot_id, {}).get("window")
            if isinstance(window, dict) and window.get("exe_path"):
                self._set_assignment(btn, {
                    "title": window.get("title", ""),
                    "exe_path": window["exe_path"],
                    "class_name": window.get("class_name", ""),
                })
            else:
                self._clear_assignment(btn)

    def _set_current_layout(self, path, remember=True):
        self.layout_path = str(path)
        label = self.current_layout_label
        if label is not None:
            stem = Path(path).stem
            label.setText(label.fontMetrics().elidedText(stem, Qt.ElideMiddle, label.width() - 8))
            label.setToolTip(str(path))
        if remember:
            QSettings("CTS", "WEN").setValue("last_layout", str(path))

    def save_layout(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save layout", self.layout_path, "WEN layout (*.json)")
        if not path:
            return
        try:
            self.write_layout(path)
        except OSError as e:
            QMessageBox.warning(self, "WEN", f"Could not save layout:\n{e}")

    def write_layout(self, path):
        for cell in self.layout_data["root"]["cells"]:
            slot_id = cell.get("slot_id", "")
            if not slot_id.startswith("Button_"):
                continue
            assignment = self.assignments.get(slot_id)
            if assignment:
                cell["style_class"] = "assigned"
                cell["action"] = "focus_window"
                cell["tooltip"] = assignment["title"]
                cell["window"] = {k: assignment[k] for k in ("title", "exe_path", "class_name")}
            else:
                cell["style_class"] = "unassigned"
                cell["action"] = "unassigned"
                cell["tooltip"] = "Unassigned"
                cell.pop("window", None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.layout_data, f, indent=2)
        self._set_current_layout(path)

    def load_layout(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load layout", os.path.dirname(self.layout_path), "WEN layout (*.json)")
        if path:
            self.read_layout(path)

    def read_layout(self, path, quiet=False):
        """Apply the assignments stored in a layout file. Returns success."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data["root"]["cells"], list):
                raise ValueError("'root.cells' is not a list")
        except (OSError, ValueError, KeyError, TypeError) as e:
            if not quiet:
                QMessageBox.warning(self, "WEN", f"Could not load layout:\n{e}")
            return False
        self._end_mode()
        self._apply_assignments(data)
        self._set_current_layout(path)
        return True

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def toggle_theme_mode(self):
        self.current_theme = self.toggle_theme(self.current_theme, self)
        icon_path = self.get_icon_path("moon")
        self.theme_toggle_btn.setIcon(QIcon(icon_path))

    def update_toggle_icon(self):
        if not self.theme_mgr:
            return
        icon_name = "sun.ico" if self.current_theme == "light" else "moon.ico"
        icon_path = self.theme_mgr.get_icon_path(icon_name)
        for btn in self.buttons:
            if btn.slot_id == "Theme_Toggle":
                btn.setIcon(QIcon(icon_path))
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = WENPalette(get_data_path(DEFAULT_LAYOUT))
    theme_mgr = ThemeManager(app, window)
    window.theme_mgr = theme_mgr
    window.set_branding_icon()
    theme_mgr.load_theme("dark_theme_wen")

    # Reopen whichever layout was last saved or loaded.
    last_layout = QSettings("CTS", "WEN").value("last_layout", "")
    if last_layout and os.path.isfile(last_layout):
        window.read_layout(last_layout, quiet=True)

    window.show()
    sys.exit(app.exec())
