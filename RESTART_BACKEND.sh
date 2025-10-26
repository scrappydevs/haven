#!/bin/bash

echo "🔄 Restarting Haven Backend..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Activate conda environment
echo "📦 Activating conda environment 'haven'..."
eval "$(conda shell.bash hook)"
conda activate haven

# Kill any existing backend process
echo "🛑 Stopping existing backend..."
pkill -f "uvicorn app.main:app" || echo "   (No existing backend running)"

# Wait a moment
sleep 2

# Start backend
echo "🚀 Starting backend server..."
echo ""
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


