# 🚀 Deploy Now - Final Steps

Your production URLs are configured:
- **Frontend**: https://use-haven.vercel.app/
- **Backend**: https://haven-u8cf.onrender.com

---

## Step 1: Commit and Push Changes (5 minutes)

```bash
cd /Users/gsdr/haven

# Check what's changed
git status

# Add all changes
git add .

# Commit with message
git commit -m "Configure production URLs, fix secrets, and update styling"

# Push to GitHub
git push origin main
```

✅ This will trigger automatic deployments on both Render and Vercel.

---

## Step 2: Verify Environment Variables

### A. Check Vercel (Frontend)

1. Go to: https://vercel.com/dashboard
2. Find your `use-haven` project
3. Go to **Settings** → **Environment Variables**
4. Verify this exists:
   ```
   NEXT_PUBLIC_API_URL = https://haven-u8cf.onrender.com
   ```
5. If missing, add it:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://haven-u8cf.onrender.com`
   - Environments: Production ✓, Preview ✓, Development ✓
   - Click "Save"
   - Click "Redeploy" on latest deployment

### B. Check Render (Backend)

1. Go to: https://dashboard.render.com/
2. Find your `haven-u8cf` service
3. Go to **Environment** tab
4. Verify these exist:
   ```
   SUPABASE_URL = https://mbmccgnixowxwryycedf.supabase.co
   SUPABASE_ANON_KEY = eyJhbGciOiJI... (long string)
   ```
5. If missing, add them:
   - Click "Add Environment Variable"
   - Add `SUPABASE_URL`
   - Add `SUPABASE_ANON_KEY`
   - Click "Save Changes" (will trigger redeploy)

---

## Step 3: Wait for Deployments (5-10 minutes)

### Monitor Render Deployment:
1. Go to https://dashboard.render.com/
2. Click your service
3. Watch the "Logs" tab
4. Wait for: `✅ Supabase client initialized`
5. Look for: `INFO: Uvicorn running on http://0.0.0.0:10000`

### Monitor Vercel Deployment:
1. Go to https://vercel.com/dashboard
2. Click your project
3. Click "Deployments" tab
4. Wait for green checkmark ✓
5. Status should show "Ready"

---

## Step 4: Test Backend (2 minutes)

```bash
# Test health endpoint
curl https://haven-u8cf.onrender.com/health

# Expected response:
# {"status":"healthy","cv_results_loaded":false,"patients_loaded":true,"trial_protocol_loaded":false}

# Test patients endpoint
curl https://haven-u8cf.onrender.com/patients/search?q=John

# Expected: JSON array of patients
```

Or open in browser:
- Health: https://haven-u8cf.onrender.com/health
- API Docs: https://haven-u8cf.onrender.com/docs

---

## Step 5: Test Frontend (5 minutes)

### A. Open Production Site
Visit: https://use-haven.vercel.app/

### B. Check Dashboard
1. Go to: https://use-haven.vercel.app/dashboard
2. Verify:
   - ✅ Page loads without errors
   - ✅ Stats display at top
   - ✅ Patient video feeds show
   - ✅ No CORS errors in console (press F12)

### C. Test Patient Search
1. Click on any patient area
2. Type a name in search
3. Verify patients appear

### D. Check Stream Page
1. Go to: https://use-haven.vercel.app/stream
2. Verify:
   - ✅ Page loads correctly
   - ✅ "Select Patient" button works
   - ✅ Patient modal opens
   - ✅ Monitoring conditions selector works

---

## Step 6: Test End-to-End (10 minutes)

### Test Live Streaming:

1. **On Computer 1 (Streamer)**:
   - Go to https://use-haven.vercel.app/stream
   - Click "Select Patient"
   - Choose a patient
   - Select monitoring conditions (e.g., CRS)
   - Click "Start Streaming with Selected Protocols"
   - Allow camera access
   - Verify FPS counter appears
   - See "LIVE" indicator

2. **On Computer 2 (Viewer)**:
   - Go to https://use-haven.vercel.app/dashboard
   - Look for your patient's feed
   - Verify you see live video
   - Check CV overlays appear (pose landmarks)

3. **Test Alert**:
   - On streamer computer, rub your face vigorously
   - Should trigger CRS detection
   - Alert should appear on both streamer and viewer

---

## Troubleshooting

### Issue: "Cannot connect to backend"

**Check:**
```bash
# Is backend running?
curl https://haven-u8cf.onrender.com/health
```

**Solutions:**
1. Render free tier sleeps after 15 min - first request wakes it (takes 30s)
2. Check Render logs for errors
3. Verify environment variables are set

### Issue: CORS errors in console

**Error**: `Access to fetch at 'https://haven-u8cf.onrender.com/...' from origin 'https://use-haven.vercel.app' has been blocked`

**Solution:**
1. Make sure you pushed the CORS changes
2. Check Render deployed latest code
3. Verify backend logs show: `✅ CORS configured`

### Issue: WebSocket connection fails

**Error**: `WebSocket connection to 'wss://haven-u8cf.onrender.com/ws/...' failed`

**Check:**
1. Backend is running (not sleeping)
2. Browser console for specific error
3. Render logs show WebSocket connection attempts

### Issue: Environment variable not found

**Frontend:**
- Check Vercel → Settings → Environment Variables
- Redeploy after adding variables

**Backend:**
- Check Render → Environment tab
- Service auto-redeploys after changing variables

---

## Success Criteria ✅

- [ ] Code pushed to GitHub
- [ ] Render deployment successful
- [ ] Vercel deployment successful
- [ ] Backend health check returns 200
- [ ] Frontend loads at https://use-haven.vercel.app/
- [ ] Dashboard displays correctly
- [ ] No CORS errors
- [ ] Patient search works
- [ ] Stream page loads
- [ ] (Optional) Live streaming works end-to-end

---

## Monitoring

### Check Backend Status:
```bash
# Health check
curl -I https://haven-u8cf.onrender.com/health

# Full response
curl https://haven-u8cf.onrender.com/health
```

### View Logs:
- **Render**: https://dashboard.render.com/ → Service → Logs
- **Vercel**: https://vercel.com/dashboard → Project → Deployments → Latest → Logs

### Check Uptime:
- **Render**: Dashboard shows service status
- **Vercel**: Deployments page shows status

---

## After Successful Deployment

### Share Your App:
- Frontend: https://use-haven.vercel.app/
- API Docs: https://haven-u8cf.onrender.com/docs

### Optional Improvements:

1. **Custom Domain**:
   - Buy domain (e.g., `trialsentinel.ai`)
   - Add to Vercel: `app.trialsentinel.ai`
   - Add to Render: `api.trialsentinel.ai`

2. **Upgrade to Paid Tier**:
   - Render: $7/mo (no sleep, faster)
   - Vercel: $20/mo (better analytics)
   - Supabase: $25/mo (more storage)

3. **Add Monitoring**:
   - Sentry for error tracking
   - LogRocket for session replay
   - Datadog for APM

4. **Enable Infisical**:
   - Store secrets securely
   - Rotate keys easily
   - Team collaboration

---

## Quick Commands

```bash
# Deploy changes
git add . && git commit -m "Update" && git push origin main

# Test backend
curl https://haven-u8cf.onrender.com/health

# View backend logs
# Go to: https://dashboard.render.com/

# View frontend
# Go to: https://use-haven.vercel.app/

# Check deployment status
# Vercel: https://vercel.com/dashboard
# Render: https://dashboard.render.com/
```

---

## Need Help?

- Backend not deploying? Check `render.yaml` configuration
- Frontend build failing? Run `cd frontend && npm run build` locally
- CORS issues? Verify `backend/app/main.py` CORS settings
- Secrets not loading? Run `backend/scripts/check_secrets.py`

---

**Ready?** Start with Step 1! 🚀

Once deployed, your app will be live at: **https://use-haven.vercel.app/**

