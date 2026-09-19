#!/bin/bash

# Miraz — single webapp runner
#   ./start-dev.sh           two-server dev (Vite HMR on :5173 + API on :8000)
#   ./start-dev.sh --single  true single webapp (build UI, serve all on :8000)

set -e

MODE="dev"
if [ "$1" = "--single" ]; then
    MODE="single"
fi

echo "Miraz — QuranLayers (Bengali-integrated) [$MODE]"
echo "================================================="

command -v python3 &> /dev/null || { echo "Python 3 is required but not installed."; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo ""
    echo "Shutting down servers..."
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Setup backend
echo ""
echo "Setting up backend..."
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi
echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing Python dependencies..."
pip install -r requirements.txt -q

FRESH_DB=0
if [ ! -f "miraz.db" ]; then
    FRESH_DB=1
    echo "   Importing Quran data (this may take a while)..."
    python scripts/import_quran.py
fi

# Backfill Bengali layers on a fresh database (fast, local data + APIs)
if [ "$FRESH_DB" = "1" ]; then
    echo "   Seeding Bengali layers..."
    python scripts/seed_bengali.py || true
    python scripts/seed_chapter_context.py || true
    python scripts/derive_root_glosses.py || true
fi

export MIRAZ_DB="$SCRIPT_DIR/backend/miraz.db"

if [ "$MODE" = "single" ]; then
    command -v npm &> /dev/null || { echo "npm is required for --single (frontend build)."; exit 1; }
    echo ""
    echo "Building frontend (same-origin bundle)..."
    cd "$SCRIPT_DIR/frontend"
    [ -d "node_modules" ] || npm install -q
    VITE_API_BASE= npm run build -q
    echo ""
    echo "Starting single webapp on http://localhost:8000 ..."
    echo "   UI:        http://localhost:8000/"
    echo "   API docs:  http://localhost:8000/docs"
    echo "   Health:    http://localhost:8000/health"
    echo ""
    echo "   Press Ctrl+C to stop"
    echo ""
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
    uvicorn app.main:app --host 127.0.0.1 --port 8000
    exit 0
fi

# dev mode: backend API + Vite HMR
command -v node &> /dev/null || { echo "Node.js is required but not installed."; exit 1; }
command -v npm &> /dev/null || { echo "npm is required but not installed."; exit 1; }

echo ""
echo "Starting backend API on http://localhost:8000 ..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 2

echo ""
echo "Setting up frontend..."
cd "$SCRIPT_DIR/frontend"
[ -d "node_modules" ] || { echo "   Installing npm dependencies..."; npm install -q; }

echo ""
echo "Starting frontend on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Miraz is running!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Tip: ./start-dev.sh --single serves everything on :8000"
echo "   Press Ctrl+C to stop all servers"
echo ""

wait
