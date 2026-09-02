#!/usr/bin/env bash
# Avvia backend (FastAPI) e frontend (Vite) insieme, raggiungibili anche da
# altri dispositivi sulla stessa rete locale (utile per usare l'app da
# tablet/telefono durante l'asta dal vivo).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
  echo "Creo il virtualenv del backend..."
  python3 -m venv "$SCRIPT_DIR/backend/venv"
  "$SCRIPT_DIR/backend/venv/bin/pip" install -q --upgrade pip
  "$SCRIPT_DIR/backend/venv/bin/pip" install -q -r "$SCRIPT_DIR/backend/requirements.txt"
fi

if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
  echo "Installo le dipendenze del frontend..."
  (cd "$SCRIPT_DIR/frontend" && npm install)
fi

trap 'kill 0' EXIT

(cd "$SCRIPT_DIR/backend" && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &
(cd "$SCRIPT_DIR/frontend" && npm run dev -- --host) &

wait
