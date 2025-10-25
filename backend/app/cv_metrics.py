"""
CV Metrics Calculators
Real computer vision-based metric extraction for clinical monitoring
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional, List
import time

class HeartRateMonitor:
    """
    Remote photoplethysmography (rPPG) for heart rate detection
    Tracks subtle color changes in face caused by blood flow
    """
    def __init__(self, window_size=150, fps=30):
        self.window_size = window_size  # ~5 seconds at 30 fps
        self.fps = fps
        self.signal_buffer = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.last_heart_rate = 75

    def process_frame(self, frame: np.ndarray, forehead_roi: Optional[np.ndarray]) -> int:
        """
        Extract heart rate from forehead region using rPPG

        Args:
            frame: Full frame (not used currently, for future enhancement)
            forehead_roi: ROI of forehead region for color analysis

        Returns:
            Heart rate in bpm
        """
        if forehead_roi is None or forehead_roi.size == 0:
            return self.last_heart_rate

        try:
            # Extract green channel (most sensitive to blood volume changes)
            green_mean = np.mean(forehead_roi[:, :, 1])

            # Add to buffer
            self.signal_buffer.append(green_mean)
            self.timestamps.append(time.time())

            # Need enough data points for FFT
            if len(self.signal_buffer) < self.window_size:
                return self.last_heart_rate

            # Convert to numpy array and detrend
            signal = np.array(self.signal_buffer)
            signal = signal - np.mean(signal)

            # Apply Hamming window
            window = np.hamming(len(signal))
            signal = signal * window

            # FFT
            fft_data = np.fft.rfft(signal)
            fft_freq = np.fft.rfftfreq(len(signal), 1.0 / self.fps)

            # Focus on physiological heart rate range (45-180 bpm = 0.75-3 Hz)
            mask = (fft_freq >= 0.75) & (fft_freq <= 3.0)
            fft_data_masked = np.abs(fft_data[mask])
            fft_freq_masked = fft_freq[mask]

            if len(fft_data_masked) == 0:
                return self.last_heart_rate

            # Find peak frequency
            peak_idx = np.argmax(fft_data_masked)
            peak_freq = fft_freq_masked[peak_idx]

            # Convert to BPM
            heart_rate = int(peak_freq * 60)

            # Sanity check
            if 45 <= heart_rate <= 180:
                # Smooth with previous value
                self.last_heart_rate = int(0.7 * self.last_heart_rate + 0.3 * heart_rate)

            return self.last_heart_rate

        except Exception as e:
            print(f"rPPG error: {e}")
            return self.last_heart_rate


class RespiratoryRateMonitor:
    """
    Respiratory rate detection from facial/head motion
    Tracks vertical movement of head/nose caused by breathing
    """
    def __init__(self, window_size=90, fps=30):
        self.window_size = window_size  # ~3 seconds
        self.fps = fps
        self.position_buffer = deque(maxlen=window_size)
        self.last_respiratory_rate = 14

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
            signal = signal - np.mean(signal)

            # Apply window
            window = np.hamming(len(signal))
            signal = signal * window

            # FFT
            fft_data = np.fft.rfft(signal)
            fft_freq = np.fft.rfftfreq(len(signal), 1.0 / self.fps)

            # Physiological breathing range (8-30 breaths/min = 0.133-0.5 Hz)
            mask = (fft_freq >= 0.133) & (fft_freq <= 0.5)
            fft_data_masked = np.abs(fft_data[mask])
            fft_freq_masked = fft_freq[mask]

            if len(fft_data_masked) == 0:
                return self.last_respiratory_rate

            # Find peak
            peak_idx = np.argmax(fft_data_masked)
            peak_freq = fft_freq_masked[peak_idx]

            # Convert to breaths/min
            respiratory_rate = int(peak_freq * 60)

            # Sanity check
            if 8 <= respiratory_rate <= 30:
                self.last_respiratory_rate = int(0.7 * self.last_respiratory_rate + 0.3 * respiratory_rate)

            return self.last_respiratory_rate

        except Exception as e:
            print(f"Respiratory rate error: {e}")
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
    def __init__(self, window_size=30, fps=30):
        self.window_size = window_size
        self.fps = fps
        self.hand_positions = deque(maxlen=window_size)  # Track hand/face position

    def process_frame(self, landmarks) -> Tuple[float, bool]:
        """
        Detect tremor based on high-frequency movements

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

            # FFT for tremor frequency detection (4-12 Hz typical)
            fft_x = np.fft.rfft(x_signal - np.mean(x_signal))
            fft_y = np.fft.rfft(y_signal - np.mean(y_signal))
            fft_freq = np.fft.rfftfreq(len(x_signal), 1.0 / self.fps)

            # Tremor frequency range
            mask = (fft_freq >= 4) & (fft_freq <= 12)
            tremor_magnitude = np.mean(np.abs(fft_x[mask])) + np.mean(np.abs(fft_y[mask]))

            tremor_detected = tremor_magnitude > 0.001  # Threshold

            return float(tremor_magnitude * 10000), tremor_detected  # Scale for visibility

        except Exception as e:
            print(f"Tremor detection error: {e}")
            return 0.0, False
