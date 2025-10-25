"""
TrialSentinel AI - Backend Application
Entry point for Gunicorn deployment
"""

# ✅ SUPPRESS MEDIAPIPE VERBOSE LOGGING - Must be FIRST before any imports
import os
os.environ['GLOG_minloglevel'] = '2'  # Suppress Google's glog INFO/WARNING
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs

from app.main import app

# This is the entry point for Gunicorn
# Run with: gunicorn main:app

if __name__ == "__main__":
    # For local development only
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
