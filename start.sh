#!/bin/bash

# This script is now configured for persistent development mode.
# It will expose services to the network by default and use nohup
# to keep servers running after the terminal is closed.
#
# Logs are saved to:
# - backend.log
# - frontend.log

# Default to exposing the network
EXPOSE_NETWORK=true
BACKEND_HOST="0.0.0.0"
FRONTEND_HOST="0.0.0.0"

# Start backend server
echo "🔧 Starting FastAPI backend server (network exposed)..."
echo "🌐 Backend will be accessible from: http://$BACKEND_HOST:8003"

cd backend

# Activate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "📦 Using active Python virtual environment: $VIRTUAL_ENV"
    PYTHON_CMD="python3"
elif [ -d "../.venv" ]; then
    echo "📦 Activating Python virtual environment"
    source ../.venv/bin/activate
    PYTHON_CMD="python"
elif [ -d ".venv" ]; then
    echo "📦 Activating Python virtual environment"
    source .venv/bin/activate
    PYTHON_CMD="python"
elif command -v uv &> /dev/null; then
    echo "📦 Using uv for dependency management"
    PYTHON_CMD="uv run python"
else
    echo "⚠️  Using system Python"
    PYTHON_CMD="python3"
fi

export NETWORK_MODE=true
if [ -d "../.venv" ] || command -v uvicorn &> /dev/null; then
    nohup $PYTHON_CMD -m uvicorn main:app --host $BACKEND_HOST --port 8003 > ../backend.log 2>&1 &
else
    echo "❌ uvicorn not available. Please install dependencies first."
    echo "   Run: pip3 install -r requirements.txt"
    exit 1
fi

# Wait a moment for backend to start
sleep 3

# Start frontend development server
echo "🎨 Starting Vue frontend development server (network exposed)..."
echo "🌐 Frontend will be accessible from: http://$FRONTEND_HOST:3003"

cd ../frontend

# Set API URL for network mode
NETWORK_IP=$(hostname -I | awk '{print $1}')
export VITE_API_URL="http://$NETWORK_IP:8003"
echo "🔗 Frontend configured to use API at: $VITE_API_URL"

nohup npm run dev -- --host $FRONTEND_HOST > ../frontend.log 2>&1 &

echo ""
echo "✅ Terminal Dashboard is starting up in persistent mode!"
echo "📊 Frontend: http://$FRONTEND_HOST:3003 (network accessible)"
echo "🔧 Backend API: http://$BACKEND_HOST:8003 (network accessible)"
echo "📝 Logs are being written to backend.log and frontend.log"
echo "⚠️  Note: Services are exposed to the network. Ensure firewall settings are appropriate."
echo ""
echo "To stop the servers, you will need to manually find and kill the processes."
echo "You can use ps aux | egrep 'uvicorn|vite' to find the PIDs or simply use pkill -f 'uvicorn|vite' to kill all related processes."

