#!/bin/bash

echo "================================================================="
echo "🚀 STARTING QUANTNOVA AI - QUANTITATIVE STOCK INTELLIGENCE PLATFORM"
echo "================================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtualenv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
fi

# Start FastAPI REST API Server on Port 8000
echo "--> Starting QuantNova AI Backend API on http://localhost:8000 ..."
PYTHONPATH=. python3 -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Vite React Frontend on Port 5173
echo "--> Starting QuantNova AI Frontend UI on http://localhost:5173 ..."
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo "================================================================="
echo "✨ QuantNova AI Web Platform Running!"
echo "   🌐 Frontend UI Dashboard : http://localhost:5173"
echo "   ⚡ Backend API Server    : http://localhost:8000"
echo "   📝 OpenAPI Swagger Docs  : http://localhost:8000/docs"
echo "================================================================="

wait $BACKEND_PID $FRONTEND_PID
