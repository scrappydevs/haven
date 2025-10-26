"""
CV Metrics Calculators
Real computer vision-based metric extraction for clinical monitoring
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional, List, Dict
import time

class HeartRateMonitor:
    """
    Remote photoplethysmography (rPPG) for heart rate detection
    Tracks subtle color changes in face caused by blood flow using:
      1) RGB signal extraction from forehead ROI
      2) Detrending & normalization
      3) Blind source separation (FastICA) to isolate the BVP signal
      4) Frequency analysis within physiological limits
    """

    def __init__(self, window_size: int = 240, fps: int = 30):
        # ~8 seconds of history @ 30 fps (enough buffer for R-R intervals)
        self.window_size = window_size
        self.expected_fps = fps
        self.rgb_buffer = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.last_heart_rate = 75
        self.freq_band = (0.75, 3.0)  # 45-180 bpm
        self._rng = np.random.default_rng(seed=2024)
        self._last_process_ts = 0.0

    def process_frame(self, frame: np.ndarray, forehead_roi: Optional[np.ndarray]) -> int:
        """
        Extract heart rate from forehead region using rPPG

        Args:
            frame: Full frame (unused placeholder for future model fusion)
            forehead_roi: ROI of forehead region for color analysis

        Returns:
            Heart rate in bpm
        """
        now = time.time()

        if forehead_roi is None or forehead_roi.size == 0:
            return self.last_heart_rate

        try:
            mean_bgr = forehead_roi.mean(axis=(0, 1))
            if np.any(np.isnan(mean_bgr)):
                return self.last_heart_rate

            # Convert BGR (OpenCV) → RGB ordering
            mean_rgb = np.array([mean_bgr[2], mean_bgr[1], mean_bgr[0]], dtype=np.float64)

            self.rgb_buffer.append(mean_rgb)
            self.timestamps.append(now)

            if len(self.rgb_buffer) < max(90, self.window_size // 2):
                return self.last_heart_rate

            duration = self.timestamps[-1] - self.timestamps[0]
            if duration < 3.0:
                return self.last_heart_rate

            # Skip heavy processing if we recently calculated (≈2 Hz cadence)
            if now - self._last_process_ts < 0.5:
                return self.last_heart_rate

            sample_rate = (len(self.timestamps) - 1) / duration if duration > 0 else self.expected_fps
            if not np.isfinite(sample_rate) or sample_rate < 10.0:
                sample_rate = float(self.expected_fps)

            rgb_matrix = np.array(self.rgb_buffer, dtype=np.float64)

            preprocessed = self._preprocess_rgb(rgb_matrix)
            if preprocessed is None:
                return self.last_heart_rate

            sources = self._fast_ica(preprocessed)
            if sources is None:
                return self.last_heart_rate

            heart_rate = self._estimate_bpm(sources, sample_rate)
            if heart_rate is None:
                return self.last_heart_rate

            if 45 <= heart_rate <= 180:
                # EMA smoothing to reduce jitter
                self.last_heart_rate = int(0.6 * self.last_heart_rate + 0.4 * heart_rate)
                self._last_process_ts = now

            return self.last_heart_rate

        except Exception as e:
            print(f"rPPG error: {e}")
            return self.last_heart_rate

    def _preprocess_rgb(self, rgb_matrix: np.ndarray) -> Optional[np.ndarray]:
        """Detrend and normalize RGB channels."""
        if rgb_matrix.shape[0] < 10:
            return None

        detrended = self._detrend(rgb_matrix)
        if detrended is None:
            return None

        std = np.std(detrended, axis=0, ddof=1)
        if np.any(std < 1e-6):
            return None

        standardized = (detrended - np.mean(detrended, axis=0)) / std
        return standardized

    def _detrend(self, data: np.ndarray) -> Optional[np.ndarray]:
        """Remove slow drift via moving-average baseline subtraction."""
        length = data.shape[0]
        if length < 5:
            return None

        window = max(5, int(min(length // 3, self.expected_fps)))
        if window % 2 == 0:
            window += 1

        kernel = np.ones(window, dtype=np.float64) / window
        detrended = np.empty_like(data)

        for idx in range(data.shape[1]):
            channel = data[:, idx]
            baseline = np.convolve(channel, kernel, mode="same")
            detrended[:, idx] = channel - baseline

        return detrended

    def _fast_ica(self, data: np.ndarray, max_iter: int = 200, tol: float = 1e-5) -> Optional[np.ndarray]:
        """Minimal FastICA implementation for three-channel signals."""
        n_samples, n_features = data.shape
        if n_samples < n_features:
            return None

        centered = data - np.mean(data, axis=0, keepdims=True)
        cov = np.cov(centered, rowvar=False)
        eigvals, eigvecs = np.linalg.eigh(cov)
        eigvals = np.clip(eigvals, 1e-6, None)
        whitening = eigvecs @ np.diag(1.0 / np.sqrt(eigvals)) @ eigvecs.T
        whitened = centered @ whitening

        n_components = n_features
        weights = np.zeros((n_components, n_components))

        for i in range(n_components):
            w = self._rng.normal(size=n_components)
            w /= np.linalg.norm(w)

            for _ in range(max_iter):
                projection = whitened @ w
                g = np.tanh(projection)
                g_prime = 1.0 - g ** 2

                w_new = (whitened * g[:, None]).mean(axis=0) - g_prime.mean() * w

                if i > 0:
                    w_new -= weights[:i].T @ (weights[:i] @ w_new)

                norm = np.linalg.norm(w_new)
                if norm < 1e-6:
                    break
                w_new /= norm

                if np.linalg.norm(w_new - w) < tol:
                    w = w_new
                    break
                w = w_new

            weights[i, :] = w

        return whitened @ weights.T

    def _estimate_bpm(self, components: np.ndarray, sample_rate: float) -> Optional[int]:
        """Pick component with strongest frequency in the physiological band."""
        if components.shape[0] < 10:
            return None

        best_freq = None
        best_power = 0.0
        low, high = self.freq_band
        window = np.hamming(components.shape[0])

        for idx in range(components.shape[1]):
            signal = components[:, idx] - np.mean(components[:, idx])
            if np.std(signal) < 1e-6:
                continue

            windowed = signal * window
            spectrum = np.fft.rfft(windowed)
            freqs = np.fft.rfftfreq(windowed.size, d=1.0 / sample_rate)

            mask = (freqs >= low) & (freqs <= high)
            band_power = np.abs(spectrum[mask])
            band_freqs = freqs[mask]

            if band_power.size == 0:
                continue

            peak_idx = int(np.argmax(band_power))
            peak_power = band_power[peak_idx]
            peak_freq = band_freqs[peak_idx]

            median_noise = np.median(band_power)
            if median_noise > 0 and peak_power / median_noise < 3.0:
                continue

            if peak_power > best_power:
                best_power = peak_power
                best_freq = peak_freq

        if best_freq is None:
            return None

        return int(best_freq * 60)


class RespiratoryRateMonitor:
    """
    Respiratory rate detection from facial/head motion
    Tracks vertical movement of head/nose caused by breathing
    """
    def __init__(self, window_size=30, fps=30):
        self.window_size = window_size  # 30 samples = ~10 seconds worth of data points
        self.fps = 3  # Effective sampling rate (called every 3 seconds)
        self.position_buffer = deque(maxlen=window_size)
        self.last_respiratory_rate = 14
        print(f"🫁 RR Monitor initialized: window_size={window_size}, effective_fps={self.fps}")

    def process_frame(self, nose_y: float) -> int:
        """
        Extract respiratory rate from nose vertical position

        Args:
            nose_y: Normalized Y position of nose tip (0-1)

        Returns:
            Respiratory rate in breaths/min
        """
        try:
            self.position_buffer.append(nose_y)

            if len(self.position_buffer) < self.window_size:
                return self.last_respiratory_rate

            # Convert to numpy and detrend
            signal = np.array(self.position_buffer)
            signal_mean = np.mean(signal)
            signal = signal - signal_mean

            # Check signal strength (movement amplitude)
            signal_std = np.std(signal)

            # Apply window
            window = np.hamming(len(signal))
            signal = signal * window

            # FFT
            fft_data = np.fft.rfft(signal)
            fft_freq = np.fft.rfftfreq(len(signal), 1.0 / self.fps)

            # Physiological breathing range (8-30 breaths/min = 0.133-0.5 Hz)
            # But since we sample slowly (every 3 sec), we need to adjust the frequency range
            # Nyquist frequency = fps/2 = 1.5 Hz, max detectable rate = 90 breaths/min
            mask = (fft_freq >= 0.133) & (fft_freq <= 0.5)
            fft_data_masked = np.abs(fft_data[mask])
            fft_freq_masked = fft_freq[mask]

            if len(fft_data_masked) == 0:
                print(f"⚠️ RR: No frequencies in breathing range")
                return self.last_respiratory_rate

            # Find peak
            peak_idx = np.argmax(fft_data_masked)
            peak_freq = fft_freq_masked[peak_idx]
            peak_magnitude = fft_data_masked[peak_idx]

            # Convert to breaths/min
            respiratory_rate = int(peak_freq * 60)

            # Diagnostic logging
            print(f"🫁 RR Debug: nose_y={nose_y:.4f}, signal_std={signal_std:.6f}, peak_freq={peak_freq:.3f}Hz, raw_rr={respiratory_rate}, peak_mag={peak_magnitude:.2f}")

            # Require minimum signal strength to avoid noise-based detection
            # Lower threshold since we're sampling slowly (3 sec intervals)
            if signal_std < 0.0005:  # Reduced threshold for slow sampling
                print(f"⚠️ RR: Signal too weak (std={signal_std:.6f}), using previous: {self.last_respiratory_rate}")
                return self.last_respiratory_rate

            # Sanity check
            if 8 <= respiratory_rate <= 30:
                prev_rr = self.last_respiratory_rate
                # Less aggressive smoothing (50/50) for faster response
                self.last_respiratory_rate = int(0.5 * self.last_respiratory_rate + 0.5 * respiratory_rate)
                print(f"✅ RR: Updated from {prev_rr} to {self.last_respiratory_rate} (raw: {respiratory_rate})")
            else:
                print(f"⚠️ RR: Out of range ({respiratory_rate}), keeping: {self.last_respiratory_rate}")

            return self.last_respiratory_rate

        except Exception as e:
            print(f"❌ Respiratory rate error: {e}")
            import traceback
            traceback.print_exc()
            return self.last_respiratory_rate


class FaceTouchingDetector:
    """
    Detects face touching by measuring hand-to-face proximity
    """
    def __init__(self, window_size=30, fps=30):
        self.window_size = window_size  # 1 second
        self.touch_events = deque(maxlen=window_size * 60)  # Last 60 seconds
        self.last_hand_near_face = False

    def process_frame(self, landmarks) -> Tuple[int, bool]:
        """
        Detect if hand is near face

        Args:
            landmarks: MediaPipe face landmarks

        Returns:
            (touch_frequency_per_minute, is_currently_touching)
        """
        # For now, approximate using face coverage and movement patterns
        # A more complete implementation would use MediaPipe Hands
        # As a proxy, we detect when facial landmarks move unusually

        current_time = time.time()

        # Simplified: detect based on landmark stability
        # Real implementation would track hand landmarks
        is_touching = False  # Placeholder for hand detection

        # Count recent touches
        self.touch_events = deque([t for t in self.touch_events if current_time - t < 60], maxlen=self.window_size * 60)

        # Detect edge (hand just approached face)
        if is_touching and not self.last_hand_near_face:
            self.touch_events.append(current_time)

        self.last_hand_near_face = is_touching

        # Calculate frequency (touches per minute)
        frequency = len(self.touch_events)

        return frequency, is_touching


class MovementVolumeTracker:
    """
    Tracks overall body movement and restlessness
    """
    def __init__(self, window_size=30, fps=30):
        self.window_size = window_size
        self.fps = fps
        self.movement_buffer = deque(maxlen=window_size * 10)  # 10 seconds
        self.prev_landmarks = None

    def process_frame(self, landmarks) -> Tuple[float, float]:
        """
        Calculate movement vigor and restlessness index

        Args:
            landmarks: Current frame landmarks

        Returns:
            (restlessness_index, movement_vigor)
        """
        if self.prev_landmarks is None:
            self.prev_landmarks = landmarks
            return 0.0, 0.0

        try:
            # Calculate movement between frames
            movement = 0.0
            for i in range(min(len(landmarks.landmark), len(self.prev_landmarks.landmark))):
                curr = landmarks.landmark[i]
                prev = self.prev_landmarks.landmark[i]
                dx = curr.x - prev.x
                dy = curr.y - prev.y
                movement += np.sqrt(dx*dx + dy*dy)

            movement /= len(landmarks.landmark)
            self.movement_buffer.append(movement)
            self.prev_landmarks = landmarks

            if len(self.movement_buffer) < self.window_size:
                return 0.0, 0.0

            # Restlessness: frequency of large movements
            movements = np.array(self.movement_buffer)
            threshold = np.mean(movements) + np.std(movements)
            restlessness = np.sum(movements > threshold) / len(movements)

            # Movement vigor: average movement magnitude
            vigor = np.mean(movements) * 1000  # Scale up for visibility

            return float(restlessness), float(vigor)

        except Exception as e:
            print(f"Movement tracking error: {e}")
            return 0.0, 0.0


class TremorDetector:
    """
    Detects high-frequency tremor movements
    """
    def __init__(self, window_size=60, fps=30):
        self.window_size = window_size  # 2 seconds for better FFT resolution
        self.fps = fps
        self.hand_positions = deque(maxlen=window_size)
        self.detection_buffer = deque(maxlen=15)  # Track last 15 detections for persistence

    def process_frame(self, landmarks) -> Tuple[float, bool]:
        """
        Detect tremor based on high-frequency movements
        Requires sustained high-frequency oscillation to reduce false positives

        Args:
            landmarks: Face landmarks (could be extended to hand landmarks)

        Returns:
            (tremor_magnitude, tremor_detected)
        """
        try:
            # Use nose tip as proxy for head tremor
            nose = landmarks.landmark[1]
            self.hand_positions.append((nose.x, nose.y))

            if len(self.hand_positions) < self.window_size:
                return 0.0, False

            # Calculate high-frequency component
            positions = np.array(self.hand_positions)
            x_signal = positions[:, 0]
            y_signal = positions[:, 1]

            # Detrend to remove slow movements
            x_signal = x_signal - np.mean(x_signal)
            y_signal = y_signal - np.mean(y_signal)

            # Apply Hamming window to reduce spectral leakage
            window = np.hamming(len(x_signal))
            x_signal = x_signal * window
            y_signal = y_signal * window

            # FFT for tremor frequency detection (4-12 Hz typical for pathological tremor)
            fft_x = np.fft.rfft(x_signal)
            fft_y = np.fft.rfft(y_signal)
            fft_freq = np.fft.rfftfreq(len(x_signal), 1.0 / self.fps)

            # Tremor frequency range (narrower range for pathological tremor)
            tremor_mask = (fft_freq >= 4) & (fft_freq <= 12)
            tremor_power = np.mean(np.abs(fft_x[tremor_mask])**2) + np.mean(np.abs(fft_y[tremor_mask])**2)

            # Normal movement frequency range (0.5-3 Hz)
            normal_mask = (fft_freq >= 0.5) & (fft_freq <= 3)
            normal_power = np.mean(np.abs(fft_x[normal_mask])**2) + np.mean(np.abs(fft_y[normal_mask])**2)

            # Tremor is detected only if high-frequency power significantly exceeds low-frequency
            # This helps distinguish tremor from normal voluntary movement
            if normal_power > 0:
                tremor_ratio = tremor_power / (normal_power + 1e-6)
            else:
                tremor_ratio = 0

            # Much higher threshold and require persistence
            tremor_magnitude = float(tremor_power * 100000)
            is_tremor_frame = tremor_magnitude > 5.0 and tremor_ratio > 1.5

            # Add to detection buffer
            self.detection_buffer.append(is_tremor_frame)

            # Require 60% of recent frames to show tremor (9 out of 15)
            tremor_detected = sum(self.detection_buffer) >= 9

            return tremor_magnitude, tremor_detected

        except Exception as e:
            print(f"Tremor detection error: {e}")
            return 0.0, False


class UpperBodyPostureTracker:
    """
    Tracks upper body posture and movement patterns
    Useful for detecting discomfort, abnormal posture, and restlessness
    """
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.shoulder_positions = deque(maxlen=window_size)
        self.posture_history = deque(maxlen=window_size * 3)  # 3 seconds
        self.prev_shoulder_distance = None

    def process_frame(self, pose_landmarks) -> Dict[str, float]:
        """
        Analyze upper body posture from MediaPipe Pose landmarks

        Args:
            pose_landmarks: MediaPipe Pose landmarks (33 points)

        Returns:
            {
                "shoulder_angle": float,  # Shoulder tilt angle (degrees)
                "posture_score": float,   # 0-1, higher = better posture
                "shoulder_width": float,  # Normalized shoulder distance
                "upper_body_movement": float,  # Movement index
                "lean_forward": float,    # Forward lean angle (degrees)
                "arm_asymmetry": float    # 0-1, 0 = symmetric
            }
        """
        if not pose_landmarks:
            return {
                "shoulder_angle": 0.0,
                "posture_score": 1.0,
                "shoulder_width": 0.0,
                "upper_body_movement": 0.0,
                "lean_forward": 0.0,
                "arm_asymmetry": 0.0
            }

        try:
            # Key landmarks (MediaPipe Pose indices)
            # 11: Left shoulder, 12: Right shoulder
            # 13: Left elbow, 14: Right elbow
            # 15: Left wrist, 16: Right wrist
            # 23: Left hip, 24: Right hip
            # 0: Nose

            left_shoulder = pose_landmarks.landmark[11]
            right_shoulder = pose_landmarks.landmark[12]
            left_elbow = pose_landmarks.landmark[13]
            right_elbow = pose_landmarks.landmark[14]
            left_hip = pose_landmarks.landmark[23]
            right_hip = pose_landmarks.landmark[24]
            nose = pose_landmarks.landmark[0]

            # === SHOULDER ANGLE (tilt) ===
            shoulder_angle = np.degrees(np.arctan2(
                right_shoulder.y - left_shoulder.y,
                right_shoulder.x - left_shoulder.x
            ))

            # === SHOULDER WIDTH (for tracking movement) ===
            shoulder_width = np.sqrt(
                (right_shoulder.x - left_shoulder.x)**2 +
                (right_shoulder.y - left_shoulder.y)**2
            )

            # === POSTURE SCORE ===
            # Good posture: shoulders level, spine straight
            # Calculate spine alignment (shoulders to hips)
            shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
            hip_center_y = (left_hip.y + right_hip.y) / 2
            shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
            hip_center_x = (left_hip.x + right_hip.x) / 2

            # Spine straightness (lower = better)
            spine_horizontal_offset = abs(shoulder_center_x - hip_center_x)

            # Shoulder levelness (lower = better)
            shoulder_tilt = abs(shoulder_angle)

            # Combined posture score (0-1, higher is better)
            posture_score = max(0.0, 1.0 - (spine_horizontal_offset * 2 + shoulder_tilt / 30))

            # === FORWARD LEAN ===
            # Compare nose position to shoulder center
            lean_forward = (shoulder_center_y - nose.y) * 100  # Positive = leaning forward

            # === ARM ASYMMETRY ===
            # Compare left and right arm positions
            left_arm_angle = np.degrees(np.arctan2(
                left_elbow.y - left_shoulder.y,
                left_elbow.x - left_shoulder.x
            ))
            right_arm_angle = np.degrees(np.arctan2(
                right_elbow.y - right_shoulder.y,
                right_elbow.x - right_shoulder.x
            ))
            arm_asymmetry = min(1.0, abs(left_arm_angle - right_arm_angle) / 90)

            # === UPPER BODY MOVEMENT ===
            self.shoulder_positions.append((shoulder_center_x, shoulder_center_y))

            if len(self.shoulder_positions) > 1:
                # Calculate movement over time
                positions = np.array(self.shoulder_positions)
                movement = np.sum(np.sqrt(np.sum(np.diff(positions, axis=0)**2, axis=1)))
                upper_body_movement = float(movement * 10)  # Scale for visibility
            else:
                upper_body_movement = 0.0

            return {
                "shoulder_angle": float(shoulder_angle),
                "posture_score": float(posture_score),
                "shoulder_width": float(shoulder_width),
                "upper_body_movement": float(upper_body_movement),
                "lean_forward": float(lean_forward),
                "arm_asymmetry": float(arm_asymmetry)
            }

        except Exception as e:
            print(f"Upper body posture tracking error: {e}")
            return {
                "shoulder_angle": 0.0,
                "posture_score": 1.0,
                "shoulder_width": 0.0,
                "upper_body_movement": 0.0,
                "lean_forward": 0.0,
                "arm_asymmetry": 0.0
            }
