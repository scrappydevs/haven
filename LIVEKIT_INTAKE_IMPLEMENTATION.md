# LiveKit Patient Intake System - Implementation Guide

## ✅ What's Been Implemented

### Backend Components

#### 1. **Database Schema** (`backend/migrations/001_create_intake_reports.sql`)
- Complete SQL migration for `intake_reports` table
- Tracks interview transcripts, vitals, urgency, and workflow status
- Includes indexes for performance and RLS policies
- **Action Required:** Run this SQL in your Supabase dashboard

#### 2. **Intake Agent** (`backend/app/agents/intake_agent.py`)
- Full LiveKit Agents implementation
- Conducts voice-based patient interviews
- Collects: chief complaint, symptoms, duration, severity, medications, allergies
- Automatic urgency detection for critical symptoms
- Saves structured reports to database
- **Features:**
  - Natural conversation flow with turn detection
  - Medical-optimized speech recognition (Deepgram nova-2-medical)
  - Claude Haiku for fast, empathetic responses
  - Natural voice synthesis (Cartesia)
  - Background noise cancellation

#### 3. **API Endpoints** (added to `backend/app/main.py`)
- `POST /api/intake/start` - Initialize intake session, get LiveKit token
- `GET /api/intake/pending` - List pending intakes (sorted by urgency)
- `GET /api/intake/{id}` - Get full intake report
- `POST /api/intake/{id}/review` - Mark as reviewed
- `POST /api/intake/{id}/assign-room` - Assign patient to room
- `GET /api/intake/stats` - Get intake statistics

#### 4. **Dependencies**
- ✅ Backend: LiveKit Agents, Anthropic, Deepgram, Cartesia plugins installed
- ✅ Frontend: LiveKit React SDK and client installed

---

## 🔧 Setup Required (Before Testing)

### Step 1: Get API Credentials

You need to obtain credentials from these services:

1. **LiveKit Cloud** (https://cloud.livekit.io)
   - Sign up for free account
   - Create a project
   - Copy: API Key, API Secret, WebSocket URL

2. **Deepgram** (https://deepgram.com)
   - Sign up for account
   - Get API key from dashboard

3. **Cartesia** (https://cartesia.ai)
   - Sign up for account
   - Get API key

4. **Anthropic** (you likely already have this)
   - Your existing Claude API key will work

### Step 2: Configure Environment Variables

Create `backend/.env.local` with:

```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
DEEPGRAM_API_KEY=xxxxxxxxxxxxxxxxxxxxx
CARTESIA_API_KEY=xxxxxxxxxxxxxxxxxxxxx

# Keep your existing Supabase, Vonage, etc. keys
```

Create `frontend/.env.local` with:

```bash
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Run Database Migration

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy/paste contents of `backend/migrations/001_create_intake_reports.sql`
4. Click "Run"
5. Verify table was created: `select * from intake_reports;`

---

## 🚀 Running the Intake System

### Start the Agent Worker

The intake agent runs as a separate process that LiveKit dispatches to rooms:

```bash
cd backend

# Download required model files (one-time setup)
python app/agents/intake_agent.py download-files

# Start agent worker in development mode
python app/agents/intake_agent.py dev
```

You should see:
```
🚀 Starting Haven Intake Agent Worker...
✅ Worker registered with LiveKit
⏳ Waiting for intake sessions...
```

### Start Backend API (in separate terminal)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend (in separate terminal)

```bash
cd frontend
npm run dev
```

---

## 📝 Next Steps: Frontend Implementation

I'll now create the frontend components:

### 1. Patient Intake Page (`frontend/app/intake/page.tsx`)
- Patient enters their ID
- Joins LiveKit room
- Sees/hears AI agent
- Real-time transcription display

### 2. Provider Dashboard Integration
- **IntakeQueue Component** - Shows pending intakes
- **IntakeReportModal** - Detailed review interface
- Add to existing dashboard as new tab

Would you like me to continue implementing the frontend components now?

---

## 🔍 Testing the System

### Manual Test Flow

1. **Start all services:**
   - Agent worker: `python app/agents/intake_agent.py dev`
   - Backend: `uvicorn app.main:app --reload`
   - Frontend: `npm run dev`

2. **Create intake session:**
   ```bash
   curl -X POST http://localhost:8000/api/intake/start \
     -H "Content-Type: application/json" \
     -d '{"patient_id": "P-001"}'
   ```

   Response will include `token` and `room_name`

3. **Join room with LiveKit (once frontend is built):**
   - Patient navigates to `/intake`
   - Enters patient ID
   - Clicks "Start Check-In"
   - Agent automatically joins and starts interview

4. **Monitor in dashboard:**
   - New intakes appear in "Intake Queue" tab
   - Review transcript, vitals, AI summary
   - Assign to room

### Expected Behavior

- **Patient hears:** "Hello! I'm Haven AI..."
- **Agent asks:** Chief complaint, duration, severity, medications, allergies
- **On completion:** Report saved to database, dashboard notified
- **Urgency detection:** High-priority symptoms flagged immediately

---

## 🏗️ Architecture Summary

### Hybrid Approach (As Recommended)

```
┌─────────────────────────────────────────┐
│ INTAKE FLOW (LiveKit)                   │
│ - Voice AI interview                    │
│ - Natural conversation                  │
│ - Automatic transcription               │
│ - Vitals collection (optional)          │
└─────────────────────────────────────────┘
              ↓
     Saves intake report
              ↓
┌─────────────────────────────────────────┐
│ MONITORING DASHBOARD (Existing WebSocket)│
│ - Multi-patient grid view               │
│ - CV metrics processing                 │
│ - Guardian agent monitoring             │
│ - Keeps your proven system intact       │
└─────────────────────────────────────────┘
```

### Benefits of This Approach

✅ **Separation of Concerns:** Intake uses LiveKit, monitoring uses existing WebSocket
✅ **No Breaking Changes:** Your current monitoring system untouched
✅ **Best of Both Worlds:** LiveKit for audio+video intake, optimized WebSocket for surveillance
✅ **Gradual Migration:** Can migrate monitoring to LiveKit later if desired

---

## 📊 Database Schema

```sql
intake_reports
├── id (UUID)
├── patient_id (FK)
├── session_id (unique)
├── livekit_room_name
├── transcript (JSONB) - Full Q&A conversation
├── chief_complaint
├── symptoms (TEXT[])
├── duration
├── severity (1-10)
├── medications
├── allergies
├── prior_episodes
├── vitals (JSONB) - HR, RR, etc.
├── urgency_level (low/medium/high)
├── ai_summary
├── extracted_info (JSONB)
├── status (pending_review/reviewed/assigned)
├── reviewed_by
├── reviewed_at
├── assigned_room
├── created_at
└── interview_duration_seconds
```

---

## 🐛 Troubleshooting

### Agent not starting
- Check `.env.local` has all required API keys
- Verify LiveKit credentials: `lk token create --identity test --room test-room`
- Check logs for authentication errors

### Patient can't connect
- Ensure `NEXT_PUBLIC_LIVEKIT_URL` set in frontend `.env.local`
- Check browser console for WebSocket errors
- Verify room name format: `intake-{patient_id}-{session_id}`

### No transcription
- Verify Deepgram API key is valid
- Check audio permissions in browser
- Look for "STT" errors in agent logs

### No voice output
- Verify Cartesia API key
- Check speaker/headphone connection
- Look for "TTS" errors in agent logs

---

## 💰 Cost Estimates (Typical Intake)

| Service | Usage | Cost per Intake |
|---------|-------|-----------------|
| LiveKit | 5-min session, 1 participant | ~$0.01 |
| Deepgram | 5-min transcription | ~$0.04 |
| Cartesia | 200 words TTS | ~$0.04 |
| Claude Haiku | 10 API calls | ~$0.01 |
| **Total** | | **~$0.10 per intake** |

---

## 📞 Support

If you encounter issues:

1. Check agent worker logs
2. Check backend API logs (uvicorn)
3. Check browser console (for frontend issues)
4. Verify all API keys are correct in `.env.local`
5. Test LiveKit connection: https://cloud.livekit.io/projects

---

## 🎯 Status

**✅ Completed:**
- Backend agent implementation
- Database schema
- API endpoints
- Dependencies installed

**🚧 In Progress:**
- Frontend intake page (ready to build)
- Dashboard integration (ready to build)

**📋 Next:**
- Build patient intake UI
- Build provider review UI
- Test end-to-end flow

**Ready to continue with frontend implementation!**
