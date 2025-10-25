"""Data models for Haven AI Multi-Agent System"""
from .vitals import PatientVitals
from .alerts import PatientAlert, SeverityLevel, TriageDecision, EmergencyType, EmergencyProtocol, ProtocolDeviation
from .protocols import PROTOCOL_RULES, EMERGENCY_PROTOCOLS, CRS_GRADING

__all__ = [
    "PatientVitals",
    "PatientAlert",
    "SeverityLevel",
    "TriageDecision",
    "EmergencyType",
    "EmergencyProtocol",
    "ProtocolDeviation",
    "PROTOCOL_RULES",
    "EMERGENCY_PROTOCOLS",
    "CRS_GRADING"
]

