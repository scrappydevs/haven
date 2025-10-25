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
        self.streamers: Dict[str, WebSocket] = {}  # {patient_id: websocket}
        self.viewers: List[WebSocket] = []

    def register_streamer(self, patient_id: str, websocket: WebSocket):
        """Register a streamer for a specific patient"""
        self.streamers[patient_id] = websocket
        print(f"✅ Registered streamer for patient {patient_id}. Total streamers: {len(self.streamers)}")

    def unregister_streamer(self, patient_id: str):
        """Unregister a streamer for a specific patient"""
        if patient_id in self.streamers:
            del self.streamers[patient_id]
            print(f"❌ Unregistered streamer for patient {patient_id}. Total streamers: {len(self.streamers)}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket (legacy method)"""
        # Remove from streamers (find by value)
        patient_id_to_remove = None
        for patient_id, ws in self.streamers.items():
            if ws == websocket:
                patient_id_to_remove = patient_id
                break
        if patient_id_to_remove:
            self.unregister_streamer(patient_id_to_remove)

        # Remove from viewers
        if websocket in self.viewers:
            self.viewers.remove(websocket)

    async def broadcast_frame(self, frame_data: Dict):
        """Send processed frame to all viewers"""
        if not self.viewers:
            return

        dead = []
        for viewer in self.viewers:
            try:
                await viewer.send_json(frame_data)
            except Exception as e:
                print(f"❌ Failed to send to viewer: {e}")
                dead.append(viewer)

        for viewer in dead:
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
        head_pitch = 0.0
        head_yaw = 0.0
        head_roll = 0.0
        eye_openness = 1.0
        attention_score = 1.0
        key_landmarks_data = []
        head_pose_axes = None

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            h, w = frame.shape[:2]

            # === HEAD POSE ESTIMATION ===
            # Key 3D model points for head pose
            model_points = np.array([
                (0.0, 0.0, 0.0),             # Nose tip
                (0.0, -330.0, -65.0),        # Chin
                (-225.0, 170.0, -135.0),     # Left eye corner
                (225.0, 170.0, -135.0),      # Right eye corner
                (-150.0, -150.0, -125.0),    # Left mouth corner
                (150.0, -150.0, -125.0)      # Right mouth corner
            ], dtype=np.float64)

            # 2D image points from landmarks
            image_points = np.array([
                (int(landmarks.landmark[1].x * w), int(landmarks.landmark[1].y * h)),     # Nose tip
                (int(landmarks.landmark[152].x * w), int(landmarks.landmark[152].y * h)), # Chin
                (int(landmarks.landmark[263].x * w), int(landmarks.landmark[263].y * h)), # Left eye corner
                (int(landmarks.landmark[33].x * w), int(landmarks.landmark[33].y * h)),   # Right eye corner
                (int(landmarks.landmark[287].x * w), int(landmarks.landmark[287].y * h)), # Left mouth corner
                (int(landmarks.landmark[57].x * w), int(landmarks.landmark[57].y * h))    # Right mouth corner
            ], dtype=np.float64)

            # Camera matrix
            focal_length = w
            center = (w / 2, h / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)

            dist_coeffs = np.zeros((4, 1))

            # Solve for pose
            success, rotation_vec, translation_vec = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )

            if success:
                # Convert rotation vector to Euler angles
                rotation_mat, _ = cv2.Rodrigues(rotation_vec)
                pose_mat = cv2.hconcat((rotation_mat, translation_vec))
                _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
                head_pitch = float(euler_angles[0][0])
                head_yaw = float(euler_angles[1][0])
                head_roll = float(euler_angles[2][0])

            # === EYE OPENNESS ===
            # Left eye: landmarks 159 (top) and 145 (bottom)
            # Right eye: landmarks 386 (top) and 374 (bottom)
            left_eye_top = landmarks.landmark[159]
            left_eye_bottom = landmarks.landmark[145]
            right_eye_top = landmarks.landmark[386]
            right_eye_bottom = landmarks.landmark[374]

            left_eye_height = abs(left_eye_top.y - left_eye_bottom.y)
            right_eye_height = abs(right_eye_top.y - right_eye_bottom.y)
            eye_openness = (left_eye_height + right_eye_height) / 2 * 100

            # === ATTENTION SCORE ===
            # Based on head pose and eye openness
            # Looking straight ahead and eyes open = high attention
            yaw_factor = max(0, 1 - abs(head_yaw) / 45.0)
            pitch_factor = max(0, 1 - abs(head_pitch) / 30.0)
            eye_factor = min(1.0, eye_openness / 2.0)
            attention_score = (yaw_factor * 0.4 + pitch_factor * 0.3 + eye_factor * 0.3)

            # === FACIAL FLUSHING (CRS INDICATOR) ===
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
            heart_rate = int(75 + (crs_score * 30))  # 75-105 bpm range
            respiratory_rate = int(14 + (crs_score * 10))  # 14-24 breaths/min

            # === PREPARE LANDMARK DATA FOR FRONTEND ===
            # Extract key landmarks with metadata (no drawing here)
            key_landmarks_data = []
            landmark_definitions = {
                # Face outline (yellow)
                10: {"type": "forehead", "color": "#FFFF00"},
                152: {"type": "chin", "color": "#FFFF00"},
                234: {"type": "left_face", "color": "#FFFF00"},
                454: {"type": "right_face", "color": "#FFFF00"},
                # Eyes (cyan)
                33: {"type": "right_eye_outer", "color": "#00FFFF"},
                133: {"type": "right_eye_inner", "color": "#00FFFF"},
                263: {"type": "left_eye_inner", "color": "#00FFFF"},
                362: {"type": "left_eye_outer", "color": "#00FFFF"},
                # Nose (magenta)
                1: {"type": "nose_tip", "color": "#FF00FF"},
                # Mouth (green)
                61: {"type": "upper_lip", "color": "#00FF00"},
                291: {"type": "lower_lip", "color": "#00FF00"},
                # Cheeks - CRS indicators (red)
                205: {"type": "left_cheek", "color": "#FF0000"},
                425: {"type": "right_cheek", "color": "#FF0000"},
            }

            for idx, metadata in landmark_definitions.items():
                lm = landmarks.landmark[idx]
                key_landmarks_data.append({
                    "id": int(idx),
                    "x": float(lm.x),  # Normalized 0-1
                    "y": float(lm.y),  # Normalized 0-1
                    "type": metadata["type"],
                    "color": metadata["color"]
                })

            # Prepare head pose axis data for frontend drawing
            head_pose_axes = None
            if success:
                axis_length = 50
                axis_3d = np.float32([[axis_length, 0, 0], [0, axis_length, 0], [0, 0, axis_length]])
                axis_2d, _ = cv2.projectPoints(axis_3d, rotation_vec, translation_vec, camera_matrix, dist_coeffs)

                nose_2d = image_points[0].astype(int)
                head_pose_axes = {
                    "origin": {"x": int(nose_2d[0]), "y": int(nose_2d[1])},
                    "x_axis": {"x": int(axis_2d[0].ravel()[0]), "y": int(axis_2d[0].ravel()[1]), "color": "#FF0000"},  # Red
                    "y_axis": {"x": int(axis_2d[1].ravel()[0]), "y": int(axis_2d[1].ravel()[1]), "color": "#00FF00"},  # Green
                    "z_axis": {"x": int(axis_2d[2].ravel()[0]), "y": int(axis_2d[2].ravel()[1]), "color": "#0000FF"}   # Blue
                }

        # Encode frame back to base64 (quality 65 for streaming performance)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
        frame_base64_out = base64.b64encode(buffer).decode('utf-8')

        return {
            "frame": f"data:image/jpeg;base64,{frame_base64_out}",
            "landmarks": key_landmarks_data,  # Array of {id, x, y, type, color}
            "head_pose_axes": head_pose_axes,  # {origin, x_axis, y_axis, z_axis} or None
            "metrics": {
                "crs_score": float(round(crs_score, 2)),
                "heart_rate": int(heart_rate),
                "respiratory_rate": int(respiratory_rate),
                "alert": bool(crs_score > 0.7),
                "head_pitch": float(round(head_pitch, 1)),
                "head_yaw": float(round(head_yaw, 1)),
                "head_roll": float(round(head_roll, 1)),
                "eye_openness": float(round(eye_openness, 2)),
                "attention_score": float(round(attention_score, 2))
            }
        }

    except Exception as e:
        return {
            "frame": frame_base64,
            "landmarks": [],
            "head_pose_axes": None,
            "metrics": {
                "crs_score": 0.0,
                "heart_rate": 75,
                "respiratory_rate": 14,
                "alert": False,
                "head_pitch": 0.0,
                "head_yaw": 0.0,
                "head_roll": 0.0,
                "eye_openness": 0.0,
                "attention_score": 0.0
            }
        }

