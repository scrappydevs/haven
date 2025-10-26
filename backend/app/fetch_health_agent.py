"""
Fetch.ai Health Agent Integration for Haven Backend
Sends patient data to Agentverse agent for analysis
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import json

# Import Fetch.ai uAgents framework
try:
    from uagents import Agent, Context, Model
    from uagents.query import query
    UAGENTS_AVAILABLE = True
except ImportError:
    UAGENTS_AVAILABLE = False
    print("⚠️  uAgents not available - install with: pip install uagents")

# Always import BaseModel from pydantic
from pydantic import BaseModel

# Import secrets
try:
    from app.infisical_config import get_secret
    AGENTVERSE_AGENT_ADDRESS = get_secret("AGENTVERSE_HEALTH_AGENT_ADDRESS") or "agent1q2w5ktcdjujflcq639lp6kj89zupd28yr4dla0z4qampxjf0txwtqjq3ka0"
except Exception as e:
    # Fallback to your haven_nurse agent address from Agentverse logs
    AGENTVERSE_AGENT_ADDRESS = "agent1q2w5ktcdjujflcq639lp6kj89zupd28yr4dla0z4qampxjf0txwtqjq3ka0"
    print(f"⚠️  Using haven_nurse agent address: {e}")


# ==================== DATA MODELS ====================

class PatientUpdate(Model if UAGENTS_AVAILABLE else BaseModel):
    """Patient health update from Haven CV system"""
    patient_id: str
    vitals: dict  # HR, temp, BP, SpO2
    cv_metrics: dict  # movement event, respiratory, etc
    timestamp: str


class HealthAnalysis(BaseModel):
    """Health analysis result from agent"""
    severity: str  # CRITICAL, WARNING, NORMAL
    concerns: List[str]
    recommended_action: str
    reasoning: str
    confidence: float


# ==================== FETCH.AI HEALTH AGENT ====================

class FetchHealthAgent:
    """
    Fetch.ai-based Health Monitoring Agent
    Communicates with Agentverse agent for patient analysis
    """
    
    def __init__(self):
        self.enabled = UAGENTS_AVAILABLE
        self.agentverse_address = AGENTVERSE_AGENT_ADDRESS
        self.patients: Dict[str, Dict] = {}
        self.alerts: List[Dict] = []
        self.last_agentverse_call: Dict[str, float] = {}  # {patient_id: timestamp}
        self.last_emergency_call: Dict[str, float] = {}  # {patient_id: timestamp} for voice calls
        self.agentverse_cooldown = 30.0  # Only call Agentverse every 30 seconds per patient
        self.emergency_call_cooldown = 60.0  # Only make ONE voice call per minute per patient
        
        print(f"🤖 Fetch.ai Health Agent initialized")
        print(f"   Agentverse Agent: {self.agentverse_address}")
        print(f"   Throttle: 1 call per patient every {self.agentverse_cooldown}s")
        print(f"   Emergency Call: 1 per {self.emergency_call_cooldown:.0f}s per patient")
        print(f"   Status: {'✅ Ready' if self.enabled else '❌ Disabled'}")
    
    async def analyze_patient(self, patient_id: str, vitals: Dict, cv_metrics: Dict) -> Dict:
        """
        Send patient data to Agentverse agent for analysis
        
        Args:
            patient_id: Patient identifier
            vitals: {heart_rate, temperature, blood_pressure, spo2}
            cv_metrics: {movement_event, movement_confidence, movement_details, respiratory_rate, ...}
        
        Returns:
            {severity, concerns, recommended_action, reasoning, confidence}
        """
        # Concise logging for production
        hr = vitals.get('heart_rate')
        movement_event = cv_metrics.get('movement_event', 'normal')
        movement_conf = cv_metrics.get('movement_confidence', 0.0)
        print(f"🏥 Agent analyzing {patient_id}: HR={hr}, Movement={movement_event} ({movement_conf:.0%})")
        
        # Store patient data locally
        self.patients[patient_id] = {
            "vitals": vitals,
            "cv_metrics": cv_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to Agentverse agent (with throttling to prevent overwhelming)
        import time
        current_time = time.time()
        last_call = self.last_agentverse_call.get(patient_id, 0)
        time_since_last = current_time - last_call
        
        # Only call Agentverse if enough time has passed (even for emergencies to prevent overwhelming)
        movement_event = cv_metrics.get('movement_event', 'normal').lower()
        is_emergency = movement_event in ['seizure', 'fall', 'extreme_agitation']
        
        # For emergencies, reduce cooldown to 15 seconds instead of bypassing entirely
        cooldown = 15.0 if is_emergency else self.agentverse_cooldown
        should_call_agentverse = time_since_last >= cooldown
        
        if self.enabled and should_call_agentverse:
            try:
                self.last_agentverse_call[patient_id] = current_time
                analysis = await self._query_agentverse_agent(patient_id, vitals, cv_metrics)
            except Exception as e:
                print(f"⚠️  Agentverse query failed: {str(e)[:50]}... Using fallback")
                analysis = self._fallback_analysis(vitals, cv_metrics)
        else:
            # Use fast local fallback for routine checks
            if not should_call_agentverse and self.enabled:
                cooldown_used = 15.0 if is_emergency else self.agentverse_cooldown
                print(f"⏱️  Throttled (last call {time_since_last:.1f}s ago, need {cooldown_used:.0f}s) - using fallback")
            analysis = self._fallback_analysis(vitals, cv_metrics)
        
        # Store alert if concerning
        if analysis["severity"] in ["CRITICAL", "WARNING"]:
            alert = {
                "alert_id": f"FETCH-A{len(self.alerts)}",
                "patient_id": patient_id,
                "severity": analysis["severity"],
                "reasoning": analysis["reasoning"],
                "recommended_action": analysis["recommended_action"],
                "timestamp": datetime.utcnow().isoformat(),
                "agent_type": "FETCH_AI_HEALTH_AGENT"
            }
            self.alerts.append(alert)
        
        # Concise result logging
        severity_emoji = {"CRITICAL": "🚨", "WARNING": "⚠️", "NORMAL": "✅"}.get(analysis["severity"], "ℹ️")
        print(f"{severity_emoji} {patient_id}: {analysis['severity']} (conf={analysis['confidence']})")
        
        return analysis
    
    async def _query_agentverse_agent(self, patient_id: str, vitals: Dict, cv_metrics: Dict) -> Dict:
        """Query the Agentverse agent for analysis"""
        
        # Prepare message
        patient_update = PatientUpdate(
            patient_id=patient_id,
            vitals=vitals,
            cv_metrics=cv_metrics,
            timestamp=datetime.utcnow().isoformat()
        )
        
        print(f"📤 Sending to Agentverse agent: {self.agentverse_address[:20]}...")
        
        # Query the agent with reduced timeout to prevent long hangs
        try:
            response = await query(
                destination=self.agentverse_address,
                message=patient_update,
                timeout=10.0  # 10 second timeout (reduced from 30s)
            )
            print(f"📥 ✅ Response from Agentverse agent")
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"📥 ❌ Agentverse error: {error_msg}")
            raise Exception(f"Agentverse timeout or error: {error_msg}")
        
        # Parse response (MovementAnalysis from Agentverse)
        if not response:
            raise Exception("No response from Agentverse agent (empty response)")
        
        if not hasattr(response, 'decode_payload'):
            raise Exception(f"Invalid response type from Agentverse agent: {type(response)}")
        
        try:
            result = response.decode_payload()
            
            # Validate result has required fields
            if not isinstance(result, dict):
                raise Exception(f"Agentverse returned non-dict payload: {type(result)}")
            
            if "severity" not in result:
                raise Exception(f"Agentverse response missing 'severity' field: {list(result.keys())}")
            
            # Convert action list to string
            actions = result.get("recommended_action", [])
            if isinstance(actions, list):
                action_str = "\n".join([f"• {a}" for a in actions[:5]])
            else:
                action_str = str(actions)
            
            return {
                "severity": result.get("severity", "NORMAL"),
                "concerns": result.get("concerns", []),
                "recommended_action": action_str,
                "reasoning": result.get("reasoning", "Analysis from Agentverse agent"),
                "confidence": result.get("confidence", 0.8)
            }
        except Exception as e:
            raise Exception(f"Failed to parse Agentverse response: {str(e)[:100]}")
    
    def _fallback_analysis(self, vitals: Dict, cv_metrics: Dict) -> Dict:
        """
        Fallback rule-based analysis (when Agentverse agent unavailable)
        FOCUS: Movement emergencies (falls, seizures, agitation)
        """
        concerns = []
        severity = "NORMAL"
        actions = []
        reasoning = ""
        confidence = 0.7
        
        # PRIMARY: Movement emergency detection
        movement_event = cv_metrics.get('movement_event', 'normal').lower()
        movement_conf = cv_metrics.get('movement_confidence', 0.0)
        
        if movement_event == 'fall' and movement_conf > 0.5:
            severity = "CRITICAL"
            concerns.append("FALL DETECTED - Injury risk")
            actions.extend([
                "Dispatch medical staff immediately",
                "Assess for head injury or fractures",
                "Monitor consciousness and vitals",
                "Document fall circumstances"
            ])
            reasoning = f"Fall detected with {movement_conf:.0%} confidence - immediate response required"
            confidence = movement_conf
            
        elif movement_event == 'seizure' and movement_conf > 0.5:
            severity = "CRITICAL"
            concerns.append("SEIZURE DETECTED - Neurological emergency")
            concerns.append(f"High-confidence detection ({movement_conf:.0%})")
            actions.extend([
                "🚨 CALL MEDICAL STAFF IMMEDIATELY",
                "Activate emergency response protocol",
                "Ensure patient safety (turn to side, clear area)",
                "Time seizure duration",
                "Prepare emergency medication if prolonged"
            ])
            reasoning = f"⚡ SEIZURE: {movement_conf:.0%} confidence - EMERGENCY"
            confidence = movement_conf
            
        elif movement_event == 'extreme_agitation' and movement_conf > 0.5:
            severity = "WARNING"
            concerns.append("EXTREME AGITATION - Behavioral emergency")
            actions.extend([
                "Assess patient for distress or pain",
                "Consider anxiolytic medication",
                "Increase monitoring frequency",
                "Ensure environmental safety"
            ])
            reasoning = f"Extreme agitation detected with {movement_conf:.0%} confidence - assess for underlying cause"
            confidence = movement_conf
        
        # SECONDARY: Vital sign checks (only if no movement emergency)
        if severity == "NORMAL":
            hr = vitals.get('heart_rate', 75)
            rr = cv_metrics.get('respiratory_rate', 14)
            
            if hr > 120:
                severity = "WARNING"
                concerns.append(f"Tachycardia (HR: {hr})")
                actions.append("Check for fever, pain, or anxiety")
                reasoning = f"Elevated heart rate ({hr} bpm) requires assessment"
            elif hr < 50:
                severity = "WARNING"
                concerns.append(f"Bradycardia (HR: {hr})")
                actions.append("Assess for medication effects or cardiac issues")
                reasoning = f"Low heart rate ({hr} bpm) requires evaluation"
            
            if rr > 24:
                if severity == "NORMAL":
                    severity = "WARNING"
                concerns.append(f"Tachypnea (RR: {rr})")
                actions.append("Assess oxygen saturation and lung sounds")
                reasoning += f" | Elevated respiratory rate ({rr}/min)"
        
        # Default actions if none set
        if not actions:
            actions = ["Continue routine monitoring", "Document baseline metrics", "No intervention needed"]
            reasoning = "All metrics within normal parameters"
        
        return {
            "severity": severity,
            "concerns": concerns,
            "recommended_action": "\n".join([f"• {a}" for a in actions[:5]]),
            "reasoning": reasoning[:150],  # Truncate for UI
            "confidence": confidence
        }
    
    # ==================== EMERGENCY CALL MANAGEMENT ====================

    def should_make_emergency_call(self, patient_id: str, severity: str) -> bool:
        """Check if we should make an emergency voice call (prevents spam)"""
        import time
        
        # Only call for CRITICAL events
        if severity != "CRITICAL":
            return False
        
        # Check cooldown
        current_time = time.time()
        last_call = self.last_emergency_call.get(patient_id, 0)
        time_since_last = current_time - last_call
        
        if time_since_last >= self.emergency_call_cooldown:
            self.last_emergency_call[patient_id] = current_time
            return True
        else:
            print(f"📞 Emergency call suppressed (last call {time_since_last:.0f}s ago, need {self.emergency_call_cooldown:.0f}s)")
            return False
    
    # ==================== STATUS METHODS ====================
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "enabled": self.enabled,
            "agentverse_address": self.agentverse_address,
            "patients_monitored": len(self.patients),
            "active_alerts": len([a for a in self.alerts if a.get("severity") in ["CRITICAL", "WARNING"]])
        }
    
    def get_all_patients(self) -> List[Dict]:
        """Get all monitored patients"""
        return [
            {"patient_id": pid, **data}
            for pid, data in self.patients.items()
        ]
    
    def get_patient_status(self, patient_id: str) -> Optional[Dict]:
        """Get specific patient status"""
        return self.patients.get(patient_id)
    
    def get_active_alerts(self) -> List[Dict]:
        """Get active alerts"""
        return [a for a in self.alerts if a.get("severity") in ["CRITICAL", "WARNING"]]
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """Get recent alert history"""
        return self.alerts[-limit:]


# ==================== SINGLETON INSTANCE ====================

# Create global instance for backend integration
fetch_health_agent = FetchHealthAgent()
