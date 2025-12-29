import sys
import os
import pyautogui as pyg
from typing import List, Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QFileDialog, QLabel, QMessageBox, QComboBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QSpacerItem, QSizePolicy

from button import FloatingButton, MouseController
from storage import load_actions, save_actions

class ActionManagerWindow(QMainWindow):
    """Window to add/manage actions (type + parameter) and spawn floating buttons bound to them.
    Dark theme / modern styling.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Bot Aplications")
        self.setMinimumSize(720, 420)

        # global font
        app_font = QFont("Segoe UI", 10)
        self.setFont(app_font)

        # Dark Palette
        MAIN_BG = "#0B1220"        # page background
        CARD_BG = "#0F1A2B"        # panels / cards
        PANEL_BORDER = "#293241"   # subtle border
        PRIMARY = "#1E90FF"        # primary blue (accent)
        ACCENT = "#0A68FF"
        MUTED = "#94A3B8"          # muted text
        TEXT = "#E6EEF3"           # main text color
        INPUT_BG = "#0B1320"

        # central widget + layout
        central = QWidget()
        central.setStyleSheet(f"background: {MAIN_BG}; color: {TEXT};")  # apply main background + text color
        self.setCentralWidget(central)
        main_l = QVBoxLayout(central)
        main_l.setContentsMargins(16, 12, 16, 12)
        main_l.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Autobot Action Aplications")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT};")
        subtitle = QLabel("Manage actions and create bot controls")
        subtitle.setStyleSheet(f"color: {MUTED};")
        header_row.addWidget(title)
        header_row.addSpacing(8)
        header_row.addWidget(subtitle)
        header_row.addStretch()
        main_l.addLayout(header_row)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setStyleSheet(f"color: {PANEL_BORDER};")
        main_l.addWidget(sep)

        # content: left = list, right = controls
        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        # left: action list
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        lbl_actions = QLabel("Actions")
        lbl_actions.setStyleSheet(f"color: {TEXT}; font-weight: 600;")
        left_col.addWidget(lbl_actions)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet(
            f"QListWidget {{ background: {CARD_BG}; border: 1px solid {PANEL_BORDER}; border-radius: 8px; padding: 6px; color: {TEXT}; }}"
            f"QListWidget::item {{ padding: 10px; color: {TEXT}; }}"
            f"QListWidget::item:selected {{ background: rgba(30,144,255,0.14); color: {TEXT}; }}"
        )
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        left_col.addWidget(self.list_widget, stretch=1)

        list_controls = QHBoxLayout()
        self.move_up_btn = QPushButton("↑")
        self.move_down_btn = QPushButton("↓")
        self.move_up_btn.setToolTip("Move action up")
        self.move_down_btn.setToolTip("Move action down")
        for b in (self.move_up_btn, self.move_down_btn):
            b.setFixedSize(36, 32)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{border-radius:6px;background:{CARD_BG};border:1px solid {PANEL_BORDER}; color:{TEXT};}} "
                f"QPushButton:hover{{background:#142033}}"
            )
        self.move_up_btn.clicked.connect(self._move_selected_up)
        self.move_down_btn.clicked.connect(self._move_selected_down)
        list_controls.addWidget(self.move_up_btn)
        list_controls.addWidget(self.move_down_btn)
        list_controls.addStretch()
        left_col.addLayout(list_controls)

        content_row.addLayout(left_col, stretch=2)

        # right: control panel
        right_col = QVBoxLayout()
        right_col.setSpacing(10)
        panel = QWidget()
        panel.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        panel.setEnabled(True)
        panel_l = QVBoxLayout(panel)
        panel_l.setContentsMargins(12, 12, 12, 12)
        panel.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {MAIN_BG}, stop:1 {CARD_BG}); "
            f"border: 1px solid {PANEL_BORDER}; border-radius: 10px;"
        )

        panel_lbl= QLabel("New action")
        panel_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600;")
        right_col.addWidget(panel_lbl)

        # type + name
        row1 = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["image", "write"])
        self.type_combo.setFixedWidth(110)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        # dark styling for combo
        self.type_combo.setStyleSheet(
            f"QComboBox{{background:{INPUT_BG}; color:{TEXT}; border:1px solid {PANEL_BORDER}; padding:6px; border-radius:6px;}}"
            f"QComboBox::drop-down{{border:0;background:transparent;}}"
            f"QComboBox QAbstractItemView{{background:{CARD_BG}; color:{TEXT}; selection-background-color: rgba(30,144,255,0.14);}}"
        )
        row1.addWidget(self.type_combo)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Optional action name")
        # dark styling for name input
        self.name_input.setStyleSheet(
            f"QLineEdit{{background:{INPUT_BG}; color:{TEXT}; border:1px solid {PANEL_BORDER}; border-radius:6px; padding:6px;}}"
        )
        row1.addWidget(self.name_input)
        panel_l.addLayout(row1)

        # param row
        param_row = QHBoxLayout()
        self.param_input = QLineEdit()
        self.param_input.setEnabled(True)
        self.param_input.setPlaceholderText("Parameter (image path or text)...")
        # dark-themed input styling
        self.param_input.setStyleSheet(
            f"QLineEdit{{background:{INPUT_BG}; color:{TEXT}; border:1px solid {PANEL_BORDER}; border-radius:6px; padding:6px;}}"
        )
        param_row.addWidget(self.param_input)

        self.choose_btn = QPushButton("Choose")
        self.choose_btn.setEnabled(True)
        self.choose_btn.setCursor(Qt.PointingHandCursor)
        self.choose_btn.clicked.connect(self.choose_image)
        self.choose_btn.setFixedHeight(30)
        # dark styling for choose button
        self.choose_btn.setStyleSheet(
            f"QPushButton{{background:{CARD_BG}; color:{TEXT}; border:1px solid {PANEL_BORDER}; border-radius:6px; padding:6px;}} "
            "QPushButton:hover{background:#142033}"
        )
        param_row.addWidget(self.choose_btn)
        panel_l.addLayout(param_row)

        # add button
        add_row = QHBoxLayout()
        add_btn = QPushButton("Add Action")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(f"QPushButton{{background:{ACCENT};color:white;border-radius:8px;}} QPushButton:hover{{background:#055ED6}}")
        add_btn.clicked.connect(self.add_action)
        add_row.addWidget(add_btn)
        panel_l.addLayout(add_row)

        # spacer
        panel_l.addItem(QSpacerItem(20, 8, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # spawn / remove (vertical stacked, larger)
        ops_col = QVBoxLayout()
        ops_col.setSpacing(10)
        # larger primary button
        spawn_btn = QPushButton("Create Floating Button")
        spawn_btn.setCursor(Qt.PointingHandCursor)
        spawn_btn.setFixedHeight(46)
        spawn_btn.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:{TEXT};border-radius:10px;padding:8px 12px;font-weight:600;}}"
            f"QPushButton:hover{{background:{ACCENT}}}"
        )
        spawn_btn.clicked.connect(self.create_floating_for_selected)
        ops_col.addWidget(spawn_btn)

        # larger danger button
        remove_btn = QPushButton("Remove Selected")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setFixedHeight(40)
        remove_btn.setStyleSheet(
            f"QPushButton{{background:#D14343;color:{TEXT};border-radius:8px;padding:6px;font-weight:600;}}"
            "QPushButton:hover{background:#B93232}"
        )
        remove_btn.clicked.connect(self.remove_selected)
        ops_col.addWidget(remove_btn)

        panel_l.addLayout(ops_col)

        right_col.addWidget(panel)
        content_row.addLayout(right_col, stretch=1)

        main_l.addLayout(content_row)

        # footer hint
        footer = QLabel("Tip: select an action and create a floating button — the floating button will run actions in sequence.")
        footer.setStyleSheet(f"color: {MUTED};")
        main_l.addWidget(footer)

        # store floating buttons to avoid GC
        self._floating_buttons: List[FloatingButton] = []

        # load saved actions AFTER widgets created
        self._actions: List[Dict[str, str]] = load_actions()
        for a in self._actions:
            name = a.get("name", "")
            atype = a.get("type", "")
            param = a.get("param", "")
            self.list_widget.addItem(f"{name} [{atype}] — {param}")

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
        save_actions(self._actions)

        self.param_input.clear()
        self.name_input.clear()

    def remove_selected(self):
        idx = self.list_widget.currentRow()
        if idx >= 0:
            self.list_widget.takeItem(idx)
            del self._actions[idx]
            save_actions(self._actions)

    def create_floating_for_selected(self):
        
        # require at least one action selected (or inform user)
        idx = self.list_widget.currentRow()
        if idx < 0 or not self._actions:
            QMessageBox.information(self, "Select action", "Please select an action from the list first.")
            return

        # Execute actions in the exact order shown in the list (top -> bottom)
        sequence = [dict(a) for a in self._actions]  # copy current order

        geom = self.geometry()
        spawn_pos = (geom.x() + geom.width() + 10, geom.y() + 30)

        fb = FloatingButton(diameter=50, initial_pos=spawn_pos)
        fb.action_sequence = sequence
        fb.show()
        self._floating_buttons.append(fb)

    def _move_selected_up(self):
        idx = self.list_widget.currentRow()
        if idx > 0:
            self._actions[idx - 1], self._actions[idx] = self._actions[idx], self._actions[idx - 1]
            item = self.list_widget.takeItem(idx)
            self.list_widget.insertItem(idx - 1, item)
            self.list_widget.setCurrentRow(idx - 1)
            save_actions(self._actions)

    def _move_selected_down(self):
        idx = self.list_widget.currentRow()
        if 0 <= idx < len(self._actions) - 1:
            self._actions[idx + 1], self._actions[idx] = self._actions[idx], self._actions[idx + 1]
            item = self.list_widget.takeItem(idx)
            self.list_widget.insertItem(idx + 1, item)
            self.list_widget.setCurrentRow(idx + 1)
            save_actions(self._actions)

    # debugging helper: klik di main window menunjukkan widget yang ada di titik tersebut
    # normal behavior: no debug logging
    # (mousePressEvent not overridden)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ActionManagerWindow()
    w.show()
    sys.exit(app.exec())