# Haven AI Multi-Agent System - Quick Start Guide

## 🚀 Installation (5 minutes)

### Step 1: Navigate to haven-agents directory
```bash
cd /Users/gsdr/haven/haven-agents
```

### Step 2: Set up environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure API key
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your ANTHROPIC_API_KEY
# Get your key from: https://console.anthropic.com/
nano .env  # or use your favorite editor
```

Your `.env` should look like:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
```

---

## 🎮 Running the Demo

### Option 1: Automated Full Demo (Recommended)
Run all 5 agents with automated scenario progression:

```bash
./run_demo.sh
```

This will:
1. ✅ Check dependencies
2. ✅ Verify API key
3. ✅ Start all 5 agents
4. ✅ Progress through 4-minute demo automatically
5. ✅ Show complete system in action

**Demo Timeline:**
- **Min 0-1:** Normal operations (all stable)
- **Min 1-2:** Concerning alert (P-002 elevated vitals)
- **Min 2-3:** Critical emergency (P-003 CRS Grade 3)
- **Min 3-4:** Pattern detection (tremor safety signal)
- **Min 4+:** Continue running for manual testing

---

### Option 2: Run Individual Agents (Testing)

**Phase 1: Single Patient Guardian**
```bash
python agents/patient_guardian.py
```
Monitors one patient (P-001) with 30-second intervals.

**Phase 2: Nurse Coordinator**
```bash
python agents/nurse_coordinator.py
```
Triages alerts from multiple Patient Guardians.

**Phase 3: Emergency Response**
```bash
python agents/emergency_response.py
```
Activates emergency protocols for critical alerts.

**Phase 4: Protocol Compliance**
```bash
python agents/protocol_compliance.py
```
Tracks vital check schedules and flags deviations.

**Phase 5: Research Insights**
```bash
python agents/research_insights.py
```
Detects safety signals across patient cohorts.

---

## 📊 What to Watch For

### Normal Operations (Min 0-1)
```
[14:30:15] ✅ P-001 - Status: NORMAL
   HR: 74 bpm (baseline 72), RR: 15 (baseline 14), CRS: 0.32
   All vitals within acceptable range...
```

### Concerning Alert (Min 1-2)
```
[14:31:45] ⚠️  P-002 - Status: CONCERNING
   HR: 88 bpm (baseline 68, Δ+20), RR: 18 (baseline 13, Δ+5), CRS: 0.68
   Tremor: True, Attention: 0.85
   🤖 Claude Reasoning: Heart rate elevated 29% above baseline and CRS score
   entering concerning range (0.68). Possible early Grade 2 CRS...
```

### Critical Emergency (Min 2-3)
```
🚨 CRITICAL EMERGENCY - INCIDENT INC-001
================================================================================
Patient: P-003
Time: 14:33:15
Vitals: HR 145bpm, RR 32, CRS 0.89
🤖 Claude Emergency Classification:
   Type: CRS_Grade_3
   
🚨 EMERGENCY PROTOCOL ACTIVATED
📋 EMERGENCY PROTOCOL CHECKLIST:
   1. Page on-call physician immediately (Dr. Smith - 555-0123)
   2. Prepare tocilizumab 8mg/kg IV (IL-6 receptor antagonist)
   3. Increase vital signs monitoring to q5min
   ...
```

### Safety Signal Detection (Min 3-4)
```
🚨 HIGH SEVERITY SAFETY SIGNAL DETECTED
================================================================================
Type: temporal_cluster
Cohort: Drug_A
Observation: 2/3 patients showing tremors in 60-minute window

🤖 Claude Analysis:
   Significantly elevated tremor rate (67%) in Cohort A suggests potential
   drug-related adverse event. This 13x increase warrants immediate investigation.
   
📋 Recommendation:
   1. Increase tremor monitoring frequency for all Cohort A patients
   2. Review dosing protocols
   3. Notify principal investigator and safety board
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'uagents'"
**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Claude API error"
**Solution:**
1. Check your `.env` file has correct `ANTHROPIC_API_KEY`
2. Verify API key is valid at https://console.anthropic.com/
3. Agents will fall back to rule-based logic if Claude unavailable

### Issue: "Address already in use"
**Solution:**
```bash
# Kill any existing agent processes
pkill -f "python.*agent"

# Then restart
./run_demo.sh
```

### Issue: Agents not communicating
**Solution:**
- uAgents requires unique ports per agent (already configured)
- Check firewall isn't blocking localhost ports 8001-8040
- Agents may take 10-20 seconds to discover each other

---

## 📝 Manual Scenario Testing

While the demo is running, you can manually trigger scenarios:

**In a separate terminal:**
```bash
cd /Users/gsdr/haven/haven-agents
source venv/bin/activate
python
```

**Then in Python console:**
```python
from utils.mock_data import mock_generator

# Trigger specific scenarios
mock_generator.set_scenario("normal")           # Reset to normal
mock_generator.set_scenario("p002_concerning")  # P-002 concerning symptoms
mock_generator.set_scenario("p003_critical")    # P-003 critical CRS
mock_generator.set_scenario("pattern_tremor")   # Multiple tremors

# Advance time manually (optional)
mock_generator.advance_time(30)  # Advance 30 seconds
```

---

## 🎯 Success Criteria Checklist

### Phase 1: Patient Guardian ✅
- [x] Runs continuously (30s intervals)
- [x] Makes correct severity assessments
- [x] Shows Claude's reasoning
- [ ] Chat protocol (future enhancement)

### Phase 2: Nurse Coordinator ✅
- [x] Receives alerts from Patient Guardians
- [x] Intelligent prioritization with Claude
- [x] Agent-to-agent communication

### Phase 3: Emergency Response ✅
- [x] Automatic escalation for critical alerts
- [x] Claude classifies emergency types
- [x] Protocol checklists displayed
- [x] Incident logging

### Phase 4: Protocol Compliance ✅
- [x] Tracks check timing
- [x] Flags deviations with severity
- [x] Context-aware justifications
- [x] Compliance reports

### Phase 5: Research Insights ✅
- [x] Aggregates data from all patients
- [x] Detects statistical patterns
- [x] Claude assesses clinical significance
- [x] Actionable recommendations

### Phase 6: Integration ✅
- [x] All 5 agents running together
- [x] Agent-to-agent communication
- [x] Complete demo flow (4+ minutes)
- [x] Automated scenario progression

---

## 🏆 Next Steps

1. **Watch the full demo** (4 minutes)
2. **Review agent logs** - see Claude reasoning in action
3. **Test manual scenarios** - trigger different conditions
4. **Explore code** - agents/*.py files have detailed comments
5. **Customize** - add your own agents or protocols

---

## 📚 Additional Resources

- **README.md** - Full project documentation
- **models/*.py** - Data model definitions
- **utils/claude_client.py** - AI reasoning implementation
- **utils/mock_data.py** - Demo data generation

---

## 💬 Chat Query Support (Future Enhancement)

To add chat queries to agents:
```python
from uagents_core.contrib.protocols.chat import chat_protocol_spec

# Add to patient guardian
chat_protocol = Protocol("PatientChat", "1.0")

@chat_protocol.on_message(model=ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    if "status" in msg.content.lower():
        # Return current patient status
        ...
```

**Planned queries:**
- "What's P-001's status?"
- "Show protocol deviations today"
- "Any safety signals?"
- "What's the emergency?"

---

**Built with ❤️ for patient safety**  
**Powered by Fetch.ai uAgents + Anthropic Claude**

