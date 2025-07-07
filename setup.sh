#!/bin/bash

# Terminal Dashboard Setup Script

echo "🚀 Setting up Terminal Dashboard..."

# Backend setup
echo "📦 Setting up Python backend..."
cd backend

# Install dependencies with uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo "Installing Python dependencies..."
uv sync

cd ..

# Frontend setup
echo "🎨 Setting up Vue frontend..."
cd frontend

# Install Node.js dependencies
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

echo "Installing Node.js dependencies..."
npm install

cd ..

echo "✅ Setup complete!"
echo ""
echo "🎯 To start the dashboard:"
echo "1. Backend: cd backend && uv run python main.py"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "📊 Dashboard will be available at: http://localhost:3003"
