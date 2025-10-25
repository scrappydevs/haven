# Infisical Setup Guide

## Overview

TrialSentinel AI uses [Infisical](https://infisical.com/) for secure, centralized secret management. Infisical provides:
- 🔐 Encrypted secret storage
- 🌍 Multi-environment support (dev, staging, prod)
- 👥 Team collaboration with access controls
- 📝 Audit logs for secret access
- 🔄 Automatic secret rotation

## Features

- **Automatic fallback**: If Infisical is not configured, the app automatically falls back to `.env` files
- **Zero downtime**: Secrets can be updated in Infisical without restarting the backend
- **Multi-environment**: Separate secrets for dev, staging, and production

## Quick Start

### 1. Create Infisical Account

1. Go to [https://app.infisical.com/signup](https://app.infisical.com/signup)
2. Sign up for a free account
3. Create a new project (e.g., "TrialSentinel")

### 2. Create Project & Environment

1. In your Infisical dashboard, create a project
2. Note your **Project ID** (found in Settings)
3. Create environments: `dev`, `staging`, `prod`

### 3. Add Secrets

Add the following secrets to your environment:

#### Required Secrets (Optional but Recommended):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJhbGciOiJIUzI1...` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |

### 4. Get Service Token

1. In Infisical, go to **Project Settings** → **Service Tokens**
2. Click **Generate New Token**
3. Select the environment (e.g., `dev`)
4. Copy the token (starts with `st.`)

### 5. Configure Backend

Create a `.env` file in the `backend/` directory:

```bash
# Infisical Configuration
INFISICAL_TOKEN=st.your-service-token-here
INFISICAL_SITE_URL=https://app.infisical.com

# Optional: Environment to use (default: dev)
INFISICAL_ENVIRONMENT=dev

# Fallback values (used if Infisical is not configured)
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_ANON_KEY=xxx
# ANTHROPIC_API_KEY=sk-ant-xxx
```

## Usage

### Backend Integration

The backend automatically uses Infisical for all secrets:

```python
from app.infisical_config import get_secret

# Get a secret (automatically uses Infisical if configured)
api_key = get_secret("ANTHROPIC_API_KEY")

# Get a secret with default value
url = get_secret("SUPABASE_URL", default="http://localhost:8000")
```

### Secret Priority

The app loads secrets in this order:

1. **Infisical** (if `INFISICAL_TOKEN` is set)
2. **.env file** (fallback)
3. **Environment variables** (system-level)
4. **Default values** (hardcoded)

## Environment Management

### Development
```bash
# Use dev environment
INFISICAL_ENVIRONMENT=dev python3 main.py
```

### Staging
```bash
# Use staging environment
INFISICAL_ENVIRONMENT=staging python3 main.py
```

### Production
```bash
# Use production environment
INFISICAL_ENVIRONMENT=prod python3 main.py
```

## Testing

Test your Infisical setup:

```bash
cd backend
source venv/bin/activate
python3 -c "from app.infisical_config import get_secret; print('✅ Infisical working!' if get_secret('SUPABASE_URL') else '❌ Not configured')"
```

## Troubleshooting

### Issue: "INFISICAL_TOKEN not found"

**Solution**: Add `INFISICAL_TOKEN` to your `.env` file or export it:
```bash
export INFISICAL_TOKEN=st.your-token-here
```

### Issue: "Failed to get secret from Infisical"

**Possible causes**:
1. Invalid or expired token
2. Wrong environment name
3. Secret doesn't exist in Infisical

**Solution**: 
- Verify token in Infisical dashboard
- Check environment name matches (dev, staging, prod)
- Add the secret in Infisical UI

### Issue: App still uses .env despite Infisical setup

**Solution**: 
- Check that `INFISICAL_TOKEN` is set correctly
- Restart the backend
- Check logs for Infisical initialization messages

## Security Best Practices

1. **Never commit tokens**: Add `.env` to `.gitignore`
2. **Rotate tokens regularly**: Generate new service tokens monthly
3. **Use least privilege**: Only grant access to required environments
4. **Audit logs**: Regularly review secret access in Infisical
5. **Production tokens**: Use separate tokens for production

## CLI Commands

```bash
# Install Infisical CLI (optional)
brew install infisical/get-cli/infisical

# Login
infisical login

# View secrets for current project
infisical secrets

# Export secrets to .env
infisical export > .env
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Backend Application               │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │   app/infisical_config.py             │ │
│  │   - SecretManager class               │ │
│  │   - Automatic Infisical/env fallback  │ │
│  └───────────────────────────────────────┘ │
│                    ↓                        │
│  ┌───────────────────────────────────────┐ │
│  │   Secrets consumed by:                │ │
│  │   - app/supabase_client.py            │ │
│  │   - app/main.py (Anthropic)           │ │
│  │   - Future integrations               │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │  Secret Sources      │
         ├──────────────────────┤
         │  1. Infisical Cloud  │
         │  2. .env file        │
         │  3. ENV variables    │
         └──────────────────────┘
```

## Additional Resources

- **Infisical Docs**: https://infisical.com/docs
- **Python SDK**: https://infisical.com/docs/sdks/languages/python
- **Service Tokens**: https://infisical.com/docs/documentation/platform/token

## Need Help?

- Check `/backend/ENV_SETUP.md` for basic .env setup
- See logs in console for Infisical initialization status
- All secrets are **optional** - the app works without them!

