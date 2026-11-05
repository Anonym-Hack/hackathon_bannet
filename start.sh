#!/usr/bin/env bash
set -e

echo "========================================================"
echo "       ReSource AI - Industrial Waste Exchange"
echo "        Circular Economy & AI Matching Platform"
echo "========================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Check/create .env
if [ ! -f ".env" ]; then
    echo "[1/4] Creating .env from .env.example..."
    cp ".env.example" ".env"
else
    echo "[1/4] .env configuration detected."
fi

# 2. Python Virtual Environment
echo "[2/4] Setting up backend Python virtual environment..."
if [ ! -f "backend/venv/bin/python" ]; then
    python3 -m venv backend/venv
fi

backend/venv/bin/pip install -r backend/requirements.txt --quiet

# 3. Frontend packages
echo "[3/4] Checking frontend node_modules..."
if [ ! -d "frontend/node_modules" ]; then
    cd frontend && npm install && cd ..
fi

# 4. Start Servers
echo "[4/4] Starting ReSource AI Servers..."
echo ""
echo "--------------------------------------------------------"
echo " Backend API:  http://localhost:8000/docs"
echo " Frontend Web: http://localhost:3000"
echo "--------------------------------------------------------"
echo ""
echo "Demo Login Credentials:"
echo "  Supplier: supplier@demo.com  (Password: password123)"
echo "  Buyer:    buyer@demo.com     (Password: password123)"
echo ""

export PYTHONPATH="$SCRIPT_DIR/backend"
backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
