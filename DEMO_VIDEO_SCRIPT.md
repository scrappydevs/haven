# 🎥 Demo Video Script - Fetch.ai Prize Submission

## 🎯 Goal
Record a **3-5 minute video** showing your Fetch.ai multi-agent system integrated with Haven.

## 📋 Pre-Recording Checklist

### Setup (5 minutes before recording)

```bash
# Terminal 1: Start Backend
cd /Users/gsdr/haven/backend
source venv/bin/activate
python main.py

# Wait for: "✅ Agent system enabled"

# Terminal 2: Start Frontend  
cd /Users/gsdr/haven/frontend
npm run dev

# Wait for: "Local: http://localhost:3000"
```

**Open in browser:**
- Frontend: http://localhost:3000
- Backend logs visible in Terminal 1

**Prepare to show:**
- ✅ Backend terminal (with agent logs)
- ✅ Frontend dashboard
- ✅ Code editor (optional, to show agent code)

---

## 🎬 VIDEO SCRIPT (3-5 minutes)

### **MINUTE 0-1: INTRODUCTION (60 seconds)**

**[Show: Haven Dashboard]**

> "Hi! I'm presenting Haven AI - a multi-agent system for clinical trial monitoring built with **Fetch.ai's uAgents framework** and **Anthropic Claude**."

> "The problem: CAR-T therapy patients need 24/7 monitoring for life-threatening complications like Cytokine Release Syndrome. Current approach costs $18,800 per day and can miss critical symptoms."

**[Show: Backend Terminal]**

> "Our solution uses **5 autonomous Fetch.ai agents** that continuously monitor patients, reason with Claude AI, and coordinate responses."

**[Point to terminal logs showing agent startup]**

> "Here you can see all 5 agents starting:
> - 3 Patient Guardian agents monitoring individual patients
> - 1 Nurse Coordinator for intelligent triage
> - 1 Emergency Response agent for critical situations
> - Plus Protocol Compliance and Research Insights agents"

---

### **MINUTE 1-2: AGENT SYSTEM DEMO (60 seconds)**

**[Show: Backend Terminal - Agent Logs]**

> "Let me show you how the agents work. Here's a Patient Guardian agent monitoring Patient P-001."

**[Point to logs showing:]**
```
INFO: [Guardian_P001]: ✅ P-001 - Status: NORMAL
   HR: 74 bpm (baseline 72), RR: 15 (baseline 14), CRS: 0.32
   All vitals within acceptable range...
```

> "Every 30 seconds, the agent analyzes vital signs and compares them to the patient's baseline."

**[Show: Claude reasoning in logs]**

> "Here's the key: the agent uses **Anthropic Claude** for clinical reasoning. You can see Claude's assessment here - it's analyzing heart rate deviation, respiratory rate, and CRS score to determine severity."

**[Point to agent address in logs]**
```
Agent address: agent1q...
```

> "Each agent has a unique Fetch.ai address, enabling agent-to-agent communication."

---

### **MINUTE 2-3: CONCERNING ALERT (60 seconds)**

**[Show: Frontend Dashboard]**

> "Now watch what happens when a patient's condition changes."

**[Click on patient card to expand]**

> "I'm opening Patient P-002's detailed view. The CV pipeline is analyzing their vital signs in real-time using computer vision."

**[Show: AI Agent Alert appears]**

> "There! The agent just detected elevated vitals and generated a **CONCERNING** alert."

**[Show: Backend Terminal]**
```
WARNING: [Guardian_P002]: ⚠️ P-002 - Status: CONCERNING
   HR: 95 bpm (baseline 68, +27), RR: 22 (baseline 16, +6), CRS: 0.68
   🤖 Claude Reasoning: Heart rate elevated 40% above baseline...
```

> "Look at the backend - the Patient Guardian detected the change, Claude assessed it as concerning, and the alert was sent to the Nurse Coordinator."

**[Show: Nurse Coordinator logs]**
```
INFO: [nurse_coordinator]: 📨 Received alert from Patient Guardian: P-002
   Severity: CONCERNING
INFO: [nurse_coordinator]: ✅ TRIAGE DECISION #1
   Patient: P-002
   Assigned: Nurse A
   Reasoning: Elevated heart rate and CRS score require immediate assessment
```

> "The Nurse Coordinator agent received the alert and intelligently assigned Nurse A to respond, considering severity and available staff."

---

### **MINUTE 3-4: TIMELINE & INTEGRATION (60 seconds)**

**[Show: Frontend - Patient Timeline Component]**

> "Here's one of my favorite features - the patient timeline."

**[Scroll to timeline under feed/logs]**

> "You can see the patient's status history with color-coded bars - green for normal, yellow for concerning, red for critical."

**[Click on a timeline event]**

> "Clicking any point shows you exactly what happened at that moment - the agent's assessment, Claude's reasoning, and recommended actions."

**[Show: Real-time updates]**

> "This is all happening in real-time through WebSockets. The CV pipeline analyzes video, the agent system assesses the metrics, and the dashboard updates instantly."

---

### **MINUTE 4-5: CHAT PROTOCOL & IMPACT (60 seconds)**

**[Show: Backend Terminal]**

> "The agents also implement Fetch.ai's **chat protocol**, making them compatible with ASI:One."

**[Optional: Show chat interaction in logs or mention it]**

> "You can query any agent directly - for example, 'What's the patient's status?' - and it responds with Claude-powered insights."

**[Show: Code Editor - patient_guardian.py (optional)]**
```python
from uagents_core.contrib.protocols.chat import chat_protocol_spec
self.agent.include(chat_proto, publish_manifest=True)
```

> "Here's the chat protocol implementation - it's fully compatible with Fetch.ai's Agentverse and ASI:One marketplace."

**[Return to Dashboard]**

> "So to summarize what we built:
> - **5 autonomous Fetch.ai agents** monitoring patients continuously
> - **Anthropic Claude AI** providing clinical reasoning
> - **Agent-to-agent communication** for intelligent triage
> - **Chat protocol** for ASI:One compatibility
> - **Full integration** with our CV monitoring pipeline"

**[Show: Impact slide or mention]**

> "The real-world impact: this system can save **$5.28 million per clinical trial** and detect life-threatening complications **2-4 hours earlier** than manual monitoring."

> "All built with Fetch.ai uAgents and Anthropic Claude. Thank you!"

---

## 🎬 ALTERNATIVE: CRITICAL EMERGENCY DEMO

**If you want to show a critical emergency instead of concerning alert:**

### **Replace Minute 2-3 with:**

> "Now let me trigger a critical emergency scenario..."

**[Show: P-003 CRITICAL alert]**

```
ERROR: [Guardian_P003]: 🚨 P-003 - Status: CRITICAL
   HR: 145 bpm (baseline 80, +65), CRS: 0.89, Tremor: True
   🤖 Claude Reasoning: Severe tachycardia with Grade 3 CRS. Medical emergency.
```

> "Patient P-003 is in crisis - heart rate 145, CRS score 0.89. The Patient Guardian immediately flagged this as CRITICAL."

**[Show: Emergency Response activation]**

```
INFO: [emergency_response]: 🚨 EMERGENCY ACTIVATED
Type: CRS Grade 3
Protocol:
  ✓ Page on-call physician (Dr. Smith - 555-0123)
  ✓ Preparing tocilizumab (medication)
  ✓ Vitals monitoring increased to q5min
  ✓ ICU bed on standby
```

> "The Emergency Response agent automatically activated the Grade 3 CRS protocol - paging the doctor, preparing medications, and escalating monitoring. All autonomous, all coordinated through Fetch.ai's agent communication."

---

## 📊 KEY POINTS TO EMPHASIZE

Make sure you mention:

1. ✅ **"Fetch.ai uAgents framework"** (say this explicitly)
2. ✅ **"Anthropic Claude"** (say this explicitly)
3. ✅ **"5 autonomous agents"**
4. ✅ **"Agent-to-agent communication"**
5. ✅ **"Chat protocol / ASI:One compatible"**
6. ✅ **"Real-world impact"** ($5.28M savings)
7. ✅ **"Clinical reasoning"** (not just rules)

---

## 🎥 RECORDING TIPS

### **Setup:**
- Use screen recording software (OBS, QuickTime, Loom)
- Record at 1080p minimum
- Include system audio if possible
- Use good microphone

### **Framing:**
- Show full terminal with agent logs
- Show dashboard clearly
- Highlight key log messages
- Use cursor/pointer to guide viewer

### **Pacing:**
- Speak clearly and not too fast
- Pause after showing important logs
- Let alerts/actions complete before moving on
- Total: 3-5 minutes (judges prefer concise)

### **Editing:**
- Add title card: "Haven AI - Fetch.ai Multi-Agent System"
- Add captions/annotations for key moments
- Speed up boring parts (waiting for alerts)
- Add background music (optional, keep low)

---

## 🎯 POST-RECORDING CHECKLIST

After recording:

- [ ] Video is 3-5 minutes
- [ ] Shows all 5 agents running
- [ ] Mentions Fetch.ai uAgents explicitly
- [ ] Mentions Anthropic Claude explicitly
- [ ] Shows agent-to-agent communication
- [ ] Shows Claude reasoning in logs
- [ ] Shows real-time dashboard updates
- [ ] Explains real-world impact
- [ ] Audio is clear
- [ ] Screen is readable

---

## 📤 SUBMISSION

Upload video to:
- YouTube (unlisted or public)
- Vimeo
- Loom

Include in hackathon submission:
- Video link
- GitHub repo link: `https://github.com/yourusername/haven`
- README with Innovation Lab badges
- Emphasize: "Built with Fetch.ai uAgents + Anthropic Claude"

---

## 🏆 YOU'RE READY!

**Your system meets ALL Fetch.ai prize requirements.**  
**Just need this demo video and you're done!**

Good luck! 🚀

