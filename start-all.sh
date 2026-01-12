#!/bin/zsh

# Gmail Pub/Sub - Start All Services
# This script starts the backend, gmail agent, and frontend services

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "${BLUE}================================================${NC}"
echo "${BLUE}  Gmail Pub/Sub - Starting All Services${NC}"
echo "${BLUE}================================================${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "${YELLOW}Warning: backend/.env file not found!${NC}"
    echo "${YELLOW}Please copy backend/.env.example to backend/.env and configure it.${NC}"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "${YELLOW}Port $1 is already in use. Killing the process...${NC}"
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Kill any processes on our ports
echo "${GREEN}Checking for existing processes...${NC}"
check_port 8000  # Backend
check_port 3000  # Frontend

# Create log directory
mkdir -p logs

# Start Backend Server
echo "${GREEN}Starting Backend Server (Port 8000)...${NC}"
cd backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
cd ..

# Wait for backend to be ready
echo "${BLUE}Waiting for backend to be ready...${NC}"
sleep 5
until curl -s http://localhost:8000/docs > /dev/null 2>&1; do
    sleep 1
done
echo "${GREEN}✓ Backend is ready${NC}"

# Start Frontend
echo "${GREEN}Starting Frontend (Port 3000)...${NC}"
cd client

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "${BLUE}Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend in background
nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
cd ..

# Wait for frontend to be ready
echo "${BLUE}Waiting for frontend to be ready...${NC}"
sleep 10
until curl -s http://localhost:3000 > /dev/null 2>&1; do
    sleep 1
done
echo "${GREEN}✓ Frontend is ready${NC}"

# Save PIDs to file for easy shutdown
echo "$BACKEND_PID" > .pids
echo "$FRONTEND_PID" >> .pids

echo ""
echo "${GREEN}================================================${NC}"
echo "${GREEN}  All Services Started Successfully!${NC}"
echo "${GREEN}================================================${NC}"
echo ""
echo "${BLUE}Backend API:${NC}      http://localhost:8000"
echo "${BLUE}API Docs:${NC}         http://localhost:8000/docs"
echo "${BLUE}Frontend:${NC}         http://localhost:3000"
echo ""
echo "${BLUE}Logs:${NC}"
echo "  Backend:  ${SCRIPT_DIR}/logs/backend.log"
echo "  Frontend: ${SCRIPT_DIR}/logs/frontend.log"
echo ""
echo "${YELLOW}To stop all services, run: ./stop-all.sh${NC}"
echo ""

# Open frontend in default browser
if command -v open >/dev/null 2>&1; then
    # macOS
    open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open http://localhost:3000
elif command -v start >/dev/null 2>&1; then
    # Windows (Git Bash/WSL)
    start http://localhost:3000
fi

echo "${GREEN}Opening frontend in your default browser...${NC}"
echo ""

# Keep script running to show logs
echo "${BLUE}Press Ctrl+C to stop watching logs (services will continue running)${NC}"
echo ""
tail -f logs/backend.log logs/frontend.log
