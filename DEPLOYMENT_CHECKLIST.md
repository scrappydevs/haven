# Deployment Checklist

Use this checklist to ensure a smooth deployment to production.

## Pre-Deployment

### Backend (Render)
- [ ] All secrets configured in Infisical or Render environment variables
- [ ] `requirements.txt` is up to date
- [ ] Test Gunicorn locally: `cd backend && gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`
- [ ] Verify `/health` endpoint returns healthy status
- [ ] Test WebSocket connection locally
- [ ] Review CORS settings in `backend/app/main.py`

### Frontend (Vercel)
- [ ] Update `NEXT_PUBLIC_API_URL` in Vercel environment variables
- [ ] Update backend URL in `vercel.json`
- [ ] Test production build locally: `cd frontend && npm run build && npm start`
- [ ] Verify all pages load correctly
- [ ] Test API connections to backend

### Repository
- [ ] Code pushed to GitHub
- [ ] `.gitignore` excludes sensitive files
- [ ] No `.env` files committed
- [ ] All dependencies listed in `requirements.txt` and `package.json`

## Deployment Steps

### Step 1: Deploy Backend (Render)

1. **Create Render Account**: https://dashboard.render.com/register

2. **Choose Deployment Method**:

   **Option A: Blueprint (Recommended)**
   - Click "New +" → "Blueprint"
   - Connect GitHub repository
   - Render auto-detects `render.yaml`
   - Click "Apply"
   
   **Option B: Manual**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Configure:
     ```
     Name: trialsentinel-backend
     Region: Oregon
     Branch: main
     Root Directory: backend
     Runtime: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
     Instance Type: Free (or paid)
     ```

3. **Add Environment Variables** in Render Dashboard:
   ```
   INFISICAL_CLIENT_ID=<your_value>
   INFISICAL_CLIENT_SECRET=<your_value>
   INFISICAL_PROJECT_ID=<your_value>
   SUPABASE_URL=<your_value>
   SUPABASE_KEY=<your_value>
   ANTHROPIC_API_KEY=<your_value>  # Optional
   ```

4. **Deploy**: Click "Create Web Service" or wait for Blueprint to deploy

5. **Copy Backend URL**: Save it (e.g., `https://trialsentinel-backend.onrender.com`)

6. **Test Deployment**:
   - Visit: `https://trialsentinel-backend.onrender.com/health`
   - Should return: `{"status":"healthy",...}`
   - Check logs in Render dashboard

### Step 2: Deploy Frontend (Vercel)

1. **Update Configuration**:
   
   Edit `vercel.json` and replace backend URL:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://trialsentinel-backend.onrender.com/:path*"
       }
     ],
     "env": {
       "NEXT_PUBLIC_API_URL": "https://trialsentinel-backend.onrender.com"
     }
   }
   ```
   
   Commit and push:
   ```bash
   git add vercel.json
   git commit -m "Update backend URL for production"
   git push origin main
   ```

2. **Create Vercel Account**: https://vercel.com/signup

3. **Import Project**:
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Configure:
     ```
     Framework Preset: Next.js
     Root Directory: frontend
     Build Command: npm run build
     Output Directory: .next
     Install Command: npm install
     ```

4. **Add Environment Variable**:
   - Go to Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://trialsentinel-backend.onrender.com`
   - Apply to: Production, Preview, Development

5. **Deploy**: Click "Deploy"

6. **Copy Frontend URL**: Save it (e.g., `https://trialsentinel.vercel.app`)

7. **Test Deployment**:
   - Visit your Vercel URL
   - Check dashboard loads
   - Test patient search
   - Try starting a stream (may fail if no webcam data)

### Step 3: Update CORS

1. **Edit Backend CORS Settings**:
   
   In `backend/app/main.py`, update:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://trialsentinel.vercel.app",
           "http://localhost:3000"  # Keep for local dev
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Commit and Push**:
   ```bash
   git add backend/app/main.py
   git commit -m "Update CORS for production"
   git push origin main
   ```

3. **Render Auto-Deploys**: Wait for new deployment

## Post-Deployment

### Testing
- [ ] Frontend loads at Vercel URL
- [ ] Backend health check returns healthy
- [ ] Patient search works
- [ ] Dashboard statistics load
- [ ] WebSocket connection works (if streaming)
- [ ] No CORS errors in browser console
- [ ] API documentation accessible at `/docs`

### Monitoring
- [ ] Set up Render log monitoring
- [ ] Enable Vercel Analytics (optional)
- [ ] Set up error tracking (Sentry, etc.) - optional
- [ ] Configure uptime monitoring (UptimeRobot, etc.) - optional

### Security
- [ ] CORS restricted to your domains only
- [ ] No sensitive data in logs
- [ ] HTTPS enforced (automatic on Render/Vercel)
- [ ] Rate limiting considered
- [ ] Environment variables not exposed in frontend

### Performance
- [ ] Check Render logs for errors
- [ ] Monitor response times
- [ ] Test from different locations
- [ ] Consider upgrading Render instance if slow

## Troubleshooting

### Backend won't start
- **Check Render logs**: Dashboard → Service → Logs
- **Common issues**:
  - Missing environment variables
  - Wrong Python version
  - Import errors (missing dependencies)
  - Wrong start command

### Frontend can't connect to backend
- **Check**:
  - NEXT_PUBLIC_API_URL is set correctly
  - Backend URL in vercel.json is correct
  - CORS allows your Vercel domain
  - Backend is running (check /health)

### WebSocket connection fails
- **Check**:
  - Render plan supports WebSockets (Free tier does)
  - URL uses `wss://` not `ws://` for production
  - CORS allows WebSocket connections
  - Backend logs show connection attempts

### 502 Bad Gateway on Render
- **Possible causes**:
  - Backend crashed (check logs)
  - Long cold start time (wait and retry)
  - Out of memory (upgrade instance)

### Build fails on Vercel
- **Check**:
  - `npm run build` works locally
  - Node version compatible
  - Environment variables set
  - Root directory is `frontend`

## Rollback Procedure

### Render
1. Go to Dashboard → Service → Deploys
2. Click "..." on previous working deploy
3. Click "Redeploy"

### Vercel
1. Go to Dashboard → Project → Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

## Custom Domain (Optional)

### Vercel
1. Go to Project → Settings → Domains
2. Add your domain (e.g., `app.trialsentinel.ai`)
3. Configure DNS:
   - Type: CNAME
   - Name: app (or @)
   - Value: cname.vercel-dns.com

### Render
1. Go to Service → Settings → Custom Domain
2. Add your domain (e.g., `api.trialsentinel.ai`)
3. Configure DNS:
   - Type: CNAME
   - Name: api
   - Value: [provided by Render]

## Cost Monitoring

### Free Tier Limits
- **Render**: 750 hours/month (1 service), auto-sleep after 15 min inactivity
- **Vercel**: 100 GB bandwidth/month, unlimited deployments
- **Supabase**: 500 MB database, 2 GB bandwidth

### Signs You Need to Upgrade
- Backend frequently sleeps (slow cold starts)
- High traffic (>100 users/day)
- WebSocket connections timing out
- Database storage exceeded

## Support Resources

- **Render Support**: https://render.com/docs
- **Vercel Support**: https://vercel.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Gunicorn Docs**: https://docs.gunicorn.org/

---

## Quick Reference

### Render Start Command
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

### Test Locally
```bash
# Backend
cd backend
gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend
cd frontend
npm run build
npm start
```

### Environment Variables

**Backend (Render)**:
- INFISICAL_CLIENT_ID
- INFISICAL_CLIENT_SECRET
- INFISICAL_PROJECT_ID
- SUPABASE_URL
- SUPABASE_KEY
- ANTHROPIC_API_KEY (optional)

**Frontend (Vercel)**:
- NEXT_PUBLIC_API_URL

---

**Ready to Deploy!** 🚀

Follow this checklist step-by-step for a successful deployment.

