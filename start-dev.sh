#!/bin/bash

# Miraz — Development Startup Script
# This script starts both the backend and frontend servers for local development

set -e

echo "🕌 Starting Miraz — Al-Quran Re-think"
echo "====================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed."
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Setup backend
echo ""
echo "📦 Setting up backend..."
cd "$SCRIPT_DIR/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "   Installing Python dependencies..."
pip install -r requirements.txt -q

# Check if database exists
if [ ! -f "miraz.db" ]; then
    echo "   Importing Quran data (this may take a moment)..."
    python scripts/import_quran.py
fi

# Start backend server
echo ""
echo "🚀 Starting backend server on http://localhost:8000..."
echo "   API docs: http://localhost:8000/docs"
echo "   Health check: http://localhost:8000/health"
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Setup frontend
echo ""
echo "📦 Setting up frontend..."
cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "   Installing npm dependencies..."
    npm install -q
fi

# Start frontend server
echo ""
echo "🚀 Starting frontend server on http://localhost:5173..."
echo "   The frontend will proxy API requests to http://localhost:8000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Miraz is running!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop all servers"
echo ""

# Wait for background processes
wait
