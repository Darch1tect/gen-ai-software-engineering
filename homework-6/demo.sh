#!/usr/bin/env bash
# End-to-end demo, zero manual steps: bootstraps the venv if needed, starts the REST API,
# submits every sample-transactions.json transaction through it, fetches and prints the
# results, then stops the server. See HOWTORUN.md for the equivalent manual steps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${DEMO_PORT:-8811}"
BASE_URL="http://127.0.0.1:${PORT}"
PY="$SCRIPT_DIR/.venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "==> No .venv found — bootstrapping one (Python >= 3.10 required, this only happens once)..."
    PYTHON_BIN=""
    for candidate in python3.13 python3.12 python3.11 python3.10 \
                     /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.13; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PYTHON_BIN="$candidate"
            break
        fi
    done
    if [ -z "$PYTHON_BIN" ]; then
        echo "No Python >= 3.10 found (fastmcp/fastapi require it). Install one (e.g." >&2
        echo "'brew install python@3.12') and re-run ./demo.sh." >&2
        exit 1
    fi
    "$PYTHON_BIN" -m venv .venv
    "$PY" -m pip install -q --upgrade pip
    "$PY" -m pip install -q -r requirements.txt
fi

echo "==> Starting API server on ${BASE_URL} ..."
"$PY" -m uvicorn api.app:app --port "$PORT" --log-level warning &
SERVER_PID=$!
trap 'echo "==> Stopping API server (pid $SERVER_PID)"; kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT

echo "==> Waiting for the server to be ready..."
READY=0
for _ in $(seq 1 40); do
    if curl -sf -o /dev/null "${BASE_URL}/health"; then
        READY=1
        break
    fi
    sleep 0.25
done
if [ "$READY" -ne 1 ]; then
    echo "Server did not become ready in time." >&2
    exit 1
fi
echo "==> Server is ready."
echo

"$PY" - "$BASE_URL" <<'PYEOF'
import json
import sys
import urllib.request

base_url = sys.argv[1]

with open("sample-transactions.json") as f:
    transactions = json.load(f)

print(f"==> Submitting {len(transactions)} transactions via POST {base_url}/transactions ...")
for txn in transactions:
    req = urllib.request.Request(
        f"{base_url}/transactions",
        data=json.dumps(txn).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    reason = result.get("reason", "")
    print(f"  {result.get('transaction_id', '?'):10s} -> {result.get('status', '?'):10s} {reason}")

print()
print(f"==> Fetching results via GET {base_url}/transactions ...")
with urllib.request.urlopen(f"{base_url}/transactions") as resp:
    results = json.loads(resp.read())

print()
header = f"{'ID':12s} {'STATUS':10s} {'CURRENCY':9s} {'AMOUNT':12s} {'RISK':6s}"
print(header)
print("-" * len(header))
for r in results:
    print(
        f"{r.get('transaction_id', ''):12s} {r.get('status', ''):10s} "
        f"{(r.get('currency') or '-'):9s} {(r.get('amount') or '-'):12s} "
        f"{(r.get('risk_level') or '-'):6s}"
    )

settled = sum(1 for r in results if r.get("status") == "settled")
rejected = sum(1 for r in results if r.get("status") == "rejected")
print()
print(f"==> {len(results)} total, {settled} settled, {rejected} rejected.")
PYEOF

echo
echo "==> Demo complete."
