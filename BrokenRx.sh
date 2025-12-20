#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

mkdir -p "$PID_DIR"

echo "[*] Starting BrokenRx stack..."
echo
echo "[*] Initializing main database..."
python3 "$PROJECT_ROOT/models/database.py"

echo "[*] Initializing auth database..."
cd "$PROJECT_ROOT/AuthServer"
python3 "./models/auth_database.py"
cd "$PROJECT_ROOT"

echo "[*] Starting main Flask app..."
python3 "$PROJECT_ROOT/app.py" > "$PID_DIR/app.log" 2>&1 &
echo $! > "$PID_DIR/app.pid"
echo "[*] Starting API server (port 9000)..."
uvicorn api:app --reload --port 9000 > "$PID_DIR/api.log" 2>&1 &
echo $! > "$PID_DIR/api.pid"

echo "[*] Starting Auth Server (port 8000)..."
cd "$PROJECT_ROOT/AuthServer"
uvicorn auth_app:app --reload --port 8000 > "$PID_DIR/auth.log" 2>&1 &
echo $! > "$PID_DIR/auth.pid"

echo "[*] Creating Admin..."
python3 create_admin.py
cd "$PROJECT_ROOT"

echo
echo "[✓] BrokenRx successfully started"
echo "[→] Main App    : http://localhost:5000"
echo "[→] API Server  : http://localhost:9000"
echo "[→] Auth Server : http://localhost:8000"
echo
