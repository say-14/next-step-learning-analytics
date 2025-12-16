#!/bin/bash

# 백엔드 + 프론트엔드 동시 실행 스크립트

cd /home/say/pjt/education

# 백엔드 실행 (백그라운드)
echo "Starting backend on http://localhost:8000..."
cd backend
source .venv/bin/activate
python main.py &
BACKEND_PID=$!

# 프론트엔드 실행
echo "Starting frontend on http://localhost:5173..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "==================================="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo "==================================="
echo "Press Ctrl+C to stop both servers"

# Ctrl+C로 둘 다 종료
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
