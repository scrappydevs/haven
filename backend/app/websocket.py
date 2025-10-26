"""
WebSocket manager for live video streaming
Handles connections from streamers (webcam computers) and viewers (dashboards)
"""

from app.patient_guardian_agent import patient_guardian
from app.monitoring_control import monitoring_manager
from app.cv_metrics import (
    HeartRateMonitor,
    RespiratoryRateMonitor,
    FaceTouchingDetector,
    MovementVolumeTracker,
    TremorDetector,
    UpperBodyPostureTracker
)
import time
import queue
import threading
import json
import mediapipe as mp
from fastapi import WebSocket
from typing import List, Dict, Optional
import base64
import cv2
import numpy as np
import os
import logging

# ✅ SUPPRESS MEDIAPIPE VERBOSE LOGGING - Must be set BEFORE importing mediapipe
# Suppress INFO and WARNING logs from Google's glog
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs (if used)

# Suppress MediaPipe's Python logging
logging.getLogger('mediapipe').setLevel(logging.ERROR)

# Legacy agents disabled - using Fetch.ai Health Agent instead
# from app.patient_guardian_agent import patient_guardian
# from app.agent_system import agent_system

# MediaPipe models - lazy initialized per worker to avoid fork issues
_face_mesh = None
_pose = None


def get_face_mesh():
    """Lazy-load face mesh (thread-safe after fork)"""
    global _face_mesh
    if _face_mesh is None:
        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            static_image_mode=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
    return _face_mesh


def get_pose():
    """Lazy-load pose model (thread-safe after fork)"""
    global _pose
    if _pose is None:
        _pose = mp.solutions.pose.Pose(
            # Optimized for speed - video mode with lite model
            static_image_mode=False,
            model_complexity=0,  # 0 = lite model (fastest)
            smooth_landmarks=True,  # Smooth tracking
            min_detection_confidence=0.3,  # Lower for speed
            min_tracking_confidence=0.3,  # Lower for speed
            enable_segmentation=False  # Disable segmentation for speed
        )
    return _pose


class PatientMetricTrackers:
    """Container for per-patient metric tracking instances"""

    def __init__(self):
        self.heart_rate = HeartRateMonitor()
        self.respiratory_rate = RespiratoryRateMonitor()
        self.face_touching = FaceTouchingDetector()
        self.movement = MovementVolumeTracker()
        self.tremor = TremorDetector()
        self.upper_body = UpperBodyPostureTracker()
        self.analysis_mode: str = "normal"  # "normal" or "enhanced"


class ConnectionManager:
    def __init__(self):
        self.streamers: Dict[str, WebSocket] = {}  # {patient_id: websocket}
        self.viewers: List[WebSocket] = []
        # {patient_id: trackers}
        self.patient_trackers: Dict[str, PatientMetricTrackers] = {}
        
        # MOVEMENT EMERGENCY DETECTION (Simple & Reliable)
        # {patient_id: SimpleMovementDetector}
        from app.simple_movement_detector import SimpleMovementDetector
        self.movement_detectors: Dict[str, SimpleMovementDetector] = {}

        # Queue-based processing (one queue per patient)
        # {patient_id: queue}
        self.processing_queues: Dict[str, queue.Queue] = {}
        # {patient_id: thread}
        self.worker_threads: Dict[str, threading.Thread] = {}
        # {patient_id: stop_event}
        self.worker_stop_flags: Dict[str, threading.Event] = {}

    def register_streamer(self, patient_id: str, websocket: WebSocket, analysis_mode: Optional[str] = "normal"):
        """Register a streamer for a specific patient"""
        self.streamers[patient_id] = websocket

        # Initialize metric trackers for this patient
        trackers = PatientMetricTrackers()
        trackers.analysis_mode = analysis_mode if analysis_mode in [
            "normal", "enhanced"] else "normal"
        self.patient_trackers[patient_id] = trackers
        
        # Initialize simple movement detector for this patient
        from app.simple_movement_detector import SimpleMovementDetector
        self.movement_detectors[patient_id] = SimpleMovementDetector()
        print(f"✓ Simple movement detector initialized for {patient_id}")

        # Start dedicated processing worker for this patient
        self.processing_queues[patient_id] = queue.Queue(
            maxsize=2)  # Small queue, discard old frames
        self.worker_stop_flags[patient_id] = threading.Event()

        worker = threading.Thread(
            target=self._processing_worker,
            args=(patient_id,),
            daemon=True,
            name=f"CV-Worker-{patient_id}"
        )
        worker.start()
        self.worker_threads[patient_id] = worker

        print(
            f"✅ Registered streamer for patient {patient_id}. Analysis mode: {analysis_mode}. Worker started. Total streamers: {len(self.streamers)}")

    def unregister_streamer(self, patient_id: str):
        """Unregister a streamer for a specific patient"""
        # Stop worker thread
        if patient_id in self.worker_stop_flags:
            self.worker_stop_flags[patient_id].set()

        if patient_id in self.worker_threads:
            worker = self.worker_threads[patient_id]
            worker.join(timeout=2.0)  # Wait up to 2 seconds
            del self.worker_threads[patient_id]

        if patient_id in self.processing_queues:
            # Clear the queue before deleting
            try:
                while True:
                    self.processing_queues[patient_id].get_nowait()
            except queue.Empty:
                pass
            del self.processing_queues[patient_id]

        if patient_id in self.worker_stop_flags:
            del self.worker_stop_flags[patient_id]

        if patient_id in self.streamers:
            del self.streamers[patient_id]

        if patient_id in self.patient_trackers:
            del self.patient_trackers[patient_id]
        
        # Clean up fetch health agent state
        from app.fetch_health_agent import fetch_health_agent
        if patient_id in fetch_health_agent.patients:
            del fetch_health_agent.patients[patient_id]
            print(f"🧹 Cleaned up health agent data for {patient_id}")

        print(
            f"❌ Unregistered streamer for patient {patient_id}. Worker stopped. Total streamers: {len(self.streamers)}")

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

    def queue_frame_for_processing(self, patient_id: str, frame_data: str, frame_num: int):
        """Add frame to processing queue (non-blocking, discards if full)"""
        if patient_id not in self.processing_queues:
            return

        try:
            # Non-blocking put - if queue is full, discard frame (keep video real-time)
            self.processing_queues[patient_id].put_nowait({
                "frame_data": frame_data,
                "frame_num": frame_num
            })
        except queue.Full:
            # Queue full, skip this frame (worker is busy)
            pass

    def _processing_worker(self, patient_id: str):
        """
        Worker thread that processes frames sequentially (NO concurrency = NO lock needed)
        Runs in background, processes one frame at a time
        """
        import asyncio

        print(f"🔧 CV Worker started for patient {patient_id}")

        frame_count = 0
        last_slow_frame = 0

        while not self.worker_stop_flags[patient_id].is_set():
            try:
                # Double-check stream is still active
                if patient_id not in self.streamers:
                    print(f"⏹️  Worker exiting - {patient_id} stream no longer active")
                    break
                
                # Get trackers to check analysis mode
                trackers = self.get_trackers(patient_id)
                analysis_mode = trackers.analysis_mode if trackers else "normal"

                # Get frame from queue (blocking with timeout)
                frame_task = self.processing_queues[patient_id].get(
                    timeout=0.5)
                frame_data = frame_task["frame_data"]
                frame_num = frame_task["frame_num"]
                frame_count += 1

                # Check analysis mode
                if analysis_mode == "normal":
                    # NORMAL MODE: No AI/CV processing, just send empty overlay
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.broadcast_frame({
                        "type": "overlay_data",
                        "patient_id": patient_id,
                        "frame_num": frame_num,
                        "data": {
                            "landmarks": [],
                            "connections": [],
                            "head_pose_axes": None,
                            "metrics": None
                        }
                    }))
                    loop.close()
                    continue

                # ENHANCED MODE: Full AI/CV analysis
                # Get monitoring config for this patient
                monitoring_config = monitoring_manager.get_config(patient_id)

                # FAST: Process overlay every frame (pose only, ~50ms)
                start_time = time.time()
                fast_result = process_frame_fast(frame_data, patient_id)
                fast_time = time.time() - start_time

                # SLOW: Process metrics at configured frequency (respects monitoring level)
                slow_result = None
                frames_per_interval = monitoring_config.frequency_seconds * 30  # Assume 30 FPS
                if frame_num - last_slow_frame >= frames_per_interval:
                    slow_start = time.time()
                    slow_result = process_frame_metrics(
                        frame_data, patient_id, monitoring_config)
                    slow_time = time.time() - slow_start
                    last_slow_frame = frame_num
                    print(
                        f"📊 Patient {patient_id} - Frame #{frame_num} [{monitoring_config.level}] CRS: {slow_result['metrics'].get('crs_score', 0)}, HR: {slow_result['metrics'].get('heart_rate', 0)} (took {slow_time*1000:.0f}ms)")

                # Merge fast overlays with slow metrics
                overlay_data = {
                    "landmarks": fast_result["landmarks"],
                    "connections": fast_result["connections"],
                    "head_pose_axes": fast_result["head_pose_axes"],
                    "metrics": slow_result["metrics"] if slow_result else None
                }

                # Broadcast overlay data (async operation, need event loop)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.broadcast_frame({
                    "type": "overlay_data",
                    "patient_id": patient_id,
                    "frame_num": frame_num,
                    "data": overlay_data
                }))

                # Agent analysis: if we just calculated metrics, analyze them
                if slow_result and slow_result.get("metrics"):
                    try:
                        # DISABLED: Old "thinking" message (replaced by Fetch.ai Health Agent logs)
                        # loop.run_until_complete(self.broadcast_frame({
                        #     "type": "agent_thinking",
                        #     "patient_id": patient_id,
                        #     "message": "🤖 AI Agent analyzing...",
                        #     "timestamp": time.time()
                        # }))

                        # ====== FETCH.AI HEALTH AGENT (PRIMARY) ======
                        from app.fetch_health_agent import fetch_health_agent
                        from app.voice_call import voice_service
                        
                        # Prepare vitals and CV metrics (NEW MOVEMENT EMERGENCY FOCUS)
                        vitals = {
                            "heart_rate": slow_result["metrics"].get("heart_rate", 75),
                            "temperature": 37.0,  # Would come from sensors in production
                            "blood_pressure": "120/80",  # Would come from sensors
                            "spo2": 98  # Would come from sensors
                        }
                        cv_metrics = {
                            # PRIMARY: Movement emergency detection
                            "movement_event": slow_result["metrics"].get("movement_event", "normal"),
                            "movement_confidence": slow_result["metrics"].get("movement_confidence", 0.0),
                            "movement_details": slow_result["metrics"].get("movement_details", ""),
                            "calibration_status": slow_result["metrics"].get("calibration_status", {}),
                            
                            # SECONDARY: Legacy metrics (keep for context)
                            "respiratory_rate": slow_result["metrics"].get("respiratory_rate", 14),
                            "tremor_detected": slow_result["metrics"].get("tremor_detected", False),
                            "attention_score": slow_result["metrics"].get("attention_score", 0.5)
                        }
                        
                        # Analyze with Fetch.ai Health Agent (NON-BLOCKING)
                        # Run agent in separate thread to never block CV processing
                        from datetime import datetime as dt
                        import threading
                        
                        def agent_worker():
                            """Background thread for agent analysis - never blocks CV"""
                            try:
                                # Check if stream is still active before running agent
                                if patient_id not in self.streamers:
                                    print(f"⏹️  Skipping agent analysis - {patient_id} stream closed")
                                    return
                                
                                # Create new event loop for this thread
                                import asyncio
                                thread_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(thread_loop)
                                
                                # Run analysis
                                analysis = thread_loop.run_until_complete(
                                    fetch_health_agent.analyze_patient(patient_id, vitals, cv_metrics)
                                )
                                
                                # Truncate reasoning for UI (keep first 150 chars)
                                reasoning_full = analysis["reasoning"]
                                reasoning_short = reasoning_full[:150] + "..." if len(reasoning_full) > 150 else reasoning_full
                                
                                # Format action as bullet list (first 3 items only if list)
                                action = analysis["recommended_action"]
                                if isinstance(action, list):
                                    action_short = "\n".join([f"• {a}" for a in action[:3]])
                                    if len(action) > 3:
                                        action_short += f"\n• ...{len(action) - 3} more"
                                else:
                                    action_short = action[:200] + "..." if len(str(action)) > 200 else str(action)
                                
                                # Create log entry for TerminalLog component
                                severity_icon = {
                                    "CRITICAL": "🚨",
                                    "WARNING": "⚠️",
                                    "NORMAL": "✅"
                                }.get(analysis["severity"], "ℹ️")
                                
                                log_message = {
                                    "type": "terminal_log",
                                    "patient_id": patient_id,
                                    "timestamp": dt.now().isoformat(),
                                    "message": f"{severity_icon} Fetch.ai Agent: {analysis['severity']}",
                                    "details": reasoning_short,
                                    "action": action_short
                                }
                                
                                # Also send as alert for AlertPanel
                                alert_message = {
                                    "type": "agent_alert",
                            "patient_id": patient_id,
                                    "severity": analysis["severity"],
                                    "agent": "FETCH_AI_HEALTH_AGENT",
                                    "message": f"Patient {patient_id}: {analysis['severity']}",
                                    "reasoning": reasoning_short,
                                    "recommended_action": action_short,
                                    "concerns": analysis["concerns"],
                                    "confidence": analysis["confidence"],
                                    "timestamp": dt.now().isoformat()
                                }
                                
                                # === EMERGENCY CALL SYSTEM ===
                                # Check if we should make emergency call (throttled to prevent spam)
                                if fetch_health_agent.should_make_emergency_call(patient_id, analysis["severity"]):
                                    movement_event = cv_metrics.get("movement_event", "unknown")
                                    if movement_event in ["seizure", "fall"]:
                                        emergency_msg = f"{movement_event.upper()} DETECTED! Medical help needed!"
                                    elif movement_event == "extreme_agitation":
                                        emergency_msg = "EXTREME AGITATION! Patient needs attention!"
                                    else:
                                        emergency_msg = "ALERT! Patient needs assessment!"
                                    
                                    print(f"📞 CALLING AVAILABLE NURSE: {emergency_msg}")
                                    
                                    # === VONAGE VOICE CALL ===
                                    # Make actual phone call for CRITICAL alerts (only once per cooldown period)
                                    voice_service.make_emergency_call(
                                        patient_id=patient_id,
                                        event_type=movement_event,
                                        details=reasoning_short
                                    )
                                    
                                    # Send call notification FIRST (before other logs)
                                    call_message = {
                                        "type": "emergency_call",
                                        "patient_id": patient_id,
                                        "message": f"📞 Calling nurse: {emergency_msg}",
                                        "severity": analysis["severity"],
                                        "timestamp": dt.now().isoformat()
                                    }
                                    thread_loop.run_until_complete(self.broadcast_frame(call_message))
                                    # Small delay to prevent WebSocket overflow
                                    thread_loop.run_until_complete(asyncio.sleep(0.05))
                                
                                # Send log and alert messages
                                thread_loop.run_until_complete(self.broadcast_frame(log_message))
                                thread_loop.run_until_complete(asyncio.sleep(0.05))
                                thread_loop.run_until_complete(self.broadcast_frame(alert_message))
                                
                                thread_loop.close()
                                
                            except Exception as e:
                                print(f"⚠️ Agent thread error: {e}")
                        
                        # Start agent in background thread - CV processing continues immediately
                        # Only start if stream is still active
                        if patient_id in self.streamers:
                            threading.Thread(target=agent_worker, daemon=True).start()
                        else:
                            print(f"⏹️  Skipping agent thread - {patient_id} stream closed")
                        
                        # LEGACY AGENTS (DISABLED - using Fetch.ai Health Agent instead)
                        # if agent_system.enabled:
                        #     assessment = loop.run_until_complete(
                        #         agent_system.analyze_patient_metrics(patient_id, slow_result["metrics"])
                        #     )
                        # 
                        # decision = patient_guardian.analyze_metrics(patient_id, slow_result["metrics"])
                        # if decision["action"] != "MAINTAIN":
                        #     loop.run_until_complete(
                        #         patient_guardian.execute_decision(patient_id, decision, self)
                        #     )
                    except Exception as e:
                        print(f"⚠️ Agent analysis error: {e}")

                loop.close()

                # Only log if extremely slow (>200ms)
                if fast_time > 0.2:
                    print(f"⚠️ Slow frame {frame_num}: {fast_time*1000:.0f}ms")

            except queue.Empty:
                # No frames to process, continue waiting
                continue
            except Exception as e:
                print(f"❌ Worker error for patient {patient_id}: {e}")
                import traceback
                traceback.print_exc()

        print(f"🔧 CV Worker stopped for patient {patient_id}")

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
        dead = [
            r for r in results if r is not None and not isinstance(r, Exception)]
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

        # AGGRESSIVE downsampling for speed (smaller = faster pose detection)
        small_frame = cv2.resize(frame, (128, 72))
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        resize_time = time.time() - start - decode_time

        # MediaPipe Pose (no lock needed - single worker thread per patient)
        mediapipe_start = time.time()
        pose_model = get_pose()
        pose_results = pose_model.process(rgb_frame)
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
        # Only log if extremely slow (>200ms) to reduce noise
        if total_time > 0.2:
            print(f"⚠️ Slow CV: {total_time*1000:.0f}ms (MP: {mediapipe_time*1000:.0f}ms)")

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


def process_frame_metrics(frame_base64: str, patient_id: Optional[str] = None, monitoring_config=None) -> Dict:
    """
    SLOW: Expensive tracker operations (rPPG, FFT, etc.) - respects monitoring config
    Returns ONLY metrics that are enabled in monitoring_config
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

        # MediaPipe processing (no lock needed - single worker thread per patient)
        face_model = get_face_mesh()
        pose_model = get_pose()
        face_results = face_model.process(rgb_frame)
        pose_results = pose_model.process(rgb_frame)

        # Get trackers for this patient
        trackers = manager.get_trackers(patient_id) if patient_id else None

        # Get enabled metrics from config (default to all if not specified)
        enabled_metrics = monitoring_config.enabled_metrics if monitoring_config else [
            "heart_rate", "respiratory_rate", "crs_score", "face_touching_frequency",
            "restlessness_index", "movement_vigor", "tremor_magnitude", "tremor_detected",
            "head_pitch", "head_yaw", "head_roll", "eye_openness", "attention_score",
            "shoulder_angle", "posture_score", "upper_body_movement", "lean_forward", "arm_asymmetry"
        ]

        # Initialize default values (only for enabled metrics)
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

            # === HEAD POSE ESTIMATION === (only if attention or head pose metrics enabled)
            needs_head_pose = any(m in enabled_metrics for m in [
                                  "head_pitch", "head_yaw", "head_roll", "attention_score"])
            if needs_head_pose:
                model_points = np.array([
                    (0.0, 0.0, 0.0),
                    (0.0, -330.0, -65.0),
                    (-225.0, 170.0, -135.0),
                    (225.0, 170.0, -135.0),
                    (-150.0, -150.0, -125.0),
                    (150.0, -150.0, -125.0)
                ], dtype=np.float64)

                image_points = np.array([
                    (int(landmarks.landmark[1].x * w),
                     int(landmarks.landmark[1].y * h)),
                    (int(landmarks.landmark[152].x * w),
                     int(landmarks.landmark[152].y * h)),
                    (int(landmarks.landmark[263].x * w),
                     int(landmarks.landmark[263].y * h)),
                    (int(landmarks.landmark[33].x * w),
                     int(landmarks.landmark[33].y * h)),
                    (int(landmarks.landmark[287].x * w),
                     int(landmarks.landmark[287].y * h)),
                    (int(landmarks.landmark[57].x * w),
                     int(landmarks.landmark[57].y * h))
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
                    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(
                        pose_mat)
                    head_pitch = float(euler_angles[0][0])
                    head_yaw = float(euler_angles[1][0])
                    head_roll = float(euler_angles[2][0])

            # === EYE OPENNESS === (only if eye_openness or attention_score enabled)
            needs_eye = any(m in enabled_metrics for m in [
                            "eye_openness", "attention_score"])
            if needs_eye:
                left_eye_top = landmarks.landmark[159]
                left_eye_bottom = landmarks.landmark[145]
                right_eye_top = landmarks.landmark[386]
                right_eye_bottom = landmarks.landmark[374]

                left_eye_height = abs(left_eye_top.y - left_eye_bottom.y)
                right_eye_height = abs(right_eye_top.y - right_eye_bottom.y)
                eye_openness = (left_eye_height + right_eye_height) / 2 * 100

            # === ATTENTION SCORE === (only if enabled)
            if "attention_score" in enabled_metrics:
                yaw_factor = max(0, 1 - abs(head_yaw) / 45.0)
                pitch_factor = max(0, 1 - abs(head_pitch) / 30.0)
                eye_factor = min(1.0, eye_openness / 2.0)
                attention_score = (yaw_factor * 0.4 +
                                   pitch_factor * 0.3 + eye_factor * 0.3)

            # === FACIAL FLUSHING (CRS INDICATOR) === (only if crs_score enabled)
            if "crs_score" in enabled_metrics:
                cheek_redness = 0.0
                for idx in [205, 425]:
                    lm = landmarks.landmark[idx]
                    x, y = int(lm.x * w), int(lm.y * h)
                    roi = frame[max(0, y-10):min(h, y+10),
                                max(0, x-10):min(w, x+10)]

                    if roi.size > 0:
                        r = np.mean(roi[:, :, 2])
                        g = np.mean(roi[:, :, 1])
                        b = np.mean(roi[:, :, 0])
                        cheek_redness += (r - (g + b) / 2) / 255.0

                cheek_redness /= 2
                crs_score = min(1.0, max(0.0, cheek_redness * 2.5))

            # === EXPENSIVE TRACKER OPERATIONS === (only if enabled)
            if trackers:
                # rPPG heart rate (FFT on forehead color changes) - expensive!
                if "heart_rate" in enabled_metrics:
                    forehead_lm = landmarks.landmark[10]
                    fx, fy = int(forehead_lm.x * w), int(forehead_lm.y * h)
                    forehead_roi = frame[max(
                        0, fy-30):min(h, fy+10), max(0, fx-40):min(w, fx+40)]
                    heart_rate = trackers.heart_rate.process_frame(frame, forehead_roi)

                # Respiratory rate (FFT on nose movement)
                if "respiratory_rate" in enabled_metrics:
                    nose_y = landmarks.landmark[1].y
                    respiratory_rate = trackers.respiratory_rate.process_frame(nose_y)

                # Face touching detection
                if "face_touching_frequency" in enabled_metrics:
                    face_touching_freq, is_touching = trackers.face_touching.process_frame(
                        landmarks)

                # Movement and restlessness
                if any(m in enabled_metrics for m in ["restlessness_index", "movement_vigor"]):
                    restlessness_index, movement_vigor = trackers.movement.process_frame(
                        landmarks)

                # Tremor detection (FFT on hand positions) - very expensive!
                if any(m in enabled_metrics for m in ["tremor_magnitude", "tremor_detected"]):
                    tremor_magnitude, tremor_detected = trackers.tremor.process_frame(
                        landmarks)

                # Upper body posture tracking
                needs_upper_body = any(m in enabled_metrics for m in [
                                       "shoulder_angle", "posture_score", "upper_body_movement", "lean_forward", "arm_asymmetry"])
                if needs_upper_body and pose_results.pose_landmarks:
                    upper_body_metrics = trackers.upper_body.process_frame(
                        pose_results.pose_landmarks)
            else:
                # Fallback if no trackers - only calculate if enabled
                if "heart_rate" in enabled_metrics:
                    heart_rate = int(75 + (crs_score * 30))
                if "respiratory_rate" in enabled_metrics:
                    respiratory_rate = int(14 + (crs_score * 10))
        
        # === MOVEMENT EMERGENCY DETECTION (NEW - Replacing CRS focus) ===
        movement_event = None
        movement_confidence = 0.0
        movement_details = ""
        calibration_status = {}
        
        # DEBUG: Check if pose data exists
        if not pose_results.pose_landmarks:
            print(f"⚠️ NO POSE LANDMARKS for {patient_id}")
        
        if pose_results.pose_landmarks and patient_id:
            # Get simple movement detector for this patient
            detector = manager.movement_detectors.get(patient_id)
            
            if not detector:
                print(f"❌ NO DETECTOR for {patient_id}")
            else:
                print(f"✅ Processing movement for {patient_id}")
                # Process with simple detector
                movement_result = detector.process(pose_results.pose_landmarks.landmark, time.time())
                
                movement_event = movement_result["event"]
                movement_confidence = movement_result["confidence"]
                movement_details = movement_result["details"]
                # Simple detector doesn't have separate calibration status
                calibration_status = {
                    "calibrated": detector.is_calibrated,
                    "progress": min(100, int((detector.calibration_count / detector.CALIBRATION_FRAMES) * 100)),
                    "message": "✓ Ready" if detector.is_calibrated else "Calibrating..."
                }
        else:
            print(f"⚠️ Skipping movement detection: pose={pose_results.pose_landmarks is not None}, patient={patient_id}")

        # Return ONLY metrics (no overlay data)
        return {
            "metrics": {
                # Basic vitals (CV-derived)
                "heart_rate": int(heart_rate),
                "respiratory_rate": int(respiratory_rate),

                # === MOVEMENT EMERGENCY METRICS (PRIMARY) ===
                "movement_event": movement_event if movement_event else "normal",
                "movement_confidence": float(round(movement_confidence, 2)),
                "movement_details": movement_details,
                "calibration_status": calibration_status,

                # Legacy CRS metrics (kept for backward compat, but downweighted)
                "crs_score": float(round(crs_score, 2)),
                "face_touching_frequency": int(face_touching_freq),
                "restlessness_index": float(round(restlessness_index, 2)),

                # Legacy tremor metrics (now replaced by movement event seizure detection)
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

                # Alerts (now based on movement events)
                "alert": bool(movement_event in ["fall", "seizure", "extreme_agitation"]),
                "alert_triggers": list(filter(None, [
                    f"{movement_event.upper()}: {movement_details}" if movement_event and movement_event != "normal" else None
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
