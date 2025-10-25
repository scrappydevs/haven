# 🚀 Quick Start Guide

## Run Locally (One Command!)

```bash
./start.sh
```

This automatically:
- Pulls secrets from Infisical
- Starts backend on http://localhost:8000
- Starts frontend on http://localhost:3000

---

## Manual Setup

### Backend Only
```bash
cd backend
./dev.sh
```

### Frontend Only
```bash
cd frontend
npm run dev
```

---

## What Got Fixed

### ✅ Numpy Conflict Resolved
- Changed `numpy==2.2.2` to `numpy>=1.26.0,<2.0`
- Mediapipe requires numpy <2.0
- Now compatible!

### ✅ Infisical Working
- Secrets in Infisical (not .env files)
- Backend pulls via CLI: `infisical run --env=dev`
- Make sure you have these secrets in Infisical:
  - `SUPABASE_URL` (the actual URL, not JWT)
  - `SUPABASE_ANON_KEY` (the JWT token)
  - `ANTHROPIC_API_KEY` (optional)

### ✅ Vercel Fixed
- Simplified config
- Auto-detects Next.js
- Root directory: `frontend` (set in Vercel dashboard)

---

## Verify Secrets in Infisical

```bash
cd /Users/gsdr/haven
infisical secrets
```

Should show:
```
SUPABASE_URL          https://mbmccgnixowxwryycedf.supabase.co
SUPABASE_ANON_KEY     eyJhbGci... (JWT token)
ANTHROPIC_API_KEY     sk-ant-...
```

---

## Deployment Status

### Backend (Render)
- ✅ Numpy conflict fixed
- ✅ Reading from environment vars
- URL: https://haven-new.onrender.com

### Frontend (Vercel)  
- ✅ Config simplified
- ✅ Set Root Directory: `frontend` in Vercel dashboard
- ✅ Set env var: `NEXT_PUBLIC_API_URL=https://haven-new.onrender.com`
- URL: https://use-haven.vercel.app

---

## Test It

```bash
# Run locally
./start.sh

# Test backend
curl http://localhost:8000/health

# Test frontend
open http://localhost:3000
```

---

Done! 🎉

