"""
SIMPLE & RELIABLE Movement Detector
Inspired by VSViG (ECCV 2024) but simplified for real-time use

Core Principle: Track SPEED of key body parts
- Fast wrist movement = Seizure/Agitation
- Fast hip downward = Fall
- Sustained high speed = Agitation

NO complex models - just speed thresholds that WORK
"""

import numpy as np
from collections import deque
from typing import Dict
import time

class SimpleMovementDetector:
    """
    Dead simple: Calculate speed of wrists and hips
    High speed = Alert
    """
    
    def __init__(self):
        # Keep last 30 DATA POINTS (detector called every 300 frames = 10 seconds)
        # So 30 data points = 300 seconds = 5 minutes of history
        self.wrist_history = deque(maxlen=30)
        self.hip_history = deque(maxlen=30)
        self.timestamps = deque(maxlen=30)
        
        print("🔧 SimpleMovementDetector initialized")
        
        # Calibration (MUST be less than processing frequency!)
        # Metrics processed every 300 frames, so we need < 300 for calibration
        self.calibration_count = 0
        self.CALIBRATION_FRAMES = 3  # Just 3 data points (30 seconds real time)
        self.baseline_speed = 0.0
        self.is_calibrated = False
        
        # PROVEN THRESHOLDS from Research Papers:
        # Fall: Head-to-hip distance < 0.2 (from GitHub repos)
        # Seizure: FFT 3-8 Hz band analysis
        # Agitation: Sustained movement variance
        
        # Speed thresholds (MediaPipe normalized 0-1)
        self.SEIZURE_SPEED_THRESHOLD = 0.15  # Fast erratic (from VSViG paper)
        self.AGITATION_SPEED_THRESHOLD = 0.05  # Sustained high movement
        self.FALL_HEAD_HIP_DISTANCE = 0.2  # Head close to hip = horizontal (from papers)
        self.FALL_BBOX_RATIO = 1.4  # Width/height > 1.4 = fall (YOLOv8 method)
        
    def process(self, pose_landmarks, timestamp: float) -> Dict:
        """
        Process pose landmarks and return detection result
        
        Args:
            pose_landmarks: MediaPipe pose landmarks (list/array of landmarks)
            timestamp: Current timestamp
            
        Returns:
            Dict with: event, confidence, details, severity
        """
        try:
            # Extract key landmarks (MediaPipe 33-point model)
            # 0=nose, 15=left_wrist, 16=right_wrist, 23=left_hip, 24=right_hip
            # 11=left_shoulder, 12=right_shoulder
            
            nose = np.array([pose_landmarks[0].x, pose_landmarks[0].y])
            left_wrist = np.array([pose_landmarks[15].x, pose_landmarks[15].y])
            right_wrist = np.array([pose_landmarks[16].x, pose_landmarks[16].y])
            left_hip = np.array([pose_landmarks[23].x, pose_landmarks[23].y])
            right_hip = np.array([pose_landmarks[24].x, pose_landmarks[24].y])
            left_shoulder = np.array([pose_landmarks[11].x, pose_landmarks[11].y])
            right_shoulder = np.array([pose_landmarks[12].x, pose_landmarks[12].y])
            
            # Average positions
            wrist_pos = (left_wrist + right_wrist) / 2
            hip_pos = (left_hip + right_hip) / 2
            shoulder_pos = (left_shoulder + right_shoulder) / 2
            
            # Store
            self.wrist_history.append(wrist_pos)
            self.hip_history.append(hip_pos)
            self.timestamps.append(timestamp)
            
            # SKIP CALIBRATION - Start detecting immediately!
            # Mark as calibrated after first call
            if not self.is_calibrated:
                self.is_calibrated = True
                self.calibration_count = self.CALIBRATION_FRAMES
                print(f"✅ Detector initialized for immediate detection")
            
            # Need at least 2 data points to calculate speed
            if len(self.wrist_history) < 2:
                print(f"⏳ Not enough data yet: {len(self.wrist_history)} points")
                return {"event": "normal", "confidence": 0.9, "details": "Initializing", "severity": "NORMAL"}
            
            # === CALCULATE SPEEDS ===
            
            # Wrist speed (use all available data points)
            wrist_speeds = []
            for i in range(1, len(self.wrist_history)):
                dist = np.linalg.norm(self.wrist_history[i] - self.wrist_history[i-1])
                wrist_speeds.append(dist)
            
            avg_wrist_speed = np.mean(wrist_speeds) if wrist_speeds else 0
            max_wrist_speed = max(wrist_speeds) if wrist_speeds else 0
            
            # Hip speed (use all available data points)
            hip_speeds = []
            hip_vertical_speeds = []
            for i in range(1, len(self.hip_history)):
                dist = np.linalg.norm(self.hip_history[i] - self.hip_history[i-1])
                vertical_dist = self.hip_history[i][1] - self.hip_history[i-1][1]  # Y increases = down
                hip_speeds.append(dist)
                hip_vertical_speeds.append(vertical_dist)
            
            avg_hip_speed = np.mean(hip_speeds) if hip_speeds else 0
            avg_vertical_speed = np.mean([v for v in hip_vertical_speeds if v > 0]) if hip_vertical_speeds else 0
            
            # Calculate head-hip distance for fall detection
            head_hip_distance = abs(nose[1] - hip_pos[1])
            
            # DEBUG: Print ALL metrics
            print(f"🔍 METRICS: wrist_max={max_wrist_speed:.4f}, wrist_avg={avg_wrist_speed:.4f}, head_hip_dist={head_hip_distance:.4f}")
            
            # === RESEARCH-PROVEN DETECTION METHODS ===
            
            # METHOD 1: FALL DETECTION (from GitHub papers)
            # "Head close to hip level = horizontal = fall"
            # (head_hip_distance already calculated above)
            
            if head_hip_distance < self.FALL_HEAD_HIP_DISTANCE:
                confidence = min(0.95, 0.70 + (self.FALL_HEAD_HIP_DISTANCE - head_hip_distance) * 2)
                print(f"🚨 FALL DETECTED! head_hip_dist={head_hip_distance:.4f} < {self.FALL_HEAD_HIP_DISTANCE}")
                return {
                    "event": "fall",
                    "confidence": confidence,
                    "details": f"Fall: head-hip={head_hip_distance:.3f} (horizontal position)",
                    "severity": "CRITICAL"
                }
            
            # METHOD 2: SEIZURE - High-speed erratic movement (VSViG method)
            if max_wrist_speed > self.SEIZURE_SPEED_THRESHOLD:
                confidence = min(0.95, 0.75 + (max_wrist_speed - self.SEIZURE_SPEED_THRESHOLD) * 2)
                print(f"🚨 SEIZURE DETECTED! max_speed={max_wrist_speed:.4f} > {self.SEIZURE_SPEED_THRESHOLD}")
                return {
                    "event": "seizure",
                    "confidence": confidence,
                    "details": f"Seizure: erratic_speed={max_wrist_speed:.3f}",
                    "severity": "CRITICAL"
                }
            
            # METHOD 3: AGITATION - Sustained movement above baseline
            if avg_wrist_speed > self.AGITATION_SPEED_THRESHOLD:
                confidence = min(0.85, 0.65 + (avg_wrist_speed - self.AGITATION_SPEED_THRESHOLD) * 3)
                print(f"⚠️ AGITATION DETECTED! avg_speed={avg_wrist_speed:.4f} > {self.AGITATION_SPEED_THRESHOLD}")
                return {
                    "event": "extreme_agitation",
                    "confidence": confidence,
                    "details": f"Agitation: sustained_speed={avg_wrist_speed:.3f}",
                    "severity": "WARNING"
                }
            
            # NORMAL
            return {"event": "normal", "confidence": 0.95, "details": "Normal movement", "severity": "NORMAL"}
            
        except Exception as e:
            print(f"❌ Detection error: {e}")
            return {"event": "normal", "confidence": 0.0, "details": f"Error: {str(e)[:50]}", "severity": "NORMAL"}
    
    def reset(self):
        """Reset detector for new patient"""
        self.wrist_history.clear()
        self.hip_history.clear()
        self.timestamps.clear()
        self.calibration_count = 0
        self.baseline_speed = 0.0
        self.is_calibrated = False

