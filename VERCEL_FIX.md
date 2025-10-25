# Vercel 404 Fix

## The Problem
Vercel is showing 404 because it's trying to build from the root instead of the `frontend/` directory.

## The Solution

### In Vercel Dashboard:

1. Go to your project settings: https://vercel.com/your-username/haven/settings
2. Click **"General"** tab
3. Find **"Root Directory"** setting
4. Set it to: `frontend`
5. Click **"Save"**

### Environment Variables:

In Vercel Dashboard > Environment Variables, add:
```
NEXT_PUBLIC_API_URL=https://haven-new.onrender.com
```

### Then Redeploy:

1. Go to **Deployments** tab
2. Click **"Redeploy"** on the latest deployment
3. Check **"Use existing build cache"** is OFF
4. Click **"Redeploy"**

## Verification

After deployment, your frontend should be live at:
- https://use-haven.vercel.app

And it will proxy API calls to:
- https://haven-new.onrender.com

