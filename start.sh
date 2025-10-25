#!/bin/bash
# Quick start script for local development

echo "🚀 Starting Haven..."

# Start backend with Infisical
echo "📦 Starting backend..."
cd backend
infisical run --env=dev -- python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for user interrupt
echo ""
echo "✅ Haven is running!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop..."

# Handle cleanup
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
