# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**TrialSentinel AI** is a real-time computer vision monitoring system for clinical trial safety, specifically designed for detecting Cytokine Release Syndrome (CRS) in patients receiving BCMA bispecific antibody treatments. Built for CalHacks 12.0.

The system monitors multiple patients simultaneously via video feeds, detecting CRS 2-4 hours earlier than manual observation through facial flushing detection, heart rate estimation (rPPG), and real-time risk scoring.

## Common Commands

### Frontend (Next.js 15 + React 19)

```bash
cd frontend

# Development
npm run dev              # Start dev server on http://localhost:3000

# Build & Production
npm run build           # Build for production
npm start               # Start production server

# Linting
npm run lint            # Run ESLint
```

### Backend (FastAPI + Python 3.12)

```bash
cd backend

# Development (with Infisical secrets)
python3 main.py         # Auto-loads secrets from Infisical and starts on port 8000
# OR
./dev.sh               # Explicit Infisical wrapper script

# Manual start (without auto-wrapper)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (used by Render)
./start.sh             # Uses gunicorn with Infisical CLI

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/patients/search?q=John
```

### Environment Setup

```bash
# Backend - uses Infisical CLI for secret management
cd backend
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# Check Infisical is configured
infisical --version
infisical secrets       # View secrets in Infisical

# Frontend
cd frontend
npm install

# Set environment variable for API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### Running Full Stack

```bash
# Terminal 1 - Backend
cd backend
python3 main.py

# Terminal 2 - Frontend
cd frontend
npm run dev

# Access at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## High-Level Architecture

### Technology Stack

**Frontend:**
- Next.js 15 (App Router) + React 19
- TypeScript
- Tailwind CSS v3 (v4 mentioned in docs but v3 in package.json)
- Framer Motion (animations)
- Recharts (graphs)
- Lucide React (icons)

**Backend:**
- FastAPI (Python 3.12)
- OpenCV + MediaPipe (computer vision)
- Anthropic Claude API (AI recommendations)
- Supabase (PostgreSQL database)
- Infisical CLI (secret management)
- Uvicorn (dev) / Gunicorn (prod)

**Deployment:**
- Frontend: Vercel (https://use-haven.vercel.app)
- Backend: Render (https://haven-new.onrender.com)

### System Design Patterns

**1. Pre-Computed CV Results for Demo:**
The system uses pre-computed computer vision results stored in `backend/data/precomputed_cv.json` for demo purposes. Videos are processed ahead of time using `backend/scripts/precompute_cv.py`, which runs MediaPipe face detection and CV algorithms on patient videos, then saves timestamped results to JSON.

**2. Dual Video Mode:**
- **Pre-recorded videos** (patients 1-5): Serve static MP4 files with pre-computed CV overlays fetched from JSON
- **Live webcam stream** (patient 6): Real-time WebSocket streaming with on-the-fly CV processing

**3. Secret Management with Infisical CLI:**
Instead of storing credentials, the backend uses Infisical CLI to inject secrets at runtime:
- `backend/main.py` checks if Infisical CLI is available and auto-wraps itself with `infisical run`
- Secrets (SUPABASE_URL, SUPABASE_ANON_KEY, ANTHROPIC_API_KEY) are injected as env vars
- No credentials stored in code or `.env` files
- The repo root contains `.infisical.json` with project configuration

**4. WebSocket Architecture:**
- **`/ws/stream`**: Accepts frames from streaming clients (Computer 1 with webcam)
- **`/ws/view`**: Broadcasts processed frames to dashboard viewers (Computer 2+)
- ConnectionManager in `backend/app/websocket.py` manages streamer/viewer connections
- Backend processes frames with MediaPipe in real-time and broadcasts CV results

### Directory Structure

```
haven/
├── frontend/                  # Next.js application
│   ├── app/
│   │   ├── dashboard/        # Multi-patient monitoring view
│   │   ├── stream/           # Webcam streaming interface
│   │   ├── page.tsx          # Home page
│   │   └── layout.tsx        # Root layout
│   ├── components/           # React components
│   └── lib/                  # Utilities
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main.py          # Core API endpoints
│   │   ├── websocket.py     # WebSocket connection manager
│   │   ├── cv_metrics.py    # Computer vision algorithms
│   │   ├── monitoring_protocols.py  # Clinical monitoring rules
│   │   ├── supabase_client.py      # Database connection
│   │   └── infisical_config.py     # Secret management
│   ├── data/
│   │   ├── patients.json         # Patient profiles (legacy)
│   │   ├── precomputed_cv.json   # Pre-computed CV results
│   │   └── nct04649359.json      # Regeneron trial protocol
│   ├── scripts/              # Data generation and CV pre-computation
│   ├── main.py              # Entry point with Infisical wrapper
│   ├── dev.sh               # Dev start script
│   └── start.sh             # Production start script (Gunicorn)
│
├── docs/                     # Architecture and technical docs
├── .infisical.json          # Infisical project config (safe to commit)
├── render.yaml              # Render deployment config
└── vercel.json              # Vercel deployment config
```

### Key API Endpoints

**REST API:**
- `GET /health` - Health check
- `GET /patients/search?q={query}` - Search patients in Supabase by name
- `GET /patients/by-id/{patient_id}` - Get single patient (e.g., "P-001")
- `GET /cv-data/{patient_id}/{timestamp}` - Get pre-computed CV results for video timestamp
- `GET /streams/active` - List active video streams
- `GET /protocols` - Get all monitoring protocols
- `POST /protocols/recommend` - Get AI/keyword-based protocol recommendations

**WebSocket:**
- `WS /ws/stream` - Send video frames for processing (streamer endpoint)
- `WS /ws/view` - Receive processed frames with CV overlays (viewer endpoint)

### Computer Vision Pipeline

1. **Face Detection**: MediaPipe Face Mesh (468 landmarks)
2. **Facial Flushing**: Extract cheek ROIs (landmarks 205, 425), calculate redness: `(R - (G+B)/2) / 255`
3. **Heart Rate (rPPG)**: Extract forehead ROI, analyze green channel via FFT over 5-second window (150 frames @ 30 FPS)
4. **CRS Risk Score**: Weighted algorithm:
   - Facial flushing: 40%
   - Heart rate delta: 30%
   - Baseline CRS risk: 20%
   - Respiratory rate delta: 10%
5. **Alert Generation**: Trigger when CRS score > 0.70

### Database Schema (Supabase)

**`patients` table:**
- `patient_id` (text, primary key): e.g., "P-001"
- `name` (text): Patient full name
- `age` (int)
- `gender` (text)
- `enrollment_status` (text): "active", "completed", "withdrawn"
- Demographics, medical history, baseline vitals, etc.

### Important Files

**Configuration:**
- `backend/main.py` - Entry point with Infisical auto-wrapper logic
- `backend/app/infisical_config.py` - Secret manager abstraction
- `backend/.infisical.json` - Infisical project config (DO commit)
- `frontend/.env.local` - Frontend env vars (DO NOT commit)

**Core Application:**
- `backend/app/main.py` - FastAPI app with all REST endpoints
- `backend/app/websocket.py` - WebSocket manager and CV frame processing
- `backend/app/cv_metrics.py` - CV algorithms (flushing, rPPG, CRS scoring)
- `frontend/app/stream/page.tsx` - Webcam streaming interface

**Documentation:**
- `README.md` - Project overview and quick start
- `SYSTEM_DESIGN.md` - Comprehensive 100KB technical design doc
- `QUICKSTART.md` - Step-by-step setup guide
- `DEPLOYMENT.md` - Deployment instructions
- `TEST_CHECKLIST.md` - Testing procedures

## Development Patterns

### Infisical Secret Management

The backend uses a unique pattern where `backend/main.py` acts as a wrapper:
1. Checks if Infisical CLI is installed
2. Checks if already running with Infisical (via env var `INFISICAL_PROJECT_ID`)
3. If not, restarts itself with `infisical run --env=dev -- python3 main.py`
4. Imports the actual app from `backend/app/main.py`

This means:
- Developers just run `python3 main.py` and secrets auto-load
- Production uses `./start.sh` which wraps Gunicorn with Infisical
- No credentials in code or committed `.env` files

### WebSocket Message Protocol

**Streamer → Backend:**
```json
{
  "type": "frame",
  "timestamp": 1634567890.123,
  "frame": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Backend → Viewers:**
```json
{
  "type": "live_frame",
  "patient_id": "live-1",
  "timestamp": 1634567890.123,
  "data": {
    "frame": "data:image/jpeg;base64,/9j/4AAQ...",
    "crs_score": 0.45,
    "heart_rate": 82,
    "respiratory_rate": 16,
    "facial_flushing": 0.38,
    "alert": false
  }
}
```

### Adding New Endpoints

When adding new API endpoints to the backend:
1. Add endpoint to `backend/app/main.py`
2. If using secrets, get them via `get_secret()` from `app.infisical_config`
3. If using Supabase, import `supabase` from `app.supabase_client`
4. Frontend should call backend via `NEXT_PUBLIC_API_URL` env var

### Deployment

**Backend (Render):**
- Configured via `render.yaml`
- Start command: `bash start.sh` (uses Gunicorn with Infisical)
- Environment variables set in Render Dashboard
- Health check: `/health`

**Frontend (Vercel):**
- Auto-deploys from `main` branch
- API requests proxied via `vercel.json` rewrites to backend
- Set `NEXT_PUBLIC_API_URL` in Vercel environment variables

## Debugging Tips

**Backend won't start:**
- Check Infisical CLI is installed: `infisical --version`
- Check you're in repo root where `.infisical.json` exists
- Check secrets are set: `cd /path/to/haven && infisical secrets`
- Look for "✅ Secrets loaded from Infisical CLI" in startup output

**Frontend can't connect to backend:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check `.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Restart frontend after changing `.env.local`
- Check browser console for CORS errors

**WebSocket not connecting:**
- Verify backend WebSocket endpoints are running
- Check CORS allows frontend origin in `backend/app/main.py`
- Test with: `wscat -c ws://localhost:8000/ws/view`

**CV results not showing:**
- Check `backend/data/precomputed_cv.json` exists
- If missing, run: `cd backend && python scripts/precompute_cv.py`
- Verify videos exist in `videos/` directory

## Clinical Trial Context

This project is built around monitoring patients receiving **Regeneron's BCMA x CD3 bispecific antibodies** (Linvoseltamab, Odronextamab) for multiple myeloma. Key clinical facts:
- 65% of patients develop Cytokine Release Syndrome (CRS)
- CRS grading: Grade 1-4 severity (FDA criteria)
- Current monitoring cost: $18,800/day per patient
- Target: Detect CRS 2-4 hours earlier than manual observation

**Trial NCT04649359** is the real-world reference trial used for protocols and data validation.
