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

print("=" * 60)
print("🔧 Supabase Client Initialization")
print("=" * 60)
print(f"SUPABASE_URL present: {bool(SUPABASE_URL)}")
print(f"SUPABASE_ANON_KEY present: {bool(SUPABASE_ANON_KEY)}")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Supabase NOT configured - missing credentials")
    print("   Patient search will return empty results")
    supabase: Client | None = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print(f"✅ Supabase configured: {SUPABASE_URL[:30]}...")
    except Exception as e:
        print(f"⚠️ Failed to initialize Supabase client: {e}")
        print("⚠️ Backend will run without database integration")
        supabase: Client | None = None
print("=" * 60)
