"""
Supabase client for database operations
Reads from environment variables (Infisical CLI or Render dashboard)
"""

import inspect
import os

from supabase import create_client, Client
from supabase._sync.client import (
    DEFAULT_POSTGREST_CLIENT_TIMEOUT,
    SyncClient,
)

try:
    from postgrest._sync.client import SyncPostgrestClient
except ImportError:
    SyncPostgrestClient = None  # type: ignore

# Get secrets from environment - works with both:
# 1. Infisical CLI (injects into environment when you run: infisical run -- python3 main.py)
# 2. Render dashboard (sets env vars directly)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Temporary compatibility shim:
# Supabase >= 2.22 expects the postgrest client to accept an `http_client` kwarg.
# Older postgrest releases (<0.19) do not support this argument which results in
# a TypeError during patient search. We detect the available signature at runtime
# and strip unsupported kwargs when needed so the backend stays functional until
# dependencies are aligned upstream.
if SyncPostgrestClient is not None:
    postgrest_init_params = inspect.signature(
        SyncPostgrestClient.__init__
    ).parameters

    if "http_client" not in postgrest_init_params:
        def _compat_init_postgrest_client(  # type: ignore[override]
            rest_url: str,
            headers: dict[str, str],
            schema: str,
            timeout: float | int = DEFAULT_POSTGREST_CLIENT_TIMEOUT,
            verify: bool = True,
            proxy: str | None = None,
            http_client=None,
        ) -> SyncPostgrestClient:
            if http_client is not None:
                print(
                    "⚠️  postgrest client does not support custom http_client; ignoring provided instance."
                )

            kwargs: dict[str, object] = {}
            if "timeout" in postgrest_init_params:
                kwargs["timeout"] = timeout
            if "verify" in postgrest_init_params:
                kwargs["verify"] = verify
            if "proxy" in postgrest_init_params:
                kwargs["proxy"] = proxy

            return SyncPostgrestClient(
                rest_url,
                headers=headers,
                schema=schema,
                **kwargs,
            )

        SyncClient._init_postgrest_client = staticmethod(_compat_init_postgrest_client)

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
