#!/usr/bin/env python3
"""
Check Secrets Configuration
Verifies that Infisical and environment variables are properly configured
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infisical_config import secret_manager, get_secret

def check_secrets():
    """Check all secrets and their sources"""
    
    print("\n" + "="*70)
    print("  HAVEN AI - SECRETS CONFIGURATION CHECK")
    print("="*70 + "\n")
    
    # Check Infisical status
    print("📋 INFISICAL STATUS:")
    print(f"   Infisical Enabled: {'✅ Yes' if secret_manager.use_infisical else '❌ No'}")
    if secret_manager.project_id:
        print(f"   Project ID: {secret_manager.project_id}")
    print()
    
    # Required secrets
    print("🔐 REQUIRED SECRETS:")
    secrets_to_check = [
        ("SUPABASE_URL", True, "Database connection"),
        ("SUPABASE_ANON_KEY", True, "Database authentication"),
        ("ANTHROPIC_API_KEY", False, "AI-powered recommendations"),
    ]
    
    all_required_found = True
    
    for secret_name, required, description in secrets_to_check:
        value = get_secret(secret_name)
        
        if value:
            # Mask the value for security
            if len(value) > 20:
                masked = value[:10] + "..." + value[-10:]
            else:
                masked = value[:5] + "..."
            
            status = "✅"
            status_text = f"Found ({masked})"
        else:
            status = "❌" if required else "⚠️ "
            status_text = "Not found"
            if required:
                all_required_found = False
        
        req_text = "[REQUIRED]" if required else "[OPTIONAL]"
        print(f"   {status} {secret_name:25} {req_text:12} - {description}")
        print(f"      {status_text}")
    
    print()
    
    # Infisical configuration check
    if not secret_manager.use_infisical:
        print("⚠️  INFISICAL NOT CONFIGURED")
        print("   To enable Infisical, add to your .env file:")
        print()
        print("   Option 1 (OAuth - Recommended):")
        print("   INFISICAL_CLIENT_ID=your_client_id")
        print("   INFISICAL_CLIENT_SECRET=your_client_secret")
        print("   INFISICAL_PROJECT_ID=your_project_id")
        print()
        print("   Option 2 (Service Token):")
        print("   INFISICAL_TOKEN=st.your_token")
        print()
    
    # Summary
    print("="*70)
    if all_required_found:
        print("✅ All required secrets configured!")
        print("   Your backend is ready to run.")
        return 0
    else:
        print("❌ Some required secrets are missing!")
        print("   Add them to .env file or configure Infisical.")
        print("   See backend/.env.template for template")
        return 1
    
    print("="*70 + "\n")

if __name__ == "__main__":
    sys.exit(check_secrets())
