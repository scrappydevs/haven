"""
Fetch.ai Handoff Form Generator Agent
Monitors alerts table and generates handoff forms for healthcare professionals
"""
from uagents import Agent, Context, Model, Protocol
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import anthropic
import os
import logging
from collections import defaultdict

from app.services.alerts_service import alerts_service
from app.services.pdf_generator import pdf_generator
from app.services.email_service import email_service
from app.supabase_client import supabase
from app.models.handoff_forms import (
    HandoffForm,
    HandoffFormContent,
    PatientInfo,
    AlertInfo,
    AlertSeverity,
    FormGenerationResponse
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models for Fetch.ai Agent Communication
# ============================================================================

class AlertNotification(Model):
    """Notification of new alerts requiring handoff"""
    alert_ids: List[str]
    patient_id: str
    severity: str
    trigger_immediate: bool = False


class HandoffFormRequest(Model):
    """Request to generate handoff form"""
    alert_ids: Optional[List[str]] = None
    patient_id: Optional[str] = None
    recipient_emails: Optional[List[str]] = None
    force_regenerate: bool = False


class HandoffFormResult(Model):
    """Result of handoff form generation"""
    success: bool
    form_id: Optional[str] = None
    form_number: Optional[str] = None
    pdf_path: Optional[str] = None
    message: str
    alerts_processed: int = 0


# ============================================================================
# Fetch.ai Handoff Agent
# ============================================================================

class FetchHandoffAgent:
    """
    Fetch.ai agent that monitors alerts and generates handoff forms
    """

    def __init__(
        self,
        name: str = "haven-handoff-agent",
        seed: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        nurse_emails: Optional[List[str]] = None,
        check_interval_seconds: int = 300  # Check every 5 minutes
    ):
        """
        Initialize Fetch.ai Handoff Agent

        Args:
            name: Agent name
            seed: Agent seed for address generation
            anthropic_api_key: Claude API key for content generation
            nurse_emails: Default nurse email addresses
            check_interval_seconds: How often to check for new alerts
        """
        self.agent_seed = seed or os.getenv("HANDOFF_AGENT_SEED", "handoff_agent_secret_seed_123")
        self.agent = Agent(name=name, seed=self.agent_seed, port=8001, endpoint=["http://localhost:8001/submit"])

        # Initialize Claude client
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.anthropic_api_key:
            self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        else:
            self.claude_client = None
            logger.warning("No Anthropic API key provided. Will use basic form generation.")

        # Configuration
        self.nurse_emails = nurse_emails or os.getenv("NURSE_EMAILS", "").split(",")
        self.nurse_emails = [email.strip() for email in self.nurse_emails if email.strip()]
        self.check_interval = check_interval_seconds

        # State
        self.processed_alerts = set()  # Track processed alert IDs
        self.generated_forms = []  # Track generated forms
        self.last_check_time = datetime.utcnow()

        # Setup agent protocols
        self._setup_protocols()

        logger.info(f"✅ Fetch.ai Handoff Agent initialized: {self.agent.address}")
        logger.info(f"📧 Default nurse emails: {self.nurse_emails}")

    def _setup_protocols(self):
        """Setup agent protocols and message handlers"""

        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            """Agent startup handler"""
            ctx.logger.info(f"Handoff Agent started with address: {self.agent.address}")
            ctx.logger.info(f"Monitoring alerts every {self.check_interval} seconds")

        @self.agent.on_interval(period=self.check_interval)
        async def check_alerts(ctx: Context):
            """Periodically check for alerts requiring handoff"""
            ctx.logger.info("Checking for alerts requiring handoff...")
            await self._process_pending_alerts(ctx)

        @self.agent.on_message(model=HandoffFormRequest)
        async def handle_form_request(ctx: Context, sender: str, msg: HandoffFormRequest):
            """Handle manual handoff form generation request"""
            ctx.logger.info(f"Received handoff form request from {sender}")

            result = await self._generate_handoff_form(
                ctx=ctx,
                alert_ids=msg.alert_ids,
                patient_id=msg.patient_id,
                recipient_emails=msg.recipient_emails,
                force_regenerate=msg.force_regenerate
            )

            # Send result back to sender
            await ctx.send(sender, result)

    async def _process_pending_alerts(self, ctx: Context):
        """Process all pending alerts that need handoff forms"""
        try:
            # Get alerts requiring handoff
            alerts = alerts_service.get_alerts_requiring_handoff()

            if not alerts:
                ctx.logger.info("No alerts requiring handoff at this time")
                return

            # Group alerts by patient
            alerts_by_patient = defaultdict(list)
            for alert in alerts:
                if alert.id not in self.processed_alerts:
                    alerts_by_patient[alert.patient_id].append(alert)

            ctx.logger.info(f"Found {len(alerts)} alerts for {len(alerts_by_patient)} patients")

            # Generate handoff form for each patient
            for patient_id, patient_alerts in alerts_by_patient.items():
                ctx.logger.info(f"Generating handoff form for patient {patient_id} ({len(patient_alerts)} alerts)")

                alert_ids = [alert.id for alert in patient_alerts]
                result = await self._generate_handoff_form(
                    ctx=ctx,
                    alert_ids=alert_ids,
                    patient_id=patient_id,
                    recipient_emails=self.nurse_emails
                )

                if result.success:
                    # Mark alerts as processed
                    self.processed_alerts.update(alert_ids)
                    ctx.logger.info(f"✅ Successfully generated form {result.form_number}")
                else:
                    ctx.logger.error(f"❌ Failed to generate form: {result.message}")

        except Exception as e:
            ctx.logger.error(f"Error processing pending alerts: {e}")

    async def _generate_handoff_form(
        self,
        ctx: Context,
        alert_ids: Optional[List[str]] = None,
        patient_id: Optional[str] = None,
        recipient_emails: Optional[List[str]] = None,
        force_regenerate: bool = False
    ) -> HandoffFormResult:
        """
        Generate handoff form from alerts

        Args:
            ctx: Agent context
            alert_ids: Specific alert IDs to include
            patient_id: Generate for all alerts of this patient
            recipient_emails: Email addresses to send form
            force_regenerate: Regenerate even if already exists

        Returns:
            HandoffFormResult with generation status
        """
        try:
            # Fetch alerts
            if alert_ids:
                alerts = alerts_service.get_alerts_by_ids(alert_ids)
            elif patient_id:
                alerts = alerts_service.get_alerts_by_patient(patient_id, include_resolved=False)
            else:
                return HandoffFormResult(
                    success=False,
                    message="Must provide either alert_ids or patient_id",
                    alerts_processed=0
                )

            if not alerts:
                return HandoffFormResult(
                    success=False,
                    message="No alerts found",
                    alerts_processed=0
                )

            # Get patient ID from first alert
            patient_id = alerts[0].patient_id
            if not patient_id:
                return HandoffFormResult(
                    success=False,
                    message="No patient_id found in alerts",
                    alerts_processed=0
                )

            # Fetch patient info
            patient_data = alerts_service.get_patient_info(patient_id)
            patient_info = PatientInfo(
                patient_id=patient_id,
                name=patient_data.get("name") if patient_data else None,
                age=patient_data.get("age") if patient_data else None,
                room_number=patient_data.get("room_number") if patient_data else None,
                diagnosis=patient_data.get("diagnosis") if patient_data else None,
                treatment_status=patient_data.get("treatment_status") if patient_data else None,
                allergies=patient_data.get("allergies") if patient_data else None,
                current_medications=patient_data.get("current_medications") if patient_data else None
            )

            # Generate form content using Claude
            form_content = await self._generate_form_content(ctx, alerts, patient_info, patient_data)

            # Generate form number
            form_number = self._generate_form_number()

            # Generate PDF
            pdf_path = pdf_generator.generate_handoff_pdf(
                form_content=form_content,
                form_number=form_number
            )

            ctx.logger.info(f"Generated PDF: {pdf_path}")

            # Save to database
            form_id = await self._save_form_to_database(
                form_number=form_number,
                patient_id=patient_id,
                alert_ids=[alert.id for alert in alerts],
                content=form_content,
                pdf_path=pdf_path
            )

            # Send email if recipients provided
            email_result = None
            if recipient_emails and recipient_emails[0]:  # Check if list is not empty
                email_result = email_service.send_handoff_form(
                    recipient_emails=recipient_emails,
                    form_number=form_number,
                    patient_id=patient_id,
                    patient_name=patient_info.name,
                    severity=form_content.severity_level.value,
                    alert_summary=form_content.alert_summary,
                    pdf_path=pdf_path
                )

                if email_result["success"]:
                    ctx.logger.info(f"📧 Email sent to {len(recipient_emails)} recipients")
                    # Update database with email info
                    await self._update_form_email_status(form_id, recipient_emails, email_result)
                else:
                    ctx.logger.error(f"Failed to send email: {email_result['message']}")

            return HandoffFormResult(
                success=True,
                form_id=form_id,
                form_number=form_number,
                pdf_path=pdf_path,
                message=f"Successfully generated handoff form {form_number}",
                alerts_processed=len(alerts)
            )

        except Exception as e:
            ctx.logger.error(f"Error generating handoff form: {e}")
            return HandoffFormResult(
                success=False,
                message=f"Error: {str(e)}",
                alerts_processed=0
            )

    async def _generate_form_content(
        self,
        ctx: Context,
        alerts: List[AlertInfo],
        patient_info: PatientInfo,
        patient_data: Optional[Dict[str, Any]]
    ) -> HandoffFormContent:
        """Generate handoff form content using Claude AI"""

        # Determine highest severity
        severity_order = ["info", "low", "medium", "high", "critical"]
        max_severity = max(alerts, key=lambda a: severity_order.index(a.severity.value))

        # Create timeline from alerts
        timeline = []
        for alert in sorted(alerts, key=lambda a: a.triggered_at or datetime.min):
            timeline.append({
                "timestamp": alert.triggered_at.strftime("%Y-%m-%d %H:%M") if alert.triggered_at else "N/A",
                "event": f"[{alert.severity.value.upper()}] {alert.alert_type.value}",
                "details": alert.title
            })

        # Generate AI summary if Claude available
        if self.claude_client:
            try:
                summary_data = await self._generate_ai_summary(alerts, patient_info, patient_data)
                alert_summary = summary_data["summary"]
                primary_concern = summary_data["primary_concern"]
                recommended_actions = summary_data["actions"]
                urgency_notes = summary_data.get("urgency_notes")
                protocols = summary_data.get("protocols")
            except Exception as e:
                ctx.logger.error(f"Claude AI error, using basic summary: {e}")
                alert_summary, primary_concern, recommended_actions, urgency_notes, protocols = self._generate_basic_summary(alerts)
        else:
            alert_summary, primary_concern, recommended_actions, urgency_notes, protocols = self._generate_basic_summary(alerts)

        # Build form content
        form_content = HandoffFormContent(
            patient_info=patient_info,
            alert_summary=alert_summary,
            primary_concern=primary_concern,
            severity_level=max_severity.severity,
            recent_vitals=self._extract_recent_vitals(alerts),
            relevant_history=patient_data.get("medical_history") if patient_data else None,
            current_treatments=patient_info.current_medications,
            recommended_actions=recommended_actions,
            urgency_notes=urgency_notes,
            protocols_to_follow=protocols,
            related_alerts=alerts,
            timeline=timeline,
            generated_at=datetime.utcnow(),
            generated_by="FETCH_AI_HANDOFF_AGENT",
            intended_recipient="Nurse/Doctor",
            special_instructions=None,
            contact_information={"Emergency": "x5555", "Charge Nurse": "x5556"}
        )

        return form_content

    async def _generate_ai_summary(
        self,
        alerts: List[AlertInfo],
        patient_info: PatientInfo,
        patient_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use Claude to generate intelligent summary and recommendations"""

        # Build context for Claude
        alerts_text = "\n".join([
            f"- [{alert.severity.value.upper()}] {alert.title}: {alert.description or 'N/A'}"
            for alert in alerts
        ])

        patient_context = f"""
Patient ID: {patient_info.patient_id}
Name: {patient_info.name or 'N/A'}
Age: {patient_info.age or 'N/A'}
Diagnosis: {patient_info.diagnosis or 'N/A'}
Treatment Status: {patient_info.treatment_status or 'N/A'}
Allergies: {', '.join(patient_info.allergies) if patient_info.allergies else 'None'}
Current Medications: {', '.join(patient_info.current_medications) if patient_info.current_medications else 'None'}
"""

        prompt = f"""You are a clinical decision support AI generating a handoff form for healthcare professionals.

PATIENT INFORMATION:
{patient_context}

RECENT ALERTS:
{alerts_text}

Please provide a concise clinical handoff summary in the following JSON format:
{{
  "summary": "2-3 sentence overview of the patient's current situation",
  "primary_concern": "One sentence describing the main concern requiring attention",
  "actions": ["Action 1", "Action 2", "Action 3"],
  "urgency_notes": "Any time-sensitive information (or null if not urgent)",
  "protocols": ["Protocol 1", "Protocol 2"] (or null if no specific protocols needed)
}}

Focus on actionable information that helps the receiving healthcare professional quickly understand and respond to the situation."""

        try:
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)
            return result

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise

    def _generate_basic_summary(self, alerts: List[AlertInfo]) -> tuple:
        """Generate basic summary without AI"""
        alert_count = len(alerts)
        critical_count = sum(1 for a in alerts if a.severity.value == "critical")
        high_count = sum(1 for a in alerts if a.severity.value == "high")

        summary = f"Patient has {alert_count} active alert(s) requiring attention."
        if critical_count > 0:
            summary += f" {critical_count} CRITICAL alert(s) present."
        if high_count > 0:
            summary += f" {high_count} HIGH severity alert(s)."

        primary_concern = alerts[0].title if alerts else "Multiple alerts require review"

        actions = [
            "Review all active alerts immediately",
            "Assess patient condition and vital signs",
            "Contact physician if condition deteriorating",
            "Document all interventions in patient record"
        ]

        urgency_notes = "Multiple alerts present - immediate assessment required" if alert_count > 2 else None
        protocols = None

        return summary, primary_concern, actions, urgency_notes, protocols

    def _extract_recent_vitals(self, alerts: List[AlertInfo]) -> Optional[Dict[str, Any]]:
        """Extract vital signs from alert metadata"""
        vitals = {}
        for alert in alerts:
            if alert.alert_type.value == "vital_sign" and alert.metadata:
                reading = alert.metadata.get("reading", {})
                if reading:
                    vitals.update(reading)

        return vitals if vitals else None

    def _generate_form_number(self) -> str:
        """Generate unique form number"""
        try:
            # Call database function to generate sequential form number
            result = supabase.rpc("generate_form_number").execute()
            if result.data:
                return result.data
        except Exception as e:
            logger.error(f"Error generating form number: {e}")

        # Fallback: timestamp-based number
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"HO-{timestamp}"

    async def _save_form_to_database(
        self,
        form_number: str,
        patient_id: str,
        alert_ids: List[str],
        content: HandoffFormContent,
        pdf_path: str
    ) -> str:
        """Save generated form to database"""
        try:
            data = {
                "form_number": form_number,
                "patient_id": patient_id,
                "alert_ids": alert_ids,
                "content": content.dict(),
                "pdf_path": pdf_path,
                "status": "generated",
                "created_by": "FETCH_AI_HANDOFF_AGENT"
            }

            result = supabase.table("handoff_forms").insert(data).execute()

            if result.data and len(result.data) > 0:
                form_id = result.data[0]["id"]
                logger.info(f"Saved form to database: {form_id}")
                return form_id
            else:
                logger.error("No data returned from database insert")
                return None

        except Exception as e:
            logger.error(f"Error saving form to database: {e}")
            raise

    async def _update_form_email_status(
        self,
        form_id: str,
        recipient_emails: List[str],
        email_result: Dict[str, Any]
    ):
        """Update form with email delivery status"""
        try:
            data = {
                "emailed_to": recipient_emails,
                "email_sent_at": datetime.utcnow().isoformat(),
                "email_delivery_status": "sent" if email_result["success"] else "failed",
                "status": "sent" if email_result["success"] else "generated"
            }

            supabase.table("handoff_forms").update(data).eq("id", form_id).execute()

        except Exception as e:
            logger.error(f"Error updating email status: {e}")

    def get_agent(self) -> Agent:
        """Get the uAgent instance"""
        return self.agent

    def run(self):
        """Run the agent"""
        logger.info("Starting Fetch.ai Handoff Agent...")
        self.agent.run()


# ============================================================================
# Create singleton instance
# ============================================================================

fetch_handoff_agent = FetchHandoffAgent(
    name="haven-handoff-agent",
    nurse_emails=os.getenv("NURSE_EMAILS", "").split(",")
)

# Export the agent for use in main.py
handoff_agent = fetch_handoff_agent.get_agent()
