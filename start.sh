#!/bin/bash

# Parse command line arguments
EXPOSE_NETWORK=false
BACKEND_HOST="127.0.0.1"
FRONTEND_HOST="localhost"

while [[ $# -gt 0 ]]; do
    case $1 in
        --network|--expose)
            EXPOSE_NETWORK=true
            BACKEND_HOST="0.0.0.0"
            FRONTEND_HOST="0.0.0.0"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --network, --expose    Expose services to network (0.0.0.0)"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Default: Services run on localhost only"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Start backend server
if [ "$EXPOSE_NETWORK" = true ]; then
    echo "🔧 Starting FastAPI backend server (network exposed)..."
    echo "🌐 Backend will be accessible from: http://$BACKEND_HOST:8003"
else
    echo "🔧 Starting FastAPI backend server (localhost only)..."
fi

cd backend

# Activate virtual environment if it exists
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

if [ "$EXPOSE_NETWORK" = true ]; then
    export NETWORK_MODE=true
    if [ -d "../.venv" ] || command -v uvicorn &> /dev/null; then
        $PYTHON_CMD -m uvicorn main:app --host $BACKEND_HOST --port 8003 &
    else
        echo "❌ uvicorn not available. Please install dependencies first."
        echo "   Run: pip3 install -r requirements.txt"
        exit 1
    fi
else
    export NETWORK_MODE=false
    $PYTHON_CMD main.py &
fi
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend development server
if [ "$EXPOSE_NETWORK" = true ]; then
    echo "🎨 Starting Vue frontend development server (network exposed)..."
    echo "🌐 Frontend will be accessible from: http://$FRONTEND_HOST:3003"
else
    echo "🎨 Starting Vue frontend development server (localhost only)..."
fi

cd ../frontend

# Set API URL for network mode
if [ "$EXPOSE_NETWORK" = true ]; then
    # Get the primary network IP
    NETWORK_IP=$(hostname -I | awk '{print $1}')
    export VITE_API_URL="http://$NETWORK_IP:8003"
    echo "🔗 Frontend configured to use API at: $VITE_API_URL"
fi

if [ "$EXPOSE_NETWORK" = true ]; then
    npm run dev -- --host $FRONTEND_HOST &
else
    npm run dev &
fi
FRONTEND_PID=$!

echo ""
echo "✅ Terminal Dashboard is starting up!"
if [ "$EXPOSE_NETWORK" = true ]; then
    echo "📊 Frontend: http://$FRONTEND_HOST:3003 (network accessible)"
    echo "🔧 Backend API: http://$BACKEND_HOST:8003 (network accessible)"
    echo "⚠️  Note: Services are exposed to the network. Ensure firewall settings are appropriate."
else
    echo "📊 Frontend: http://localhost:3003"
    echo "🔧 Backend API: http://localhost:8003"
    echo "💡 Use --network flag to expose services to network"
fi
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    
    # Deactivate virtual environment if it was activated by this script
    if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" != "${VIRTUAL_ENV_BACKUP:-}" ]; then
        deactivate 2>/dev/null || true
    fi
    
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
