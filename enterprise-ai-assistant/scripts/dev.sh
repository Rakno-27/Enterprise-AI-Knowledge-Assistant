#!/usr/bin/env bash
echo "========================================="
echo " Starting Enterprise AI Assistant System"
echo "========================================="

# Start backend in background
echo "[1/2] Starting FastAPI Backend on http://localhost:8000..."
cd backend && python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend in background
echo "[2/2] Starting Next.js Frontend on http://localhost:3000..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo "Services started! Press Ctrl+C to terminate."
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
