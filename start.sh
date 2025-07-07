#!/bin/bash

# Start backend server
echo "🔧 Starting FastAPI backend server..."
cd backend
uv run python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend development server
echo "🎨 Starting Vue frontend development server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Terminal Dashboard is starting up!"
echo "📊 Frontend: http://localhost:3003"
echo "🔧 Backend API: http://localhost:8003"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
