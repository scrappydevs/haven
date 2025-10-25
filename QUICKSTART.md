# TrialSentinel AI - Quick Start Guide

**Get the project running in 10 minutes!**

---

## Prerequisites

- **Node.js** 18+ (check: `node --version`)
- **Python** 3.12+ (check: `python3 --version`)
- **Git** (check: `git --version`)

---

## Step 1: Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate mock patient data
python scripts/generate_patients.py

# Start the backend server
uvicorn app.main:app --reload
```

✅ Backend running at: http://localhost:8000
✅ API docs at: http://localhost:8000/docs

---

## Step 2: Frontend Setup (5 minutes)

Open a **new terminal**:

```bash
# Navigate to frontend
cd frontend

# Initialize Next.js (follow prompts)
npx create-next-app@latest . --typescript --tailwind --app

# Install additional dependencies
npm install framer-motion recharts lucide-react

# Install shadcn/ui
npx shadcn-ui@latest init

# Start the frontend server
npm run dev
```

✅ Frontend running at: http://localhost:3000

---

## Step 3: Verify Everything Works

### Backend Check:
Open http://localhost:8000/health

Should see:
```json
{
  "status": "healthy",
  "cv_results_loaded": false,  // Will be true after Step 4
  "patients_loaded": true,
  "trial_protocol_loaded": false  // Will be true after Step 4
}
```

### Frontend Check:
Open http://localhost:3000

Should see the Next.js default page.

---

## Step 4: Generate Data (Pre-Hackathon)

Run these scripts to prepare demo data:

### 1. Generate Patient Data
```bash
cd backend
python scripts/generate_patients.py
```

Output: `backend/data/patients.json` (47 patients)

### 2. Pull Real Trial Data
```bash
python scripts/pull_trial_data.py
```

Output: `backend/data/nct04649359.json` (Regeneron trial protocol)

### 3. Pre-compute CV Results (IMPORTANT!)
```bash
# After filming videos, run:
python scripts/precompute_cv.py
```

Output: `backend/data/precomputed_cv.json` (CV analysis for all videos)

⚠️ **Note**: You need to film 6 videos first (see README.md "Video Requirements")

---

## Step 5: Test API Endpoints

Open http://localhost:8000/docs (FastAPI auto-generated docs)

Try these endpoints:
- `GET /patients` - Should return 47 patients
- `GET /patient/1` - Should return Patient #1 details
- `GET /trial-protocol` - Should return NCT04649359 info
- `GET /roi-calculation` - Should return cost savings

---

## Step 6: Build the Dashboard

Now you're ready to start building!

### Priority 1: Multi-Video Dashboard
Create: `frontend/app/dashboard/page.tsx`

### Priority 2: Video Player Component
Create: `frontend/components/VideoPlayer.tsx`

### Priority 3: Alert Panel
Create: `frontend/components/AlertPanel.tsx`

See `/docs/FRONTEND_GUIDE.md` for detailed implementation.

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -ti:8000
kill -9 $(lsof -ti:8000)

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
# Check if port 3000 is in use
lsof -ti:3000
kill -9 $(lsof -ti:3000)

# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

### "Module not found" errors
```bash
# Backend:
pip install -r requirements.txt

# Frontend:
npm install
```

### Can't activate venv (Windows)
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
venv\Scripts\activate
```

---

## Development Workflow

### Starting Work
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Adding New Dependencies

**Backend**:
```bash
pip install <package-name>
pip freeze > requirements.txt  # Update requirements
```

**Frontend**:
```bash
npm install <package-name>
```

---

## Project Status Checklist

Track your progress:

### Pre-Hackathon:
- [ ] Backend running locally
- [ ] Frontend running locally
- [ ] 47 patients generated
- [ ] 6 videos filmed
- [ ] CV results pre-computed

### Hour 0-8:
- [ ] Dashboard page created
- [ ] Video player component working
- [ ] Alerts firing at correct timestamps
- [ ] Backend serving pre-computed data

### Hour 8-16:
- [ ] Alert panel with animations
- [ ] Patient detail modal
- [ ] ROI calculator widget
- [ ] Styling polished

### Hour 16-24:
- [ ] Demo video recorded
- [ ] Mobile mockup created
- [ ] Technical docs written

### Hour 24-30:
- [ ] Deployed to Vercel (frontend)
- [ ] Deployed to Railway (backend)
- [ ] Production tested

### Hour 30-36:
- [ ] Demo rehearsed 10+ times
- [ ] All backup plans tested
- [ ] Ready to WIN!

---

## Need Help?

- **API not working?** Check http://localhost:8000/docs
- **Frontend error?** Check browser console (F12)
- **Data missing?** Run the scripts in Step 4
- **General questions?** See `/docs/FAQ.md`

---

## Next Steps

1. ✅ Complete Steps 1-5 above
2. 📹 Film 6 patient videos (see `README.md`)
3. 💻 Start building the dashboard
4. 🚀 Follow the 36-hour build plan

**You're all set! Let's build and WIN! 🏆**
