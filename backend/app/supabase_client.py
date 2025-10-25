"""
Supabase client for database operations
Uses Infisical for secure secret management with .env fallback
"""

from supabase import create_client, Client
from app.infisical_config import get_secret

# Get secrets from Infisical (or .env fallback)
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️  Warning: SUPABASE_URL or SUPABASE_ANON_KEY not found")
    print("⚠️  Configure secrets in Infisical or add to .env file")
    supabase: Client | None = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print(f"✅ Supabase client initialized: {SUPABASE_URL}")
