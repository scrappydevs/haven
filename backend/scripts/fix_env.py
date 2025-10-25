#!/usr/bin/env python3
"""
Automatic .env File Fixer
Corrects common issues with environment variable configuration
"""

import os
from pathlib import Path

def fix_env_file():
    """Fix the .env file with correct variable names and values"""
    
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    
    print("\n" + "="*70)
    print("  HAVEN AI - .env FILE FIXER")
    print("="*70 + "\n")
    
    if not env_file.exists():
        print(f"❌ .env file not found at: {env_file}")
        print("   Creating new .env file from template...")
        
        # Create from template
        template = backend_dir / ".env.template"
        if template.exists():
            import shutil
            shutil.copy(template, env_file)
            print(f"✅ Created .env file at: {env_file}")
            print("   Please edit it and add your actual credentials.")
            return
        else:
            print("❌ Template file not found. Cannot create .env")
            return
    
    # Read current .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    print(f"📁 Found .env file at: {env_file}")
    print(f"   File has {len(lines)} lines")
    print()
    
    # Parse and fix
    fixed_lines = []
    changes_made = []
    supabase_url = None
    supabase_anon_key = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # Parse key=value
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Fix NEXT_PUBLIC_SUPABASE_URL
            if key == 'NEXT_PUBLIC_SUPABASE_URL':
                # This is actually the anon key (JWT token)
                if value.startswith('eyJ'):
                    # Decode JWT to get project ref
                    import json, base64
                    try:
                        payload = json.loads(base64.urlsafe_b64decode(value.split('.')[1] + '==').decode())
                        project_ref = payload.get('ref')
                        if project_ref:
                            supabase_url = f"https://{project_ref}.supabase.co"
                            changes_made.append(f"✓ Extracted Supabase URL from JWT: {supabase_url}")
                        else:
                            # It's the anon key, not the URL
                            supabase_anon_key = value
                            changes_made.append("✓ Found anon key in NEXT_PUBLIC_SUPABASE_URL")
                    except:
                        fixed_lines.append(line)
                else:
                    # It's an actual URL
                    supabase_url = value
                    changes_made.append(f"✓ Found Supabase URL: {value}")
                continue
            
            # Fix NEXT_PUBLIC_SUPABASE_ANON_KEY
            elif key == 'NEXT_PUBLIC_SUPABASE_ANON_KEY':
                supabase_anon_key = value
                changes_made.append("✓ Found anon key")
                continue
            
            # Keep other variables
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Create corrected content
    corrected_content = []
    
    # Add header
    corrected_content.append("# Haven AI - Backend Environment Variables")
    corrected_content.append("# Auto-corrected by fix_env.py")
    corrected_content.append("")
    
    # Add Supabase config
    if supabase_url or supabase_anon_key:
        corrected_content.append("# ===== SUPABASE CONFIGURATION =====")
        if supabase_url:
            corrected_content.append(f"SUPABASE_URL={supabase_url}")
        if supabase_anon_key:
            corrected_content.append(f"SUPABASE_ANON_KEY={supabase_anon_key}")
        corrected_content.append("")
    
    # Add other existing config
    corrected_content.extend(fixed_lines)
    
    # Add Infisical placeholder if not present
    if not any('INFISICAL' in line for line in corrected_content):
        corrected_content.append("")
        corrected_content.append("# ===== INFISICAL CONFIGURATION (OPTIONAL) =====")
        corrected_content.append("# Uncomment and add your credentials to use Infisical")
        corrected_content.append("# INFISICAL_CLIENT_ID=your_client_id")
        corrected_content.append("# INFISICAL_CLIENT_SECRET=your_client_secret")
        corrected_content.append("# INFISICAL_PROJECT_ID=14641fd2-4afc-48b6-a138-c18fd6d65181")
    
    # Backup original
    backup_file = env_file.parent / ".env.backup"
    with open(env_file, 'r') as f:
        with open(backup_file, 'w') as b:
            b.write(f.read())
    print(f"💾 Backup created: {backup_file}")
    print()
    
    # Write corrected file
    with open(env_file, 'w') as f:
        f.write('\n'.join(corrected_content) + '\n')
    
    print("✅ CORRECTIONS MADE:")
    for change in changes_made:
        print(f"   {change}")
    print()
    
    print(f"✅ .env file has been corrected!")
    print(f"   Location: {env_file}")
    print()
    
    # Summary
    print("📋 CORRECTED CONFIGURATION:")
    if supabase_url:
        print(f"   SUPABASE_URL: {supabase_url}")
    if supabase_anon_key:
        masked_key = supabase_anon_key[:20] + "..." + supabase_anon_key[-10:]
        print(f"   SUPABASE_ANON_KEY: {masked_key}")
    print()
    
    print("="*70)
    print("✅ NEXT STEPS:")
    print("   1. Review the corrected .env file")
    print("   2. Run: python3 scripts/check_secrets.py")
    print("   3. Restart backend: python3 main.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    fix_env_file()
