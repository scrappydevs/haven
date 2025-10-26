# Haven

A multi-agent hospital intelligence platform that coordinates autonomous and contextually aware AI agents for comprehensive patient monitoring and clinical decision support.

## System Overview

Haven operates as a multi-agent hospital command center that coordinates autonomous and contextually aware AI agents for comprehensive patient monitoring and clinical decision support. The platform employs a voice intake agent via **LiveKit and OpenAI** to facilitate natural patient conversations, conducting structured follow-up questioning to collect missing clinical details, accessing validated EHR data, and generating nurse-ready summaries and action items. Multiple **Fetch.ai agents** function as health monitoring agents that continuously track patient vitals and coordinate with specialized agents (including Alert Response Agents) to detect clinical issues and generate appropriate alerts. The system incorporates spatial intelligence capabilities through a **live 3D hospital map** with real-time alert-based room visualization, powered by a **chat agent** with Anthropic Claude chain-tool calling, enabling nurses to manage hospital resources and request clinical summaries through natural language queries.

## System Architecture

**Voice Processing Pipeline**: The system implements a robust voice interaction framework using LiveKit for real-time audio streaming, OpenAI Whisper for speech-to-text conversion, and Groq LLM for rapid response generation. Voice activity detection utilizes Silero VAD with configurable silence detection (0.3s) and minimum speech duration (0.1s) parameters. The pipeline handles connection drops, partial transcriptions, and overlapping speech through comprehensive exception handling and recovery mechanisms.

**Multi-Stream Synchronization**: Haven manages concurrent WebSocket streams from multiple sources including LiveKit (voice/video), Fetch.ai agents (vital alerts), and Claude toolchain (map updates). The system implements optimized synchronization protocols to maintain real-time data consistency while processing computer vision pipelines in background threads to prevent UI blocking.

**Conversation Management**: The platform includes an intelligent summarization pipeline that compresses extended patient conversations while preserving critical clinical information including pain levels, symptom descriptions, and emotional context. This ensures efficient context management across agent communications and LLM interactions.

## Technical Architecture

**Multi-Agent Coordination**: Haven employs a distributed agent architecture where specialized agents communicate through message passing and shared state management. Each agent operates independently while maintaining awareness of system-wide events through a centralized event bus.

**Real-Time Data Pipeline**: The system processes multiple concurrent data streams including video feeds (30fps), audio streams (16kHz), vital signs (1Hz), and agent communications. All data flows through WebSocket connections with sub-100ms latency requirements.

**Computer Vision Pipeline**: Facial photoplethysmography (FPPG) implementation using OpenCV for ROI detection, per-channel standardization for signal preprocessing, and FastICA source separation for heart rate extraction. The pipeline processes forehead regions at 30fps with 8-second rolling windows for frequency domain analysis.

**Voice Processing Stack**: LiveKit integration with OpenAI Whisper for real-time transcription, Groq LLM for 75% faster response times, and OpenAI TTS with Nova voice for natural speech synthesis. Voice activity detection uses Silero VAD with 0.3s silence detection and 0.1s speech minimum duration.

**Spatial Intelligence**: 3D hospital map rendered with Three.js, updated in real-time through Claude chain-tool calling. Room states are managed through Supabase with WebSocket synchronization for instant updates across all connected clients.

## Future Development

**Agent Ecosystem Expansion**:
- Medication Reconciliation Agent: Cross-references patient meds with new prescriptions to catch dangerous interactions before they happen
- Discharge Planning Agent: Coordinates with social workers, pharmacies, and home health services to streamline patient transitions
- Resource Allocation Agent: Dynamically assigns rooms, equipment, and staff based on real-time hospital capacity and patient acuity
- Family Communication Agent: Proactively updates loved ones and schedules care conferences, reducing the communication burden on clinical staff

**Technical Enhancements**:
- Reinforcement Learning from Clinical Feedback: nurses would rate agent suggestions, allowing the system to improve accuracy over time and learn hospital-specific workflows
- Multi-modal Patient Monitoring: Integrate computer vision to detect patient movement patterns, fall risk, and behavioral changes that complement vital sign monitoring
- Federated Learning Across Hospitals: Enable Haven deployments to learn from each other while maintaining patient privacy, creating a collective intelligence that improves with every installation

## Live Agent Access

[haven_nurse on Agentverse](https://agentverse.ai/agents/agent1q2w5ktcdjujflcq639lp6kj89zupd28yr4dla0z4qampxjf0txwtqjq3ka0)

