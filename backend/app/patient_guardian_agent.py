"""
Patient Guardian Agent
Monitors patient metrics and dynamically adjusts monitoring levels
Uses Claude for intelligent reasoning about clinical significance
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from app.monitoring_control import monitoring_manager, MonitoringLevel
from app.infisical_config import get_secret

# Try to import anthropic (with fallback if not installed)
try:
    import anthropic
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.environ.get(
        "ANTHROPIC_MODEL",
        "claude-haiku-4-5-20251001"  # Default Anthropic model for Haven
    )
    if ANTHROPIC_API_KEY:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print(f"✅ Claude API initialized with model {ANTHROPIC_MODEL}")
    else:
        client = None
        print("⚠️ No ANTHROPIC_API_KEY found - Claude reasoning will use fallback rules")
except ImportError:
    client = None
    ANTHROPIC_MODEL = None
    print("⚠️ Anthropic library not installed - Claude reasoning will use fallback rules")

class PatientGuardianAgent:
    """
    Autonomous agent that monitors patient vitals and adjusts monitoring levels
    """

    def __init__(self):
        self.patient_baselines = {}  # {patient_id: baseline_vitals}
        self.alert_history = {}  # {patient_id: [alerts]}

    def set_baseline(self, patient_id: str, baseline: Dict):
        """Set baseline vitals for a patient"""
        self.patient_baselines[patient_id] = baseline
        print(f"📝 Baseline set for {patient_id}: HR={baseline.get('heart_rate', 75)}, RR={baseline.get('respiratory_rate', 14)}")

    def analyze_metrics(self, patient_id: str, metrics: Dict) -> Dict:
        """
        Analyze patient metrics and decide monitoring level
        Returns: {
            "action": "MAINTAIN" | "ESCALATE_TO_ENHANCED" | "ESCALATE_TO_CRITICAL" | "RETURN_TO_BASELINE",
            "reasoning": "...",
            "concerns": [...],
            "duration_minutes": 15 (for enhanced monitoring)
        }
        """
        # Get current monitoring config
        current_config = monitoring_manager.get_config(patient_id)
        current_level = current_config.level

        # Get baseline (or use defaults)
        baseline = self.patient_baselines.get(patient_id, {
            "heart_rate": 75,
            "respiratory_rate": 14,
            "crs_score": 0.0
        })

        # Calculate deviations
        hr_deviation = metrics.get("heart_rate", 75) - baseline.get("heart_rate", 75)
        rr_deviation = metrics.get("respiratory_rate", 14) - baseline.get("respiratory_rate", 14)
        crs_score = metrics.get("crs_score", 0.0)

        # Get recent alert history
        recent_alerts = self.alert_history.get(patient_id, [])[-5:]  # Last 5 alerts

        # Build Claude prompt for reasoning
        prompt = self._build_reasoning_prompt(
            patient_id=patient_id,
            current_level=current_level,
            metrics=metrics,
            baseline=baseline,
            hr_deviation=hr_deviation,
            rr_deviation=rr_deviation,
            recent_alerts=recent_alerts
        )

        # Get Claude's reasoning (or use fallback if no API key)
        if client is None:
            # Fallback: Use rule-based decision when Claude API unavailable
            print("⚠️ Using fallback rules (no Claude API)")
            return self._fallback_decision(current_level, metrics, hr_deviation, rr_deviation, crs_score)

        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse Claude's response
            reasoning_text = response.content[0].text
            decision = self._parse_claude_decision(reasoning_text, current_level)

            # Add to alert history if escalating
            if decision["action"] in ["ESCALATE_TO_ENHANCED", "ESCALATE_TO_CRITICAL"]:
                if patient_id not in self.alert_history:
                    self.alert_history[patient_id] = []
                self.alert_history[patient_id].append({
                    "timestamp": datetime.now().isoformat(),
                    "action": decision["action"],
                    "reasoning": decision["reasoning"],
                    "metrics": metrics
                })

            return decision

        except Exception as e:
            print(f"❌ Claude API error: {e}")
            # Fallback to rule-based decision
            return self._fallback_decision(current_level, metrics, hr_deviation, rr_deviation, crs_score)

    def _build_reasoning_prompt(
        self,
        patient_id: str,
        current_level: MonitoringLevel,
        metrics: Dict,
        baseline: Dict,
        hr_deviation: float,
        rr_deviation: float,
        recent_alerts: List
    ) -> str:
        """Build prompt for Claude reasoning"""

        alert_history_text = "No recent alerts"
        if recent_alerts:
            alert_history_text = "\n".join([
                f"- {alert['timestamp']}: {alert['action']} - {alert.get('reasoning', 'N/A')[:100]}"
                for alert in recent_alerts
            ])

        prompt = f"""You are a clinical monitoring AI agent for a patient undergoing CAR-T cell therapy. Your role is to analyze vital signs and determine the appropriate monitoring level.

**Patient ID:** {patient_id}
**Current Monitoring Level:** {current_level}

**Current Vitals:**
- Heart Rate: {metrics.get('heart_rate', 'N/A')} bpm (baseline: {baseline.get('heart_rate', 75)} bpm, deviation: {hr_deviation:+.0f} bpm)
- Respiratory Rate: {metrics.get('respiratory_rate', 'N/A')} breaths/min (baseline: {baseline.get('respiratory_rate', 14)} breaths/min, deviation: {rr_deviation:+.0f})
- CRS Score: {metrics.get('crs_score', 0.0):.2f} (0.0-1.0 scale, >0.5 concerning, >0.7 critical)
- Attention Score: {metrics.get('attention_score', 'N/A')}
- Eye Openness: {metrics.get('eye_openness', 'N/A')}
- Tremor Detected: {metrics.get('tremor_detected', False)}
- Tremor Magnitude: {metrics.get('tremor_magnitude', 0.0):.2f}

**Monitoring Levels:**
- BASELINE: Monitor HR, RR, CRS only (standard monitoring)
- ENHANCED: Add tremor detection, attention tracking, face touching (15 min duration, auto-returns to baseline)
- CRITICAL: All metrics + high frequency (for severe CRS or seizure risk, requires manual de-escalation)

**Recent Alert History:**
{alert_history_text}

**Clinical Context:**
- CRS (Cytokine Release Syndrome) is a common CAR-T complication
- Grade 1 CRS: Mild fever, no intervention needed → BASELINE monitoring
- Grade 2 CRS: Fever + hypotension or hypoxia → ENHANCED monitoring
- Grade 3-4 CRS: Severe symptoms, ICU-level care → CRITICAL monitoring
- Neurological symptoms (tremor, altered attention) may indicate ICANS (neurotoxicity)

**Your Task:**
Analyze the current metrics and decide:
1. Should we MAINTAIN current level?
2. Should we ESCALATE_TO_ENHANCED (add tremor, attention tracking for 15 minutes)?
3. Should we ESCALATE_TO_CRITICAL (activate full monitoring protocol)?
4. Should we RETURN_TO_BASELINE (patient stable, de-escalate)?

**Response Format (JSON):**
{{
  "action": "MAINTAIN" | "ESCALATE_TO_ENHANCED" | "ESCALATE_TO_CRITICAL" | "RETURN_TO_BASELINE",
  "reasoning": "Brief clinical reasoning (2-3 sentences)",
  "concerns": ["list", "of", "specific", "concerns"],
  "confidence": 0.0-1.0
}}

**Guidelines:**
- Be conservative: better to escalate and find stability than miss deterioration
- Enhanced monitoring is temporary (15 min), use it liberally for "watchful waiting"
- Only escalate to CRITICAL if truly severe (CRS >0.7, confirmed tremor + altered attention)
- Consider trend: is patient improving, stable, or deteriorating?
- Don't oscillate: avoid rapid level changes unless justified

Provide your clinical decision:"""

        return prompt

    def _parse_claude_decision(self, reasoning_text: str, current_level: MonitoringLevel) -> Dict:
        """Parse Claude's JSON response"""
        try:
            # Find JSON in response
            start = reasoning_text.find('{')
            end = reasoning_text.rfind('}') + 1
            json_str = reasoning_text[start:end]
            decision = json.loads(json_str)

            # Validate action
            valid_actions = ["MAINTAIN", "ESCALATE_TO_ENHANCED", "ESCALATE_TO_CRITICAL", "RETURN_TO_BASELINE"]
            if decision.get("action") not in valid_actions:
                raise ValueError(f"Invalid action: {decision.get('action')}")

            # Add duration for enhanced monitoring
            if decision["action"] == "ESCALATE_TO_ENHANCED":
                decision["duration_minutes"] = 15

            return decision

        except Exception as e:
            print(f"⚠️ Failed to parse Claude decision: {e}")
            # Fallback
            return {
                "action": "MAINTAIN",
                "reasoning": f"Failed to parse Claude response. Maintaining {current_level} for safety.",
                "concerns": ["Error in decision parsing"],
                "confidence": 0.3
            }

    def _fallback_decision(
        self,
        current_level: MonitoringLevel,
        metrics: Dict,
        hr_deviation: float,
        rr_deviation: float,
        crs_score: float
    ) -> Dict:
        """Rule-based fallback if Claude API fails"""

        # Critical thresholds
        if crs_score > 0.7 or (metrics.get("tremor_detected") and metrics.get("attention_score", 1.0) < 0.5):
            return {
                "action": "ESCALATE_TO_CRITICAL",
                "reasoning": "Critical CRS score or neurological symptoms detected (fallback rules)",
                "concerns": ["High CRS", "Tremor + altered attention"],
                "confidence": 0.8
            }

        # Enhanced monitoring triggers
        if crs_score > 0.5 or abs(hr_deviation) > 20 or abs(rr_deviation) > 6:
            if current_level == MonitoringLevel.BASELINE:
                return {
                    "action": "ESCALATE_TO_ENHANCED",
                    "reasoning": "Concerning vital signs - activating enhanced monitoring (fallback rules)",
                    "concerns": ["Elevated CRS", "Vital sign deviations"],
                    "confidence": 0.7,
                    "duration_minutes": 15
                }

        # Return to baseline if currently enhanced and stable
        if current_level == MonitoringLevel.ENHANCED and crs_score < 0.4:
            return {
                "action": "RETURN_TO_BASELINE",
                "reasoning": "Patient stable - returning to baseline monitoring (fallback rules)",
                "concerns": [],
                "confidence": 0.6
            }

        return {
            "action": "MAINTAIN",
            "reasoning": "No significant changes - maintaining current monitoring level (fallback rules)",
            "concerns": [],
            "confidence": 0.5
        }

    async def execute_decision(self, patient_id: str, decision: Dict, manager) -> Dict:
        """
        Execute the monitoring decision and broadcast to dashboard

        Args:
            patient_id: Patient identifier
            decision: Decision dict from analyze_metrics
            manager: WebSocket ConnectionManager instance

        Returns:
            Status dict
        """
        action = decision["action"]
        reasoning = decision["reasoning"]

        print(f"🤖 Agent Decision for {patient_id}: {action}")
        print(f"   Reasoning: {reasoning}")

        # Broadcast agent reasoning (so dashboard can show AI thinking)
        await manager.broadcast_frame({
            "type": "agent_reasoning",
            "patient_id": patient_id,
            "reasoning": reasoning,
            "concerns": decision.get("concerns", []),
            "confidence": decision.get("confidence", 0.7),
            "timestamp": datetime.now().isoformat()
        })

        # Execute monitoring change
        if action == "ESCALATE_TO_ENHANCED":
            duration = decision.get("duration_minutes", 15)
            config = monitoring_manager.set_enhanced_monitoring(
                patient_id=patient_id,
                duration_minutes=duration,
                reason=reasoning
            )

            # Broadcast state change
            await manager.broadcast_frame({
                "type": "monitoring_state_change",
                "patient_id": patient_id,
                "level": "ENHANCED",
                "reason": reasoning,
                "duration_minutes": duration,
                "enabled_metrics": config.enabled_metrics,
                "expires_at": config.expires_at.isoformat() if config.expires_at else None
            })

            # Send agent alert
            await manager.broadcast_frame({
                "type": "agent_alert",
                "patient_id": patient_id,
                "severity": "MONITORING",
                "message": f"🤖 Enhanced monitoring activated for {duration} minutes",
                "reasoning": reasoning,
                "concerns": decision.get("concerns", []),
                "confidence": decision.get("confidence", 0.7),
                "actions": [
                    f"Monitoring: {', '.join(config.enabled_metrics)}",
                    f"Duration: {duration} minutes",
                    "Will auto-return to baseline if stable"
                ]
            })

        elif action == "ESCALATE_TO_CRITICAL":
            config = monitoring_manager.set_critical_monitoring(
                patient_id=patient_id,
                reason=reasoning
            )

            # Broadcast state change
            await manager.broadcast_frame({
                "type": "monitoring_state_change",
                "patient_id": patient_id,
                "level": "CRITICAL",
                "reason": reasoning,
                "enabled_metrics": config.enabled_metrics
            })

            # Send critical alert
            await manager.broadcast_frame({
                "type": "agent_alert",
                "patient_id": patient_id,
                "severity": "CRITICAL",
                "message": "🚨 CRITICAL monitoring protocol activated",
                "reasoning": reasoning,
                "concerns": decision.get("concerns", []),
                "confidence": decision.get("confidence", 0.9),
                "actions": [
                    "All metrics enabled",
                    "High-frequency sampling (3s)",
                    "Manual de-escalation required",
                    "Consider clinical intervention"
                ]
            })

        elif action == "RETURN_TO_BASELINE":
            config = monitoring_manager.set_baseline_monitoring(
                patient_id=patient_id,
                reason=reasoning
            )

            # Broadcast state change
            await manager.broadcast_frame({
                "type": "monitoring_state_change",
                "patient_id": patient_id,
                "level": "BASELINE",
                "reason": reasoning,
                "enabled_metrics": config.enabled_metrics
            })

            # Send info notification
            await manager.broadcast_frame({
                "type": "agent_alert",
                "patient_id": patient_id,
                "severity": "INFO",
                "message": "✅ Patient stable - returned to baseline monitoring",
                "reasoning": reasoning,
                "confidence": decision.get("confidence", 0.8)
            })

        return {
            "status": "success",
            "action": action,
            "patient_id": patient_id
        }

# Global agent instance
patient_guardian = PatientGuardianAgent()
