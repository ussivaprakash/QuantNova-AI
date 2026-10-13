#!/bin/bash
set -e

# QuantNova AI - Production Render Startup Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/stock_market_analysis" ]; then
    cd "$SCRIPT_DIR/stock_market_analysis"
else
    cd "$SCRIPT_DIR"
fi

export PORT="${PORT:-8000}"
export HOST="${HOST:-0.0.0.0}"
export PYTHONPATH=".:backend:$PYTHONPATH"

echo "================================================================="
echo "🚀 Starting QuantNova AI Backend on Port $PORT..."
echo "================================================================="

# Run Alembic migrations safely if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "--> Running database migrations..."
    python3 -m alembic -c backend/alembic.ini upgrade head || echo "⚠️ Database migrations pending; continuing in resilient mode."
fi

# Launch Uvicorn ASGI server
echo "--> Launching FastAPI with Uvicorn on $HOST:$PORT..."
exec python3 -m uvicorn backend.api:app --host "$HOST" --port "$PORT"
