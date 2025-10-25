"""
Haven AI Multi-Agent System Integration
Autonomous agents for patient monitoring using Fetch.ai uAgents + Anthropic Claude
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import json

from app.infisical_config import get_secret

# Try to import uagents (optional dependency)
try:
    from uagents import Agent, Context
    UAGENTS_AVAILABLE = True
except ImportError:
    UAGENTS_AVAILABLE = False
    print("⚠️  uAgents not installed. Run: pip install uagents>=0.12.0")

# Try to import anthropic
try:
    import anthropic
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except ImportError:
    anthropic_client = None


class AgentSystem:
    """
    Integrated multi-agent system for Haven
    Manages 5 autonomous agents for patient monitoring
    """
    
    def __init__(self):
        self.enabled = UAGENTS_AVAILABLE and anthropic_client is not None
        self.agents = {}
        self.agent_status = {}
        
        # Agent event logs for dashboard
        self.agent_events = []  # For GlobalActivityFeed
        self.agent_alerts = []  # For AlertPanel
        
        # Patient baselines
        self.patient_baselines = {}
        
        # Alert history
        self.alert_history = defaultdict(list)
        
        # Timeline events (for PatientTimeline component)
        self.timeline_events = defaultdict(list)  # {patient_id: [timeline_events]}
        
        if not self.enabled:
            print("⚠️  Agent system disabled - missing dependencies")
            return
        
        print("✅ Agent system initialized")
    
    async def analyze_patient_metrics(self, patient_id: str, metrics: Dict) -> Dict:
        """
        Analyze patient metrics using AI agent logic
        Called by CV processing pipeline
        
        Args:
            patient_id: Patient identifier (e.g., "P-001")
            metrics: Dict with heart_rate, respiratory_rate, crs_score, tremor_detected, etc.
        
        Returns:
            {
                "severity": "NORMAL" | "CONCERNING" | "CRITICAL",
                "reasoning": "AI explanation...",
                "concerns": ["concern1", "concern2"],
                "confidence": 0.0-1.0,
                "actions": ["action1", "action2"]
            }
        """
        if not self.enabled:
            return {"severity": "NORMAL", "reasoning": "Agent system disabled"}
        
        # Get or set baseline
        if patient_id not in self.patient_baselines:
            self.patient_baselines[patient_id] = {
                "heart_rate": metrics.get("heart_rate", 75),
                "respiratory_rate": metrics.get("respiratory_rate", 14),
                "crs_score": 0.0
            }
        
        baseline = self.patient_baselines[patient_id]
        
        # Calculate deviations
        hr_deviation = metrics.get("heart_rate", 75) - baseline["heart_rate"]
        hr_deviation_pct = (hr_deviation / baseline["heart_rate"]) * 100
        rr_deviation = metrics.get("respiratory_rate", 14) - baseline["respiratory_rate"]
        rr_deviation_pct = (rr_deviation / baseline["respiratory_rate"]) * 100
        
        # Use Claude for assessment
        assessment = await self._assess_with_claude(
            patient_id=patient_id,
            metrics=metrics,
            baseline=baseline,
            hr_deviation=hr_deviation,
            hr_deviation_pct=hr_deviation_pct,
            rr_deviation=rr_deviation,
            rr_deviation_pct=rr_deviation_pct
        )
        
        # Log to dashboard if concerning or critical
        if assessment["severity"] in ["CONCERNING", "CRITICAL"]:
            await self._log_agent_event(patient_id, assessment, metrics)
        
        return assessment
    
    async def _assess_with_claude(
        self,
        patient_id: str,
        metrics: Dict,
        baseline: Dict,
        hr_deviation: float,
        hr_deviation_pct: float,
        rr_deviation: float,
        rr_deviation_pct: float
    ) -> Dict:
        """Use Claude to assess patient severity"""
        
        if not anthropic_client:
            return self._fallback_assessment(metrics, baseline)
        
        prompt = f"""You are a clinical monitoring AI for CAR-T therapy patients. Assess this patient's severity.

**Patient ID:** {patient_id}

**Current Vitals:**
- Heart Rate: {metrics.get('heart_rate')} bpm (baseline: {baseline['heart_rate']} bpm, deviation: {hr_deviation:+.0f} bpm, {hr_deviation_pct:+.1f}%)
- Respiratory Rate: {metrics.get('respiratory_rate')} breaths/min (baseline: {baseline['respiratory_rate']} breaths/min, deviation: {rr_deviation:+.0f}, {rr_deviation_pct:+.1f}%)
- CRS Score: {metrics.get('crs_score', 0):.2f} (0.0-1.0 scale)
- Tremor: {metrics.get('tremor_detected', False)}
- Attention: {metrics.get('attention_score', 1.0):.2f}

**Severity Levels:**
- NORMAL: Vitals within 15% of baseline, CRS < 0.5
- CONCERNING: 15-30% deviation OR CRS 0.5-0.7
- CRITICAL: >30% deviation OR CRS > 0.7

Respond in JSON:
{{
  "severity": "NORMAL" | "CONCERNING" | "CRITICAL",
  "reasoning": "Brief clinical explanation (2-3 sentences)",
  "concerns": ["specific concern 1", "concern 2"],
  "confidence": 0.0-1.0,
  "actions": ["recommended action 1", "action 2"]
}}"""

        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Latest Claude 3.5 Sonnet v2
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            result = json.loads(json_str)
            
            # Validate
            if result.get("severity") not in ["NORMAL", "CONCERNING", "CRITICAL"]:
                return self._fallback_assessment(metrics, baseline)
            
            return result
            
        except Exception as e:
            print(f"❌ Claude assessment error: {e}")
            return self._fallback_assessment(metrics, baseline)
    
    def _fallback_assessment(self, metrics: Dict, baseline: Dict) -> Dict:
        """Rule-based fallback"""
        hr = metrics.get("heart_rate", 75)
        rr = metrics.get("respiratory_rate", 14)
        crs_score = metrics.get("crs_score", 0)
        
        hr_dev_pct = abs((hr - baseline["heart_rate"]) / baseline["heart_rate"]) * 100
        rr_dev_pct = abs((rr - baseline["respiratory_rate"]) / baseline["respiratory_rate"]) * 100
        
        if crs_score > 0.7 or hr_dev_pct > 30 or rr_dev_pct > 30:
            return {
                "severity": "CRITICAL",
                "reasoning": f"Critical CRS score ({crs_score:.2f}) or vital signs >30% from baseline",
                "concerns": ["High CRS", "Significant vital deviation"],
                "confidence": 0.8,
                "actions": ["Notify physician immediately", "Increase monitoring to q5min"]
            }
        elif crs_score > 0.5 or hr_dev_pct > 15 or rr_dev_pct > 15:
            return {
                "severity": "CONCERNING",
                "reasoning": f"Elevated CRS ({crs_score:.2f}) or vital signs 15-30% from baseline",
                "concerns": ["Rising CRS", "Moderate vital deviation"],
                "confidence": 0.7,
                "actions": ["Increase monitoring to q15min", "Notify charge nurse"]
            }
        else:
            return {
                "severity": "NORMAL",
                "reasoning": f"All vitals within acceptable range",
                "concerns": [],
                "confidence": 0.9,
                "actions": ["Continue routine monitoring"]
            }
    
    async def _log_agent_event(self, patient_id: str, assessment: Dict, metrics: Dict):
        """Log agent decision to dashboard"""
        
        severity = assessment["severity"]
        
        # Add to agent events (GlobalActivityFeed)
        event = {
            "timestamp": datetime.now().isoformat(),
            "patientId": patient_id,
            "patientName": f"Patient {patient_id}",
            "type": "alert" if severity == "CRITICAL" else "warning",
            "severity": severity,
            "message": f"🤖 AI Agent: {severity}",
            "details": assessment["reasoning"][:100]
        }
        self.agent_events.append(event)
        
        # Add to timeline events (for PatientTimeline component)
        timeline_event = {
            "timestamp": datetime.now().isoformat(),
            "status": severity,
            "message": assessment["reasoning"],
            "metrics": metrics,
            "reasoning": assessment["reasoning"],
            "concerns": assessment["concerns"],
            "actions": assessment["actions"]
        }
        self.timeline_events[patient_id].append(timeline_event)
        
        # Keep last 500 timeline events per patient (covers ~4 hours at 30s intervals)
        if len(self.timeline_events[patient_id]) > 500:
            self.timeline_events[patient_id] = self.timeline_events[patient_id][-500:]
        
        # Keep last 100 events
        if len(self.agent_events) > 100:
            self.agent_events = self.agent_events[-100:]
        
        # Add to alerts if concerning/critical
        alert = {
            "patient_id": patient_id,
            "severity": severity,
            "message": assessment["reasoning"],
            "concerns": assessment["concerns"],
            "confidence": assessment["confidence"],
            "actions": assessment["actions"],
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        self.agent_alerts.append(alert)
        
        # Keep last 50 alerts
        if len(self.agent_alerts) > 50:
            self.agent_alerts = self.agent_alerts[-50:]
        
        # Broadcast to WebSocket viewers (import here to avoid circular import)
        try:
            from app.websocket import manager
            await manager.broadcast_frame({
                "type": "agent_alert",
                "patient_id": patient_id,
                "severity": severity,
                "message": f"🤖 AI Agent Assessment: {severity}",
                "reasoning": assessment["reasoning"],
                "concerns": assessment["concerns"],
                "confidence": assessment["confidence"],
                "actions": assessment["actions"],
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️  Failed to broadcast agent alert: {e}")
    
    def get_agent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent agent events for dashboard"""
        return self.agent_events[-limit:]
    
    def get_agent_alerts(self) -> List[Dict]:
        """Get active agent alerts"""
        return self.agent_alerts
    
    def get_patient_timeline(self, patient_id: str, limit: int = 100) -> List[Dict]:
        """Get timeline events for a specific patient"""
        return self.timeline_events[patient_id][-limit:]
    
    def get_system_status(self) -> Dict:
        """Get agent system status"""
        return {
            "enabled": self.enabled,
            "uagents_available": UAGENTS_AVAILABLE,
            "claude_available": anthropic_client is not None,
            "total_events": len(self.agent_events),
            "active_alerts": len(self.agent_alerts),
            "patients_monitored": len(self.patient_baselines),
            "total_timeline_events": sum(len(events) for events in self.timeline_events.values())
        }


# Global agent system instance
agent_system = AgentSystem()

