"""
Lightweight heart rate analysis utilities shared by Haven agents.

This mirrors the backend rPPG implementation so that agent-side tooling
can produce consistent readings from the same algorithm.
"""

from collections import deque
from typing import Optional
import time

import numpy as np


class HeartRateMonitor:
    """
    Remote photoplethysmography (rPPG) for heart rate detection.
    Matches backend implementation to keep vitals consistent.
    """

    def __init__(self, window_size: int = 240, fps: int = 30):
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
        Extract heart rate from forehead region using rPPG.

        Args:
            frame: Full frame (reserved for future fusion, unused for now)
            forehead_roi: BGR ROI focused on forehead skin pixels

        Returns:
            Smoothed heart rate in bpm
        """
        now = time.time()

        if forehead_roi is None or forehead_roi.size == 0:
            return self.last_heart_rate

        try:
            mean_bgr = forehead_roi.mean(axis=(0, 1))
            if np.any(np.isnan(mean_bgr)):
                return self.last_heart_rate

            mean_rgb = np.array([mean_bgr[2], mean_bgr[1], mean_bgr[0]], dtype=np.float64)

            self.rgb_buffer.append(mean_rgb)
            self.timestamps.append(now)

            if len(self.rgb_buffer) < max(90, self.window_size // 2):
                return self.last_heart_rate

            duration = self.timestamps[-1] - self.timestamps[0]
            if duration < 3.0:
                return self.last_heart_rate

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
                self.last_heart_rate = int(0.6 * self.last_heart_rate + 0.4 * heart_rate)
                self._last_process_ts = now

            return self.last_heart_rate

        except Exception:
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
