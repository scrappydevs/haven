# Production URLs

## Live Application

### Frontend (Vercel)
- **URL**: https://use-haven.vercel.app/
- **Dashboard**: https://use-haven.vercel.app/dashboard
- **Stream Page**: https://use-haven.vercel.app/stream

### Backend (Render)
- **Base URL**: https://haven-u8cf.onrender.com
- **Health Check**: https://haven-u8cf.onrender.com/health
- **API Docs**: https://haven-u8cf.onrender.com/docs
- **Patient Search**: https://haven-u8cf.onrender.com/patients/search?q=test

### Database
- **Supabase**: https://mbmccgnixowxwryycedf.supabase.co

---

## Environment Variables

### Render (Backend)
Make sure these are set in Render Dashboard → Service → Environment:

```
SUPABASE_URL=https://mbmccgnixowxwryycedf.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ibWNjZ25peG93eHdyeXljZWRmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMzNjg5MywiZXhwIjoyMDc2OTEyODkzfQ.5IzbpqPhzLaQ-MZs2OeoIB037uibA6PVCSzUxwi1_Rc
ANTHROPIC_API_KEY=sk-ant-... (optional)
```

### Vercel (Frontend)
Make sure this is set in Vercel Dashboard → Project → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://haven-u8cf.onrender.com
```

---

## Quick Tests

### Test Backend Health
```bash
curl https://haven-u8cf.onrender.com/health
```

Expected response:
```json
{"status":"healthy","cv_results_loaded":false,"patients_loaded":true,"trial_protocol_loaded":false}
```

### Test Backend API Docs
Visit: https://haven-u8cf.onrender.com/docs

### Test Frontend
Visit: https://use-haven.vercel.app/

---

## Deployment Commands

### After making changes:

```bash
# 1. Commit changes
git add .
git commit -m "Your commit message"
git push origin main

# 2. Render will auto-deploy backend
# 3. Vercel will auto-deploy frontend
```

### Check deployment status:
- **Render**: https://dashboard.render.com/ → haven-u8cf
- **Vercel**: https://vercel.com/dashboard → use-haven

---

## CORS Configuration

Backend CORS is configured to allow:
- ✅ `https://use-haven.vercel.app` (production)
- ✅ `http://localhost:3000` (local dev)
- ✅ `http://localhost:3001` (local dev alt)

---

## WebSocket Endpoints

### For streaming (from browser):
```javascript
// Production
ws://haven-u8cf.onrender.com/ws/stream/{patient_id}
wss://haven-u8cf.onrender.com/ws/stream/{patient_id}

// Local dev
ws://localhost:8000/ws/stream/{patient_id}
```

### For viewing dashboard:
```javascript
// Production
wss://haven-u8cf.onrender.com/ws/view

// Local dev
ws://localhost:8000/ws/view
```

---

## Monitoring

### Check Backend Logs
1. Go to https://dashboard.render.com/
2. Select "haven-u8cf" service
3. Click "Logs" tab

### Check Frontend Logs
1. Go to https://vercel.com/dashboard
2. Select "use-haven" project
3. Click "Deployments"
4. Select latest deployment
5. Click "View Function Logs"

---

## Status

- ✅ Backend deployed: https://haven-u8cf.onrender.com
- ✅ Frontend deployed: https://use-haven.vercel.app/
- ✅ Database connected: Supabase
- ✅ CORS configured
- ⚠️ Need to commit and push latest changes

---

## Next Steps

1. **Commit the CORS update**:
   ```bash
   cd /Users/gsdr/haven
   git add backend/app/main.py vercel.json
   git commit -m "Configure production URLs and CORS"
   git push origin main
   ```

2. **Verify in Vercel Dashboard**:
   - Go to Settings → Environment Variables
   - Confirm `NEXT_PUBLIC_API_URL=https://haven-u8cf.onrender.com`
   - If not set, add it and redeploy

3. **Wait for auto-deployment** (both services will redeploy)

4. **Test the application**:
   - Visit https://use-haven.vercel.app/
   - Check browser console for CORS errors
   - Test patient search
   - Try viewing dashboard

5. **Test WebSocket streaming**:
   - Go to https://use-haven.vercel.app/stream
   - Select a patient
   - Start streaming
   - Open https://use-haven.vercel.app/dashboard on another device
   - Verify live feed appears

---

## Troubleshooting

### If CORS errors appear:
1. Check backend logs for request origins
2. Verify CORS configuration in `backend/app/main.py`
3. Redeploy backend after changes

### If "Cannot connect to backend":
1. Check Render service is running (not sleeping)
2. Visit health endpoint directly
3. Check frontend environment variable is set
4. Check browser network tab for actual URL being called

### If WebSocket fails:
1. Check browser uses `wss://` not `ws://` for production
2. Verify Render service supports WebSockets (it does)
3. Check firewall/proxy settings

