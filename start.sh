#!/bin/bash
# Haven AI - Unified Startup Script
# Starts both backend and frontend with automatic port detection

echo "🚀 Starting Haven..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Haven AI - Startup Script                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Clean up any existing processes
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
pkill -9 -f "uvicorn\|python.*main\|node.*next" 2>/dev/null || true
for port in 3000 3001 8000 8001 8002 8003; do
  lsof -ti:$port 2>/dev/null | xargs -r kill -9 2>/dev/null || true
done
sleep 2
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Step 2: Start Backend
echo -e "${YELLOW}🚀 Starting Backend Server...${NC}"
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

cd ..
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 🎉 Haven AI is Running!                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📡 Frontend:${NC}  http://localhost:3000"
echo -e "${GREEN}🔌 Backend:${NC}   http://localhost:8000"
echo -e "${GREEN}📚 API Docs:${NC}  http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f /tmp/backend.log"
echo -e "  Frontend: tail -f /tmp/frontend.log"
echo ""
echo -e "${YELLOW}To stop:${NC}"
echo -e "  Kill processes: pkill -f 'uvicorn|node.*next'"
echo -e "  Or: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${GREEN}Press Ctrl+C to view logs (servers will keep running)${NC}"
echo ""

# Handle cleanup
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Show logs
tail -f /tmp/backend.log /tmp/frontend.log
