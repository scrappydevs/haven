#!/bin/bash
# Start script for backend with Infisical CLI
# This injects secrets from Infisical without needing credentials

# Check if Infisical CLI is available
if command -v infisical &> /dev/null; then
    echo "✅ Infisical CLI found, injecting secrets..."
    # Run with Infisical CLI (auto-detects .infisical.json in repo)
    exec infisical run --env=prod -- gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120
else
    echo "⚠️  Infisical CLI not found, using environment variables..."
    # Fallback to environment variables
    exec gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120
fi

