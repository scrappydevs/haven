"""
Supabase client for database operations
Uses Infisical for secure secret management
"""

from supabase import create_client, Client
from app.infisical_config import get_secret

# Get secrets from Infisical
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️ SUPABASE_URL or SUPABASE_ANON_KEY not configured")
    supabase: Client | None = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print(f"✅ Supabase client initialized: {SUPABASE_URL}")
    except Exception as e:
        print(f"⚠️ Failed to initialize Supabase client: {e}")
        print("⚠️ Backend will run without database integration")
        supabase: Client | None = None
