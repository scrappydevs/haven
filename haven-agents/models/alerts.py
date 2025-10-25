"""
Data models for patient alerts and communications
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SeverityLevel(str, Enum):
    """Alert severity levels"""
    NORMAL = "NORMAL"
    CONCERNING = "CONCERNING"
    CRITICAL = "CRITICAL"


class PatientAlert(BaseModel):
    """Alert message from Patient Guardian Agent"""
    patient_id: str = Field(..., description="Patient identifier")
    severity: SeverityLevel = Field(..., description="Alert severity level")
    vitals: dict = Field(..., description="Patient vitals at time of alert")
    reasoning: str = Field(..., description="Claude's clinical reasoning")
    timestamp: datetime = Field(default_factory=datetime.now)
    concerns: List[str] = Field(default_factory=list, description="Specific clinical concerns")
    confidence: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="AI confidence in assessment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "P-002",
                "severity": "CONCERNING",
                "vitals": {
                    "heart_rate": 88,
                    "respiratory_rate": 18,
                    "crs_score": 0.68
                },
                "reasoning": "Heart rate elevated 35% above baseline and CRS score entering concerning range. Possible early Grade 2 CRS.",
                "timestamp": "2025-10-25T14:23:15",
                "concerns": ["Elevated HR", "Rising CRS score"],
                "confidence": 0.85
            }
        }


class TriageDecision(BaseModel):
    """Triage decision from Nurse Coordinator Agent"""
    priority: int = Field(..., ge=1, description="Priority ranking (1 = most urgent)")
    patient_id: str
    assigned_nurse: Optional[str] = Field(default=None, description="Assigned nurse identifier")
    reasoning: str = Field(..., description="Triage reasoning from Claude")
    estimated_response_time: int = Field(..., description="Estimated response time in minutes")
    timestamp: datetime = Field(default_factory=datetime.now)


class EmergencyType(str, Enum):
    """Types of emergency situations"""
    CRS_GRADE_3 = "CRS_Grade_3"
    CRS_GRADE_4 = "CRS_Grade_4"
    SEIZURE = "Seizure"
    CARDIAC_EVENT = "Cardiac_Event"
    ICANS = "ICANS"  # Immune effector cell-associated neurotoxicity syndrome
    OTHER = "Other"


class EmergencyProtocol(BaseModel):
    """Emergency protocol activation"""
    emergency_type: EmergencyType
    patient_id: str
    protocol_steps: List[str] = Field(..., description="Ordered list of protocol actions")
    timestamp: datetime = Field(default_factory=datetime.now)
    physician_paged: bool = Field(default=False)
    medications_prepared: List[str] = Field(default_factory=list)
    reasoning: str = Field(..., description="Claude's emergency classification reasoning")


class ProtocolDeviation(BaseModel):
    """Protocol compliance deviation record"""
    patient_id: str
    deviation_type: str = Field(..., description="Type: 'late_check', 'missed_check', 'documentation_gap'")
    severity: str = Field(..., description="Severity: 'minor', 'major', 'critical'")
    scheduled_time: datetime
    actual_time: Optional[datetime] = Field(default=None)
    delay_minutes: Optional[int] = Field(default=None)
    reason: Optional[str] = Field(default=None, description="Justification for deviation")
    justified: bool = Field(default=False, description="Whether deviation is clinically justified")
    timestamp: datetime = Field(default_factory=datetime.now)

