import sys
import time
import threading
import math

import pyautogui as pyg
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout
)
from PySide6.QtCore import Qt, QEvent

pyg.FAILSAFE = True

class MouseController:
    """A class to control mouse actions using pyautogui."""
    @staticmethod
    def move_to(x: int, y: int, duration: float = 0.4) -> None:
        """Move the mouse to a specific (x, y) position."""
        pyg.moveTo(x, y, duration=duration)
    
    @staticmethod
    def click(x: int, y: int, button: str = 'left', duration: float = 0.4) -> None:
        """Click at a specific (x, y) position, with specified button."""
        if button not in ['left', 'right', 'middle']:
            raise ValueError("Button must be 'left', 'right', or 'middle'")
        pyg.click(x, y, button=button, duration=duration)
        
    @staticmethod
    def image_click(img_pth: str, confidence: float = 0.7, duration: float = 0.4) -> None:
        """Find an image on the screen and click it."""
        location = pyg.locateCenterOnScreen(img_pth, confidence=confidence)
        if location:
            x, y = location
            pyg.click(x, y, duration=duration)
        else:
            print(f"Image {img_pth} not found on screen.")

class FloatingButton(QWidget):
    """A small draggable circular floating button (blue) with arc options to the right."""
    def __init__(self, diameter: int = 50, initial_pos: tuple | None = None):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_offset = None

        self.diameter = diameter
        self.opt_size = max(36, diameter - 6)
        self.spacing = 6

        self.opt_dist = int(self.diameter * 1.6)
        self.opt_angles = (-45, 45)
        self._base_margin = 8

        self.collapsed_size = (diameter, diameter)
        self.setFixedSize(*self.collapsed_size)

        radius = diameter // 2
        self.main_btn = QPushButton(" ⚙︎ ", self)
        self.main_btn.setFixedSize(diameter, diameter)
        self.main_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #007BFF;
                border-radius: {radius}px;
                color: white;
                font-size: 18px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #0056b3; }}
            QPushButton:pressed {{ background-color: #003f7f; padding-top: 2px; }}
            """
        )
        self.main_btn.setFocusPolicy(Qt.NoFocus)
        self.main_btn.setCursor(Qt.PointingHandCursor)
        self.main_btn.clicked.connect(self.toggle_options)
        self.main_btn.installEventFilter(self)

        opt_radius = self.opt_size // 2
        self.start_btn = QPushButton(" ▶ ", self)
        self.start_btn.setFixedSize(self.opt_size, self.opt_size)
        self.start_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #28a745;
                border-radius: {opt_radius}px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #1e7e34; }}
            QPushButton:pressed {{ background-color: #155d27; padding-top: 2px; }}
            """
        )
        self.start_btn.setVisible(False)
        self.start_btn.setFocusPolicy(Qt.NoFocus)
        self.start_btn.clicked.connect(lambda: threading.Thread(target=self.perform_mouse_action, daemon=True).start())

        self.exit_btn = QPushButton(" ✖ ", self)
        self.exit_btn.setFixedSize(self.opt_size, self.opt_size)
        self.exit_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #dc3545;
                border-radius: {opt_radius}px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #bd2130; }}
            QPushButton:pressed {{ background-color: #82181f; padding-top: 2px; }}
            """
        )
        self.exit_btn.setVisible(False)
        self.exit_btn.setFocusPolicy(Qt.NoFocus)
        self.exit_btn.clicked.connect(lambda: QApplication.instance().quit())

        self._layout_dummy = QVBoxLayout(self)
        self._layout_dummy.setContentsMargins(0, 0, 0, 0)
        self._layout_dummy.setSpacing(0)
        self._layout_dummy.addWidget(self.main_btn)

        self._options_visible = False
        self._offset = (0, 0)

        self._relayout()
        if initial_pos:
            self.move(*initial_pos)

    def eventFilter(self, obj, event):
        # catch mouse events on main_btn so dragging starts even when pressing the button
        if obj is self.main_btn:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                # allow button click processing as well
                return False
            if event.type() == QEvent.MouseMove:
                if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
                    self.move(event.globalPosition().toPoint() - self._drag_offset)
                    return True
            if event.type() == QEvent.MouseButtonRelease:
                self._drag_offset = None
                return False
        return super().eventFilter(obj, event)

    def _relayout(self):
        """Position main button and option buttons using current offset."""
        ox, oy = self._offset
        cx = self.diameter / 2
        cy = self.diameter / 2

        main_x = int(ox + cx - self.diameter / 2)
        main_y = int(oy + cy - self.diameter / 2)
        self.main_btn.move(main_x, main_y)

        for btn, ang in ((self.start_btn, self.opt_angles[0]), (self.exit_btn, self.opt_angles[1])):
            rad = math.radians(ang)
            bx = ox + cx + math.cos(rad) * self.opt_dist - self.opt_size / 2
            by = oy + cy + math.sin(rad) * self.opt_dist - self.opt_size / 2
            btn.move(int(bx), int(by))

    def _compute_expanded_size(self):
        """Return (width, height, offset_x, offset_y) that fully contains main+options."""
        cx = self.diameter / 2
        cy = self.diameter / 2

        xs = [0, self.diameter]
        ys = [0, self.diameter]

        for ang in self.opt_angles:
            rad = math.radians(ang)
            center_x = cx + math.cos(rad) * self.opt_dist
            center_y = cy + math.sin(rad) * self.opt_dist
            xs.extend([center_x - self.opt_size / 2, center_x + self.opt_size / 2])
            ys.extend([center_y - self.opt_size / 2, center_y + self.opt_size / 2])

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        width = int(math.ceil(max_x - min_x + self._base_margin))
        height = int(math.ceil(max_y - min_y + self._base_margin))

        width = max(width, self.diameter)
        height = max(height, self.diameter)

        offset_x = -min_x + (self._base_margin / 2)
        offset_y = -min_y + (self._base_margin / 2)
        return (width, height, int(offset_x), int(offset_y))

    def toggle_options(self):
        """Toggle expanded/collapsed while keeping main button absolute position stable."""
        old_offset = self._offset
        old_pos = self.pos()

        self._options_visible = not self._options_visible
        if self._options_visible:
            w, h, ox, oy = self._compute_expanded_size()
            dx = old_offset[0] - ox
            dy = old_offset[1] - oy
            self.move(old_pos.x() + dx, old_pos.y() + dy)
            self.setFixedSize(w, h)
            self.start_btn.setVisible(True)
            self.exit_btn.setVisible(True)
            self._offset = (ox, oy)
        else:
            ox, oy = 0, 0
            dx = old_offset[0] - ox
            dy = old_offset[1] - oy
            self.move(old_pos.x() + dx, old_pos.y() + dy)
            self.setFixedSize(*self.collapsed_size)
            self.start_btn.setVisible(False)
            self.exit_btn.setVisible(False)
            self._offset = (ox, oy)

        self._relayout()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()

    def perform_mouse_action(self):
        """Entrypoint dijalankan oleh Start. Jika ada self.action_sequence -> jalankan berurutan."""
        seq = getattr(self, "action_sequence", None)
        if seq:
            self.run_actions(seq)
            return

        try:
            MouseController.image_click("./msg.png")
            time.sleep(0.5)
            pyg.write("Hello, World!", interval=0.1)
            pyg.press("enter")
        except Exception as e:
            print("Mouse action error:", e)

    def run_actions(self, actions):
        """Run a list of action dicts in order. action = {'type': 'image'|'write', 'param': ...}."""
        for a in actions:
            try:
                a_type = a.get("type", "image")
                param = a.get("param", "")
                if a_type == "image":
                    if param:
                        MouseController.image_click(param)
                    else:
                        print("Skipping image action with empty param")
                elif a_type == "write":
                    if param:
                        pyg.write(param, interval=0.2)
                        pyg.press("enter")
                    else:
                        print("Skipping write action with empty param")
                else:
                    print("Unknown action type:", a_type)
                time.sleep(0.35)
            except Exception as e:
                print("Error running action:", e)