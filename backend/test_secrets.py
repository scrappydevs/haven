#!/usr/bin/env python
"""
Test script to verify all required secrets are available
Run with: infisical run -- python test_secrets.py
"""

import os
from dotenv import load_dotenv

# Load .env.local as fallback
load_dotenv(".env.local")

print("🔐 Checking Required Secrets for Intake System")
print("=" * 60)
print()

required_secrets = {
    "LiveKit": [
        ("LIVEKIT_URL", "LiveKit WebSocket URL"),
        ("LIVEKIT_API_KEY", "LiveKit API Key"),
        ("LIVEKIT_API_SECRET", "LiveKit API Secret"),
    ],
    "AI Services": [
        ("OPENAI_API_KEY", "OpenAI API Key (for Realtime API)"),
        ("ANTHROPIC_API_KEY", "Anthropic API Key (optional, for monitoring agent)"),
    ],
    "Database": [
        ("SUPABASE_URL", "Supabase URL"),
        ("SUPABASE_ANON_KEY", "Supabase Anon Key"),
    ]
}

all_present = True
missing_secrets = []

for category, secrets in required_secrets.items():
    print(f"\n📋 {category}:")
    for secret_name, description in secrets:
        value = os.getenv(secret_name)
        if value:
            # Show first/last 4 chars for verification
            if len(value) > 20:
                masked = f"{value[:4]}...{value[-4:]}"
            else:
                masked = "***"
            print(f"   ✅ {secret_name}: {masked}")
        else:
            print(f"   ❌ {secret_name}: MISSING")
            all_present = False
            missing_secrets.append((secret_name, description))

print()
print("=" * 60)

if all_present:
    print("✅ All required secrets are configured!")
    print()
    print("Ready to start intake system:")
    print("  1. Agent worker: ./start_intake_agent.sh dev")
    print("  2. Backend API: infisical run -- uvicorn app.main:app --reload")
    print("  3. Frontend: cd ../frontend && npm run dev")
else:
    print("⚠️  Missing secrets detected!")
    print()
    print("Please add these secrets to Infisical:")
    for secret_name, description in missing_secrets:
        print(f"   • {secret_name} - {description}")
    print()
    print("Add secrets via Infisical CLI:")
    print("   infisical secrets set <SECRET_NAME> <value>")
    print()
    print("Or add to backend/.env.local for local development")

print("=" * 60)
