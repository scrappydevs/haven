#!/bin/bash
# Start backend with virtual environment
# Usage: ./start_backend.sh

cd "$(dirname "$0")"
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting TrialSentinel backend..."
echo "📍 Server will be available at http://localhost:8000"
echo "📚 API docs at http://localhost:8000/docs"
echo ""

python main.py

