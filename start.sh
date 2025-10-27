#!/bin/bash

# Terminal Dashboard Startup Script
#
# Usage:
#   ./start.sh [OPTIONS]
#
# Options:
#   --backend-port PORT    Backend port (default: 8003)
#   --frontend-port PORT   Frontend port (default: 3003)
#   --persistent          Run in persistent mode with nohup (stays running after terminal closes)
#   --network             Expose services to network (default: localhost only)
#   --help                Show this help message
#
# Examples:
#   ./start.sh                                    # Start with defaults (localhost, ports 8003/3003)
#   ./start.sh --persistent                       # Start in persistent mode
#   ./start.sh --network                          # Expose to network
#   ./start.sh --backend-port 8080 --frontend-port 3000
#   ./start.sh --persistent --network --backend-port 8080

# Parse command line arguments
BACKEND_PORT=8003
FRONTEND_PORT=3003
PERSISTENT=false
EXPOSE_NETWORK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --persistent)
            PERSISTENT=true
            shift
            ;;
        --network)
            EXPOSE_NETWORK=true
            shift
            ;;
        --help)
            echo "Terminal Dashboard Startup Script"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend-port PORT    Backend port (default: 8003)"
            echo "  --frontend-port PORT   Frontend port (default: 3003)"
            echo "  --persistent          Run in persistent mode with nohup"
            echo "  --network             Expose services to network"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./start.sh"
            echo "  ./start.sh --persistent"
            echo "  ./start.sh --network"
            echo "  ./start.sh --backend-port 8080 --frontend-port 3000"
            echo "  ./start.sh --persistent --network"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set host based on network exposure
if [ "$EXPOSE_NETWORK" = true ]; then
    BACKEND_HOST="0.0.0.0"
    FRONTEND_HOST="0.0.0.0"
    NETWORK_MODE_TEXT="network exposed"
else
    BACKEND_HOST="127.0.0.1"
    FRONTEND_HOST="127.0.0.1"
    NETWORK_MODE_TEXT="localhost only"
fi

# Print configuration
echo "═══════════════════════════════════════════════════════════"
echo "🚀 Terminal Dashboard Startup"
echo "═══════════════════════════════════════════════════════════"
echo "Configuration:"
echo "  Backend Port:    $BACKEND_PORT"
echo "  Frontend Port:   $FRONTEND_PORT"
echo "  Network Mode:    $NETWORK_MODE_TEXT"
echo "  Persistent:      $PERSISTENT"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Start backend server
echo "🔧 Starting FastAPI backend server..."
echo "🌐 Backend will be accessible from: http://$BACKEND_HOST:$BACKEND_PORT"

cd backend

# Activate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "📦 Using active Python virtual environment: $VIRTUAL_ENV"
    PYTHON_CMD="python"
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

export NETWORK_MODE=$EXPOSE_NETWORK
export BACKEND_PORT=$BACKEND_PORT

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null && [ ! -d "../.venv" ]; then
    echo "❌ uvicorn not available. Please install dependencies first."
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

# Start backend
if [ "$PERSISTENT" = true ]; then
    echo "📝 Running in persistent mode - logs will be saved to ../backend.log"
    nohup $PYTHON_CMD -m uvicorn main:app --host $BACKEND_HOST --port $BACKEND_PORT > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
else
    $PYTHON_CMD -m uvicorn main:app --host $BACKEND_HOST --port $BACKEND_PORT &
    BACKEND_PID=$!
fi

# Wait a moment for backend to start
sleep 3

# Start frontend development server
echo ""
echo "🎨 Starting Vue frontend development server..."
echo "🌐 Frontend will be accessible from: http://$FRONTEND_HOST:$FRONTEND_PORT"

cd ../frontend

# Set API URL based on network mode
if [ "$EXPOSE_NETWORK" = true ]; then
    NETWORK_IP=$(hostname -I | awk '{print $1}')
    export VITE_API_URL="http://$NETWORK_IP:$BACKEND_PORT"
    echo "🔗 Frontend configured to use API at: $VITE_API_URL"
else
    export VITE_API_URL="http://localhost:$BACKEND_PORT"
    echo "🔗 Frontend configured to use API at: $VITE_API_URL"
fi

# Start frontend
if [ "$PERSISTENT" = true ]; then
    echo "📝 Running in persistent mode - logs will be saved to ../frontend.log"
    nohup npm run dev -- --host $FRONTEND_HOST --port $FRONTEND_PORT > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
else
    npm run dev -- --host $FRONTEND_HOST --port $FRONTEND_PORT &
    FRONTEND_PID=$!
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Terminal Dashboard is starting up!"
echo "═══════════════════════════════════════════════════════════"
echo "📊 Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "🔧 Backend API: http://$BACKEND_HOST:$BACKEND_PORT"

if [ "$PERSISTENT" = true ]; then
    echo "📝 Logs: backend.log and frontend.log"
    echo ""
    echo "To stop the servers:"
    echo "  kill $BACKEND_PID $FRONTEND_PID"
    echo "  or use: pkill -f 'uvicorn|vite'"
else
    echo ""
    echo "To stop the servers, press Ctrl+C"
    echo ""
    # Wait for background processes
    wait
fi

echo "═══════════════════════════════════════════════════════════"

