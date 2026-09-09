# youtube_grid_item.py
from PyQt6 import QtWidgets, QtCore

class YouTubeGrid(QtWidgets.QWidget):
    """Container for one YouTube video + its gaze count label"""
    def __init__(self, url, index):
        super().__init__()
        self.url = url
        self.index = index
        self.gaze_count = 0
        self.is_ad = False

        # Layout
        self.layout = QtWidgets.QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setStackingMode(QtWidgets.QStackedLayout.StackAll)

        # YouTube view
        self.web_view = QtWidgets.QWidget()  # Placeholder
        self.layout.addWidget(self.web_view)

        # Label overlay
        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("""
            color: white;
            background-color: rgba(0, 0, 0, 100);
            padding: 4px;
            border-radius: 6px;
            font-size: 14px;
        """)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        self.label.move(10, 10)
        self.label.resize(160, 30)
        self.label.setText(f"Grid {index+1}: 0")

        self.layout.addWidget(self.label)

    def set_web_view(self, web_view):
        """Attach QWebEngineView after it's created externally"""
        self.layout.removeWidget(self.web_view)
        self.web_view.deleteLater()
        self.web_view = web_view
        self.layout.insertWidget(0, web_view)
        self.layout.setCurrentWidget(web_view)

    def increment_gaze(self):
        """Increase gaze counter and update label"""
        self.gaze_count += 1
        self.label.setText(f"Grid {self.index+1}: {self.gaze_count}")