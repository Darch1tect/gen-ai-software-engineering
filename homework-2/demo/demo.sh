#!/usr/bin/env bash
# End-to-end demo of the Intelligent Customer Support System.
# Starts its own server on a throwaway database, walks through the full
# feature set, and cleans up after itself. Requirements: uv, curl, python3.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT=8030
BASE="http://127.0.0.1:$PORT"
DB="$ROOT/demo/.demo.db"
SERVER_PID=""

cleanup() {
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
    rm -f "$DB"
}
trap cleanup EXIT

say()  { printf '\n════ %s ════\n' "$1"; }
json() { python3 -m json.tool; }
field() { python3 -c "import json,sys; print(json.load(sys.stdin)[\"$1\"])"; }

rm -f "$DB"
say "Starting server on port $PORT (throwaway DB)"
DATABASE_URL="sqlite:///$DB" uv run uvicorn app.main:app --port "$PORT" >/dev/null 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 40); do
    curl -sf "$BASE/health" >/dev/null && break || sleep 0.25
done
curl -sf "$BASE/health" >/dev/null || { echo "server failed to start"; exit 1; }
echo "server is up: $(curl -s "$BASE/health")"

say "1. Create a single ticket (as if from a web form)"
TICKET_JSON=$(curl -s -X POST "$BASE/tickets" -H 'Content-Type: application/json' -d '{
  "customer_id": "CUST-DEMO-1",
  "customer_email": "olena@example.com",
  "customer_name": "Olena K",
  "subject": "Cannot access my account since yesterday",
  "description": "My password is rejected and the 2FA code never arrives. This is urgent, I am locked out.",
  "metadata": {"source": "web_form", "browser": "Chrome 126", "device_type": "desktop"}
}')
echo "$TICKET_JSON" | json
TICKET_ID=$(echo "$TICKET_JSON" | field id)

say "2. Auto-classify it — note the reasoning, keywords and confidence"
curl -s -X POST "$BASE/tickets/$TICKET_ID/auto-classify" | json

say "3. Bulk import 50 tickets from CSV with auto-classification"
curl -s -X POST "$BASE/tickets/import?auto_classify=true" \
     -F 'file=@samples/sample_tickets.csv' \
    | python3 -c 'import json,sys; s=json.load(sys.stdin); print("total=%s  successful=%s  failed=%s" % (s["total_records"], s["successful"], s["failed"]))'

say "4. Import a file with broken records — per-record error reporting"
curl -s -X POST "$BASE/tickets/import" -F 'file=@samples/invalid/invalid_tickets.json' | json

say "5. A malformed file never crashes the API"
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/tickets/import" \
     -F 'file=@samples/invalid/malformed.xml'

say "6. Filtering: urgent tickets first"
curl -s "$BASE/tickets?priority=urgent&limit=5" \
    | python3 -c 'import json,sys; [print("- [%s] %s  (%s)" % (t["priority"], t["subject"], t["category"])) for t in json.load(sys.stdin)]'

say "7. Combined filter: medium-priority billing questions"
curl -s "$BASE/tickets?category=billing_question&priority=medium&limit=5" \
    | python3 -c 'import json,sys; [print("- [%s] %s" % (t["priority"], t["subject"])) for t in json.load(sys.stdin)]'

say "8. A human disagrees: manual override of category and priority"
curl -s -X PUT "$BASE/tickets/$TICKET_ID" -H 'Content-Type: application/json' \
     -d '{"category": "technical_issue", "priority": "high"}' \
    | python3 -c 'import json,sys; t=json.load(sys.stdin); print("category=%s  priority=%s  source=%s  confidence=%s" % (t["category"], t["priority"], t["classification_source"], t["classification_confidence"]))'

say "9. The audit log remembers every decision — auto and manual"
curl -s "$BASE/tickets/$TICKET_ID/classification-log" \
    | python3 -c 'import json,sys; [print("#%s [%s] %s/%s conf=%s\n    %s" % (e["id"], e["source"], e["category"], e["priority"], e["confidence"], e["reasoning"][:120])) for e in json.load(sys.stdin)]'

say "Demo finished — server stopped, throwaway DB removed"
