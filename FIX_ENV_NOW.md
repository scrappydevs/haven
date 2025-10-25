# 🔧 URGENT: Fix Your .env File Now

## The Problem

Your `.env` file has **WRONG VARIABLE NAMES** and **WRONG VALUES**.

Current (WRONG):
```
NEXT_PUBLIC_SUPABASE_URL=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  ❌ (This is a JWT token, not a URL!)
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  ❌ (Wrong prefix!)
```

## The Fix (2 Minutes)

### Option A: Quick Manual Fix

1. **Edit the .env file:**
```bash
nano /Users/gsdr/haven/backend/.env
```

2. **Replace everything with this** (update the values with YOUR actual credentials):

```bash
# ===== SUPABASE CONFIGURATION =====
# Get from: https://supabase.com/dashboard → Your Project → Settings → API

# This should be a URL like: https://xxxxx.supabase.co
SUPABASE_URL=https://mbmccgnixowxwryyceddf.supabase.co

# This is the anon/public key (the long JWT-looking string)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ibWNjZ25peG93eHdyeXljZWRmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMzY4OTMsImV4cCI6MjA3NjkxMjg5M30.GigugW5iVpVRg2BqVy5qEtsZ4VadD1hvva6z-qo3tdk

# Optional: Anthropic API key for AI features
# ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

3. **Save and exit** (Ctrl+X, then Y, then Enter)

### Option B: Get Real Values from Supabase

If you don't know your Supabase URL:

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **API**
4. Look for:
   - **Project URL** (copy this to `SUPABASE_URL`)
   - **Project API keys** → **anon public** (copy this to `SUPABASE_ANON_KEY`)

The URL should look like: `https://xxxxx.supabase.co` (NOT a JWT token!)

## Verify the Fix

```bash
cd /Users/gsdr/haven/backend
source venv/bin/activate
python3 scripts/check_secrets.py
```

You should see:
```
✅ SUPABASE_URL              [REQUIRED]   - Database connection
   Found (https://mbm...eddf.supabase.co)
✅ SUPABASE_ANON_KEY         [REQUIRED]   - Database authentication
   Found (eyJ...tdk)
```

## Restart Backend

```bash
# Stop current backend if running (Ctrl+C)

# Start fresh
cd /Users/gsdr/haven/backend
python3 main.py
```

You should now see:
```
✅ Using SUPABASE_URL from .env file
✅ Using SUPABASE_ANON_KEY from .env file
✅ Supabase client initialized: https://mbmccgnixowxwryyceddf.supabase.co
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Still Having Issues?

### Common Mistakes:

1. **Wrong file location**: Must be `/Users/gsdr/haven/backend/.env` (not in frontend!)
2. **Wrong variable name**: Must be `SUPABASE_URL` (not `NEXT_PUBLIC_SUPABASE_URL`)
3. **JWT token as URL**: The URL value should NOT start with `eyJ...`
4. **Missing quotes**: Values don't need quotes in .env files
5. **Spaces around =**: Use `KEY=value` not `KEY = value`

### Debug Command:

```bash
cd /Users/gsdr/haven/backend
source venv/bin/activate

# This will show you exactly what's loaded
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SUPABASE_URL:', os.getenv('SUPABASE_URL', 'NOT FOUND'))
print('SUPABASE_ANON_KEY:', os.getenv('SUPABASE_ANON_KEY', 'NOT FOUND')[:20] + '...' if os.getenv('SUPABASE_ANON_KEY') else 'NOT FOUND')
"
```

Expected output:
```
SUPABASE_URL: https://mbmccgnixowxwryyceddf.supabase.co
SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIsI...
```

---

**Do this NOW before continuing!** The backend won't work properly without correct secrets.

