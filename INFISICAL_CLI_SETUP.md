# Infisical CLI Setup (No Credentials Needed!)

## Overview

This project uses the **Infisical CLI** method for secrets management. This means:
- ✅ No SDK installation needed
- ✅ No credentials stored in code
- ✅ No `.env` files needed
- ✅ Secrets injected at runtime
- ✅ Works locally and in production

## How It Works

```bash
# Instead of running directly:
gunicorn main:app

# Run with Infisical CLI:
infisical run -- gunicorn main:app
```

The CLI automatically injects secrets from Infisical into the environment!

---

## Local Development Setup

### 1. Install Infisical CLI

**macOS:**
```bash
brew install infisical/get-cli/infisical
```

**Linux:**
```bash
curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash
sudo apt-get update && sudo apt-get install -y infisical
```

**Windows:**
```powershell
scoop bucket add org https://github.com/Infisical/scoop-infisical.git
scoop install infisical
```

### 2. Login to Infisical

```bash
infisical login
```

This opens a browser window to authenticate.

### 3. Initialize Project

In the repository root (where `.infisical.json` exists):

```bash
cd /Users/gsdr/haven
infisical init
```

Select your project (workspace ID: `14641fd2-4afc-48b6-a138-c18fd6d65181`)

### 4. Run Backend with Secrets

```bash
cd backend
infisical run --env=dev -- python3 main.py
```

That's it! Secrets are automatically injected.

---

## Production Setup (Render)

### Option 1: Use Environment Variables (Current)

Set in Render Dashboard → Environment:
```
SUPABASE_URL=https://mbmccgnixowxwryycedf.supabase.co
SUPABASE_ANON_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

The app works without Infisical CLI.

### Option 2: Use Infisical CLI (Advanced)

1. **Install CLI in Render** - Add to build command:
```bash
curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | bash && \
apt-get update && apt-get install -y infisical && \
pip install -r requirements.txt
```

2. **Set Machine Identity** in Render env vars:
```
INFISICAL_MACHINE_IDENTITY_ID=your_id
INFISICAL_MACHINE_IDENTITY_TOKEN=your_token
```

3. **Start command automatically uses CLI**:
```bash
bash start.sh
```

The script checks if CLI is available and uses it!

---

## Frontend (Vercel)

Frontend doesn't use Infisical - it only needs:

**Vercel Dashboard → Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://haven-new.onrender.com
```

Set this in Vercel dashboard (Settings → Environment Variables).

---

## File Structure

```
haven/
├── .infisical.json              # Project config (auto-created)
├── backend/
│   ├── start.sh                 # Smart start script (uses CLI if available)
│   ├── app/
│   │   └── infisical_config.py  # Simplified (just reads env vars)
│   └── requirements.txt         # No infisical-python needed!
└── frontend/
    └── lib/
        └── api-config.ts        # Reads NEXT_PUBLIC_API_URL
```

---

## Benefits

### ✅ No Credential Management
- No `.env` files to track
- No credentials in code
- No SDK tokens to rotate

### ✅ Automatic Sync
- Update secrets in Infisical dashboard
- Changes available immediately
- No redeployment needed

### ✅ Environment Switching
```bash
# Development
infisical run --env=dev -- python main.py

# Staging
infisical run --env=staging -- python main.py

# Production
infisical run --env=prod -- gunicorn main:app
```

### ✅ Team Collaboration
- Everyone uses same project
- No sharing `.env` files
- Permissions managed in Infisical

---

## Commands Reference

```bash
# Login (one time)
infisical login

# Initialize project (one time per machine)
infisical init

# Run backend locally
cd backend
infisical run --env=dev -- python3 main.py

# Run with gunicorn (production mode locally)
infisical run --env=dev -- gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# View available secrets
infisical secrets

# Export secrets to check them
infisical export --env=dev
```

---

## Troubleshooting

### "Infisical not found"

Install the CLI:
```bash
brew install infisical/get-cli/infisical
```

### "Not logged in"

Login first:
```bash
infisical login
```

### "Project not initialized"

Initialize in repo root:
```bash
cd /Users/gsdr/haven
infisical init
```

### "Secrets not loading"

Check you're in correct directory and environment:
```bash
pwd  # Should be in backend/
infisical run --env=dev -- env | grep SUPABASE
```

---

## Migration from .env

If you have a `.env` file, you can import it to Infisical:

```bash
# Upload all secrets from .env
infisical secrets set --env=dev --from-file=backend/.env

# Then delete the .env file
rm backend/.env
```

---

## Security Best Practices

1. ✅ Never commit `.env` files (already in `.gitignore`)
2. ✅ Use different environments (dev, staging, prod)
3. ✅ Rotate secrets regularly in Infisical dashboard
4. ✅ Use Machine Identities for CI/CD
5. ✅ Audit secret access in Infisical logs

---

## Current Setup Status

- ✅ `.infisical.json` configured (workspace ID: 14641fd2-4afc-48b6-a138-c18fd6d65181)
- ✅ Backend simplified (no SDK needed)
- ✅ `start.sh` auto-detects CLI
- ✅ Fallback to env vars if CLI not available
- ✅ Frontend uses Vercel env vars only

---

**Result**: Clean, secure secrets management without files or credentials in code! 🎉

