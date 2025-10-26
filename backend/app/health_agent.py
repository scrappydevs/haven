"""
Simple Health Agent Integration for Haven
Single focused agent that monitors patient health
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import json

from app.infisical_config import get_secret

# Try to import anthropic
try:
    import anthropic
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
    CLAUDE_AVAILABLE = True
except ImportError:
    claude_client = None
    CLAUDE_AVAILABLE = False


class HealthAgent:
    """
    Single AI health monitoring agent for Haven
    Analyzes patient data and generates intelligent alerts
    """
    
    def __init__(self):
        self.enabled = CLAUDE_AVAILABLE
        self.patients = {}  # {patient_id: latest_data}
        self.alerts = []  # Active alerts
        self.alert_history = []  # All alerts
        
        print(f"🏥 Health Agent: {'Enabled' if self.enabled else 'Disabled (Claude API not available)'}")
    
    async def analyze_patient(self, patient_id: str, vitals: Dict, cv_metrics: Dict) -> Dict:
        """
        Analyze patient health data using Claude
        
        Args:
            patient_id: Patient identifier
            vitals: {heart_rate, temperature, blood_pressure, spo2}
            cv_metrics: {distress_score, movement_score, posture_alert}
        
        Returns:
            {severity, concerns, recommended_action, reasoning, confidence}
        """
        # Store patient data
        self.patients[patient_id] = {
            "vitals": vitals,
            "cv_metrics": cv_metrics,
            "last_update": datetime.utcnow().isoformat()
        }
        
        # Analyze with Claude if available
        if self.enabled and claude_client:
            try:
                analysis = await self._analyze_with_claude(patient_id, vitals, cv_metrics)
            except Exception as e:
                print(f"⚠️  Claude analysis failed: {e}")
                analysis = self._fallback_analysis(vitals, cv_metrics)
        else:
            analysis = self._fallback_analysis(vitals, cv_metrics)
        
        # Create alert if needed
        if analysis["severity"] in ["CRITICAL", "WARNING"]:
            alert = {
                "alert_id": f"A{len(self.alert_history)}",
                "patient_id": patient_id,
                "severity": analysis["severity"],
                "message": self._create_alert_message(patient_id, analysis),
                "reasoning": analysis["reasoning"],
                "recommended_action": analysis["recommended_action"],
                "timestamp": datetime.utcnow().isoformat(),
                "vitals": vitals,
                "cv_metrics": cv_metrics
            }
            
            self.alerts.append(alert)
            self.alert_history.append(alert)
            
            # Keep only last 20 active alerts
            if len(self.alerts) > 20:
                self.alerts.pop(0)
        
        return analysis
    
    async def _analyze_with_claude(self, patient_id: str, vitals: Dict, cv_metrics: Dict) -> Dict:
        """Use Claude to analyze patient health"""
        prompt = f"""You are a medical AI monitoring a patient in a CAR-T therapy clinical trial.

Patient ID: {patient_id}

Current Vitals:
- Heart Rate: {vitals.get('heart_rate', 'N/A')} bpm
- Temperature: {vitals.get('temperature', 'N/A')}°C
- Blood Pressure: {vitals.get('blood_pressure', 'N/A')}
- SpO2: {vitals.get('spo2', 'N/A')}%

Computer Vision Metrics:
- Distress Score: {cv_metrics.get('distress_score', 0)}/10
- Movement Score: {cv_metrics.get('movement_score', 0)}/10
- Posture Alert: {cv_metrics.get('posture_alert', False)}

Analyze this data and respond with JSON:
{{
  "severity": "CRITICAL" | "WARNING" | "NORMAL",
  "concerns": ["list", "of", "concerns"],
  "recommended_action": "what staff should do",
  "reasoning": "brief explanation",
  "confidence": 0.0-1.0
}}

Focus on:
- Cytokine Release Syndrome (CRS): fever + tachycardia + hypotension
- Neurotoxicity: confusion, altered behavior
- Cardiac events
- Respiratory distress"""

        response = await asyncio.to_thread(
            claude_client.messages.create,
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse Claude's response
        text = response.content[0].text
        
        # Extract JSON from response
        if "{" in text and "}" in text:
            json_start = text.index("{")
            json_end = text.rindex("}") + 1
            analysis = json.loads(text[json_start:json_end])
            return analysis
        else:
            # Fallback if Claude doesn't return JSON
            return self._fallback_analysis(vitals, cv_metrics)
    
    def _fallback_analysis(self, vitals: Dict, cv_metrics: Dict) -> Dict:
        """Rule-based analysis when Claude is unavailable"""
        hr = vitals.get("heart_rate", 70)
        temp = vitals.get("temperature", 37.0)
        spo2 = vitals.get("spo2", 98)
        distress = cv_metrics.get("distress_score", 0)
        
        severity = "NORMAL"
        concerns = []
        
        # Check for critical conditions
        if spo2 < 90:
            severity = "CRITICAL"
            concerns.append("severe_hypoxia")
        
        if hr > 130 or hr < 45:
            severity = "CRITICAL" if severity == "CRITICAL" else "WARNING"
            concerns.append("severe_arrhythmia")
        
        if temp > 39.0:
            severity = "WARNING" if severity == "NORMAL" else severity
            concerns.append("high_fever")
        
        if distress > 8:
            severity = "CRITICAL" if temp > 38.0 or hr > 120 else "WARNING"
            concerns.append("severe_distress")
        
        # Check for CRS (fever + tachycardia)
        if temp > 38.0 and hr > 100:
            concerns.append("possible_CRS")
            severity = "WARNING" if severity == "NORMAL" else severity
        
        # Recommended actions
        if severity == "CRITICAL":
            action = "Immediate medical intervention - notify physician, prepare emergency equipment"
        elif severity == "WARNING":
            action = "Increased monitoring - assess in person, prepare for potential escalation"
        else:
            action = "Continue routine monitoring"
        
        reasoning = f"HR: {hr} bpm, Temp: {temp}°C, SpO2: {spo2}%, Distress: {distress}/10"
        if concerns:
            reasoning += f". Concerns: {', '.join(concerns)}"
        
        return {
            "severity": severity,
            "concerns": concerns,
            "recommended_action": action,
            "reasoning": reasoning,
            "confidence": 0.75
        }
    
    def _create_alert_message(self, patient_id: str, analysis: Dict) -> str:
        """Create human-readable alert message"""
        if analysis["severity"] == "CRITICAL":
            return f"🚨 CRITICAL: Patient {patient_id} requires immediate attention"
        elif analysis["severity"] == "WARNING":
            return f"⚠️ WARNING: Patient {patient_id} showing concerning signs"
        else:
            return f"✅ Patient {patient_id} status normal"
    
    def get_patient_status(self, patient_id: str) -> Optional[Dict]:
        """Get current status for a patient"""
        return self.patients.get(patient_id)
    
    def get_all_patients(self) -> Dict:
        """Get all monitored patients"""
        return self.patients
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts"""
        return self.alerts
    
    def get_alert_history(self) -> List[Dict]:
        """Get alert history"""
        return self.alert_history
    
    def get_status(self) -> Dict:
        """Get agent status"""
        critical = sum(1 for a in self.alerts if a["severity"] == "CRITICAL")
        warning = sum(1 for a in self.alerts if a["severity"] == "WARNING")
        
        return {
            "enabled": self.enabled,
            "patients_monitored": len(self.patients),
            "active_alerts": len(self.alerts),
            "critical_alerts": critical,
            "warning_alerts": warning,
            "total_alerts_processed": len(self.alert_history),
            "claude_available": CLAUDE_AVAILABLE
        }


# Global instance
health_agent = HealthAgent()

