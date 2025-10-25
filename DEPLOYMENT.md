# Deployment Guide - TrialSentinel AI

This guide covers deploying the TrialSentinel AI application to production using **Vercel** (frontend) and **Render** (backend).

## Architecture

- **Frontend**: Next.js app deployed on Vercel
- **Backend**: FastAPI app deployed on Render with Gunicorn + Uvicorn workers
- **Database**: Supabase (already configured)
- **Secrets Management**: Infisical or Render environment variables

---

## Backend Deployment (Render)

### Prerequisites
- Render account (https://render.com)
- GitHub repository with your code
- Infisical credentials OR manual environment variables

### Option 1: Deploy with render.yaml (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **Create New Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**
   In the Render dashboard, add these environment variables:
   ```
   INFISICAL_CLIENT_ID=your_client_id
   INFISICAL_CLIENT_SECRET=your_client_secret
   INFISICAL_PROJECT_ID=your_project_id
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

4. **Deploy**
   - Render will automatically build and deploy
   - Your backend will be available at: `https://trialsentinel-backend.onrender.com`

### Option 2: Manual Deployment

1. **Create New Web Service**
   - Go to Render Dashboard → "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

2. **Configure Build Settings**
   ```
   Name: trialsentinel-backend
   Region: Oregon (or nearest to your users)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
   ```

3. **Add Environment Variables** (same as Option 1)

4. **Deploy** - Click "Create Web Service"

### Verify Backend Deployment

Once deployed, test these endpoints:
- Health check: `https://your-backend-url.onrender.com/health`
- API docs: `https://your-backend-url.onrender.com/docs`
- Root: `https://your-backend-url.onrender.com/`

---

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (https://vercel.com)
- GitHub repository

### Steps

1. **Update vercel.json**
   
   Edit `/vercel.json` and replace `your-backend-url.onrender.com` with your actual Render backend URL:
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

2. **Push to GitHub**
   ```bash
   git add vercel.json
   git commit -m "Update backend URL for production"
   git push origin main
   ```

3. **Deploy to Vercel**
   - Go to https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Configure project:
     ```
     Framework Preset: Next.js
     Root Directory: frontend
     Build Command: npm run build
     Output Directory: .next
     Install Command: npm install
     ```

4. **Add Environment Variable**
   In Vercel project settings → Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://trialsentinel-backend.onrender.com
   ```

5. **Deploy**
   - Vercel will automatically build and deploy
   - Your frontend will be available at: `https://trialsentinel.vercel.app` (or custom domain)

### Custom Domain (Optional)

1. Go to Vercel project → Settings → Domains
2. Add your custom domain (e.g., `trialsentinel.ai`)
3. Configure DNS records as instructed by Vercel

---

## Environment Variables Reference

### Backend (Render)

| Variable | Description | Required |
|----------|-------------|----------|
| `INFISICAL_CLIENT_ID` | Infisical OAuth client ID | Yes* |
| `INFISICAL_CLIENT_SECRET` | Infisical OAuth client secret | Yes* |
| `INFISICAL_PROJECT_ID` | Infisical project ID | Yes* |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon/public key | Yes |
| `ANTHROPIC_API_KEY` | Claude API key for LLM recommendations | No |
| `PORT` | Server port (auto-set by Render) | Auto |

*Or configure secrets directly in environment variables instead of using Infisical

### Frontend (Vercel)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |

---

## Post-Deployment

### 1. Update CORS Settings

The backend is configured to allow all origins (`allow_origins=["*"]`). For production, update this in `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trialsentinel.vercel.app",
        "https://your-custom-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Test WebSocket Connection

WebSockets should work automatically on Render and Vercel. Test by:
1. Opening the stream page on your deployed frontend
2. Starting a patient stream
3. Verifying live video appears

### 3. Monitor Logs

- **Render**: Dashboard → Your Service → Logs
- **Vercel**: Dashboard → Your Project → Deployments → [Deployment] → Logs

### 4. Set Up Monitoring

Consider adding:
- **Render**: Auto-scaling and health checks (configured in render.yaml)
- **Vercel**: Analytics and Web Vitals
- **External**: Sentry for error tracking, Datadog/New Relic for APM

---

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Ensure `startCommand` includes `cd backend` before running gunicorn

**Problem**: WebSocket connection fails
- **Solution**: Check that Render plan supports WebSockets (free tier does)

**Problem**: Slow cold starts
- **Solution**: Render free tier has cold starts. Upgrade to paid plan for always-on

### Frontend Issues

**Problem**: `API_URL is not defined`
- **Solution**: Ensure `NEXT_PUBLIC_API_URL` is set in Vercel environment variables

**Problem**: CORS errors
- **Solution**: Update backend CORS settings to include your Vercel domain

**Problem**: Build fails
- **Solution**: Check Node version compatibility. Vercel uses Node 18+ by default

---

## Scaling Considerations

### Backend (Render)

- **Workers**: Adjust `--workers` in start command based on traffic
- **Instance Type**: Upgrade from free tier for better performance
- **Auto-scaling**: Configure in Render dashboard

### Frontend (Vercel)

- Vercel automatically scales
- Consider Edge Functions for API routes if needed
- Use Vercel Analytics for performance monitoring

---

## Security Checklist

- [ ] Update CORS to whitelist only your domains
- [ ] Use HTTPS only (automatic on Render/Vercel)
- [ ] Rotate Supabase keys if previously exposed
- [ ] Set up rate limiting on Render
- [ ] Enable Vercel DDoS protection
- [ ] Review Infisical access controls
- [ ] Set up logging and alerting

---

## Cost Estimate

### Free Tier
- **Render**: Free (750 hrs/month, auto-sleep after inactivity)
- **Vercel**: Free (100 GB bandwidth, unlimited deployments)
- **Supabase**: Free (500 MB database, 2 GB bandwidth)
- **Total**: $0/month (with limitations)

### Production Tier
- **Render**: $7-25/month (always-on, better specs)
- **Vercel**: $20/month (Pro plan, analytics)
- **Supabase**: $25/month (Pro plan, more storage)
- **Total**: ~$52-70/month

---

## Continuous Deployment

Both Render and Vercel support automatic deployments:

1. **Push to main branch** → Auto-deploy to production
2. **Push to feature branch** → Auto-deploy preview (Vercel) / manual deploy (Render)
3. **Pull request** → Preview deployment with unique URL

Enable this in:
- **Render**: Settings → Auto-Deploy
- **Vercel**: Settings → Git → Automatically deploy

---

## Support

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Next.js Deployment**: https://nextjs.org/docs/deployment

---

## Quick Commands Reference

### Local Development
```bash
# Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py

# Frontend
cd frontend
npm run dev
```

### Production Simulation
```bash
# Backend (test Gunicorn locally)
cd backend
gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend (test production build)
cd frontend
npm run build
npm start
```

---

**Deployment Ready!** 🚀

Your TrialSentinel AI application is now configured for production deployment on Vercel and Render.

