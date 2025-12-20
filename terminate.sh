#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

echo "[*] Stopping BrokenRx stack..."
echo

if [[ ! -d "$PID_DIR" ]]; then
    echo "[!] No PID directory found. Is the stack running?"
    exit 1
fi

for pidfile in "$PID_DIR"/*.pid; do
    [[ -e "$pidfile" ]] || continue

    PID=$(cat "$pidfile")
    NAME=$(basename "$pidfile" .pid)

    if kill -0 "$PID" 2>/dev/null; then
        echo "[*] Stopping $NAME (PID $PID)"
        kill "$PID"
    else
        echo "[!] $NAME already stopped"
    fi
done

sleep 1

for pidfile in "$PID_DIR"/*.pid; do
    PID=$(cat "$pidfile")
    if kill -0 "$PID" 2>/dev/null; then
        echo "[!] Force killing PID $PID"
        kill -9 "$PID"
    fi
done

rm -rf "$PID_DIR"

echo
echo "[✓] BrokenRx stopped cleanly"
echo
