"""
Haven AI - Backend Application
Entry point for Gunicorn deployment
"""

from app.main import app

# This is the entry point for Gunicorn
# Run with: gunicorn main:app

if __name__ == "__main__":
    # For local development only
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
