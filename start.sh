#!/bin/bash
# Haven AI - Unified Startup Script
# Starts both backend and frontend with automatic port detection

set -e

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
if [ ! -d "venv" ]; then
  echo -e "${RED}❌ Virtual environment not found${NC}"
  echo -e "${YELLOW}💡 Run: cd backend && python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
  exit 1
fi

source venv/bin/activate
python3 main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to start and write port file
echo -e "${YELLOW}⏳ Waiting for backend to initialize...${NC}"
for i in {1..15}; do
  if [ -f ".port" ]; then
    PORT=$(cat .port)
    echo -e "${GREEN}✅ Backend running on http://localhost:$PORT${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:$PORT/docs${NC}"
    break
  fi
  sleep 1
done

if [ ! -f ".port" ]; then
  echo -e "${RED}❌ Backend failed to start. Check logs:${NC}"
  tail -20 /tmp/backend.log
  exit 1
fi

cd ..
echo ""

# Step 3: Configure Frontend
echo -e "${YELLOW}🔧 Configuring Frontend API URL...${NC}"
cd frontend
node scripts/setup-api-url.js
cd ..
echo ""

# Step 4: Start Frontend
echo -e "${YELLOW}🌐 Starting Frontend Server...${NC}"
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to start
echo -e "${YELLOW}⏳ Waiting for frontend to initialize...${NC}"
for i in {1..15}; do
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend running on http://localhost:3000${NC}"
    break
  fi
  sleep 1
done

cd ..
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 🎉 Haven AI is Running!                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📡 Frontend:${NC}  http://localhost:3000"
echo -e "${GREEN}🔌 Backend:${NC}   http://localhost:$PORT"
echo -e "${GREEN}📚 API Docs:${NC}  http://localhost:$PORT/docs"
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

# Show logs
tail -f /tmp/backend.log /tmp/frontend.log
