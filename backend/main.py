"""
TrialSentinel AI - Backend Application
Entry point for Gunicorn deployment
Auto-loads secrets from Infisical when run directly
"""

import sys
import os
import subprocess
from pathlib import Path

def check_infisical_cli():
    """Check if Infisical CLI is available"""
    try:
        subprocess.run(['infisical', '--version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def restart_with_infisical():
    """Restart the script with Infisical CLI"""
    print("🔐 Loading secrets from Infisical...")
    print()
    
    # Set environment variable to prevent infinite loop
    env = os.environ.copy()
    env['_INFISICAL_WRAPPER'] = '1'
    
    # Prepare the command
    infisical_cmd = [
        'infisical', 'run', '--env=dev', '--',
        sys.executable, __file__
    ]
    
    # Execute with Infisical (from repo root where .infisical.json is)
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir.parent)
    
    # Use subprocess instead of execvp to avoid exec issues
    try:
        subprocess.run(infisical_cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

# Check if we need to restart with Infisical
# Only do this if:
# 1. Running as main script
# 2. Not already wrapped (check for our flag)
# 3. No Infisical project ID in env (not running with infisical run)
# 4. Infisical CLI is available
if (__name__ == "__main__" and 
    not os.getenv("_INFISICAL_WRAPPER") and
    not os.getenv("INFISICAL_PROJECT_ID") and 
    check_infisical_cli()):
    restart_with_infisical()
    sys.exit(0)  # Exit after restart

# If we get here, either we're running with Infisical or it's not available
from app.main import app

# This is the entry point for Gunicorn
# Run with: gunicorn main:app

if __name__ == "__main__":
    # For local development only
    import uvicorn
    # Add backend to path so imports work
    backend_dir = Path(__file__).parent
    import sys
    sys.path.insert(0, str(backend_dir))
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
