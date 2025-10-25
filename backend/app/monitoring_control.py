"""
Dynamic Monitoring Control System
Manages monitoring levels and enabled metrics per patient
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

class MonitoringLevel(str, Enum):
    BASELINE = "BASELINE"      # Routine monitoring: HR, RR, CRS
    ENHANCED = "ENHANCED"      # Add tremor, attention, face touching
    CRITICAL = "CRITICAL"      # All metrics + high frequency

class MonitoringConfig:
    """Configuration for a patient's monitoring"""

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.level = MonitoringLevel.BASELINE
        self.enabled_metrics = ["heart_rate", "respiratory_rate", "crs_score"]
        self.frequency_seconds = 10  # Reduced from 5s to 10s for better performance
        self.activated_at = datetime.now()
        self.expires_at = None  # None = indefinite
        self.activation_reason = ""

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "level": self.level,
            "enabled_metrics": self.enabled_metrics,
            "frequency_seconds": self.frequency_seconds,
            "activated_at": self.activated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "activation_reason": self.activation_reason
        }

class MonitoringManager:
    """Global monitoring configuration manager"""

    def __init__(self):
        self.configs: Dict[str, MonitoringConfig] = {}

    def get_config(self, patient_id: str) -> MonitoringConfig:
        """Get monitoring config for a patient, create default if not exists"""
        if patient_id not in self.configs:
            self.configs[patient_id] = MonitoringConfig(patient_id)

        # Check if enhanced monitoring expired
        config = self.configs[patient_id]
        if config.expires_at and datetime.now() > config.expires_at:
            print(f"⏰ Enhanced monitoring expired for {patient_id}, returning to baseline")
            self.set_baseline_monitoring(patient_id, "Enhanced monitoring period completed")

        return self.configs[patient_id]

    def set_baseline_monitoring(self, patient_id: str, reason: str = ""):
        """Set patient to baseline monitoring"""
        config = self.get_config(patient_id)
        config.level = MonitoringLevel.BASELINE
        config.enabled_metrics = ["heart_rate", "respiratory_rate", "crs_score"]
        config.frequency_seconds = 10  # Reduced from 5s to 10s for better performance
        config.expires_at = None
        config.activation_reason = reason
        config.activated_at = datetime.now()

        print(f"📊 {patient_id}: BASELINE monitoring - {reason}")
        return config

    def set_enhanced_monitoring(
        self,
        patient_id: str,
        duration_minutes: int = 15,
        reason: str = ""
    ):
        """Activate enhanced monitoring with tremor, attention tracking"""
        config = self.get_config(patient_id)
        config.level = MonitoringLevel.ENHANCED
        config.enabled_metrics = [
            "heart_rate",
            "respiratory_rate",
            "crs_score",
            "tremor_magnitude",
            "tremor_detected",
            "attention_score",
            "eye_openness",
            "face_touching_frequency"
        ]
        config.frequency_seconds = 5
        config.expires_at = datetime.now() + timedelta(minutes=duration_minutes)
        config.activation_reason = reason
        config.activated_at = datetime.now()

        print(f"⚡ {patient_id}: ENHANCED monitoring activated for {duration_minutes}min - {reason}")
        return config

    def set_critical_monitoring(self, patient_id: str, reason: str = ""):
        """Activate critical protocol - all metrics, high frequency"""
        config = self.get_config(patient_id)
        config.level = MonitoringLevel.CRITICAL
        config.enabled_metrics = [
            "heart_rate",
            "respiratory_rate",
            "crs_score",
            "tremor_magnitude",
            "tremor_detected",
            "attention_score",
            "eye_openness",
            "face_touching_frequency",
            "restlessness_index",
            "movement_vigor",
            "head_pitch",
            "head_yaw",
            "head_roll",
            "posture_score"
        ]
        config.frequency_seconds = 3  # Faster sampling
        config.expires_at = None  # Critical doesn't expire automatically
        config.activation_reason = reason
        config.activated_at = datetime.now()

        print(f"🚨 {patient_id}: CRITICAL monitoring activated - {reason}")
        return config

    def enable_metric(self, patient_id: str, metric: str):
        """Add a specific metric to monitoring"""
        config = self.get_config(patient_id)
        if metric not in config.enabled_metrics:
            config.enabled_metrics.append(metric)
            print(f"🔧 {patient_id}: Enabled metric '{metric}'")
        return config

    def disable_metric(self, patient_id: str, metric: str):
        """Remove a specific metric from monitoring"""
        config = self.get_config(patient_id)
        if metric in config.enabled_metrics:
            config.enabled_metrics.remove(metric)
            print(f"🔧 {patient_id}: Disabled metric '{metric}'")
        return config

    def set_frequency(self, patient_id: str, seconds: int):
        """Change monitoring frequency"""
        config = self.get_config(patient_id)
        config.frequency_seconds = seconds
        print(f"⏱️ {patient_id}: Frequency set to {seconds}s")
        return config

    def get_all_configs(self) -> Dict[str, dict]:
        """Get all patient monitoring configs"""
        return {
            patient_id: config.to_dict()
            for patient_id, config in self.configs.items()
        }

# Global monitoring manager instance
monitoring_manager = MonitoringManager()
