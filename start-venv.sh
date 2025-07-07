#!/bin/bash

# Alternative start script for systems without uv
# Uses standard Python virtual environment instead

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
            echo ""
            echo "Note: This script uses standard Python virtual environment"
            echo "      instead of uv for compatibility"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Python virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "📦 Installing Python dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend server
if [ "$EXPOSE_NETWORK" = true ]; then
    echo "🔧 Starting FastAPI backend server (network exposed)..."
    echo "🌐 Backend will be accessible from: http://$BACKEND_HOST:8003"
    export NETWORK_MODE=true
else
    echo "🔧 Starting FastAPI backend server (localhost only)..."
    export NETWORK_MODE=false
fi

cd backend
if [ "$EXPOSE_NETWORK" = true ]; then
    python -m uvicorn main:app --host $BACKEND_HOST --port 8003 &
else
    python main.py &
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
    deactivate 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
