# Infisical Configuration Fix Guide

## Problem
The backend is showing:
```
⚠️  INFISICAL_TOKEN not found in environment
⚠️  Using .env file for secrets
⚠️  Warning: SUPABASE_URL or SUPABASE_ANON_KEY not found
```

This means secrets are not being loaded properly from either Infisical or the `.env` file.

## Root Causes

1. **Wrong variable names in `.env`**: Currently has `NEXT_PUBLIC_SUPABASE_URL` instead of `SUPABASE_URL`
2. **Infisical not configured**: Missing OAuth credentials or service token
3. **API keys look like JWTs**: The values in `.env` appear to be JWT tokens, not actual Supabase credentials

## Quick Fix (5 minutes)

### Step 1: Check Your Current `.env` File

```bash
cd /Users/gsdr/haven/backend
cat .env
```

### Step 2: Get Correct Supabase Credentials

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **API**
4. Copy these values:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon/public key** (long string starting with `eyJ...`)

### Step 3: Update `.env` File

Create or update `/Users/gsdr/haven/backend/.env` with correct variable names:

```bash
# ===== SUPABASE CONFIGURATION (REQUIRED) =====
SUPABASE_URL=https://your-actual-project-url.supabase.co
SUPABASE_ANON_KEY=eyJ...your-actual-anon-key

# ===== ANTHROPIC API (OPTIONAL) =====
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here

# ===== INFISICAL (OPTIONAL BUT RECOMMENDED) =====
# Add these if you want to use Infisical for secrets management
# INFISICAL_CLIENT_ID=your_client_id
# INFISICAL_CLIENT_SECRET=your_client_secret
# INFISICAL_PROJECT_ID=14641fd2-4afc-48b6-a138-c18fd6d65181
```

**Important**: Remove the `NEXT_PUBLIC_` prefix! That's for frontend only.

### Step 4: Verify Configuration

Run the secrets checker:

```bash
cd /Users/gsdr/haven/backend
python3 scripts/check_secrets.py
```

You should see:
```
✅ SUPABASE_URL             [REQUIRED]   - Database connection
   Found (https://xxx...xxx)
✅ SUPABASE_ANON_KEY        [REQUIRED]   - Database authentication
   Found (eyJ...xxx)
```

### Step 5: Restart Backend

```bash
# Stop current backend (Ctrl+C)
# Start fresh
cd /Users/gsdr/haven/backend
python3 main.py
```

You should now see:
```
✅ Using SUPABASE_URL from .env file
✅ Using SUPABASE_ANON_KEY from .env file
✅ Supabase client initialized: https://your-project.supabase.co
```

## Advanced: Enable Infisical (Optional)

For better security and team collaboration:

### Step 1: Set Up Infisical

1. Go to https://app.infisical.com/
2. Login or create account
3. Go to your project (workspace ID: `14641fd2-4afc-48b6-a138-c18fd6d65181`)
4. Navigate to **Project Settings** → **Access Control** → **Machine Identities**
5. Create a new Universal Auth Identity
6. Copy the `Client ID` and `Client Secret`

### Step 2: Add Secrets to Infisical

In Infisical Dashboard:
1. Go to your project → **Secrets**
2. Select environment (e.g., `dev`)
3. Add these secrets:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_ANON_KEY`: Your Supabase anon key
   - `ANTHROPIC_API_KEY`: Your Anthropic API key (if you have one)

### Step 3: Update `.env` with Infisical Credentials

```bash
# Infisical OAuth Configuration
INFISICAL_CLIENT_ID=your_client_id_from_step1
INFISICAL_CLIENT_SECRET=your_client_secret_from_step1
INFISICAL_PROJECT_ID=14641fd2-4afc-48b6-a138-c18fd6d65181
INFISICAL_ENVIRONMENT=dev

# You can now remove these (they'll come from Infisical)
# SUPABASE_URL=...
# SUPABASE_ANON_KEY=...
# ANTHROPIC_API_KEY=...
```

### Step 4: Install Infisical SDK (if not installed)

```bash
cd /Users/gsdr/haven/backend
source venv/bin/activate
pip install infisical-python
```

### Step 5: Test Infisical Connection

```bash
python3 scripts/check_secrets.py
```

You should see:
```
✅ Infisical client initialized with OAuth
✅ Retrieved SUPABASE_URL from Infisical
✅ Retrieved SUPABASE_ANON_KEY from Infisical
```

## Troubleshooting

### Issue: "Module not found: infisical_client"

**Solution**: Install the SDK
```bash
cd backend
source venv/bin/activate
pip install infisical-python
```

### Issue: "Failed to initialize Infisical with OAuth"

**Possible causes**:
1. Wrong Client ID or Secret
2. Machine Identity not granted access to project
3. Wrong project ID

**Solution**:
1. Verify credentials in Infisical dashboard
2. Check Machine Identity has proper permissions
3. Confirm project ID matches

### Issue: "SUPABASE_URL not found"

**Check**:
1. Variable name is correct (not `NEXT_PUBLIC_SUPABASE_URL`)
2. `.env` file is in `/backend/` directory
3. Value is a URL starting with `https://`

### Issue: Values are JWT tokens instead of URLs

If your `SUPABASE_URL` looks like `eyJhbGciOiJI...`, you have the wrong value.

**Solution**:
- Go to Supabase Dashboard → Settings → API
- Copy the **Project URL** (not the API key)
- The URL should look like: `https://mbmccgnixowxwryyceddf.supabase.co`

## Verification Checklist

- [ ] `.env` file exists in `/backend/` directory
- [ ] Variable names are correct (no `NEXT_PUBLIC_` prefix)
- [ ] `SUPABASE_URL` is an actual URL (starts with https://)
- [ ] `SUPABASE_ANON_KEY` is a long JWT-like string
- [ ] Backend starts without warnings
- [ ] `check_secrets.py` shows all required secrets found
- [ ] (Optional) Infisical shows as enabled in logs

## Testing

Once configured, test that everything works:

```bash
# 1. Check secrets
python3 backend/scripts/check_secrets.py

# 2. Start backend
cd backend
python3 main.py

# 3. Test API
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","cv_results_loaded":false,"patients_loaded":false,"trial_protocol_loaded":false}

# 4. Test Supabase connection
curl http://localhost:8000/patients/search?q=test

# Should return patient data from Supabase (not error)
```

## Reference

- Backend `.env` location: `/Users/gsdr/haven/backend/.env`
- Template: `/Users/gsdr/haven/backend/.env.template`
- Infisical workspace ID: `14641fd2-4afc-48b6-a138-c18fd6d65181`
- Check script: `backend/scripts/check_secrets.py`

## Quick Command Reference

```bash
# Check current configuration
cd /Users/gsdr/haven/backend && python3 scripts/check_secrets.py

# Edit .env file
nano /Users/gsdr/haven/backend/.env

# Test backend startup
cd /Users/gsdr/haven/backend && python3 main.py

# View .env template
cat /Users/gsdr/haven/backend/.env.template
```

---

**Need more help?** Check:
- `/backend/INFISICAL_SETUP.md` - Full Infisical guide
- `/backend/ENV_SETUP.md` - Environment setup guide
- Infisical Docs: https://infisical.com/docs

