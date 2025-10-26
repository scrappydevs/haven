# Haven Clinical Safety Monitor - Agentverse Ready
# For deployment to Agentverse - DO NOT instantiate Agent(), use preloaded 'agent'

import os
from uagents import Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage, ChatAcknowledgement, TextContent,
    StartSessionContent, EndSessionContent, chat_protocol_spec
)
from datetime import datetime
from typing import List
from uuid import uuid4

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Data models
class PatientUpdate(Model):
    patient_id: str
    timestamp: str
    vitals: dict
    cv_metrics: dict

class MovementAnalysis(Model):
    patient_id: str
    severity: str
    reasoning: str
    recommended_action: List[str]
    concerns: List[str]
    confidence: float
    requires_call: bool

# State tracking (simple dict for Agentverse)
state = {
    "patients": {},
    "alerts": [],
    "interaction_count": 0,
    "stats": {"total": 0, "critical": 0, "warning": 0, "normal": 0}
}

# Analysis function
def analyze_patient(patient_id: str, vitals: dict, cv_metrics: dict) -> MovementAnalysis:
    movement_event = cv_metrics.get("movement_event", "normal")
    movement_conf = cv_metrics.get("movement_confidence", 0.0)
    hr = vitals.get("heart_rate", 75)
    
    state["stats"]["total"] += 1
    
    # Critical movement emergencies
    if movement_event == "seizure" and movement_conf > 0.5:
        state["stats"]["critical"] += 1
        return MovementAnalysis(
            patient_id=patient_id,
            severity="CRITICAL",
            reasoning=f"Seizure detected ({movement_conf:.0%}) - immediate response required",
            recommended_action=[
                "Activate seizure protocol",
                "Position patient safely",
                "Time duration",
                "Notify physician"
            ],
            concerns=["Active seizure", "Airway risk", "Post-ictal state"],
            confidence=movement_conf,
            requires_call=True
        )
    
    elif movement_event == "fall" and movement_conf > 0.5:
        state["stats"]["critical"] += 1
        return MovementAnalysis(
            patient_id=patient_id,
            severity="CRITICAL",
            reasoning=f"Fall detected ({movement_conf:.0%}) - assess for injury",
            recommended_action=[
                "Dispatch response team",
                "Assess ABCs",
                "Check for trauma",
                "Obtain vitals"
            ],
            concerns=["Trauma", "Head injury", "Orthopedic injury"],
            confidence=movement_conf,
            requires_call=True
        )
    
    elif movement_event == "extreme_agitation" and movement_conf > 0.5:
        state["stats"]["warning"] += 1
        return MovementAnalysis(
            patient_id=patient_id,
            severity="WARNING",
            reasoning=f"Agitation ({movement_conf:.0%}) - evaluate for delirium",
            recommended_action=[
                "Bedside assessment",
                "Rule out hypoxia/pain",
                "Screen for neurotoxicity",
                "Consider 1:1 observation"
            ],
            concerns=["Delirium", "Neurotoxicity", "Safety"],
            confidence=movement_conf,
            requires_call=False
        )
    
    elif hr > 140 or hr < 45:
        state["stats"]["warning"] += 1
        return MovementAnalysis(
            patient_id=patient_id,
            severity="WARNING",
            reasoning=f"Critical HR {hr} bpm - requires evaluation",
            recommended_action=[
                "Obtain ECG",
                "Assess symptoms",
                "Check medications",
                "Monitor continuously"
            ],
            concerns=["Dysrhythmia", "Hemodynamic instability"],
            confidence=0.85,
            requires_call=False
        )
    
    state["stats"]["normal"] += 1
    return MovementAnalysis(
        patient_id=patient_id,
        severity="NORMAL",
        reasoning="Stable - vitals within normal parameters",
        recommended_action=["Continue routine monitoring"],
        concerns=[],
        confidence=0.95,
        requires_call=False
    )

# Patient monitoring protocol
monitoring_proto = Protocol(name="patient_monitoring", version="1.0.0")

@monitoring_proto.on_message(model=PatientUpdate)
async def handle_patient_update(ctx: Context, sender: str, msg: PatientUpdate):
    state["interaction_count"] += 1
    
    movement_event = msg.cv_metrics.get("movement_event", "normal")
    movement_conf = msg.cv_metrics.get("movement_confidence", 0.0)
    
    ctx.logger.info(f"[{state['interaction_count']}] {msg.patient_id}: {movement_event} ({movement_conf:.0%})")
    
    state["patients"][msg.patient_id] = {
        "vitals": msg.vitals,
        "cv_metrics": msg.cv_metrics,
        "timestamp": msg.timestamp
    }
    
    analysis = analyze_patient(msg.patient_id, msg.vitals, msg.cv_metrics)
    
    ctx.logger.info(f"Analysis: {analysis.severity} ({analysis.confidence:.0%})")
    
    if analysis.severity in ["CRITICAL", "WARNING"]:
        alert_id = f"ALERT-{len(state['alerts']) + 1:04d}"
        state["alerts"].append({
            "alert_id": alert_id,
            "patient_id": msg.patient_id,
            "severity": analysis.severity,
            "timestamp": datetime.utcnow().isoformat()
        })
        ctx.logger.info(f"Alert {alert_id} created")
    
    await ctx.send(sender, analysis)

agent.include(monitoring_proto, publish_manifest=True)

# Chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

def create_chat(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)]
    )

@chat_proto.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(),
        acknowledged_msg_id=msg.msg_id
    ))
    
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Chat started: {sender[:20]}")
        
        elif isinstance(item, TextContent):
            query = item.text.lower()
            
            if "status" in query or "stats" in query:
                response = (
                    f"🏥 Haven Safety Monitor\n\n"
                    f"📊 Monitoring: {len(state['patients'])} patients\n"
                    f"🔄 Interactions: {state['interaction_count']}\n\n"
                    f"📈 Analysis:\n"
                    f"  🚨 Critical: {state['stats']['critical']}\n"
                    f"  ⚠️ Warning: {state['stats']['warning']}\n"
                    f"  ✅ Normal: {state['stats']['normal']}\n\n"
                    f"🚨 Alerts: {len(state['alerts'])}\n\n"
                    f"System operational."
                )
            
            elif "patients" in query or "list" in query:
                if state["patients"]:
                    patient_list = []
                    for pid, data in state["patients"].items():
                        event = data["cv_metrics"].get("movement_event", "normal")
                        hr = data["vitals"].get("heart_rate", "N/A")
                        patient_list.append(f"• {pid}: {event} (HR: {hr})")
                    response = f"👥 Patients ({len(state['patients'])}):\n" + "\n".join(patient_list)
                else:
                    response = "No patients currently monitored."
            
            elif "alert" in query:
                recent = state["alerts"][-5:]
                if recent:
                    alert_list = [f"🚨 {a['alert_id']}: {a['patient_id']} - {a['severity']}" for a in recent]
                    response = f"Recent Alerts ({len(recent)}):\n" + "\n".join(alert_list)
                else:
                    response = "✅ No alerts - all stable."
            
            elif "help" in query or "commands" in query:
                response = (
                    "🤖 Haven Safety Monitor\n\n"
                    "📊 'status' - System overview\n"
                    "👥 'list patients' - Show patients\n"
                    "🚨 'show alerts' - Recent alerts\n"
                    "❓ 'help' - Commands\n\n"
                    "CAR-T trial monitoring."
                )
            
            else:
                response = (
                    f"🏥 Haven Clinical Safety Monitor\n\n"
                    f"Active: {len(state['patients'])} patients\n"
                    f"Total: {state['interaction_count']} interactions\n\n"
                    f"Type 'help' for commands."
                )
            
            await ctx.send(sender, create_chat(response))
        
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Chat ended: {sender[:20]}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()

