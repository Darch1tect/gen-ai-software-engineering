#!/usr/bin/env bash
# Sample API calls demonstrating every endpoint of the Transactions API.
#
# Prerequisite: the server must already be running, e.g. via ./run.sh in
# this same folder (or `uvicorn src.app:app --reload` from the project root).
#
# Usage:
#   ./sample-requests.sh
#   BASE_URL=http://127.0.0.1:8080 ./sample-requests.sh   # custom host/port
set -uo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_DATA="$SCRIPT_DIR/sample-data.json"

# Pretty-print JSON if a formatter is available, otherwise print as-is.
pretty() {
    if command -v jq >/dev/null 2>&1; then
        jq .
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m json.tool
    else
        cat
    fi
}

step() {
    echo
    echo "=================================================================="
    echo "==> $1"
    echo "=================================================================="
}

# Emit one compact JSON object per line from sample-data.json.
each_sample_payload() {
    if command -v jq >/dev/null 2>&1; then
        jq -c '.[]' "$SAMPLE_DATA"
    else
        python3 -c "
import json
with open('$SAMPLE_DATA') as f:
    for item in json.load(f):
        print(json.dumps(item))
"
    fi
}

step "Health check (GET /)"
curl -s "$BASE_URL/" | pretty

step "Seeding sample transactions from sample-data.json"
LAST_ID=""
while IFS= read -r payload; do
    response=$(curl -s -X POST "$BASE_URL/transactions" \
        -H "Content-Type: application/json" \
        -d "$payload")
    echo "$response" | pretty
    if command -v python3 >/dev/null 2>&1; then
        LAST_ID=$(echo "$response" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
    fi
done < <(each_sample_payload)

step "List all transactions (GET /transactions)"
curl -s "$BASE_URL/transactions" | pretty

step "Filter: only transfers (GET /transactions?type=transfer)"
curl -s "$BASE_URL/transactions?type=transfer" | pretty

step "Filter: by account (GET /transactions?accountId=ACC-00001)"
curl -s "$BASE_URL/transactions?accountId=ACC-00001" | pretty

step "Filter: combined accountId + type + date range"
curl -s "$BASE_URL/transactions?accountId=ACC-00001&type=transfer&from=2020-01-01&to=2030-12-31" | pretty

if [ -n "$LAST_ID" ]; then
    step "Get a single transaction by id (GET /transactions/$LAST_ID)"
    curl -s "$BASE_URL/transactions/$LAST_ID" | pretty
fi

step "Export transactions as CSV (GET /transactions/export)"
curl -s "$BASE_URL/transactions/export"
echo

step "Account balance (GET /accounts/ACC-00001/balance)"
curl -s "$BASE_URL/accounts/ACC-00001/balance" | pretty

step "Account summary (GET /accounts/ACC-00001/summary)"
curl -s "$BASE_URL/accounts/ACC-00001/summary" | pretty

step "Simple interest: 5% annual rate over 30 days (GET /accounts/ACC-00001/interest)"
curl -s "$BASE_URL/accounts/ACC-00001/interest?rate=0.05&days=30" | pretty

step "--- Error examples ---"

step "Invalid amount (negative) -> 400"
curl -s -X POST "$BASE_URL/transactions" \
    -H "Content-Type: application/json" \
    -d '{"toAccount": "ACC-00001", "amount": -10, "currency": "USD", "type": "deposit"}' | pretty

step "Amount with too many decimal places -> 400"
curl -s -X POST "$BASE_URL/transactions" \
    -H "Content-Type: application/json" \
    -d '{"toAccount": "ACC-00001", "amount": 10.999, "currency": "USD", "type": "deposit"}' | pretty

step "Invalid currency code -> 400"
curl -s -X POST "$BASE_URL/transactions" \
    -H "Content-Type: application/json" \
    -d '{"toAccount": "ACC-00001", "amount": 10, "currency": "XXX", "type": "deposit"}' | pretty

step "Invalid account format -> 400"
curl -s -X POST "$BASE_URL/transactions" \
    -H "Content-Type: application/json" \
    -d '{"toAccount": "acc-1", "amount": 10, "currency": "USD", "type": "deposit"}' | pretty

step "Unknown transaction id -> 404"
curl -s "$BASE_URL/transactions/does-not-exist" | pretty

step "Unknown account balance -> 404"
curl -s "$BASE_URL/accounts/ACC-99999/balance" | pretty

step "Done. Re-run with BASE_URL=... to point at a different server."
