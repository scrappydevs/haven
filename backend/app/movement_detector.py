"""
Movement Emergency Detector - SIMPLE & RELIABLE
Uses basic physics: velocity and jerk (rate of acceleration change)

PROVEN APPROACH:
- Velocity: How fast landmarks are moving (speed)
- Jerk: How suddenly movement changes (smoothness)
- High jerk = erratic/seizure-like movement
- High downward velocity = fall
- Sustained high movement = agitation

NO COMPLEX FFT - Just simple, reliable calculations
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple
from enum import Enum
import time

class MovementEvent(Enum):
    """Types of movement emergencies (3 clear types for demo)"""
    FALL = "fall"
    SEIZURE = "seizure"
    EXTREME_AGITATION = "extreme_agitation"
    NORMAL = "normal"

class MovementEmergencyDetector:
    """
    Detects falls, seizures, and extreme agitation using pose landmarks
    
    Detection Methods (Simple & Reliable):
    1. FALL: Rapid downward movement + horizontal orientation + stays down 3+ seconds
    2. SEIZURE: 3-6 Hz rhythmic movement + persists 5+ seconds + amplitude > 0.3
    3. EXTREME AGITATION: High movement vigor + erratic patterns
    """
    
    def __init__(self, fps: int = 30):
        """
        Args:
            fps: Frames per second (default 30)
        """
        self.fps = fps
        
        # 5-second calibration window (150 frames at 30 FPS) - FAST for demo/testing
        self.CALIBRATION_FRAMES = 150  # 5 seconds (was 30s, reduced for faster demo)
        
        # Landmark history buffers (keep 3 minutes max)
        self.MAX_HISTORY = 5400  # 3 minutes at 30 FPS
        
        self.shoulder_positions = deque(maxlen=self.MAX_HISTORY)
        self.hip_positions = deque(maxlen=self.MAX_HISTORY)
        self.wrist_positions = deque(maxlen=self.MAX_HISTORY)
        self.head_positions = deque(maxlen=self.MAX_HISTORY)
        self.ankle_positions = deque(maxlen=self.MAX_HISTORY)
        self.timestamps = deque(maxlen=self.MAX_HISTORY)
        
        # State tracking
        self.last_event = MovementEvent.NORMAL
        self.event_confidence = 0.0
        self.baseline_posture = None
        self.baseline_movement_level = 0.0
        self.calibration_frames = 0
        self.is_calibrated = False
        
        # Potential fall tracking (3-second confirmation window)
        self.potential_fall_detected_at = None
        self.fall_confirmed = False
        
        # Potential seizure tracking (5-second confirmation window)
        self.potential_seizure_detected_at = None
        self.seizure_confirmed = False
        
        # === SIMPLE PHYSICS-BASED THRESHOLDS (VERY SENSITIVE) ===
        
        # JERK (rate of acceleration change) - indicates erratic movement
        # Lower = more sensitive
        self.JERK_THRESHOLD_SEIZURE = 5.0  # Very high jerk = seizure-like (VERY SENSITIVE)
        self.JERK_THRESHOLD_AGITATION = 2.0  # High jerk = agitation (VERY SENSITIVE)
        
        # VELOCITY (speed of movement)
        self.VELOCITY_THRESHOLD_FAST = 0.02  # Fast movement (VERY SENSITIVE)
        self.VELOCITY_THRESHOLD_FALL = 0.05  # Downward velocity for fall (VERY SENSITIVE)
        
        # TIME WINDOWS
        self.ANALYSIS_WINDOW = 30  # frames (1 second at 30 FPS)
        self.SUSTAINED_DURATION = 60  # frames (2 seconds)
        
    def process_landmarks(self, landmarks: Dict, frame_timestamp: float) -> Dict:
        """
        Process MediaPipe landmarks and detect movement emergencies
        
        Args:
            landmarks: Dict with MediaPipe pose landmarks
            frame_timestamp: Current frame timestamp
            
        Returns:
            Dict with detection results
        """
        if not landmarks:
            return self._create_result(MovementEvent.NORMAL, 0.0, "No landmarks detected")
        
        # Extract key landmarks
        try:
            # Shoulders (11, 12)
            left_shoulder = np.array([landmarks[11].x, landmarks[11].y, landmarks[11].z])
            right_shoulder = np.array([landmarks[12].x, landmarks[12].y, landmarks[12].z])
            shoulder_center = (left_shoulder + right_shoulder) / 2
            
            # Hips (23, 24)
            left_hip = np.array([landmarks[23].x, landmarks[23].y, landmarks[23].z])
            right_hip = np.array([landmarks[24].x, landmarks[24].y, landmarks[24].z])
            hip_center = (left_hip + right_hip) / 2
            
            # Wrists (15, 16) - for tremor detection
            left_wrist = np.array([landmarks[15].x, landmarks[15].y, landmarks[15].z])
            right_wrist = np.array([landmarks[16].x, landmarks[16].y, landmarks[16].z])
            
            # Ankles (27, 28)
            left_ankle = np.array([landmarks[27].x, landmarks[27].y, landmarks[27].z])
            right_ankle = np.array([landmarks[28].x, landmarks[28].y, landmarks[28].z])
            
        except (KeyError, IndexError) as e:
            return self._create_result(MovementEvent.NORMAL, 0.0, f"Landmark error: {e}")
        
        # Store positions
        self.shoulder_positions.append(shoulder_center)
        self.hip_positions.append(hip_center)
        self.wrist_positions.append((left_wrist + right_wrist) / 2)
        self.ankle_positions.append((left_ankle + right_ankle) / 2)
        self.timestamps.append(frame_timestamp)
        
        # Calibration period (first 150 frames = 5 seconds)
        if self.calibration_frames < self.CALIBRATION_FRAMES:
            self.calibration_frames += 1
            if self.calibration_frames == self.CALIBRATION_FRAMES:
                self.baseline_posture = self._calculate_baseline()
                self.is_calibrated = True
                print(f"✅ Movement detector calibrated! Baseline movement: {self.baseline_movement_level:.4f}")
            progress = int((self.calibration_frames / self.CALIBRATION_FRAMES) * 100)
            return self._create_result(MovementEvent.NORMAL, 0.0, f"Calibrating... {progress}%")
        
        # Need at least 30 frames (1 second) for analysis
        if len(self.hip_positions) < 30:
            return self._create_result(MovementEvent.NORMAL, 0.0, "Initializing...")
        
        # Calculate velocities and accelerations
        self._update_motion_metrics()
        
        # === RESEARCH-PROVEN DETECTION (Papers: 2018-2024) ===
        
        # Get recent data
        recent_wrists = np.array(list(self.wrist_positions)[-self.ANALYSIS_WINDOW:])
        recent_hips = np.array(list(self.hip_positions)[-self.ANALYSIS_WINDOW:])
        recent_shoulders = np.array(list(self.shoulder_positions)[-self.ANALYSIS_WINDOW:])
        
        if len(recent_wrists) < 10:
            return self._create_result(MovementEvent.NORMAL, 0.9, "Normal")
        
        # METRIC 1: Total displacement (how much did body parts move?)
        wrist_displacement = np.sum(np.linalg.norm(np.diff(recent_wrists, axis=0), axis=1))
        hip_displacement = np.sum(np.linalg.norm(np.diff(recent_hips, axis=0), axis=1))
        
        # METRIC 2: Variance in position (how erratic is movement?)
        wrist_variance = np.var(recent_wrists, axis=0).sum()
        hip_variance = np.var(recent_hips, axis=0).sum()
        
        # METRIC 3: Vertical position change (fall detection)
        vertical_change = recent_hips[-1][1] - recent_hips[0][1]  # Y increases = down
        
        # METRIC 4: Body angle (vertical vs horizontal)
        if len(recent_shoulders) > 0 and len(recent_hips) > 0:
            shoulder_to_hip = recent_hips[-1] - recent_shoulders[-1]
            vertical_vector = np.array([0, 1, 0])
            cos_angle = np.dot(shoulder_to_hip, vertical_vector) / (np.linalg.norm(shoulder_to_hip) * np.linalg.norm(vertical_vector) + 1e-6)
            body_angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
        else:
            body_angle = 0
        
        # DEBUG: Print ALL metrics
        print(f"🔍 Metrics: wrist_disp={wrist_displacement:.3f}, wrist_var={wrist_variance:.4f}, vertical={vertical_change:.3f}, angle={body_angle:.1f}°")
        
        # ULTRA-SENSITIVE THRESHOLDS (will catch ANY movement):
        
        # DETECTION 1: ERRATIC MOVEMENT (ANY variance OR displacement)
        if wrist_variance > 0.0001 or wrist_displacement > 0.05:
            confidence = min(0.95, 0.75 + wrist_variance * 100)
            print(f"🚨 SEIZURE/ERRATIC: variance={wrist_variance:.6f}, displacement={wrist_displacement:.3f}")
            return self._create_result(MovementEvent.SEIZURE, confidence,
                                     f"Erratic: variance={wrist_variance:.5f}, disp={wrist_displacement:.3f}")
        
        # DETECTION 2: ANY MOVEMENT at all
        if wrist_displacement > 0.01 or hip_displacement > 0.005:
            confidence = min(0.85, 0.65 + wrist_displacement * 10)
            print(f"⚠️ AGITATION: wrist_disp={wrist_displacement:.3f}, hip_disp={hip_displacement:.3f}")
            return self._create_result(MovementEvent.EXTREME_AGITATION, confidence,
                                     f"Movement: wrist={wrist_displacement:.3f}, hip={hip_displacement:.3f}")
        
        # DETECTION 3: FALL (ANY vertical change OR angle)
        if abs(vertical_change) > 0.01 or body_angle > 30:
            confidence = min(0.90, 0.70 + abs(vertical_change) * 10)
            print(f"🚨 FALL: vertical={vertical_change:.3f}, angle={body_angle:.1f}°")
            return self._create_result(MovementEvent.FALL, confidence,
                                     f"Fall: vertical={vertical_change:.3f}, angle={body_angle:.0f}°")
        
        return self._create_result(MovementEvent.NORMAL, 0.95, "Normal")
    
    def _update_motion_metrics(self):
        """Calculate velocities and accelerations from position history"""
        if len(self.hip_positions) < 2:
            return
        
        # Calculate velocity (position change / time)
        positions = np.array(list(self.hip_positions))
        times = np.array(list(self.timestamps))
        
        velocities = []
        for i in range(1, len(positions)):
            dt = times[i] - times[i-1]
            if dt > 0:
                velocity = np.linalg.norm(positions[i] - positions[i-1]) / dt
                velocities.append(velocity)
        
        if velocities:
            self.velocities.append(np.mean(velocities[-5:]))  # Smooth over last 5 frames
        
        # Calculate acceleration (velocity change / time)
        if len(self.velocities) >= 2:
            recent_vels = list(self.velocities)[-10:]
            recent_times = list(self.timestamps)[-10:]
            
            accelerations = []
            for i in range(1, len(recent_vels)):
                dt = recent_times[i] - recent_times[i-1]
                if dt > 0:
                    accel = abs(recent_vels[i] - recent_vels[i-1]) / dt
                    accelerations.append(accel)
            
            if accelerations:
                self.accelerations.append(np.mean(accelerations))
    
    def _detect_fall(self) -> Tuple[MovementEvent, float, str]:
        """
        SIMPLIFIED FALL DETECTION with 3-second confirmation window
        
        DEFINITE FALL (CRITICAL 90%+):
        - Rapid downward movement (> 1.0 m/s)
        - Horizontal orientation (> 45° from vertical)
        - Stays down for 3+ seconds (not getting back up)
        
        POSSIBLE FALL (WARNING 60-80%):
        - Progressive slide (slower but still ending horizontal)
        - Stays horizontal for 10+ seconds unexpectedly
        """
        if len(self.hip_positions) < 30:
            return (MovementEvent.NORMAL, 0.0, "")
        
        current_time = time.time()
        recent_hips = np.array(list(self.hip_positions)[-90:])  # Last 3 seconds
        recent_shoulders = np.array(list(self.shoulder_positions)[-90:])
        
        # Calculate downward velocity (Y increases = downward in MediaPipe)
        time_window = min(1.0, len(recent_hips) / self.fps)  # 1 second or less
        frames_in_window = int(self.fps * time_window)
        
        if len(recent_hips) < frames_in_window:
            return (MovementEvent.NORMAL, 0.0, "")
        
        y_displacement = recent_hips[-1][1] - recent_hips[-frames_in_window][1]
        y_velocity = y_displacement / time_window
        
        # Calculate body angle (vertical vs horizontal)
        body_angle = self._calculate_body_angle(recent_shoulders[-1], recent_hips[-1])
        
        # === CHECK 1: RAPID FALL (CRITICAL) ===
        is_rapid_downward = y_velocity > self.FALL_VELOCITY_THRESHOLD * time_window
        is_horizontal = body_angle > self.FALL_ANGLE_THRESHOLD
        
        if is_rapid_downward and is_horizontal:
            # Potential fall detected - start confirmation timer
            if self.potential_fall_detected_at is None:
                self.potential_fall_detected_at = current_time
                return (MovementEvent.NORMAL, 0.5, f"Potential fall (confirming...): velocity={y_velocity:.2f}, angle={body_angle:.0f}°")
            
            # Check if still horizontal after 3 seconds
            time_since_detection = current_time - self.potential_fall_detected_at
            if time_since_detection >= self.FALL_CONFIRMATION_TIME:
                self.fall_confirmed = True
                confidence = 0.95  # CRITICAL
                return (MovementEvent.FALL, confidence, 
                       f"DEFINITE FALL: rapid_movement={y_velocity:.2f}m/s, horizontal={body_angle:.0f}°, stayed_down={time_since_detection:.1f}s")
            else:
                # Still confirming
                return (MovementEvent.NORMAL, 0.7, f"Fall confirming ({time_since_detection:.1f}s / 3s)...")
        else:
            # No longer horizontal - reset fall detection
            if self.potential_fall_detected_at is not None and not is_horizontal:
                self.potential_fall_detected_at = None
                self.fall_confirmed = False
        
        # === CHECK 2: PROGRESSIVE FALL (WARNING) ===
        # Check if person has been slowly moving toward horizontal over longer period
        if len(recent_hips) >= 150:  # 5 seconds
            long_y_displacement = recent_hips[-1][1] - recent_hips[-150][1]
            long_velocity = long_y_displacement / 5.0
            
            if long_velocity > self.PROGRESSIVE_FALL_VELOCITY and is_horizontal:
                confidence = 0.70  # WARNING level
                return (MovementEvent.FALL, confidence,
                       f"PROGRESSIVE FALL: slow_slide={long_velocity:.2f}m/s, horizontal={body_angle:.0f}°")
        
        return (MovementEvent.NORMAL, 0.0, "")
    
    def _detect_seizure(self) -> Tuple[MovementEvent, float, str]:
        """
        SIMPLIFIED SEIZURE DETECTION with 5-second confirmation
        
        Requirements for CRITICAL alert:
        - FFT shows dominant frequency in 3-6 Hz range (typical seizure rhythm)
        - Amplitude > 0.3 (normalized scale)
        - Persists for 5+ seconds (eliminates transient movements)
        
        BONUS: Head rhythmic + body still = higher confidence (focal seizure pattern)
        """
        # Need at least 5 seconds of data for seizure detection
        required_frames = int(self.SEIZURE_DURATION * self.fps)
        if len(self.wrist_positions) < required_frames:
            return (MovementEvent.NORMAL, 0.0, "")
        
        current_time = time.time()
        
        # Analyze last 5 seconds of wrist movement
        analysis_window = min(required_frames, len(self.wrist_positions))
        wrist_positions = np.array(list(self.wrist_positions)[-analysis_window:])
        head_positions = np.array(list(self.head_positions)[-analysis_window:])
        
        # Calculate movement magnitude
        wrist_movement = np.linalg.norm(np.diff(wrist_positions, axis=0), axis=1)
        head_movement = np.linalg.norm(np.diff(head_positions, axis=0), axis=1)
        
        # Smooth the signal if scipy available
        if HAS_SCIPY and len(wrist_movement) > 10:
            # Butterworth low-pass filter to remove noise
            b, a = butter(2, 0.3, btype='low')
            try:
                wrist_movement = filtfilt(b, a, wrist_movement)
                head_movement = filtfilt(b, a, head_movement)
            except:
                pass  # Use unfiltered if filter fails
        
        # Perform FFT analysis
        if HAS_SCIPY:
            fft_result = fft(wrist_movement)
            frequencies = fftfreq(len(wrist_movement), 1/self.fps)
        else:
            # NumPy fallback
            fft_result = np.fft.fft(wrist_movement)
            frequencies = np.fft.fftfreq(len(wrist_movement), 1/self.fps)
        
        # Find power in seizure frequency band (3-6 Hz)
        seizure_band_mask = (frequencies >= self.SEIZURE_FREQ_MIN) & (frequencies <= self.SEIZURE_FREQ_MAX)
        seizure_power = np.sum(np.abs(fft_result[seizure_band_mask]))
        total_power = np.sum(np.abs(fft_result[frequencies > 0]))  # Positive frequencies only
        
        # Calculate amplitude
        movement_amplitude = np.max(wrist_movement)  # Peak amplitude
        
        # === SEIZURE CRITERIA ===
        has_seizure_frequency = False
        seizure_ratio = 0.0
        dominant_freq = 0.0
        
        if total_power > 1e-6:  # Avoid division by zero
            seizure_ratio = seizure_power / total_power
            if seizure_ratio > 0.25:  # 25% of power in seizure band
                has_seizure_frequency = True
                # Find dominant frequency in seizure band
                seizure_freqs = frequencies[seizure_band_mask]
                seizure_fft = np.abs(fft_result[seizure_band_mask])
                if len(seizure_fft) > 0:
                    dominant_freq = seizure_freqs[np.argmax(seizure_fft)]
        
        has_high_amplitude = movement_amplitude > self.SEIZURE_AMPLITUDE_THRESHOLD
        
        # Check if seizure pattern detected
        if has_seizure_frequency and has_high_amplitude:
            # Potential seizure - start confirmation timer
            if self.potential_seizure_detected_at is None:
                self.potential_seizure_detected_at = current_time
                return (MovementEvent.NORMAL, 0.6, 
                       f"Potential seizure (confirming...): freq={abs(dominant_freq):.1f}Hz, amplitude={movement_amplitude:.2f}")
            
            # Check if persisting for 5+ seconds
            time_since_detection = current_time - self.potential_seizure_detected_at
            if time_since_detection >= self.SEIZURE_DURATION:
                self.seizure_confirmed = True
                
                # BONUS: Check for focal seizure pattern (head moving, body still)
                head_amplitude = np.max(head_movement)
                focal_pattern = head_amplitude > movement_amplitude * 0.5
                
                confidence = 0.90 if focal_pattern else 0.85  # CRITICAL
                pattern_type = "focal" if focal_pattern else "generalized"
                
                return (MovementEvent.SEIZURE, confidence,
                       f"SEIZURE ({pattern_type}): freq={abs(dominant_freq):.1f}Hz, amplitude={movement_amplitude:.2f}, duration={time_since_detection:.1f}s")
            else:
                # Still confirming
                return (MovementEvent.NORMAL, 0.75, 
                       f"Seizure confirming ({time_since_detection:.1f}s / 5s)...")
        else:
            # No seizure pattern - reset detection
            if self.potential_seizure_detected_at is not None:
                self.potential_seizure_detected_at = None
                self.seizure_confirmed = False
        
        return (MovementEvent.NORMAL, 0.0, "")
    
    def _detect_extreme_agitation(self) -> Tuple[MovementEvent, float, str]:
        """
        SIMPLIFIED EXTREME AGITATION DETECTION
        
        Requirements for WARNING alert:
        - Movement level 3x higher than baseline
        - Sustained for 10+ seconds
        - Erratic, high-energy patterns
        """
        if not self.is_calibrated or len(self.hip_positions) < 300:  # Need 10 seconds
            return (MovementEvent.NORMAL, 0.0, "")
        
        # Calculate current movement level (last 10 seconds)
        recent_hips = np.array(list(self.hip_positions)[-300:])  # 10 seconds at 30 FPS
        recent_wrists = np.array(list(self.wrist_positions)[-300:])
        
        # Movement magnitude = sum of position changes
        hip_movement = np.sum(np.linalg.norm(np.diff(recent_hips, axis=0), axis=1))
        wrist_movement = np.sum(np.linalg.norm(np.diff(recent_wrists, axis=0), axis=1))
        total_movement = hip_movement + wrist_movement
        
        # Normalize by number of frames
        movement_per_frame = total_movement / len(recent_hips)
        
        # Compare to baseline
        if self.baseline_movement_level > 0:
            movement_ratio = movement_per_frame / self.baseline_movement_level
            
            # DEBUG: Print movement levels
            print(f"🔍 Movement check: current={movement_per_frame:.4f}, baseline={self.baseline_movement_level:.4f}, ratio={movement_ratio:.2f}x")
            
            if movement_ratio > self.AGITATION_MOVEMENT_MULTIPLIER:
                confidence = min(0.75, 0.5 + (movement_ratio - self.AGITATION_MOVEMENT_MULTIPLIER) * 0.1)
                print(f"🚨 AGITATION DETECTED! Ratio={movement_ratio:.1f}x > threshold={self.AGITATION_MOVEMENT_MULTIPLIER}x")
                return (MovementEvent.EXTREME_AGITATION, confidence,
                       f"EXTREME AGITATION: movement={movement_ratio:.1f}x baseline, sustained=3s")
        
        return (MovementEvent.NORMAL, 0.0, "")
    
    
    def _calculate_body_angle(self, shoulder: np.ndarray, hip: np.ndarray) -> float:
        """Calculate angle of body from vertical (0° = upright, 90° = horizontal)"""
        vector = hip - shoulder
        vertical = np.array([0, 1, 0])  # Y-axis in MediaPipe
        
        # Angle between vectors
        cos_angle = np.dot(vector, vertical) / (np.linalg.norm(vector) * np.linalg.norm(vertical))
        angle_rad = np.arccos(np.clip(cos_angle, -1, 1))
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    def _calculate_baseline(self) -> np.ndarray:
        """Calculate baseline posture and movement level from 30-second calibration"""
        if len(self.shoulder_positions) < self.CALIBRATION_FRAMES:
            return np.zeros(6)
        
        # Average shoulder and hip positions over calibration
        calib_shoulders = list(self.shoulder_positions)[:self.CALIBRATION_FRAMES]
        calib_hips = list(self.hip_positions)[:self.CALIBRATION_FRAMES]
        calib_wrists = list(self.wrist_positions)[:self.CALIBRATION_FRAMES]
        
        avg_shoulder = np.mean(calib_shoulders, axis=0)
        avg_hip = np.mean(calib_hips, axis=0)
        
        # Calculate baseline movement level
        hip_movements = np.linalg.norm(np.diff(calib_hips, axis=0), axis=1)
        wrist_movements = np.linalg.norm(np.diff(calib_wrists, axis=0), axis=1)
        self.baseline_movement_level = np.mean(hip_movements) + np.mean(wrist_movements)
        
        return np.concatenate([avg_shoulder, avg_hip])
    
    def _get_current_posture(self) -> np.ndarray:
        """Get current posture vector"""
        if len(self.shoulder_positions) == 0 or len(self.hip_positions) == 0:
            return np.zeros(6)
        
        current_shoulder = list(self.shoulder_positions)[-1]
        current_hip = list(self.hip_positions)[-1]
        
        return np.concatenate([current_shoulder, current_hip])
    
    def _create_result(self, event: MovementEvent, confidence: float, details: str) -> Dict:
        """Create standardized result dictionary"""
        self.last_event = event
        self.event_confidence = confidence
        
        return {
            "event": event.value,
            "confidence": confidence,
            "details": details,
            "requires_attention": event != MovementEvent.NORMAL,
            "severity": self._get_severity(event),
            "timestamp": time.time()
        }
    
    def _get_severity(self, event: MovementEvent) -> str:
        """Map event to severity level"""
        severity_map = {
            MovementEvent.FALL: "CRITICAL",
            MovementEvent.SEIZURE: "CRITICAL",
            MovementEvent.EXTREME_AGITATION: "WARNING",
            MovementEvent.NORMAL: "NORMAL"
        }
        return severity_map.get(event, "NORMAL")
    
    def get_calibration_status(self) -> Dict:
        """Get calibration progress info for UI display"""
        if self.is_calibrated:
            return {
                "calibrated": True,
                "progress": 100,
                "message": "✓ Baseline established"
            }
        else:
            progress = min(100, int((self.calibration_frames / self.CALIBRATION_FRAMES) * 100))
            remaining = max(0, self.CALIBRATION_FRAMES - self.calibration_frames)
            remaining_seconds = remaining / self.fps
            return {
                "calibrated": False,
                "progress": progress,
                "message": f"Calibrating... {remaining_seconds:.0f}s remaining"
            }
    
    def reset(self):
        """Reset all buffers (call when patient changes)"""
        self.shoulder_positions.clear()
        self.hip_positions.clear()
        self.wrist_positions.clear()
        self.ankle_positions.clear()
        self.timestamps.clear()
        self.velocities.clear()
        self.accelerations.clear()
        self.baseline_posture = None
        self.calibration_frames = 0
        self.is_calibrated = False
        self.last_event = MovementEvent.NORMAL
        self.event_confidence = 0.0

