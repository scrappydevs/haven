"""
Listener Agent
--------------

Lightweight orchestration helper that watches for patient speech activity on
the client and triggers downstream LiveKit voice workflows.

The actual wake-word / speech detection happens client-side (browser or edge
process). When speech is detected, the client notifies this agent so it can
coordinate with the Haven voice agent pipeline.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ListenerAgent:
    """
    Encapsulates the minimal coordination required to bridge between
    client-side speech detection and backend Haven voice agents.

    The agent does not perform audio processing itself; instead it receives
    callbacks when the browser detects patient speech (or a wake word) and
    triggers whatever downstream coroutine is provided.
    """

    def __init__(
        self,
        patient_id: str,
        on_trigger: Optional[Callable[[str], None]] = None,
        *,
        wake_words: Optional[list[str]] = None,
    ) -> None:
        self.patient_id = patient_id
        self.on_trigger = on_trigger
        self.wake_words = [w.lower() for w in (wake_words or [])]
        self.is_active = False

    def start(self) -> None:
        """Mark the listener as active so it can react to transcripts."""
        logger.info("🎧 ListenerAgent started for patient %s", self.patient_id)
        self.is_active = True

    def stop(self) -> None:
        """Stop reacting to speech events."""
        if self.is_active:
            logger.info("🛑 ListenerAgent stopped for patient %s", self.patient_id)
        self.is_active = False

    def handle_transcript(self, transcript: str) -> None:
        """
        Accept a transcript snippet from the client. If the listener is active
        and the transcript is non-empty (optionally matching a configured wake
        word), invoke the downstream callback.
        """
        if not self.is_active:
            logger.debug(
                "ListenerAgent for patient %s received transcript while inactive",
                self.patient_id,
            )
            return

        normalized = (transcript or "").strip().lower()
        if not normalized:
            return

        if self.wake_words and not any(word in normalized for word in self.wake_words):
            logger.debug(
                "ListenerAgent for patient %s ignored transcript (no wake word match)",
                self.patient_id,
            )
            return

        logger.info(
            "🔔 ListenerAgent detected speech for patient %s: %s",
            self.patient_id,
            transcript[:80],
        )
        if self.on_trigger:
            try:
                self.on_trigger(transcript)
            except Exception:  # pragma: no cover - defensive logging
                logger.exception(
                    "ListenerAgent trigger callback failed for patient %s",
                    self.patient_id,
                )
