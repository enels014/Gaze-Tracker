from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
import csv
import time
import os
import cv2

from eyetrax import GazeEstimator, run_9_point_calibration
from camera_overlay import VideoOverlay


log_file = "gaze_log.csv"
if not os.path.exists(log_file):
    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "grid_index", "is_ad", "gaze_count"])



class YouTubeGrid(QtWidgets.QWidget):
    """A single YouTube video grid with a gaze counter"""
    def __init__(self, url, is_ad=False):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Web view
        self.web = QWebEngineView()
        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        embed_url = url.replace("watch?v=", "embed/") + "?autoplay=1&mute=1"
        self.web.load(QtCore.QUrl(embed_url))
        layout.addWidget(self.web)

        # Gaze counter label
        self.counter_label = QtWidgets.QLabel("0", self)
        self.counter_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                font-size: 20px;
                padding: 4px 8px;
                border-radius: 6px;
            }
        """)
        self.counter_label.move(10, 10)
        self.counter_label.raise_()

        # Gaze count
        self.gaze_count = 0
        self.is_ad = is_ad  # <--- ensure this always exists

    def increment_gaze(self):
        self.gaze_count += 1
        self.counter_label.setText(str(self.gaze_count))



class YouTubeGridPlayer(QtWidgets.QMainWindow):
    """Main window with YouTube grids and webcam overlay"""
    def __init__(self, urls, opacity=0.5, camera_index=0, gaze_estimator=None):
        super().__init__()
        self.urls = urls
        self.grid_count = len(urls)
        self.opacity = opacity
        self.camera_index = camera_index

        self.overlay = None

        self.setWindowTitle("YouTube Grid Player")
        self.showFullScreen()

        # Central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        self.layout = QtWidgets.QHBoxLayout(central)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Build YouTube grids
        self.web_grids = []
        self.build_grid()

        # Overlay for webcam
        self.overlay = VideoOverlay(self)
        self.overlay.setGeometry(self.rect())
        self.overlay.show()

        # Camera
        self.cap = cv2.VideoCapture(self.camera_index)
        self.frame_count = 0

        # --- Eye tracker ---

        # Option A: create estimator and get the fitted instance
        self.gaze_estimator = gaze_estimator
        print("Calibration complete.")

        # Timer for webcam updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_overlay_frame)
        self.timer.start(50)


    def build_grid(self):
            
        #Create the grids and tag main vs ad videos

        # Remove old grids if any
        for grid in getattr(self, "web_grids", []):
            grid.setParent(None)
        self.web_grids = []

        if not self.urls:
            return

        # --- Main video (entertainment) ---
        main_grid = YouTubeGrid(self.urls[0], is_ad=False)
        self.layout.addWidget(main_grid, stretch=3)  # main video bigger
        self.web_grids.append(main_grid)	

        # --- Secondary videos (ads) ---
        if self.grid_count > 1:
            side_layout = QtWidgets.QVBoxLayout()
            side_layout.setContentsMargins(0, 0, 0, 0)
            side_layout.setSpacing(0)

            for url in self.urls[1:]:
                grid = YouTubeGrid(url, is_ad=True)
                side_layout.addWidget(grid)
                self.web_grids.append(grid)

            self.layout.addLayout(side_layout, stretch=1)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.overlay:
            self.overlay.setGeometry(self.rect())

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        super().closeEvent(event)
        
    def get_grid_index(self, grid):
        return self.web_grids.index(grid)

    def update_overlay_frame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("No frame captured", flush=True)
                return
            print("Frame captured", flush=True)
            #frame = cv2.flip(frame, 1)

            features, blink = self.gaze_estimator.extract_features(frame)
            print("Features:", features, "Blink:", blink, flush=True)

            if features is not None and not blink:
                x, y = self.gaze_estimator.predict([features])[0]
                print("Predicted gaze:", x, y, flush=True)
                grid_idx = self.detect_grid_hit((x, y), frame.shape)
                print("Grid index:", grid_idx, flush=True)
            
                if grid_idx is not None and grid_idx < len(self.web_grids):
                    grid = self.web_grids[grid_idx]
                    real_idx = self.get_grid_index(grid)
                    grid.increment_gaze()
                    print(f"Gaze incremented on grid {grid_idx}", flush=True)
    
                # Log CSV
                    with open(log_file, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([time.time(), real_idx, grid.is_ad, grid.gaze_count])
                        print("Logged to CSV", flush=True)
            else:
                print("No valid features or blinking", flush=True)

        except Exception as e:
            print(f"Gaze prediction error: {e}", flush=True)



    def detect_grid_hit(self, gaze_point, frame_shape):
        x, y = gaze_point
        cam_h, cam_w = frame_shape[:2]
        win_w, win_h = self.overlay.width(), self.overlay.height()
        nx = x / win_w
        ny = y / win_h
        if win_w == 0 or win_h == 0:
            return None

        nx, ny = x / cam_w, y / cam_h
        count = self.grid_count

        if count == 1:
            return 0
        elif count == 2:
            return 0 if nx < 0.75 else 1
        elif count == 3:
            if nx < 0.75:
                return 0
            return 1 if ny < 0.5 else 2

        return None


