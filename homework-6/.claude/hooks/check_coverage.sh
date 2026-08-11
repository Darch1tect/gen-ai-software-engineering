#!/usr/bin/env bash
# Claude Code PreToolUse hook: blocks `git push` attempts when unit test coverage
# for agents/ and integrator.py is below 80%.
#
# Reads the PreToolUse JSON payload on stdin ({"tool_name": "Bash", "tool_input":
# {"command": "..."}, ...}), only acts when the command looks like a git push, and
# otherwise exits 0 immediately so it never interferes with unrelated Bash calls.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

INPUT_JSON="$(cat)"
COMMAND="$(printf '%s' "$INPUT_JSON" | python3 -c "
import json, sys
try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}
print(payload.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")"

case "$COMMAND" in
  *"git push"*) ;;
  *) exit 0 ;;
esac

PY="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "check_coverage.sh: no .venv found at $PROJECT_ROOT/.venv — cannot verify coverage, blocking push to be safe." >&2
    exit 2
fi

OUTPUT_FILE="$(mktemp)"
trap 'rm -f "$OUTPUT_FILE"' EXIT

cd "$PROJECT_ROOT"
if ! "$PY" -m pytest --cov=agents --cov=integrator --cov-report=term-missing --cov-fail-under=80 -q \
    > "$OUTPUT_FILE" 2>&1; then
    echo "Coverage gate FAILED — push blocked (required: 80%)." >&2
    tail -n 15 "$OUTPUT_FILE" >&2
    exit 2
fi

echo "Coverage gate passed (>= 80%) — push allowed." >&2
tail -n 5 "$OUTPUT_FILE" >&2
exit 0
