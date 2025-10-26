# Haven

AI-powered clinical trial safety monitoring platform using real-time computer vision and autonomous agents. Detects life-threatening complications in CAR-T therapy patients through continuous movement analysis and intelligent alert systems.

## Multi-Agent System

Haven integrates 5 specialized AI agents working in concert to monitor, analyze, and respond to patient conditions. The system uses Fetch.ai uAgents for autonomous decision making, LiveKit Agents for voice interaction, and Anthropic Claude for clinical reasoning.

**Personalized Voice Agents**: Patients activate assistance with "Hey Haven" wake word. The system conducts context-aware conversations referencing patient conditions and medical history, using intelligent follow-up questioning (max 3 questions) to gather critical information before automatically creating alerts and notifying nurses.

## Advanced Vital Monitoring

**Remote Photoplethysmography (rPPG)**: Contactless heart rate detection using per-channel standardization and FastICA source separation. Real-time forehead ROI analysis with RGB signal extraction and frequency domain processing enables continuous vital tracking without patient discomfort.

**Apple Watch Integration**: Seamless wearable device pairing with 6-digit secure codes. Real-time vitals streaming via WebSocket connections includes comprehensive health metrics (heart rate, HRV, SpO2, respiratory rate, temperature) with battery monitoring and offline synchronization.

## Clinical Workflows

**For Patients**: Instant voice assistance through "Hey Haven" activation provides personalized interactions based on medical condition and history, streamlining the question process and eliminating lengthy forms.

**For Healthcare Staff**: AI-powered clinical summaries generated automatically from patient interactions. Intelligent chat assistant with full database access provides context-aware decision support and automated handoff forms with AI-generated recommendations and protocols.

## Technology Stack

**Computer Vision**: Real-time movement analysis detecting falls, seizures, and agitation. Facial landmark tracking for vital sign extraction with behavioral pattern recognition and multi-modal sensor fusion combining video, audio, and wearable data.

**Infrastructure**: Supabase for real-time database operations, WebSocket for instant data streaming, Next.js frontend with real-time updates, and Python FastAPI backend with async processing.

## Live Agent Access

[haven_nurse on Agentverse](https://agentverse.ai/agents/agent1q2w5ktcdjujflcq639lp6kj89zupd28yr4dla0z4qampxjf0txwtqjq3ka0)

