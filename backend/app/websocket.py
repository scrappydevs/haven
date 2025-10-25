"""
WebSocket manager for live video streaming
Handles connections from streamers (webcam computers) and viewers (dashboards)
"""

from fastapi import WebSocket
from typing import List, Dict, Optional
import base64
import cv2
import numpy as np
import mediapipe as mp
import json
import threading
from app.cv_metrics import (
    HeartRateMonitor,
    RespiratoryRateMonitor,
    FaceTouchingDetector,
    MovementVolumeTracker,
    TremorDetector,
    UpperBodyPostureTracker
)

# Thread lock for MediaPipe processing (not thread-safe even in static mode)
cv_processing_lock = threading.Lock()

# Initialize MediaPipe Face Mesh - OPTIMIZED for speed
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=False,  # ✅ Skip refinement for speed
    static_image_mode=True,
    min_detection_confidence=0.3,  # ✅ Lower threshold for speed
    min_tracking_confidence=0.3
)

# Initialize MediaPipe Pose - OPTIMIZED for speed
pose = mp.solutions.pose.Pose(
    static_image_mode=True,
    model_complexity=0,  # ✅ 0 = lite model (faster)
    smooth_landmarks=False,
    min_detection_confidence=0.3,  # ✅ Lower threshold for speed
    min_tracking_confidence=0.3
)

class PatientMetricTrackers:
    """Container for per-patient metric tracking instances"""
    def __init__(self):
        self.heart_rate = HeartRateMonitor()
        self.respiratory_rate = RespiratoryRateMonitor()
        self.face_touching = FaceTouchingDetector()
        self.movement = MovementVolumeTracker()
        self.tremor = TremorDetector()
        self.upper_body = UpperBodyPostureTracker()
        self.monitoring_conditions: List[str] = []  # e.g., ['CRS', 'SEIZURE']

class ConnectionManager:
    def __init__(self):
        self.streamers: Dict[str, WebSocket] = {}  # {patient_id: websocket}
        self.viewers: List[WebSocket] = []
        self.patient_trackers: Dict[str, PatientMetricTrackers] = {}  # {patient_id: trackers}

    def register_streamer(self, patient_id: str, websocket: WebSocket, monitoring_conditions: Optional[List[str]] = None):
        """Register a streamer for a specific patient"""
        self.streamers[patient_id] = websocket

        # Initialize metric trackers for this patient
        trackers = PatientMetricTrackers()
        if monitoring_conditions:
            trackers.monitoring_conditions = monitoring_conditions
        self.patient_trackers[patient_id] = trackers

        print(f"✅ Registered streamer for patient {patient_id}. Monitoring: {monitoring_conditions}. Total streamers: {len(self.streamers)}")

    def unregister_streamer(self, patient_id: str):
        """Unregister a streamer for a specific patient"""
        if patient_id in self.streamers:
            del self.streamers[patient_id]
        if patient_id in self.patient_trackers:
            del self.patient_trackers[patient_id]
        print(f"❌ Unregistered streamer for patient {patient_id}. Total streamers: {len(self.streamers)}")

    def get_trackers(self, patient_id: str) -> Optional[PatientMetricTrackers]:
        """Get metric trackers for a patient"""
        return self.patient_trackers.get(patient_id)

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
        """Send processed frame to all viewers in parallel"""
        if not self.viewers:
            return

        import asyncio

        async def send_to_viewer(viewer):
            try:
                await viewer.send_json(frame_data)
                return None
            except Exception as e:
                print(f"❌ Failed to send to viewer: {e}")
                return viewer

        # Send to all viewers in parallel
        results = await asyncio.gather(*[send_to_viewer(v) for v in self.viewers], return_exceptions=True)

        # Clean up dead connections
        dead = [r for r in results if r is not None and not isinstance(r, Exception)]
        for viewer in dead:
            self.disconnect(viewer)

manager = ConnectionManager()

def process_frame_fast(frame_base64: str, patient_id: Optional[str] = None) -> Dict:
    """
    ULTRA-FAST: ONLY MediaPipe Pose for overlays (33 landmarks)
    Face mesh moved to slow processing (too expensive for real-time)
    Target: <50ms per frame
    """
    try:
        import time
        start = time.time()

        # Decode base64 to OpenCV image
        if ',' in frame_base64:
            frame_base64 = frame_base64.split(',')[1]

        img_data = base64.b64decode(frame_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Failed to decode frame")

        decode_time = time.time() - start

        # AGGRESSIVE downsampling for speed
        small_frame = cv2.resize(frame, (160, 90))
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        resize_time = time.time() - start - decode_time

        # Thread-safe MediaPipe: ONLY Pose (no face mesh - too slow)
        mediapipe_start = time.time()
        with cv_processing_lock:
            pose_results = pose.process(rgb_frame)
        mediapipe_time = time.time() - mediapipe_start

        # Extract pose landmarks as simple overlay
        landmark_data = []
        connections_data = []
        head_pose_axes = None

        if pose_results.pose_landmarks:
            # Extract key pose landmarks (head, shoulders, arms)
            pose_landmark_indices = {
                0: {"type": "nose", "color": "green"},
                2: {"type": "left_eye", "color": "cyan"},
                5: {"type": "right_eye", "color": "cyan"},
                11: {"type": "left_shoulder", "color": "red"},
                12: {"type": "right_shoulder", "color": "red"},
                13: {"type": "left_elbow", "color": "green"},
                14: {"type": "right_elbow", "color": "green"},
                15: {"type": "left_wrist", "color": "green"},
                16: {"type": "right_wrist", "color": "green"},
            }

            for idx, metadata in pose_landmark_indices.items():
                lm = pose_results.pose_landmarks.landmark[idx]
                landmark_data.append({
                    "id": int(idx),
                    "x": float(lm.x),
                    "y": float(lm.y),
                    "type": metadata["type"],
                    "color": metadata["color"]
                })

            # Simple connections for pose skeleton
            connections_data = [
                (0, 2), (0, 5),  # Nose to eyes
                (2, 11), (5, 12),  # Eyes to shoulders
                (11, 12),  # Shoulder line
                (11, 13), (13, 15),  # Left arm
                (12, 14), (14, 16),  # Right arm
            ]

            # Simple head direction indicator
            nose = pose_results.pose_landmarks.landmark[0]
            left_shoulder = pose_results.pose_landmarks.landmark[11]
            right_shoulder = pose_results.pose_landmarks.landmark[12]

            head_pose_axes = {
                "origin": {"x": int(nose.x * 640), "y": int(nose.y * 360)},
                "x_axis": {"x": int(right_shoulder.x * 640), "y": int(right_shoulder.y * 360), "color": "red"},
                "y_axis": {"x": int(nose.x * 640), "y": int(nose.y * 360 - 50), "color": "green"},
                "z_axis": {"x": int(left_shoulder.x * 640), "y": int(left_shoulder.y * 360), "color": "blue"}
            }

        total_time = time.time() - start
        if total_time > 0.1:  # Log if >100ms
            print(f"⚠️ Fast processing slow: {total_time*1000:.0f}ms (decode: {decode_time*1000:.0f}ms, resize: {resize_time*1000:.0f}ms, MediaPipe: {mediapipe_time*1000:.0f}ms)")

        return {
            "landmarks": landmark_data,
            "connections": connections_data,
            "head_pose_axes": head_pose_axes,
            "metrics": None  # Metrics come from slow processing
        }

    except Exception as e:
        print(f"❌ Fast processing error: {e}")
        return {
            "landmarks": [],
            "connections": [],
            "head_pose_axes": None,
            "metrics": None
        }


def process_frame_metrics(frame_base64: str, patient_id: Optional[str] = None) -> Dict:
    """
    SLOW: All expensive tracker operations (rPPG, FFT, etc.) - runs every 5 seconds
    Returns ONLY metrics, no overlay data (overlays come from fast function)
    Target: Can take 1-2 seconds since it runs infrequently
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

        h, w = frame.shape[:2]

        # Downsample for processing (balance between quality and speed)
        small_frame = cv2.resize(frame, (320, 180))
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Thread-safe MediaPipe processing
        with cv_processing_lock:
            face_results = face_mesh.process(rgb_frame)
            pose_results = pose.process(rgb_frame)

        # Get trackers for this patient
        trackers = manager.get_trackers(patient_id) if patient_id else None

        # Initialize default values
        heart_rate = 75
        respiratory_rate = 14
        crs_score = 0.0
        face_touching_freq = 0
        restlessness_index = 0.0
        movement_vigor = 0.0
        tremor_magnitude = 0.0
        tremor_detected = False
        head_pitch = 0.0
        head_yaw = 0.0
        head_roll = 0.0
        eye_openness = 0.0
        attention_score = 0.0
        upper_body_metrics = {
            "shoulder_angle": 0.0,
            "posture_score": 1.0,
            "upper_body_movement": 0.0,
            "lean_forward": 0.0,
            "arm_asymmetry": 0.0
        }

        if face_results.multi_face_landmarks:
            landmarks = face_results.multi_face_landmarks[0]

            # === HEAD POSE ESTIMATION ===
            model_points = np.array([
                (0.0, 0.0, 0.0),
                (0.0, -330.0, -65.0),
                (-225.0, 170.0, -135.0),
                (225.0, 170.0, -135.0),
                (-150.0, -150.0, -125.0),
                (150.0, -150.0, -125.0)
            ], dtype=np.float64)

            image_points = np.array([
                (int(landmarks.landmark[1].x * w), int(landmarks.landmark[1].y * h)),
                (int(landmarks.landmark[152].x * w), int(landmarks.landmark[152].y * h)),
                (int(landmarks.landmark[263].x * w), int(landmarks.landmark[263].y * h)),
                (int(landmarks.landmark[33].x * w), int(landmarks.landmark[33].y * h)),
                (int(landmarks.landmark[287].x * w), int(landmarks.landmark[287].y * h)),
                (int(landmarks.landmark[57].x * w), int(landmarks.landmark[57].y * h))
            ], dtype=np.float64)

            focal_length = w
            center = (w / 2, h / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)

            dist_coeffs = np.zeros((4, 1))

            success, rotation_vec, translation_vec = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )

            if success:
                rotation_mat, _ = cv2.Rodrigues(rotation_vec)
                pose_mat = cv2.hconcat((rotation_mat, translation_vec))
                _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
                head_pitch = float(euler_angles[0][0])
                head_yaw = float(euler_angles[1][0])
                head_roll = float(euler_angles[2][0])

            # === EYE OPENNESS ===
            left_eye_top = landmarks.landmark[159]
            left_eye_bottom = landmarks.landmark[145]
            right_eye_top = landmarks.landmark[386]
            right_eye_bottom = landmarks.landmark[374]

            left_eye_height = abs(left_eye_top.y - left_eye_bottom.y)
            right_eye_height = abs(right_eye_top.y - right_eye_bottom.y)
            eye_openness = (left_eye_height + right_eye_height) / 2 * 100

            # === ATTENTION SCORE ===
            yaw_factor = max(0, 1 - abs(head_yaw) / 45.0)
            pitch_factor = max(0, 1 - abs(head_pitch) / 30.0)
            eye_factor = min(1.0, eye_openness / 2.0)
            attention_score = (yaw_factor * 0.4 + pitch_factor * 0.3 + eye_factor * 0.3)

            # === FACIAL FLUSHING (CRS INDICATOR) ===
            cheek_redness = 0.0
            for idx in [205, 425]:
                lm = landmarks.landmark[idx]
                x, y = int(lm.x * w), int(lm.y * h)
                roi = frame[max(0, y-10):min(h, y+10), max(0, x-10):min(w, x+10)]

                if roi.size > 0:
                    r = np.mean(roi[:, :, 2])
                    g = np.mean(roi[:, :, 1])
                    b = np.mean(roi[:, :, 0])
                    cheek_redness += (r - (g + b) / 2) / 255.0

            cheek_redness /= 2
            crs_score = min(1.0, max(0.0, cheek_redness * 2.5))

            # === EXPENSIVE TRACKER OPERATIONS ===
            if trackers:
                # rPPG heart rate (FFT on forehead color changes)
                forehead_lm = landmarks.landmark[10]
                fx, fy = int(forehead_lm.x * w), int(forehead_lm.y * h)
                forehead_roi = frame[max(0, fy-30):min(h, fy+10), max(0, fx-40):min(w, fx+40)]
                heart_rate = trackers.heart_rate.process_frame(frame, forehead_roi)

                # Respiratory rate (FFT on nose movement)
                nose_y = landmarks.landmark[1].y
                respiratory_rate = trackers.respiratory_rate.process_frame(nose_y)

                # Face touching detection
                face_touching_freq, is_touching = trackers.face_touching.process_frame(landmarks)

                # Movement and restlessness
                restlessness_index, movement_vigor = trackers.movement.process_frame(landmarks)

                # Tremor detection (FFT on hand positions)
                tremor_magnitude, tremor_detected = trackers.tremor.process_frame(landmarks)

                # Upper body posture tracking
                if pose_results.pose_landmarks:
                    upper_body_metrics = trackers.upper_body.process_frame(pose_results.pose_landmarks)
            else:
                # Fallback if no trackers
                heart_rate = int(75 + (crs_score * 30))
                respiratory_rate = int(14 + (crs_score * 10))

        # Return ONLY metrics (no overlay data)
        return {
            "metrics": {
                # Basic vitals (CV-derived)
                "heart_rate": int(heart_rate),
                "respiratory_rate": int(respiratory_rate),

                # CRS-specific metrics
                "crs_score": float(round(crs_score, 2)),
                "face_touching_frequency": int(face_touching_freq),
                "restlessness_index": float(round(restlessness_index, 2)),

                # Seizure-specific metrics
                "tremor_magnitude": float(round(tremor_magnitude, 2)),
                "tremor_detected": bool(tremor_detected),
                "movement_vigor": float(round(movement_vigor, 2)),

                # Head pose
                "head_pitch": float(round(head_pitch, 1)),
                "head_yaw": float(round(head_yaw, 1)),
                "head_roll": float(round(head_roll, 1)),

                # Eye and attention
                "eye_openness": float(round(eye_openness, 2)),
                "attention_score": float(round(attention_score, 2)),

                # Upper body posture
                "shoulder_angle": upper_body_metrics["shoulder_angle"],
                "posture_score": upper_body_metrics["posture_score"],
                "upper_body_movement": upper_body_metrics["upper_body_movement"],
                "lean_forward": upper_body_metrics["lean_forward"],
                "arm_asymmetry": upper_body_metrics["arm_asymmetry"],

                # Alerts
                "alert": bool(crs_score > 0.7 or tremor_detected),
                "alert_triggers": list(filter(None, [
                    f"CRS Score Critical: {int(crs_score * 100)}%" if crs_score > 0.7 else None,
                    f"Tremor Detected: {tremor_magnitude:.1f}" if tremor_detected else None
                ]))
            }
        }

    except Exception as e:
        import traceback
        print(f"❌ Metrics processing exception: {e}")
        print(f"   Traceback: {traceback.format_exc()[:300]}")
        return {
            "metrics": {
                "crs_score": 0.0,
                "heart_rate": 75,
                "respiratory_rate": 14,
                "alert": False,
                "alert_triggers": [],
                "head_pitch": 0.0,
                "head_yaw": 0.0,
                "head_roll": 0.0,
                "eye_openness": 0.0,
                "attention_score": 0.0,
                "shoulder_angle": 0.0,
                "posture_score": 1.0,
                "upper_body_movement": 0.0,
                "lean_forward": 0.0,
                "arm_asymmetry": 0.0
            }
        }

