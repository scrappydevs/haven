"""
Fetch.ai Health Agent Integration for Haven Backend
This integrates the actual Fetch.ai uAgent with the Haven CV processing pipeline
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import json

# Import Fetch.ai uAgents framework
try:
    from uagents import Agent, Context, Model
    UAGENTS_AVAILABLE = True
except ImportError:
    UAGENTS_AVAILABLE = False
    print("⚠️  uAgents not available - install with: pip install uagents")

# Always import BaseModel from pydantic
from pydantic import BaseModel

# Import Claude for LLM reasoning
try:
    import anthropic
    from app.infisical_config import get_secret
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
    CLAUDE_AVAILABLE = claude_client is not None
except Exception as e:
    claude_client = None
    CLAUDE_AVAILABLE = False
    print(f"⚠️  Claude not available: {e}")


# ==================== DATA MODELS ====================

class PatientUpdate(Model if UAGENTS_AVAILABLE else BaseModel):
    """Patient health update from Haven CV system"""
    patient_id: str
    vitals: dict  # HR, temp, BP, SpO2
    cv_metrics: dict  # distress, movement, posture
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
    Uses uAgents framework + Claude for patient safety monitoring
    """
    
    def __init__(self):
        self.enabled = UAGENTS_AVAILABLE and CLAUDE_AVAILABLE
        self.agent = None
        self.patients: Dict[str, Dict] = {}
        self.alerts: List[Dict] = []
        
        if UAGENTS_AVAILABLE:
            # Create Fetch.ai uAgent
            self.agent = Agent(
                name="haven_health_backend",
                seed="haven_backend_health_monitor_2024",
                port=8001,  # Different port from main app
                endpoint=["http://localhost:8001/submit"]
            )
            
            # Register message handler for patient updates
            @self.agent.on_message(model=PatientUpdate)
            async def handle_patient_update(ctx: Context, sender: str, msg: PatientUpdate):
                """Handle incoming patient updates"""
                ctx.logger.info(f"📊 Received update for {msg.patient_id}")
                # Store in agent state
                self.patients[msg.patient_id] = {
                    "vitals": msg.vitals,
                    "cv_metrics": msg.cv_metrics,
                    "timestamp": msg.timestamp,
                    "last_sender": sender
                }
            
            print(f"✅ Fetch.ai Health Agent created")
            print(f"   Address: {self.agent.address}")
            print(f"   Name: {self.agent.name}")
        else:
            print("⚠️  Fetch.ai uAgents not available - using fallback")
        
        status = "Enabled" if self.enabled else "Disabled"
        print(f"🏥 Fetch.ai Health Agent: {status}")
        print(f"   - uAgents: {'✅' if UAGENTS_AVAILABLE else '❌'}")
        print(f"   - Claude: {'✅' if CLAUDE_AVAILABLE else '❌'}")
    
    async def analyze_patient(self, patient_id: str, vitals: Dict, cv_metrics: Dict) -> Dict:
        """
        Analyze patient health using Fetch.ai agent + Claude reasoning
        
        Args:
            patient_id: Patient identifier
            vitals: {heart_rate, temperature, blood_pressure, spo2}
            cv_metrics: {movement_event, movement_confidence, movement_details, respiratory_rate, ...}
        
        Returns:
            {severity, concerns, recommended_action, reasoning, confidence}
        """
        # Concise logging for production (NEW FOCUS: Movement Events)
        hr = vitals.get('heart_rate')
        movement_event = cv_metrics.get('movement_event', 'normal')
        movement_conf = cv_metrics.get('movement_confidence', 0.0)
        print(f"🏥 Agent analyzing {patient_id}: HR={hr}, Movement={movement_event} ({movement_conf:.0%})")
        
        # Store patient data in agent state
        self.patients[patient_id] = {
            "vitals": vitals,
            "cv_metrics": cv_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Use Claude for intelligent analysis
        if CLAUDE_AVAILABLE:
            try:
                analysis = await self._analyze_with_claude(patient_id, vitals, cv_metrics)
            except Exception as e:
                print(f"⚠️  Claude error: {str(e)[:50]}...")
                analysis = self._fallback_analysis(vitals, cv_metrics)
        else:
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
    
    async def _analyze_with_claude(self, patient_id: str, vitals: Dict, cv_metrics: Dict) -> Dict:
        """Use Claude (LLM reasoning engine) to analyze patient health (UPDATED FOR MOVEMENT EMERGENCIES)"""
        
        # Extract movement emergency data
        movement_event = cv_metrics.get('movement_event', 'normal')
        movement_conf = cv_metrics.get('movement_confidence', 0.0)
        movement_details = cv_metrics.get('movement_details', '')
        calib_status = cv_metrics.get('calibration_status', {})
        
        prompt = f"""You are a clinical AI monitoring CAR-T therapy patients for MOVEMENT EMERGENCIES (falls, seizures, agitation). Analyze this patient:

PATIENT: {patient_id}

VITALS:
- Heart Rate: {vitals.get('heart_rate', 'N/A')} bpm
- Temperature: {vitals.get('temperature', 'N/A')}°C  
- Blood Pressure: {vitals.get('blood_pressure', 'N/A')}
- SpO2: {vitals.get('spo2', 'N/A')}%
- Respiratory Rate: {cv_metrics.get('respiratory_rate', 'N/A')}/min

MOVEMENT EMERGENCY DETECTION:
- Event: {movement_event.upper()}
- Confidence: {movement_conf:.0%}
- Details: {movement_details}
- Baseline Calibration: {"✓ Complete" if calib_status.get('calibrated') else f"⏳ {calib_status.get('progress', 0)}%"}

MONITORING FOCUS:
- FALLS: Rapid downward movement, loss of upright posture, injury risk
- SEIZURES: Rhythmic tremor 3-6 Hz, convulsive movements, neurological emergency
- EXTREME AGITATION: High movement levels, distress, behavioral emergency

Provide:
1. SEVERITY: NORMAL, WARNING, or CRITICAL
   - CRITICAL for falls/seizures (immediate response)
   - WARNING for extreme agitation
   - NORMAL if movement event is "normal"
2. CONCERNS: Top 2-3 specific concerns (if any)
3. ACTION: Array of 3-5 immediate next steps (concise, actionable)
4. REASONING: Brief clinical reasoning (max 150 chars)
5. CONFIDENCE: 0.0-1.0

Format as JSON. Keep responses SHORT for real-time UI display."""

        try:
            response = await asyncio.to_thread(
                claude_client.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            content = response.content[0].text
            
            # Extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            result = json.loads(json_str)
            
            return {
                "severity": result.get("SEVERITY", "NORMAL").upper(),
                "concerns": result.get("CONCERNS", []),
                "recommended_action": result.get("ACTION", "Continue monitoring"),
                "reasoning": result.get("REASONING", "Analysis complete"),
                "confidence": float(result.get("CONFIDENCE", 0.8))
            }
            
        except Exception as e:
            print(f"⚠️  Claude parsing error: {e}")
            return self._fallback_analysis(vitals, cv_metrics)
    
    def _fallback_analysis(self, vitals: Dict, cv_metrics: Dict) -> Dict:
        """Rule-based fallback when Claude is unavailable (UPDATED FOR MOVEMENT EMERGENCIES)"""
        hr = vitals.get("heart_rate", 75)
        temp = vitals.get("temperature", 37.0)
        spo2 = vitals.get("spo2", 98)
        
        # NEW: Movement emergency data (PRIMARY)
        movement_event = cv_metrics.get("movement_event", "normal")
        movement_conf = cv_metrics.get("movement_confidence", 0.0)
        movement_details = cv_metrics.get("movement_details", "")
        
        severity = "NORMAL"
        concerns = []
        
        # PRIORITY 1: Movement Emergencies (most critical)
        if movement_event == "fall" and movement_conf > 0.6:
            severity = "CRITICAL"
            concerns.append("fall_detected")
            action = ["Immediate bedside check", "Assess for injury", "Vital signs", "Call physician if injured"]
            reasoning = f"FALL: {movement_details[:100]}"
        
        elif movement_event == "seizure" and movement_conf > 0.6:
            severity = "CRITICAL"
            concerns.append("seizure_detected")
            action = ["Protect patient", "Clear area", "Time seizure", "Call neurology", "Emergency protocol"]
            reasoning = f"SEIZURE: {movement_details[:100]}"
        
        elif movement_event == "extreme_agitation" and movement_conf > 0.6:
            severity = "WARNING"
            concerns.append("extreme_agitation")
            action = ["Bedside assessment", "Check comfort", "PRN medication if needed", "Monitor closely"]
            reasoning = f"AGITATION: {movement_details[:100]}"
        
        else:
            # PRIORITY 2: Vital signs (if no movement emergency)
            if hr > 120 or hr < 50:
                severity = "WARNING"
                concerns.append("abnormal_heart_rate")
            
            if temp > 38.5:
                severity = "WARNING"
                concerns.append("fever")
            
            if spo2 < 90:
                severity = "CRITICAL"
                concerns.append("hypoxia")
            
            action = ["Call physician immediately", "Activate emergency protocol"] if severity == "CRITICAL" else \
                    ["Bedside assessment", "Increase monitoring"] if severity == "WARNING" else \
                    ["Continue routine monitoring"]
            
            reasoning = f"HR: {hr}bpm, SpO2: {spo2}%, Movement: {movement_event}"
            if concerns:
                reasoning += f". {', '.join(concerns[:2])}"
        
        # Truncate reasoning if too long
        if len(reasoning) > 150:
            reasoning = reasoning[:147] + "..."
        
        return {
            "severity": severity,
            "concerns": concerns,
            "recommended_action": action,
            "reasoning": reasoning,
            "confidence": 0.75 if movement_event != "normal" else 0.7
        }
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "enabled": self.enabled,
            "type": "FETCH_AI_HEALTH_AGENT",
            "uagents_available": UAGENTS_AVAILABLE,
            "claude_available": CLAUDE_AVAILABLE,
            "patients_monitored": len(self.patients),
            "active_alerts": len([a for a in self.alerts if a.get("severity") in ["CRITICAL", "WARNING"]]),
            "agent_address": self.agent.address if self.agent else None
        }


# ==================== GLOBAL INSTANCE ====================

# Create singleton instance
fetch_health_agent = FetchHealthAgent()

