"""
Supabase client for database operations
Uses Infisical for secure secret management
"""

from supabase import create_client, Client
from app.infisical_config import get_secret

# Get secrets from Infisical
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")

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
    print(f"✅ Supabase configured: {SUPABASE_URL[:30]}...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
print("=" * 60)
