"""
Patient Intake Agent using LiveKit Agents Framework
Conducts voice-based patient interviews for Haven Health
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, llm, tokenize
from livekit.plugins import openai, silero, noise_cancellation

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatientIntakeAgent(Agent):
    """
    AI agent that conducts patient intake interviews.
    Collects chief complaint, symptoms, history, and urgency assessment.
    """

    def __init__(self, patient_id: str, session_id: str):
        # Comprehensive intake instructions
        instructions = """You are Haven AI, a compassionate medical intake assistant for a clinical trials monitoring facility.

Your goal is to efficiently gather key information before the patient sees a healthcare provider:

REQUIRED INFORMATION (ask until you have all):
1. Chief complaint (main reason for visit)
2. Symptom duration (when did it start?)
3. Symptom severity (1-10 scale, where 10 is worst)
4. Prior episodes (has this happened before?)
5. Current medications (what are they taking?)
6. Known allergies (any drug/food allergies?)

CONVERSATION STYLE:
- Be warm, empathetic, and professional
- Ask ONE question at a time
- Use simple, clear language (avoid medical jargon)
- Keep responses SHORT (1-2 sentences maximum)
- Acknowledge patient concerns: "I understand that must be difficult"
- If patient seems confused, rephrase more simply

URGENT SYMPTOM DETECTION:
If patient mentions ANY of these, IMMEDIATELY flag as HIGH urgency and expedite interview:
- Chest pain or pressure
- Severe bleeding or hemorrhage
- Difficulty breathing or shortness of breath
- Loss of consciousness or severe confusion
- Severe allergic reaction (anaphylaxis)
- Altered mental status or disorientation
- Severe abdominal pain
- Suspected stroke symptoms (FAST: Face drooping, Arm weakness, Speech difficulty)

FOLLOW-UP QUESTIONS (use clinical judgment):
- If "chest pain" mentioned → "Does the pain radiate to your arm, jaw, or back?"
- If "fever" mentioned → "Have you measured your temperature? What was it?"
- If "pain" mentioned → "On a scale of 1-10, how would you rate the pain?"
- If "medications" unclear → "Can you tell me the names of any medications you're taking?"
- If "allergies" unclear → "Do you have any allergies to medications or foods?"

CLOSING PROTOCOL:
When you have all required information, say:
"Thank you [patient name]. I have all the information I need. A healthcare provider will review this and see you shortly. Please remain in the waiting area."

EXAMPLE OPENING:
"Hello! I'm Haven AI, your virtual intake assistant. I'll help gather some information before you see the healthcare provider. May I start by asking your name and what brings you in today?"
"""

        super().__init__(instructions=instructions)

        self.patient_id = patient_id
        self.session_id = session_id
        self.start_time = datetime.now()

        # Structured data collection
        self.extracted_info = {
            "patient_name": None,
            "chief_complaint": None,
            "duration": None,
            "severity": None,
            "prior_episodes": None,
            "medications": None,
            "allergies": None,
            "urgency_level": "low",
            "symptoms": [],
            "urgent_flags": [],
        }

        self.conversation_transcript: List[Dict[str, Any]] = []
        self.question_count = 0
        self.max_questions = 15  # Safety limit
        self.interview_complete = False

    async def on_chat_message(self, msg: llm.ChatMessage):
        """
        Called whenever a chat message is processed.
        This is where we track conversation and extract information.
        """

        # Store transcript
        self.conversation_transcript.append({
            "role": msg.role,
            "content": msg.content,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"[{msg.role}]: {msg.content[:100]}...")

        # Extract structured information from patient responses
        if msg.role == "user":
            await self._extract_info_from_response(msg.content)
            self.question_count += 1

            # Check if interview should end
            if self._should_end_interview():
                logger.info(f"Interview complete for patient {self.patient_id}")
                self.interview_complete = True
                await self._save_intake_report()

    async def _extract_info_from_response(self, patient_response: str):
        """
        Extract structured data from patient's response using keyword matching
        and pattern detection. In production, you could use Claude for smarter extraction.
        """

        response_lower = patient_response.lower()

        # Detect urgent symptoms
        urgent_keywords = {
            "chest pain": "Chest pain reported",
            "chest pressure": "Chest pressure reported",
            "can't breathe": "Difficulty breathing",
            "difficulty breathing": "Difficulty breathing",
            "shortness of breath": "Shortness of breath",
            "bleeding": "Bleeding reported",
            "blood": "Bleeding/blood reported",
            "unconscious": "Loss of consciousness",
            "passed out": "Loss of consciousness",
            "severe pain": "Severe pain reported",
            "allergic reaction": "Allergic reaction",
            "can't feel": "Numbness/loss of sensation",
            "confused": "Altered mental status",
            "dizzy": "Dizziness"
        }

        for keyword, flag in urgent_keywords.items():
            if keyword in response_lower:
                self.extracted_info["urgency_level"] = "high"
                if flag not in self.extracted_info["urgent_flags"]:
                    self.extracted_info["urgent_flags"].append(flag)
                logger.warning(f"URGENT: {flag} detected for patient {self.patient_id}")

        # Extract patient name
        if "my name is" in response_lower or "i'm " in response_lower:
            # Simple name extraction (could be improved with NER)
            self.extracted_info["patient_name"] = patient_response

        # Detect medications
        medication_keywords = ["taking", "medication", "pills", "drug", "prescription", "medicine"]
        if any(word in response_lower for word in medication_keywords):
            if not self.extracted_info["medications"]:
                self.extracted_info["medications"] = patient_response
            else:
                self.extracted_info["medications"] += "; " + patient_response

        # Detect allergies
        if "allerg" in response_lower:
            if "no" in response_lower or "none" in response_lower:
                self.extracted_info["allergies"] = "None reported"
            else:
                self.extracted_info["allergies"] = patient_response

        # Detect duration
        duration_keywords = ["day", "week", "month", "year", "hour", "ago", "since", "yesterday", "today"]
        if any(keyword in response_lower for keyword in duration_keywords):
            self.extracted_info["duration"] = patient_response

        # Detect severity rating (1-10 scale)
        for i in range(1, 11):
            if str(i) in patient_response:
                self.extracted_info["severity"] = i
                if i >= 8:
                    # High severity automatically increases urgency
                    if self.extracted_info["urgency_level"] == "low":
                        self.extracted_info["urgency_level"] = "medium"
                break

        # Detect prior episodes
        if "before" in response_lower or "previous" in response_lower or "history" in response_lower:
            if "yes" in response_lower or "have" in response_lower:
                self.extracted_info["prior_episodes"] = patient_response
            elif "no" in response_lower or "never" in response_lower:
                self.extracted_info["prior_episodes"] = "No prior episodes"

        # Store chief complaint from first substantial response (> 10 chars)
        if not self.extracted_info["chief_complaint"] and len(patient_response) > 10:
            # Skip common filler responses
            filler_responses = ["yes", "no", "okay", "ok", "sure", "i don't know"]
            if patient_response.lower().strip() not in filler_responses:
                self.extracted_info["chief_complaint"] = patient_response

    def _should_end_interview(self) -> bool:
        """
        Determine if interview should end based on:
        1. All required fields collected
        2. Maximum questions reached
        3. Urgent situation detected (expedite)
        """

        # Emergency: end quickly if urgent
        if self.extracted_info["urgency_level"] == "high":
            # For urgent cases, require minimum info only
            required_for_urgent = ["chief_complaint", "allergies"]
            return all(self.extracted_info.get(field) for field in required_for_urgent)

        # Normal case: require all standard fields
        required_fields = [
            "chief_complaint",
            "duration",
            "medications",
            "allergies"
        ]
        all_collected = all(self.extracted_info.get(field) for field in required_fields)

        # Also end if we've asked too many questions
        max_reached = self.question_count >= self.max_questions

        if max_reached:
            logger.warning(f"Max questions ({self.max_questions}) reached for patient {self.patient_id}")

        return all_collected or max_reached

    async def _save_intake_report(self):
        """
        Save completed intake report to database and notify dashboard.
        """
        try:
            from app.supabase_client import supabase
            from app.websocket import manager as websocket_manager

            # Calculate interview duration
            duration = (datetime.now() - self.start_time).total_seconds()

            # Get vitals snapshot (will implement in next step)
            vitals = await self._collect_vitals_snapshot()

            # Generate AI summary
            ai_summary = await self._generate_summary()

            # Compile report
            report = {
                "patient_id": self.patient_id,
                "session_id": self.session_id,
                "livekit_room_name": f"intake-{self.patient_id}-{self.session_id}",
                "transcript": self.conversation_transcript,
                "chief_complaint": self.extracted_info.get("chief_complaint"),
                "symptoms": self.extracted_info.get("symptoms", []),
                "duration": self.extracted_info.get("duration"),
                "severity": self.extracted_info.get("severity"),
                "medications": self.extracted_info.get("medications"),
                "allergies": self.extracted_info.get("allergies"),
                "prior_episodes": self.extracted_info.get("prior_episodes"),
                "vitals": vitals,
                "urgency_level": self.extracted_info["urgency_level"],
                "ai_summary": ai_summary,
                "extracted_info": self.extracted_info,
                "status": "pending_review",
                "created_at": datetime.now().isoformat(),
                "interview_duration_seconds": int(duration),
            }

            # Save to database
            if supabase:
                result = supabase.table("intake_reports").insert(report).execute()
                intake_id = result.data[0]["id"] if result.data else None
                logger.info(f"✅ Intake report saved: {intake_id}")

                # Notify dashboard via WebSocket
                await websocket_manager.broadcast_frame({
                    "type": "new_intake",
                    "patient_id": self.patient_id,
                    "urgency": report["urgency_level"],
                    "chief_complaint": report["chief_complaint"],
                    "intake_id": intake_id,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info(f"📢 Dashboard notified of new intake for patient {self.patient_id}")
            else:
                logger.warning("Supabase not available, intake report not saved")

        except Exception as e:
            logger.error(f"Error saving intake report: {e}", exc_info=True)

    async def _collect_vitals_snapshot(self) -> Dict[str, Any]:
        """
        Collect vitals during interview using LiveKit video track.
        This will be implemented in the next step with CV processing integration.
        """
        # Placeholder for now
        return {
            "heart_rate": None,
            "respiratory_rate": None,
            "stress_indicator": None,
            "samples_collected": 0,
            "note": "Vitals collection will be implemented with CV processing integration"
        }

    async def _generate_summary(self) -> str:
        """
        Generate AI summary of interview for healthcare provider.
        Uses simple template for now, can be enhanced with Claude API call.
        """

        name = self.extracted_info.get("patient_name", "Patient")
        complaint = self.extracted_info.get("chief_complaint", "Not specified")
        duration = self.extracted_info.get("duration", "Unknown duration")
        severity = self.extracted_info.get("severity", "Not rated")
        meds = self.extracted_info.get("medications", "None reported")
        allergies = self.extracted_info.get("allergies", "None reported")
        urgency = self.extracted_info["urgency_level"].upper()

        summary = f"{name} presents with {complaint} for {duration}. "

        if severity:
            summary += f"Severity: {severity}/10. "

        summary += f"Current medications: {meds}. Allergies: {allergies}. "

        if self.extracted_info["urgent_flags"]:
            flags = ", ".join(self.extracted_info["urgent_flags"])
            summary += f"⚠️ URGENT FLAGS: {flags}. "

        summary += f"Urgency assessment: {urgency}."

        return summary


# LiveKit Agent Entry Point
async def entrypoint(ctx: agents.JobContext):
    """
    Main entry point for intake agent.
    Called automatically when a patient joins an intake room.
    """

    # Extract patient info from room metadata
    room_name = ctx.room.name  # Format: intake-{patient_id}-{session_id}
    logger.info(f"🎯 Agent dispatched to room: {room_name}")

    parts = room_name.split("-")
    if len(parts) >= 3 and parts[0] == "intake":
        patient_id = parts[1]
        session_id = parts[2]
    else:
        logger.error(f"Invalid room name format: {room_name}")
        patient_id = "unknown"
        session_id = "unknown"

    logger.info(f"🏥 Starting intake for patient {patient_id}, session {session_id}")

    try:
        # Create agent session with STT + LLM + TTS pipeline
        session = AgentSession(
            # Speech-to-Text
            stt=openai.STT(model="whisper-1"),

            # Language Model
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.7),

            # Text-to-Speech
            tts=openai.TTS(voice="alloy"),  # Options: alloy, echo, shimmer, fable, onyx, nova

            # Voice Activity Detection
            vad=silero.VAD.load(),
        )

        # Start session with agent
        logger.info("🤖 Starting agent session...")
        await session.start(
            room=ctx.room,
            agent=PatientIntakeAgent(patient_id, session_id),
            room_input_options=agents.RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),  # Background noise cancellation
            ),
        )

        logger.info(f"✅ Agent session started successfully for patient {patient_id}")
        logger.info("Agent is ready and will greet the patient when they speak")

    except Exception as e:
        logger.error(f"❌ Error in agent entrypoint: {e}", exc_info=True)
        raise


# Command-line execution
if __name__ == "__main__":
    logger.info("🚀 Starting Haven Intake Agent Worker...")

    # Run agent worker
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            num_idle_processes=2,  # Keep 2 agents ready for immediate dispatch
        )
    )
