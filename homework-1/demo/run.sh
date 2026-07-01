#!/usr/bin/env bash
# Start the Transactions API: creates/activates a venv, installs dependencies,
# then runs the server with auto-reload.
#
# Usage:
#   ./run.sh            # starts on port 8000
#   PORT=8080 ./run.sh   # starts on a custom port
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="venv"
PORT="${PORT:-8000}"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing dependencies ..."
pip install -q -r requirements.txt

echo
echo "Starting Transactions API on http://127.0.0.1:$PORT"
echo "Docs (Swagger UI): http://127.0.0.1:$PORT/docs"
echo "Press Ctrl+C to stop."
echo

exec uvicorn src.app:app --reload --port "$PORT"
