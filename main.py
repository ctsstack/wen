import sys
import json
import os
import random
sys.path.insert(0, os.path.dirname(__file__))

from core.get_data_path import get_data_path
from core.branding import get_inter_font, get_theme_stylesheet
from core.branding import get_icon, get_icon_path, RESOURCES_DIR
from core.theme_manager import ThemeManager
from core.theme_utils import highlight_buttons, clear_highlights
# type: ignore
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QToolTip
from PySide6.QtWidgets import QGridLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout
from PySide6.QtCore import Qt, QRect, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QColor, QPalette

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
                btn.setText(label.replace('_', ' ').split()[-1] if label else "(no file selected)")  # Set text from label or default
                btn.setStyleSheet("border: 1px solid gray;")  # Add border
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
                btn.clicked.connect(self.highlight_remove_assignment)
#               Tooltip handling
            if tooltip:
                def make_tooltip_handler(button, text):
                    def show_tooltip():
                        QToolTip.showText(button.mapToGlobal(button.rect().center()), text)
                    return show_tooltip
                btn.enterEvent = lambda event, f=make_tooltip_handler(btn, tooltip): QTimer.singleShot(800, f)

            self.buttons.append(btn)

        # Connect unassigned buttons
        for btn in self.buttons:
            if btn.property("class") == "unassigned":
                btn.clicked.connect(lambda _, b=btn: self.assign_window(b))

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

        # Initialize add_mode and timers
        self.add_mode = False
        self.add_timer = QTimer()
        self.add_timer.setSingleShot(True)
        self.add_timer.timeout.connect(lambda: clear_highlights(self.buttons))

        self.highlight_timer = QTimer()
        self.highlight_timer.setSingleShot(True)
        self.highlight_active = False
        self.highlight_timer.timeout.connect(self.cancel_highlight)

        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(500)
        self.pulse_timer.timeout.connect(self._toggle_pulse)
        self.pulse_state = False

#        print(f"Layout contains {main_layout.count()} widgets")
        print("[WEN INIT] Layout setup complete.")
#
#
    def toggle_window_assignment_mode(self):
        print(f"[+] Add window assignment mode toggled. Active? {self.highlight_active}")

        if self.highlight_active:
            self._deactivate_highlight()
        else:
            self._activate_highlight()



    def assign_window(self, btn):
        # Stub for now: simulate assigning a dummy app / ico
        print("f self.highlight_active")
        if not self.highlight_active:
            print("Use the '+' button to associate a window with this button")
            return

        print(f">> Assigning window to: {btn.slot_id}")

        # Simulate the assigned window/app metadata  The CWT DB will be the ultimate source for this info
        used_icons = [v.get("icon", "") for v in self.layout_data.values() if isinstance(v, dict)]
        random_icon = self.get_unused_icon(used_icons)

        icon_path = get_icon_path(random_icon or "WEN_square.ico")

        assigned_window = {
            "name": "ExampleApp",
            "exe_path": "C:/Path/To/ExampleApp.exe",
            "icon": random_icon,
            "tooltip": "ExampleApp"
    }
        # Apply metadata to the button
        btn.setProperty("class", "assigned")
        btn.setToolTip(assigned_window["tooltip"])
        btn.setText("")  # clear numeric label
#       btn.setIcon(QIcon(assigned_window["icon_path"]))
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(btn.size())

        # Optionally store the metadata
        self.layout_data[btn.slot_id] = assigned_window

        # Refresh style
        btn.style().unpolish(btn)
        btn.style().polish(btn)

        # Exit window assignment mode
        self._deactivate_highlight()

    def _activate_highlight(self):
#        print(" ENTERING activate_highlight")
        self.highlight_active = True
        self._apply_class_to_unassigned("unassigned highlight")  # <== changed
        self.highlight_timer.start(15000)
#        self.pulse_timer.start(500)
#        print(f">> highlight_active SET TO: {self.highlight_active}")

    def _deactivate_highlight(self):
#        print(" ENTERING deactivate_highlight")
        self.highlight_active = False
        self.highlight_timer.stop()
        self._apply_class_to_unassigned("unassigned")
        self.pulse_timer.stop()
#        print(f">> highlight_active SET TO: {self.highlight_active}")

    def _apply_class_to_unassigned(self, cls):
        for btn in self.buttons:
            if btn.property("class") in ["unassigned", "unassigned highlight"]:
                print(f"Updating {btn.slot_id} → {cls}")
                btn.setProperty("class", cls)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()

    def cancel_highlight(self):
        for btn in self.buttons:
            if btn.property("class") == "unassigned highlight":
                btn.setProperty("class", "unassigned")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        self.highlight_timer.stop()
        self.highlight_active = False
        self.pulse_timer.stop()

    def highlight_remove_assignment(self):
        """Highlight assigned buttons after '-' is clicked."""
        highlight_buttons(
        [b for b in self.buttons if b.slot_id.startswith("Button_")],
        lambda b: b.property("class") != "unassigned"
    )

    def clear_all_highlights(self):
        """Reset buttons to original style_class from layout data."""
        clear_highlights(
        [b for b in self.buttons if b.slot_id.startswith("Button_")],
        lambda b: self.layout_data.get(b.slot_id, {}).get("style_class", "primary")
    )
# Define the method inside WENPalette
    def _toggle_pulse(self):
        for btn in self.buttons:
            if btn.property("class") == "unassigned highlight":
                style = "unassigned highlight pulse" if self.pulse_state else "unassigned highlight"
                btn.setProperty("class", style)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            self.pulse_state = not self.pulse_state

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

    def get_unused_icon(self, existing_icons, icon_folder=RESOURCES_DIR):
        all_icons = [f for f in os.listdir(icon_folder) if f.endswith(".ico")]
        unused = list(set(all_icons) - set(existing_icons))
        if not unused:
            print("[INFO] All icons are used.")
            return None
        return random.choice(unused)

if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = WENPalette(get_data_path("WEN_palette_runtime_layout_default.json"))
    theme_mgr = ThemeManager(app, window)
    window.theme_mgr = theme_mgr
    window.set_branding_icon()
    theme_mgr = ThemeManager(app, window)
    window.theme_mgr = theme_mgr
    theme_mgr.load_theme("dark_theme_wen")

    window.show()
    QTimer.singleShot(60000, app.quit)
    sys.exit(app.exec())