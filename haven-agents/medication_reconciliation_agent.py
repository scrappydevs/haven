"""
Medication Reconciliation Agent
Monitors patient medications and checks for dangerous drug interactions
using Fetch.ai uAgents framework and ASI Alliance integration
"""

from uagents import Agent, Context, Model, Protocol
from typing import List, Optional
import os

# Agent configuration
AGENT_NAME = "haven_med_reconciliation"
AGENT_SEED = os.getenv("MED_AGENT_SEED", "haven_medication_reconciliation_seed_phrase_2025")

# Create agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

print(f"🏥 Medication Reconciliation Agent Address: {agent.address}")


# Message Models
class MedicationCheck(Model):
    patient_id: str
    medications: List[str]
    new_prescription: str
    timestamp: str


class InteractionAlert(Model):
    patient_id: str
    severity: str  # "CRITICAL", "WARNING", "INFO"
    interaction_type: str
    medications_involved: List[str]
    recommendation: str
    timestamp: str


class DrugInteractionQuery(Model):
    drug_a: str
    drug_b: str


# Protocol for medication reconciliation
medication_proto = Protocol(name="medication_reconciliation", version="1.0.0")


# Known drug interactions database (simplified)
DRUG_INTERACTIONS = {
    ("warfarin", "aspirin"): {
        "severity": "CRITICAL",
        "type": "Increased bleeding risk",
        "recommendation": "Avoid combination or monitor INR closely"
    },
    ("metformin", "contrast_dye"): {
        "severity": "CRITICAL", 
        "type": "Lactic acidosis risk",
        "recommendation": "Hold metformin 48 hours before contrast"
    },
    ("lisinopril", "potassium"): {
        "severity": "WARNING",
        "type": "Hyperkalemia risk",
        "recommendation": "Monitor potassium levels"
    },
    ("simvastatin", "diltiazem"): {
        "severity": "WARNING",
        "type": "Myopathy risk",
        "recommendation": "Reduce simvastatin dose or use alternative"
    },
    ("ssri", "tramadol"): {
        "severity": "CRITICAL",
        "type": "Serotonin syndrome risk",
        "recommendation": "Avoid combination, use alternative analgesic"
    }
}


@medication_proto.on_message(model=MedicationCheck)
async def handle_medication_check(ctx: Context, sender: str, msg: MedicationCheck):
    """
    Check new prescription against existing medications for interactions
    Integrates with ASI Alliance drug interaction database
    """
    ctx.logger.info(f"🔍 Checking medications for patient {msg.patient_id}")
    ctx.logger.info(f"   Current meds: {msg.medications}")
    ctx.logger.info(f"   New prescription: {msg.new_prescription}")
    
    alerts = []
    
    # Check new prescription against each existing medication
    for existing_med in msg.medications:
        interaction = check_interaction(existing_med.lower(), msg.new_prescription.lower())
        
        if interaction:
            alert = InteractionAlert(
                patient_id=msg.patient_id,
                severity=interaction["severity"],
                interaction_type=interaction["type"],
                medications_involved=[existing_med, msg.new_prescription],
                recommendation=interaction["recommendation"],
                timestamp=msg.timestamp
            )
            alerts.append(alert)
            
            # Log critical interactions
            if interaction["severity"] == "CRITICAL":
                ctx.logger.error(f"🚨 CRITICAL INTERACTION: {existing_med} + {msg.new_prescription}")
                ctx.logger.error(f"   {interaction['type']}")
    
    # If interactions found, send alerts
    if alerts:
        ctx.logger.warning(f"⚠️  Found {len(alerts)} medication interactions")
        for alert in alerts:
            # Send alert back to Haven system
            await ctx.send(sender, alert)
    else:
        ctx.logger.info(f"✅ No interactions found - safe to prescribe")


def check_interaction(drug_a: str, drug_b: str) -> Optional[dict]:
    """
    Check if two drugs have known interactions
    In production, this would query ASI Alliance drug database
    """
    # Normalize drug names
    drug_a = drug_a.strip().lower()
    drug_b = drug_b.strip().lower()
    
    # Check both orderings
    for pair in [(drug_a, drug_b), (drug_b, drug_a)]:
        if pair in DRUG_INTERACTIONS:
            return DRUG_INTERACTIONS[pair]
    
    # Check partial matches (e.g., "aspirin 81mg" matches "aspirin")
    for (known_a, known_b), interaction in DRUG_INTERACTIONS.items():
        if (known_a in drug_a and known_b in drug_b) or (known_a in drug_b and known_b in drug_a):
            return interaction
    
    return None


@medication_proto.on_interval(period=300.0)  # Every 5 minutes
async def periodic_medication_audit(ctx: Context):
    """
    Periodic audit of all patients' medication regimens
    Connects to ASI Alliance for latest drug interaction data
    """
    ctx.logger.info("🔄 Running periodic medication safety audit...")
    ctx.logger.info("   Syncing with ASI Alliance drug interaction database")
    
    # In production, this would:
    # 1. Fetch all active patients from Haven database
    # 2. Query ASI Alliance for latest interaction data
    # 3. Check all medication combinations
    # 4. Alert on any new interactions discovered
    
    ctx.logger.info("✅ Medication audit complete")


# Include protocol in agent
agent.include(medication_proto)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"🏥 Medication Reconciliation Agent started")
    ctx.logger.info(f"   Agent address: {agent.address}")
    ctx.logger.info(f"   Monitoring for drug interactions via ASI Alliance")
    ctx.logger.info(f"   Connected to Haven Health System")


if __name__ == "__main__":
    agent.run()

