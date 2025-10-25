"""
Clinical trial protocol definitions and rules
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProtocolRules(BaseModel):
    """Clinical trial protocol requirements"""
    vitals_frequency: int = Field(..., description="Required vital check frequency in minutes")
    required_checks: List[str] = Field(..., description="Required vital signs to monitor")
    symptom_checklist_frequency: Optional[str] = Field(default=None, description="Symptom assessment frequency")


# Clinical trial protocol definitions
PROTOCOL_RULES = {
    "high_risk_patients": {
        "vitals_frequency": 15,  # Check every 15 minutes
        "required_checks": ["HR", "RR", "CRS", "tremor"],
        "description": "High-risk CAR-T patients with previous CRS history"
    },
    "post_infusion_day_1_3": {
        "vitals_frequency": 30,  # Check every 30 minutes
        "symptom_checklist": "q2h",  # Every 2 hours
        "required_checks": ["HR", "RR", "CRS"],
        "description": "Days 1-3 post-infusion monitoring"
    },
    "post_infusion_day_4_7": {
        "vitals_frequency": 60,  # Hourly
        "symptom_checklist": "q4h",  # Every 4 hours
        "required_checks": ["HR", "RR", "CRS"],
        "description": "Days 4-7 post-infusion monitoring"
    },
    "baseline_monitoring": {
        "vitals_frequency": 120,  # Every 2 hours
        "required_checks": ["HR", "RR"],
        "description": "Standard baseline monitoring"
    }
}

# Emergency protocol definitions
EMERGENCY_PROTOCOLS = {
    "CRS_Grade_3": [
        "Page on-call physician immediately (Dr. Smith - 555-0123)",
        "Prepare tocilizumab 8mg/kg IV (IL-6 receptor antagonist)",
        "Increase vital signs monitoring to q5min",
        "Alert ICU - reserve bed on standby",
        "Prepare vasopressors (norepinephrine) if hypotension",
        "Obtain STAT labs: CBC, CMP, LFTs, troponin, CRP, ferritin",
        "Consider corticosteroids (dexamethasone 10mg IV) if no response"
    ],
    "CRS_Grade_4": [
        "IMMEDIATE ICU transfer - life-threatening condition",
        "Page attending physician + ICU team",
        "Tocilizumab 8mg/kg IV STAT",
        "Dexamethasone 10-20mg IV STAT",
        "Continuous cardiopulmonary monitoring",
        "Prepare for mechanical ventilation if respiratory failure",
        "Aggressive fluid resuscitation + vasopressor support",
        "STAT labs: CBC, CMP, LFTs, cardiac enzymes, coags, blood cultures"
    ],
    "Seizure": [
        "Activate rapid response team",
        "Protect patient from injury (pad side rails, clear area)",
        "Prepare lorazepam 2-4mg IV (first-line anticonvulsant)",
        "Turn patient to side (prevent aspiration)",
        "Supplemental oxygen - prepare for intubation if status epilepticus",
        "Continuous EEG monitoring",
        "STAT head CT to rule out intracranial hemorrhage",
        "Neurology consult - possible ICANS (CAR-T neurotoxicity)"
    ],
    "ICANS": [
        "Neurology consult immediately",
        "Assess ICE score (Immune Effector Cell-Associated Encephalopathy)",
        "Dexamethasone 10mg IV q6h",
        "MRI brain with contrast (rule out cerebral edema)",
        "EEG monitoring (non-convulsive seizures common)",
        "Discontinue any CNS-active medications",
        "1:1 nursing observation",
        "Consider levetiracetam prophylaxis"
    ],
    "Cardiac_Event": [
        "Activate Code Blue team",
        "12-lead ECG STAT",
        "Troponin, BNP, CK-MB STAT",
        "Portable chest X-ray",
        "Cardiology consult",
        "Prepare crash cart (defibrillator, ACLS medications)",
        "Consider echocardiogram (CAR-T can cause myocarditis)",
        "Telemetry monitoring"
    ]
}

# CRS Grading Criteria (FDA criteria for CAR-T trials)
CRS_GRADING = {
    "Grade_1": {
        "criteria": "Fever ≥38°C only",
        "symptoms": ["Fever"],
        "intervention": "Symptomatic treatment only (acetaminophen)",
        "monitoring_frequency": 30  # minutes
    },
    "Grade_2": {
        "criteria": "Fever + hypotension not requiring vasopressors OR hypoxia requiring low-flow oxygen",
        "symptoms": ["Fever", "Hypotension", "Hypoxia"],
        "intervention": "Oxygen support, IV fluids, consider tocilizumab",
        "monitoring_frequency": 15
    },
    "Grade_3": {
        "criteria": "Fever + hypotension requiring vasopressor OR hypoxia requiring high-flow oxygen",
        "symptoms": ["Fever", "Hypotension (requiring vasopressors)", "Hypoxia (high-flow O2)"],
        "intervention": "Tocilizumab + corticosteroids, ICU-level care",
        "monitoring_frequency": 5
    },
    "Grade_4": {
        "criteria": "Life-threatening: requiring mechanical ventilation OR continuous vasopressor support",
        "symptoms": ["Respiratory failure", "Shock", "Organ dysfunction"],
        "intervention": "ICU, mechanical ventilation, aggressive immunosuppression",
        "monitoring_frequency": 1  # Continuous monitoring
    }
}

