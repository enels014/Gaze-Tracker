# overlay.py
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QImage, QPixmap, QPainter
import numpy as np

class VideoOverlay(QtWidgets.QWidget):
    """Overlay above all grids within the main window"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.overlay_img = None
        self.opacity = parent.opacity
        self._frame_data = None  # Keep reference to prevent garbage collection
        self.raise_()  # ensure it stays above child widgets

    def update_overlay(self, frame):
        h, w, _ = frame.shape
        # Make a copy to ensure data stays valid
        self._frame_data = np.ascontiguousarray(frame)
        qimg = QImage(self._frame_data.data, w, h, 3 * w, QImage.Format.Format_BGR888)
        self.overlay_img = QPixmap.fromImage(qimg.copy())  # Copy to decouple from numpy array
        self.repaint()

    def paintEvent(self, event):
        if self.overlay_img:
            painter = QPainter(self)
            painter.setOpacity(self.opacity)
            painter.drawPixmap(0, 0, self.overlay_img)
            painter.end()