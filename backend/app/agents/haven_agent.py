"""
Haven Voice Agent using LiveKit Agents Framework
Provides voice-activated assistance for patients during monitoring
Activated by "Hey Haven" wake word
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
from livekit.plugins import openai, silero, groq

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory patient name cache to avoid repeated DB queries
_patient_name_cache: Dict[str, Optional[str]] = {}


class HavenAgent(Agent):
    """
    AI agent that provides voice-activated assistance to monitored patients.
    ONLY asks follow-up questions - never provides medical advice or answers.
    """

    def __init__(self, patient_id: str, session_id: str, patient_name: str = None):
        # Haven agent instructions - ONLY ask questions, NEVER answer
        greeting = f"Hi {patient_name}, " if patient_name else "Hi, "

        instructions = f"""You are Haven AI, a patient monitoring assistant. Your greeting: "{greeting}I'm Haven AI. How can I help you today?"

RULES:
• NOT a doctor - never give medical advice
• Ask EXACTLY 3 short questions about: symptoms, location/severity, duration
• After question 3, ALWAYS say: "I've noted everything. A nurse will be notified immediately."
• Keep responses to 1 sentence max
• Be warm and empathetic

IMPORTANT: You can only ask 3 questions total. The system will enforce this limit.
"""

        super().__init__(instructions=instructions)

        self.patient_id = patient_id
        self.patient_name = patient_name
        self.session_id = session_id
        self.start_time = datetime.now()

        # Conversation data
        self.conversation_transcript: List[Dict[str, Any]] = []
        self.extracted_info = {
            "symptom_description": None,
            "body_location": None,
            "pain_level": None,
            "duration": None,
            "additional_details": []
        }

        self.question_count = 0
        self.max_questions = 3  # Maximum 3 questions
        self.conversation_complete = False

    async def on_chat_message(self, msg: llm.ChatMessage):
        """
        Track conversation and extract key information.
        """
        # Store transcript
        self.conversation_transcript.append({
            "role": msg.role,
            "content": msg.content,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"[{msg.role}]: {msg.content[:100]}...")

        # Extract info from patient responses
        if msg.role == "user":
            self._extract_info_from_response(msg.content)
            self.question_count += 1

            # Check if we should end the conversation
            if self._should_end_conversation():
                logger.info(f"Haven conversation complete for patient {self.patient_id}")
                self.conversation_complete = True
                # Save alert to database asynchronously
                asyncio.create_task(self._save_alert())

    def _extract_info_from_response(self, patient_response: str):
        """
        Extract structured data from patient's response.
        """
        response_lower = patient_response.lower()

        # Extract pain level
        for i in range(1, 11):
            if str(i) in patient_response and "pain" in self.conversation_transcript[-2]["content"].lower():
                self.extracted_info["pain_level"] = i
                break

        # Extract duration indicators
        duration_keywords = ["minute", "hour", "day", "week", "since", "ago", "started"]
        if any(keyword in response_lower for keyword in duration_keywords):
            if not self.extracted_info["duration"]:
                self.extracted_info["duration"] = patient_response

        # Extract body location indicators
        body_parts = ["chest", "head", "stomach", "abdomen", "back", "leg", "arm", "neck",
                     "shoulder", "knee", "foot", "hand", "throat", "ear", "eye"]
        for part in body_parts:
            if part in response_lower:
                if not self.extracted_info["body_location"]:
                    self.extracted_info["body_location"] = part

        # Store first substantial response as symptom description
        if not self.extracted_info["symptom_description"] and len(patient_response) > 15:
            self.extracted_info["symptom_description"] = patient_response

    def _should_end_conversation(self) -> bool:
        """
        Determine if conversation should end.
        """
        # End if we have core information or hit max questions
        has_core_info = (
            self.extracted_info.get("symptom_description") and
            (self.extracted_info.get("pain_level") or self.extracted_info.get("duration"))
        )

        return has_core_info or self.question_count >= self.max_questions

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of conversation for alert creation.
        """
        return {
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "transcript": self.conversation_transcript,
            "extracted_info": self.extracted_info,
            "full_transcript_text": "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_transcript
            ])
        }

    async def _save_alert(self):
        """
        Save alert to database and notify dashboard when conversation completes.
        Only saves once per conversation to prevent duplicates.
        """
        # Prevent duplicate alerts from being saved
        if hasattr(self, '_alert_saved') and self._alert_saved:
            logger.warning(f"⚠️ Alert already saved for patient {self.patient_id}, skipping duplicate")
            return

        try:
            # Mark as saving immediately to prevent race conditions
            self._alert_saved = True

            # Import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from supabase_client import supabase

            summary = self.get_conversation_summary()

            # Determine urgency level
            urgency = "medium"  # Default
            if self.extracted_info.get("pain_level") and self.extracted_info["pain_level"] >= 7:
                urgency = "high"

            # Create alert record
            alert_data = {
                "patient_id": self.patient_id,
                "type": "patient_concern",
                "title": f"Patient reported: {self.extracted_info.get('symptom_description', 'concern')}",
                "description": f"{self.patient_name or 'Patient'} reported {self.extracted_info.get('symptom_description', 'a concern')}",
                "urgency": urgency,
                "status": "active",
                "metadata": {
                    "source": "haven_ai",
                    "session_id": self.session_id,
                    "conversation_summary": summary,
                    "extracted_info": self.extracted_info,
                    "transcript": self.conversation_transcript
                },
                "created_at": datetime.now().isoformat()
            }

            if supabase:
                result = supabase.table("alerts").insert(alert_data).execute()
                alert_id = result.data[0]["id"] if result.data else None
                # Count how many questions were actually asked
                questions_asked = sum(1 for msg in self.conversation_transcript if msg['role'] == 'assistant' and '?' in msg['content'])
                logger.info(f"✅ Alert saved: {alert_id} for patient {self.patient_id} (after {questions_asked} questions)")

                # Notify dashboard via WebSocket
                try:
                    from websocket import manager as websocket_manager
                    await websocket_manager.broadcast_frame({
                        "type": "new_alert",
                        "patient_id": self.patient_id,
                        "alert_id": alert_id,
                        "urgency": urgency,
                        "title": alert_data["title"],
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"📢 Dashboard notified of new alert for patient {self.patient_id}")
                except Exception as e:
                    logger.error(f"Error notifying dashboard: {e}")
            else:
                logger.warning("Supabase not available, alert not saved")

        except Exception as e:
            # Reset flag on error so alert can be retried
            self._alert_saved = False
            logger.error(f"❌ Error saving alert for {self.patient_id}: {e}", exc_info=True)


# LiveKit Agent Entry Point
async def entrypoint(ctx: agents.JobContext):
    """
    Main entry point for Haven voice agent.
    Called when patient activates "Hey Haven" wake word.
    """

    # Extract patient info from room metadata
    room_name = ctx.room.name  # Format: haven-{patient_id}-{session_id}
    logger.info(f"🎯 Haven agent dispatched to room: {room_name}")

    parts = room_name.split("-")
    if len(parts) >= 3 and parts[0] == "haven":
        patient_id = parts[1]
        session_id = parts[2]
    else:
        logger.error(f"Invalid room name format: {room_name}")
        patient_id = "unknown"
        session_id = "unknown"

    logger.info(f"🛡️ Starting Haven agent for patient {patient_id}, session {session_id}")

    # Try to get patient name from cache first, then database
    patient_name = None
    if patient_id in _patient_name_cache:
        patient_name = _patient_name_cache[patient_id]
        logger.info(f"✅ Found patient name in cache: {patient_name}")
    else:
        try:
            # Import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from supabase_client import supabase

            if supabase:
                result = supabase.table("patients").select("name").eq("patient_id", patient_id).single().execute()
                if result.data:
                    patient_name = result.data.get("name")
                    _patient_name_cache[patient_id] = patient_name  # Cache it
                    logger.info(f"✅ Found patient name from DB: {patient_name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch patient name: {e}")
            _patient_name_cache[patient_id] = None  # Cache the None result

    try:
        # Create agent session with STT + LLM + TTS pipeline
        session = AgentSession(
            # Speech-to-Text
            stt=openai.STT(model="whisper-1"),

            # Language Model - Using Groq for 75% faster response time
            llm=groq.LLM(model="llama-3.1-8b-instant", temperature=0.7),

            # Text-to-Speech
            tts=openai.TTS(voice="nova"),  # Warm, caring voice

            # Voice Activity Detection - aggressive settings for faster response
            vad=silero.VAD.load(
                min_silence_duration=0.3,  # Stop after 0.3s of silence (optimized)
                min_speech_duration=0.1,   # Require only 0.1s of speech to start
                padding_duration=0.05,     # Minimal padding around speech
            ),
        )

        # Start session with agent
        logger.info("🤖 Starting Haven agent session...")
        agent_instance = HavenAgent(patient_id, session_id, patient_name)

        # ===== ENFORCE 3-QUESTION LIMIT =====
        # Wrap session.say() to count questions and force-stop after 3
        question_count = [0]  # Use list for closure mutability
        original_say = session.say

        async def limited_say(text: str, *args, **kwargs):
            """Intercept outgoing speech to enforce 3-question limit"""

            # Count questions (any message with '?')
            if '?' in text:
                question_count[0] += 1
                logger.info(f"📊 Question {question_count[0]}/3 asked to {patient_id}")

                # Block 4th question, force closing statement
                if question_count[0] > 3:
                    closing = "I've noted everything. A nurse will be notified immediately."
                    logger.info(f"🛑 Max questions reached for {patient_id}, forcing close")
                    await original_say(closing, *args, **kwargs)
                    # Save alert and mark complete
                    agent_instance.conversation_complete = True
                    await agent_instance._save_alert()
                    return  # Don't speak the 4th question

            # Allow the message through
            await original_say(text, *args, **kwargs)

            # Auto-complete after 3rd question
            if question_count[0] >= 3 and not agent_instance.conversation_complete:
                logger.info(f"📋 3 questions complete for {patient_id}, will save alert after next response")
                agent_instance.conversation_complete = True

        # Replace session.say with our enforced wrapper
        session.say = limited_say
        # ===== END 3-QUESTION LIMIT =====

        await session.start(
            room=ctx.room,
            agent=agent_instance,
        )

        logger.info(f"✅ Haven agent ready for patient {patient_id}")

        # Generate initial greeting
        greeting = f"Hi {patient_name}, " if patient_name else "Hi, "
        greeting += "I'm Haven AI. How can I help you today?"

        logger.info(f"🗣️ Speaking initial greeting: {greeting}")
        await session.say(greeting)
        logger.info("✅ Initial greeting spoken, waiting for patient response...")

    except Exception as e:
        logger.error(f"❌ Error in Haven agent entrypoint: {e}", exc_info=True)
        raise


# Command-line execution
if __name__ == "__main__":
    logger.info("🚀 Starting Haven Voice Agent Worker...")

    # Run agent worker
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            num_idle_processes=2,
        )
    )
