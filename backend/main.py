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
    
    # Prepare the command
    infisical_cmd = [
        'infisical', 'run', '--env=dev', '--',
        sys.executable, __file__
    ]
    
    # Execute with Infisical (from repo root where .infisical.json is)
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir.parent)
    os.execvp('infisical', infisical_cmd)

# Check if we need to restart with Infisical
if __name__ == "__main__" and not os.getenv("INFISICAL_PROJECT_ID") and check_infisical_cli():
    restart_with_infisical()

# If we get here, either we're running with Infisical or it's not available
from app.main import app

# This is the entry point for Gunicorn
# Run with: gunicorn main:app

if __name__ == "__main__":
    # For local development only
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
