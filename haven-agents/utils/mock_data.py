"""
Mock data generator for realistic demo scenarios
"""
import random
from datetime import datetime
from typing import Dict
from models.vitals import PatientVitals


class MockDataGenerator:
    """Generate realistic patient vitals for demo scenarios"""
    
    # Baseline vitals for each patient
    PATIENT_BASELINES = {
        "P-001": {"hr": 72, "rr": 14, "name": "John Anderson"},
        "P-002": {"hr": 68, "rr": 13, "name": "Maria Garcia"},
        "P-003": {"hr": 80, "rr": 16, "name": "David Chen"},
    }
    
    def __init__(self):
        self.time_elapsed = 0  # Seconds since demo start
        self.scenario = "normal"  # Current scenario
    
    def generate_patient_vitals(self, patient_id: str, scenario: str = "normal") -> PatientVitals:
        """
        Generate patient vitals based on scenario
        
        Scenarios:
        - "normal": All stable
        - "p002_concerning": P-002 develops concerning symptoms at T+60s
        - "p003_critical": P-003 develops critical CRS at T+120s
        - "pattern_tremor": Multiple patients show tremor (for Research Insights Agent)
        """
        baseline = self.PATIENT_BASELINES.get(patient_id, {"hr": 75, "rr": 14, "name": "Unknown"})
        baseline_hr = baseline["hr"]
        baseline_rr = baseline["rr"]
        
        # Default: stable vitals with minor variation
        hr = baseline_hr + random.randint(-3, 3)
        rr = baseline_rr + random.randint(-1, 1)
        crs_score = random.uniform(0.1, 0.4)
        tremor_detected = False
        tremor_magnitude = 0.0
        attention_score = random.uniform(0.95, 1.0)
        
        # Scenario-specific modifications
        if scenario == "normal":
            pass  # Use defaults
        
        elif scenario == "p002_concerning" and patient_id == "P-002":
            # P-002: Gradual elevation over 60 seconds
            progress = min(self.time_elapsed / 60.0, 1.0)
            hr = int(baseline_hr + (20 * progress))  # +20 bpm over 60s
            rr = int(baseline_rr + (4 * progress))   # +4 over 60s
            crs_score = 0.4 + (0.28 * progress)      # 0.4 → 0.68
            tremor_detected = progress > 0.5
            tremor_magnitude = max(0, (progress - 0.5) * 0.6)
        
        elif scenario == "p003_critical" and patient_id == "P-003":
            # P-003: Sudden spike at T+120s
            if self.time_elapsed >= 120:
                progress = min((self.time_elapsed - 120) / 30.0, 1.0)
                hr = int(baseline_hr + (65 * progress))  # Spike to 145 bpm
                rr = int(baseline_rr + (16 * progress))  # Spike to 32
                crs_score = 0.89
                tremor_detected = True
                tremor_magnitude = 0.85
                attention_score = 0.4  # Altered mental status
        
        elif scenario == "pattern_tremor":
            # Both P-002 and P-003 show tremor (for pattern detection demo)
            if patient_id in ["P-002", "P-003"] and self.time_elapsed >= 60:
                tremor_detected = True
                tremor_magnitude = random.uniform(0.4, 0.7)
                crs_score = random.uniform(0.5, 0.7)
        
        return PatientVitals(
            patient_id=patient_id,
            timestamp=datetime.now(),
            heart_rate=hr,
            respiratory_rate=rr,
            crs_score=crs_score,
            tremor_detected=tremor_detected,
            tremor_magnitude=tremor_magnitude,
            baseline_hr=baseline_hr,
            baseline_rr=baseline_rr,
            attention_score=attention_score
        )
    
    def advance_time(self, seconds: int = 30):
        """Advance demo timeline"""
        self.time_elapsed += seconds
    
    def set_scenario(self, scenario: str):
        """Change scenario"""
        self.scenario = scenario
        print(f"📋 Demo scenario changed to: {scenario}")
    
    def reset(self):
        """Reset timeline"""
        self.time_elapsed = 0
        self.scenario = "normal"


# Global generator instance
mock_generator = MockDataGenerator()

