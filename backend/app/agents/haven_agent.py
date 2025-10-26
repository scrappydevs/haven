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
from livekit.plugins import openai, silero, noise_cancellation

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HavenAgent(Agent):
    """
    AI agent that provides voice-activated assistance to monitored patients.
    ONLY asks follow-up questions - never provides medical advice or answers.
    """

    def __init__(self, patient_id: str, session_id: str, patient_name: str = None):
        # Haven agent instructions - ONLY ask questions, NEVER answer
        greeting = f"Hi {patient_name}, " if patient_name else "Hi, "

        instructions = f"""You are Haven AI, a compassionate patient monitoring assistant.

CRITICAL RULES:
- You are NOT a doctor or nurse
- You NEVER provide medical advice, diagnoses, or treatment suggestions
- You ONLY listen and ask clarifying questions (maximum 3 questions)
- You gather information to alert healthcare staff

YOUR ROLE:
When the conversation starts, greet the patient warmly:
"{greeting}I'm Haven AI. How can I help you today?"

Then, ask follow-up questions to understand:
1. What they're experiencing (symptoms, pain, discomfort)
2. Where (body location) and how severe (pain scale 1-10 if applicable)
3. How long it's been happening

CONVERSATION STYLE:
- Be warm, empathetic, and calm
- Ask ONE question at a time
- Keep responses SHORT (1 sentence)
- Ask MAXIMUM 3 follow-up questions total
- Validate their concerns: "I hear you" or "Thank you for sharing that"
- Never say "I can help with that" or give advice
- After 3 questions, ALWAYS end with: "I've noted everything. A nurse will be notified immediately."

EXAMPLE INTERACTION (Maximum 3 questions):

[Greeting]
You: "Hi [patient name], I'm Haven AI. How can I help you today?"

Patient: "I'm having chest pain"
You: "I'm sorry to hear that. Where exactly do you feel the pain, and on a scale of 1 to 10, how severe is it?"

Patient: "It's on the left side, about a 7"
You: "Thank you for sharing. How long have you been experiencing this?"

Patient: "For about 20 minutes"
You: "I've noted everything. A nurse will be notified immediately."

NEVER SAY:
- "You should take..."
- "That sounds like..."
- "Try doing..."
- "It's probably..."
- "Don't worry, it's just..."

ALWAYS SAY:
- "Can you tell me more about..."
- "Where exactly..."
- "How long..."
- "I've noted everything. A nurse will be notified immediately."
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

    # Try to get patient name from database
    patient_name = None
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
                logger.info(f"✅ Found patient name: {patient_name}")
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch patient name: {e}")
        patient_name = None

    try:
        # Create agent session with STT + LLM + TTS pipeline
        session = AgentSession(
            # Speech-to-Text
            stt=openai.STT(model="whisper-1"),

            # Language Model
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.7),

            # Text-to-Speech
            tts=openai.TTS(voice="nova"),  # Warm, caring voice

            # Voice Activity Detection
            vad=silero.VAD.load(),
        )

        # Start session with agent
        logger.info("🤖 Starting Haven agent session...")
        await session.start(
            room=ctx.room,
            agent=HavenAgent(patient_id, session_id, patient_name),
            room_input_options=agents.RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        logger.info(f"✅ Haven agent ready for patient {patient_id}")
        logger.info("Waiting for patient to speak...")

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
