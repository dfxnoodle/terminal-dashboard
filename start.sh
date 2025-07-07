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

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "📦 Using uv for dependency management"
    if [ "$EXPOSE_NETWORK" = true ]; then
        export NETWORK_MODE=true
        uv run uvicorn main:app --host $BACKEND_HOST --port 8003 &
    else
        export NETWORK_MODE=false
        uv run python main.py &
    fi
else
    echo "⚠️  uv not found, using standard Python"
    echo "💡 Consider using ./start-venv.sh for systems without uv"
    
    # Try to use uvicorn directly
    if [ "$EXPOSE_NETWORK" = true ]; then
        export NETWORK_MODE=true
        python3 -m uvicorn main:app --host $BACKEND_HOST --port 8003 &
    else
        export NETWORK_MODE=false
        python3 main.py &
    fi
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
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
