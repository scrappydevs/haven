"""
Data models for patient vitals and monitoring
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PatientVitals(BaseModel):
    """Patient vital signs data structure"""
    patient_id: str = Field(..., description="Patient identifier (e.g., P-001)")
    timestamp: datetime = Field(default_factory=datetime.now)
    heart_rate: int = Field(..., ge=30, le=200, description="Heart rate in bpm")
    respiratory_rate: int = Field(..., ge=5, le=40, description="Respiratory rate in breaths/min")
    crs_score: float = Field(..., ge=0.0, le=1.0, description="CRS severity index (0.0-1.0)")
    tremor_detected: bool = Field(default=False, description="Whether tremor is present")
    tremor_magnitude: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Tremor intensity")
    baseline_hr: int = Field(..., ge=30, le=200, description="Patient's normal heart rate")
    baseline_rr: int = Field(..., ge=5, le=40, description="Patient's normal respiratory rate")
    attention_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Attention level (1.0 = alert)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "P-001",
                "timestamp": "2025-10-25T14:30:00",
                "heart_rate": 78,
                "respiratory_rate": 16,
                "crs_score": 0.3,
                "tremor_detected": False,
                "tremor_magnitude": 0.0,
                "baseline_hr": 75,
                "baseline_rr": 14,
                "attention_score": 1.0
            }
        }

