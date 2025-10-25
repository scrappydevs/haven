# Test Checklist - Haven Application

## ✅ Quick Test Steps

### 1. Backend Test (Terminal 1)
```bash
cd backend
python3 main.py
```

**Expected Output:**
```
🔐 Loading secrets from Infisical...

============================================================
✅ Secrets loaded from Infisical CLI
============================================================

✅ Loaded secrets:
   • SUPABASE_URL
   • SUPABASE_ANON_KEY
   • ANTHROPIC_API_KEY

============================================================

🚀 TrialSentinel Backend Services:
   • Supabase: ✅ Connected
     └─ https://mbmccgnixowxwryycedf.supabase.co
   • Anthropic AI: ✅ Enabled
   
✅ Backend ready!

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Frontend Test (Terminal 2)
```bash
cd frontend
npm run dev
```

**Expected:**
```
▲ Next.js 15.0.0
- Local: http://localhost:3000
```

### 3. Test Patient Search Modal

1. Open: http://localhost:3000/stream
2. Click "Select Patient" button
3. Modal should appear with search
4. Type a name (e.g., "John")
5. Patients should load
6. Click a patient
7. Monitoring condition selector should appear
8. Select conditions
9. Click "Start Streaming"

### 4. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Patient search
curl "http://localhost:8000/patients/search?q=John"

# Active streams
curl http://localhost:8000/streams/active
```

---

## 🐛 Common Issues

### Issue: Modal Not Showing

**Check:**
1. Is backend running on port 8000?
2. Is frontend `.env.local` correct? Should have:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Restart frontend after changing `.env.local`
4. Check browser console for errors (F12)

**Fix:**
```bash
# Update env
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local

# Restart frontend
cd frontend
npm run dev
```

### Issue: Backend Secrets Not Loading

**Check:**
1. Is Infisical CLI installed? `infisical --version`
2. Are you logged in? Try: `infisical secrets`
3. Are secrets set correctly in Infisical?

**Fix:**
```bash
# Check secrets
cd /Users/gsdr/haven
infisical secrets

# Should show:
# SUPABASE_URL, SUPABASE_ANON_KEY, ANTHROPIC_API_KEY
```

### Issue: Infinite Loop on Backend Start

**Check:**
- Are you on latest code? Pull and try again

**Fix:**
```bash
git pull origin main
cd backend
python3 main.py
```

### Issue: Frontend Can't Connect to Backend

**Check:**
1. Backend running on 8000? `curl http://localhost:8000/health`
2. `.env.local` has correct URL
3. CORS allows localhost:3000 (already configured)

**Fix:**
```bash
# Make sure both are running
# Terminal 1:
cd backend && python3 main.py

# Terminal 2:
cd frontend && npm run dev
```

---

## 📋 Deployment Verification

### Render (Backend)
- URL: https://haven-new.onrender.com
- Test: `curl https://haven-new.onrender.com/health`
- Logs: https://dashboard.render.com/

### Vercel (Frontend)
- URL: https://use-haven.vercel.app
- Check: https://use-haven.vercel.app/stream
- Logs: https://vercel.com/dashboard

---

## ✅ All Tests Passing?

- [ ] Backend starts without errors
- [ ] Infisical secrets load (see ✅ in output)
- [ ] Frontend starts on port 3000
- [ ] /stream page loads
- [ ] Click "Select Patient" shows modal
- [ ] Patient search works
- [ ] Can select a patient
- [ ] Monitoring selector appears
- [ ] Backend /health returns 200
- [ ] Backend /patients/search returns data

---

## 🚀 Production Tests

After deployment:

```bash
# Test backend
curl https://haven-new.onrender.com/health

# Test frontend (in browser)
open https://use-haven.vercel.app/stream
```

---

**If all tests pass:** ✅ You're ready to stream!

**If tests fail:** Check the issue section above or check browser/terminal console for errors.

