# main.py
import sys
import time
import cv2
import csv
import os
from PyQt6 import QtWidgets
from youtube_grid import YouTubeGridPlayer  # your player class
from eyetrax import GazeEstimator, run_9_point_calibration

# --- Configuration ---


def compute_attention_percentages(log_file):
    total = 0
    ad_count = 0
    main_count = 0

    with open(log_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            total += 1
            if row['is_ad'].lower() == 'true':
                ad_count += 1
            else:
                main_count += 1

    if total == 0:
        return 0, 0

    ad_percent = (ad_count / total) * 100
    main_percent = (main_count / total) * 100
    return ad_percent, main_percent

urls = [
    "https://www.youtube.com/watch?v=bK5tLqJdtzc&list=RDbK5tLqJdtzc&start_radio=1",  # main video
    "https://www.youtube.com/watch?v=nRe3xFeyhVY&list=RDnRe3xFeyhVY&start_radio=1",
    "https://www.youtube.com/watch?v=rIoMss4Rnog&list=RDrIoMss4Rnog&start_radio=1" #ad
]
opacity = 0.5
camera_index = 0





# --- Step 1: Calibration ---
estimator = GazeEstimator()

print("Starting 9-point calibration. Please follow the points with your eyes.")

log_file = "gaze_log.csv"

with open(log_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "grid_index", "is_ad", "gaze_count"])

try:
    run_9_point_calibration(estimator, camera_index)
except Exception as e:
    print(f"Calibration failed: {e}")
else:
    print("Calibration complete.")

# --- Step 2: PyQt6 app ---
if not sys.argv:
    sys.argv = ["main.py"]

app = QtWidgets.QApplication(sys.argv)

main_window = YouTubeGridPlayer(
    urls,
    opacity=opacity,
    camera_index=camera_index,
    gaze_estimator=estimator
)

main_window.show()

exit_code = app.exec()
ad_pct, main_pct = compute_attention_percentages("gaze_log.csv")
print(f"Attention on Ad: {ad_pct:.2f}%")
print(f"Attention on Main: {main_pct:.2f}%")
os.remove("gaze_log.csv")
sys.exit(exit_code)

