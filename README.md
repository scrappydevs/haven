# Haven

<div align="center">
  <p><em>A multi-agent hospital intelligence platform that coordinates autonomous and contextually aware AI agents for comprehensive patient monitoring and clinical decision support.</em></p>
</div>

---

<div align="center">
  <img src="Haven AI.gif" alt="Haven AI Dashboard" width="800"/>
  <br/>
  <img src="Haven AI Chat.gif" alt="Haven AI Chat" width="800"/>
  <br/>
  <img src="Haven Seizure Example.gif" alt="Haven Seizure Detection" width="800"/>
  <br/>
  <img src="Haven Shoulder Pain Relief.gif" alt="Haven Shoulder Pain Relief" width="800"/>
</div>

---

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

## Fetch.ai Agent Network

Haven leverages the Fetch.ai uAgents framework and ASI Alliance (asi.one) ecosystem to deploy autonomous agents that coordinate real-time healthcare operations across decentralized infrastructure. Each agent operates independently while communicating through the ASI Alliance network, enabling inter-hospital coordination and access to decentralized AI services from Ocean Protocol and SingularityNET.

### Deployed Agents

**haven_nurse** - Primary clinical triage and monitoring agent using Claude AI for real-time patient assessment. Processes vital sign alerts, coordinates emergency responses, escalates critical conditions, and ensures clinical trial compliance. Handles 369 interactions with 2.5 rating on Agentverse.
[Access haven_nurse on Agentverse](https://agentverse.ai/agents/agent1q2w5ktcdjujflcq639lp6kj89zupd28yr4dla0z4qampxjf0txwtqjq3ka0)

**haven_asi_coordinator** - Central orchestration hub connecting Haven to the broader ASI Alliance ecosystem. Routes complex health queries to Ocean Protocol ML models for predictive analytics, SingularityNET AI services for diagnostic pattern recognition, and Fetch.ai agent networks for resource coordination. Publishes Haven's capabilities to the asi.one marketplace and monitors network health across all three alliance partners.
[Access haven_asi_coordinator on Agentverse](https://agentverse.ai/agents/details/agent1qt0f8spkqljl9w4kjth7mv6p62xpfflfwt2z8rg5dytjszsy9q2lke8gutt/profile)

**haven_resource_allocation** - Dynamic hospital resource optimizer managing ICU beds, ventilators, specialist assignments, and equipment allocation based on real-time patient acuity. Coordinates with regional hospitals through ASI Alliance for cross-facility resource sharing during capacity constraints. Monitors utilization metrics and predicts future resource needs using decentralized ML models. Handles 21 interactions on Agentverse.
[Access haven_resource_allocation on Agentverse](https://agentverse.ai/agents/details/agent1qvmkluyfdjw802w7xux9vllslsle3fhzkh5la7csjukg6q706xxk6azk66j/profile)

**haven_reconciliation** - Medication safety agent that cross-references patient medication lists against new prescriptions to identify dangerous drug interactions before administration. Maintains connection to ASI Alliance drug interaction database and performs periodic audits of all active patients. Generates critical alerts for interactions like warfarin-aspirin bleeding risks or metformin-contrast contraindications. Handles 10 interactions on Agentverse.
[Access haven_reconciliation on Agentverse](https://agentverse.ai/agents/details/agent1qg3wkffkfj7g04d5acyaqhx92ecz5w02jp8nm8pkdmurlk974pxezgfqnwf/profile)

### Agent Interlinking Architecture

The agents form a coordinated network where each specialized agent handles its domain while communicating through Fetch.ai's message-passing protocol:

**Clinical Workflow**: haven_nurse detects abnormal vitals and sends alerts. When resource escalation is needed (e.g., ICU transfer), nurse agent messages haven_resource_allocation which allocates appropriate beds and equipment. If new medications are prescribed, nurse agent triggers haven_reconciliation to validate safety before administration.

**ASI Alliance Integration**: Complex queries requiring external intelligence route through haven_asi_coordinator. When haven_resource_allocation faces local capacity constraints, coordinator queries ASI Alliance network for regional hospital availability via Ocean Protocol data sharing. When haven_reconciliation needs advanced drug interaction analysis, coordinator accesses SingularityNET AI diagnostic services. All agents publish their availability to asi.one marketplace for discoverability by other healthcare networks.

**Multi-Agent Orchestration**: haven_asi_coordinator orchestrates workflows spanning multiple alliance services - aggregating patient cohort data through Ocean Protocol, running predictive models via SingularityNET, and coordinating resource transfers through Fetch.ai agent networks. This enables capabilities beyond any single agent, such as predicting ICU demand 6 hours ahead using decentralized ML while simultaneously arranging resource pre-positioning.


