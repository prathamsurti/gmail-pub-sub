#!/bin/zsh

# Gmail Pub/Sub - Stop All Services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "${RED}Stopping all services...${NC}"

# Kill processes by PID if .pids file exists
if [ -f ".pids" ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null || true
            echo "${GREEN}✓ Stopped process $pid${NC}"
        fi
    done < .pids
    rm .pids
fi

# Also kill any processes on our ports as backup
for port in 8000 3000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        echo "${GREEN}✓ Freed port $port${NC}"
    fi
done

echo "${GREEN}All services stopped.${NC}"
