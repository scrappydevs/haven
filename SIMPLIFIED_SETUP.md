# Simplified Setup - LiveKit Patient Intake

## ✅ **You Only Need 2 API Keys!**

I've simplified the implementation to use **OpenAI's Realtime API**, which handles speech-to-text, AI reasoning, and text-to-speech all in one service.

---

## **What You Need**

### 1. **LiveKit Cloud Account**
- Go to: https://cloud.livekit.io
- Sign up (free tier available)
- Create a project
- Get your credentials:
  - `LIVEKIT_URL` (wss://your-project.livekit.cloud)
  - `LIVEKIT_API_KEY`
  - `LIVEKIT_API_SECRET`

### 2. **OpenAI API Key**
- Go to: https://platform.openai.com/api-keys
- Create API key
- Get: `OPENAI_API_KEY`

That's it! No Deepgram, no Cartesia needed. 🎉

---

## **Setup Steps**

### Step 1: Configure Environment Variables

**Backend:** Create `backend/.env.local`
```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI (for voice AI)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# Keep your existing keys
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx  # For monitoring agent
# ... rest of your existing keys
```

**Frontend:** Create `frontend/.env.local`
```bash
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 2: Run Database Migration

1. Open Supabase SQL Editor
2. Copy/paste `backend/migrations/001_create_intake_reports.sql`
3. Click "Run"
4. Verify: `SELECT * FROM intake_reports;`

### Step 3: Install Missing Dependencies (if needed)

```bash
cd backend
pip install livekit livekit-api "livekit-agents[openai,silero]" livekit-plugins-openai
```

---

## **Running the System**

### Terminal 1: Start Agent Worker
```bash
cd backend
python app/agents/intake_agent.py download-files  # One-time setup
python app/agents/intake_agent.py dev
```

### Terminal 2: Start Backend API
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Start Frontend
```bash
cd frontend
npm run dev
```

---

## **How It Works**

```
Patient speaks
    ↓
OpenAI Realtime API (does everything in one)
    ├─ Speech-to-Text
    ├─ GPT-4o processes request
    └─ Text-to-Speech
    ↓
Patient hears response
```

**Advantages:**
- ✅ Simpler setup (2 services instead of 4)
- ✅ Lower latency (single service)
- ✅ Fewer potential failure points
- ✅ Built-in turn detection and interruption handling

---

## **Cost Estimate**

| Item | Cost per 5-min Intake |
|------|----------------------|
| LiveKit bandwidth | ~$0.01 |
| OpenAI Realtime API | ~$0.15 |
| **Total** | **~$0.16** |

Slightly more expensive than the multi-service approach (~$0.10), but much simpler to manage.

---

## **Test the Setup**

Once all services are running:

```bash
# Test API endpoint
curl -X POST http://localhost:8000/api/intake/start \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "P-001"}'
```

You should get back a LiveKit token and room name.

---

## **Next: Frontend Implementation**

Once you have the credentials set up, I'll build:
1. Patient intake page (`/intake`)
2. Provider dashboard components (IntakeQueue, IntakeReportModal)

**Ready to continue?**
