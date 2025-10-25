"""
WebSocket manager for live video streaming
Handles connections from streamers (webcam computers) and viewers (dashboards)
"""

from fastapi import WebSocket
from typing import List, Dict
import base64
import cv2
import numpy as np
import mediapipe as mp
import json

# Initialize MediaPipe Face Mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class ConnectionManager:
    def __init__(self):
        self.streamers: List[WebSocket] = []  # Computers sending video
        self.viewers: List[WebSocket] = []    # Dashboards watching

    async def connect_streamer(self, websocket: WebSocket):
        await websocket.accept()
        self.streamers.append(websocket)
        print(f"✅ Streamer connected. Total streamers: {len(self.streamers)}")

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewers.append(websocket)
        print(f"✅ Viewer connected. Total viewers: {len(self.viewers)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.streamers:
            self.streamers.remove(websocket)
            print(f"❌ Streamer disconnected. Remaining: {len(self.streamers)}")
        if websocket in self.viewers:
            self.viewers.remove(websocket)
            print(f"❌ Viewer disconnected. Remaining: {len(self.viewers)}")

    async def broadcast_frame(self, frame_data: Dict):
        """Send processed frame to all viewers"""
        disconnected = []
        for viewer in self.viewers:
            try:
                await viewer.send_json(frame_data)
            except:
                disconnected.append(viewer)

        # Remove disconnected viewers
        for viewer in disconnected:
            self.disconnect(viewer)

manager = ConnectionManager()

def process_frame(frame_base64: str) -> Dict:
    """
    Process video frame with computer vision

    Args:
        frame_base64: Base64 encoded JPEG image

    Returns:
        {
            "frame": base64_string,
            "crs_score": 0.45,
            "heart_rate": 78,
            "respiratory_rate": 14,
            "alert": False
        }
    """
    try:
        # Decode base64 to OpenCV image
        if ',' in frame_base64:
            frame_base64 = frame_base64.split(',')[1]

        img_data = base64.b64decode(frame_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Failed to decode frame")

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run face detection
        results = face_mesh.process(rgb_frame)

        # Default values
        crs_score = 0.0
        heart_rate = 75
        respiratory_rate = 14

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            h, w = frame.shape[:2]

            # Detect facial flushing (CRS indicator)
            # Sample cheek regions: landmarks 205 (left) and 425 (right)
            cheek_redness = 0.0

            for idx in [205, 425]:
                lm = landmarks.landmark[idx]
                x, y = int(lm.x * w), int(lm.y * h)

                # Extract 20x20 pixel region around landmark
                roi = frame[max(0, y-10):min(h, y+10), max(0, x-10):min(w, x+10)]

                if roi.size > 0:
                    # Calculate redness: R channel minus average of G and B
                    r = np.mean(roi[:, :, 2])
                    g = np.mean(roi[:, :, 1])
                    b = np.mean(roi[:, :, 0])
                    cheek_redness += (r - (g + b) / 2) / 255.0

            # Average both cheeks
            cheek_redness /= 2

            # Calculate CRS risk score (0-1 scale)
            crs_score = min(1.0, max(0.0, cheek_redness * 2.5))

            # Simulate heart rate increase with CRS
            # In real system, would use rPPG over multiple frames
            heart_rate = int(75 + (crs_score * 30))  # 75-105 bpm range
            respiratory_rate = int(14 + (crs_score * 10))  # 14-24 breaths/min

            # Draw face landmarks (makes it look impressive!)
            for landmark in landmarks.landmark:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # Encode frame back to base64
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64_out = base64.b64encode(buffer).decode('utf-8')

        return {
            "frame": f"data:image/jpeg;base64,{frame_base64_out}",
            "crs_score": round(crs_score, 2),
            "heart_rate": heart_rate,
            "respiratory_rate": respiratory_rate,
            "alert": crs_score > 0.7
        }

    except Exception as e:
        print(f"❌ Error processing frame: {e}")
        return {
            "frame": frame_base64,
            "crs_score": 0.0,
            "heart_rate": 75,
            "respiratory_rate": 14,
            "alert": False,
            "error": str(e)
        }

