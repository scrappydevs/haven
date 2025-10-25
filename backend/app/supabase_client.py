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
    supabase: Client | None = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
