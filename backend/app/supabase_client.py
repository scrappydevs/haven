"""
Supabase client for database operations
Reads from environment variables (Infisical CLI or Render dashboard)
"""

import os
from supabase import create_client, Client

# Get secrets from environment - works with both:
# 1. Infisical CLI (injects into environment when you run: infisical run -- python3 main.py)
# 2. Render dashboard (sets env vars directly)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️  Supabase credentials not found in environment")
    print("   Set SUPABASE_URL and SUPABASE_ANON_KEY in:")
    print("   - Render dashboard (production)")
    print("   - Infisical (development)")
    supabase: Client | None = None
else:
    print(f"✅ Supabase configured: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
