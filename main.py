import sys
import os
import pyautogui as pyg
from typing import List, Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QFileDialog, QLabel, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt

from button import FloatingButton, MouseController

class ActionManagerWindow(QMainWindow):
    """Window to add/manage actions (type + parameter) and spawn floating buttons bound to them."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Action Manager")
        self.setMinimumSize(480, 360)

        self._actions: List[Dict[str, str]] = []  # each: {'name': str, 'type': str, 'param': str}

        central = QWidget()
        self.setCentralWidget(central)
        main_l = QVBoxLayout(central)

        # list of actions
        self.list_widget = QListWidget()
        main_l.addWidget(QLabel("Actions (type -> param):"))
        main_l.addWidget(self.list_widget, stretch=1)

        # controls: param input + choose (used for image)
        ctrl_row = QHBoxLayout()
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("Parameter (image path or text)...")
        ctrl_row.addWidget(self.param_input)
        self.choose_btn = QPushButton("Choose...")
        self.choose_btn.clicked.connect(self.choose_image)
        ctrl_row.addWidget(self.choose_btn)
        main_l.addLayout(ctrl_row)

        # type selector + name input + add button
        type_row = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["image", "write"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Action name (optional)")
        type_row.addWidget(self.name_input)

        add_btn = QPushButton("Add Action")
        add_btn.clicked.connect(self.add_action)
        type_row.addWidget(add_btn)
        main_l.addLayout(type_row)

        # bottom controls: spawn floating, remove action
        bottom_row = QHBoxLayout()
        spawn_btn = QPushButton("Create Floating Button for Selected")
        spawn_btn.clicked.connect(self.create_floating_for_selected)
        bottom_row.addWidget(spawn_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected)
        bottom_row.addWidget(remove_btn)

        main_l.addLayout(bottom_row)

        main_l.addWidget(QLabel("Select an action then press 'Create Floating Button...' to spawn a floating controller."))

        # store floating buttons to avoid GC
        self._floating_buttons: List[FloatingButton] = []

        # initial UI state
        self._on_type_changed(self.type_combo.currentText())

    def _on_type_changed(self, t: str):
        """Toggle choose button visibility and placeholder based on action type."""
        if t == "image":
            self.choose_btn.setVisible(True)
            self.param_input.setPlaceholderText("Path to image file (png/jpg/bmp)...")
        else:
            self.choose_btn.setVisible(False)
            self.param_input.setPlaceholderText("Text to write when action runs...")

    def choose_image(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select image", "", "Images (*.png *.jpg *.bmp *.gif)")
        if p:
            self.param_input.setText(p)

    def add_action(self):
        param = self.param_input.text().strip()
        atype = self.type_combo.currentText()
        name = self.name_input.text().strip() or (os.path.basename(param) if param else f"Action {len(self._actions)+1}")

        # validate
        if atype == "image":
            if not param:
                QMessageBox.warning(self, "Missing image", "Please provide an image path for the action.")
                return
            if not os.path.exists(param):
                QMessageBox.warning(self, "File not found", f"Image file not found:\n{param}")
                return
        else:  # write
            if not param:
                QMessageBox.warning(self, "Missing text", "Please provide the text to write for this action.")
                return

        entry = {'name': name, 'type': atype, 'param': param}
        self._actions.append(entry)
        self.list_widget.addItem(f"{name} [{atype}] — {param}")
        self.param_input.clear()
        self.name_input.clear()

    def remove_selected(self):
        idx = self.list_widget.currentRow()
        if idx >= 0:
            self.list_widget.takeItem(idx)
            del self._actions[idx]

    def create_floating_for_selected(self):
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self._actions):
            QMessageBox.information(self, "Select action", "Please select an action from the list first.")
            return

        sequence = [dict(a) for a in self._actions[idx:]]  

        geom = self.geometry()
        spawn_pos = (geom.x() + geom.width() + 10, geom.y() + 30)

        fb = FloatingButton(diameter=50, initial_pos=spawn_pos)
        fb.action_sequence = sequence

        fb.show()
        self._floating_buttons.append(fb)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ActionManagerWindow()
    w.show()
    sys.exit(app.exec())