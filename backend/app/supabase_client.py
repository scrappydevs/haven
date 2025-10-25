"""
Supabase client for database operations
"""

from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️  Warning: SUPABASE_URL or SUPABASE_ANON_KEY not found in environment variables")
    supabase: Client | None = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print(f"✅ Supabase client initialized: {SUPABASE_URL}")
