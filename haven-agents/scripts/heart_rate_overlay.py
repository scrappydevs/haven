#!/usr/bin/env python3
"""
Real-time heart rate overlay demo for Haven.

Captures webcam frames, extracts a forehead ROI, runs the shared rPPG heart
rate monitor, and overlays both the BPM estimate and the health-agent analysis.

Run from the repo root:
    python haven-agents/scripts/heart_rate_overlay.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

# Ensure project root is on sys.path for package imports
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from haven_agents.utils.heart_rate import HeartRateMonitor
from haven_agents.agents.haven_health_agent import analyze_patient_metrics


def _select_forehead_roi(frame: np.ndarray, face: Tuple[int, int, int, int]) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    x, y, w, h = face
    roi_x1 = x + int(w * 0.25)
    roi_x2 = x + int(w * 0.75)
    roi_y1 = y + int(h * 0.10)
    roi_y2 = y + int(h * 0.35)

    roi_x1 = max(0, roi_x1)
    roi_y1 = max(0, roi_y1)
    roi_x2 = min(frame.shape[1], roi_x2)
    roi_y2 = min(frame.shape[0], roi_y2)

    roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
    return roi, (roi_x1, roi_y1, roi_x2, roi_y2)


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Unable to access default camera (device 0).")

    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(str(cascade_path))
    if face_detector.empty():
        raise RuntimeError(f"Failed to load face cascade from {cascade_path}.")

    hr_monitor = HeartRateMonitor()
    last_analysis = {"severity": "NORMAL", "reasoning": "Awaiting signal", "recommended_action": "Continue monitoring"}
    severity_colors = {
        "CRITICAL": (0, 0, 255),
        "WARNING": (0, 165, 255),
        "NORMAL": (0, 200, 0)
    }
    last_analysis_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            display = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(120, 120))

            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                cv2.rectangle(display, (x, y), (x + w, y + h), (120, 200, 255), 2)

                roi, (rx1, ry1, rx2, ry2) = _select_forehead_roi(frame, (x, y, w, h))
                if roi.size > 0:
                    cv2.rectangle(display, (rx1, ry1), (rx2, ry2), (255, 180, 120), 2)
                    bpm = hr_monitor.process_frame(frame, roi)
                else:
                    bpm = hr_monitor.last_heart_rate
            else:
                bpm = hr_monitor.last_heart_rate

            now = time.time()
            if now - last_analysis_time > 0.5:
                vitals = {
                    "heart_rate": int(bpm),
                    "temperature": 37.0,
                    "blood_pressure": "120/80",
                    "spo2": 98
                }
                cv_metrics = {
                    "distress_score": 2,
                    "movement_score": 2,
                    "posture_alert": False
                }
                last_analysis = analyze_patient_metrics("DEMO", vitals, cv_metrics)
                last_analysis_time = now

            severity = last_analysis.get("severity", "NORMAL")
            color = severity_colors.get(severity, (255, 255, 255))
            hr_text = f"Heart Rate: {int(hr_monitor.last_heart_rate)} bpm"
            status_text = f"{severity} · {last_analysis.get('recommended_action', '')}"

            cv2.putText(display, hr_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)
            cv2.putText(display, status_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
            cv2.putText(display, last_analysis.get("reasoning", ""), (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2, cv2.LINE_AA)

            cv2.imshow("Haven Heart Rate Demo", display)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
