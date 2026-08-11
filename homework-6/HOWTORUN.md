# How to Run

All commands below assume your shell's working directory is this `homework-6/` folder.

## 1. Set up the environment

The pipeline and MCP server need Python ≥3.10 (`fastmcp` requires it). This project was built
against Homebrew's `python@3.12`:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. Run the pipeline

```bash
.venv/bin/python integrator.py
```

Expected output: `Pipeline run complete: 8 transactions processed`, with a per-status count and
the path to `shared/results/`. Every transaction from `sample-transactions.json` gets a JSON file
in `shared/results/`, plus `summary.json` (run totals) and `audit.log` (append-only, masked
account numbers only).

To inspect a single result:

```bash
cat shared/results/TXN003.json   # near-threshold amount -> flagged for structuring, still settled
cat shared/results/TXN006.json   # invalid currency "XYZ" -> rejected
cat shared/results/summary.json
```

## 3. Run the tests and check coverage

```bash
.venv/bin/python -m pytest --cov=agents --cov=integrator --cov-report=term-missing
```

Expect 31 tests passing at ~98% coverage (gate: 80%, target: ≥90%).

## 4. Try the coverage-gate hook

This is a Claude Code `PreToolUse` hook (`.claude/settings.json` → `.claude/hooks/check_coverage.sh`)
that fires whenever Claude Code is about to run a `git push` command via its Bash tool, and blocks
the push if coverage is below 80%. To see it fire **inside an interactive Claude Code session**,
just ask Claude to run `git push` from this repo — with the test suite in place, coverage is ~98%
so the hook allows it (prints "Coverage gate passed" to stderr, visible in the tool-call output);
if you temporarily rename/delete a test file to drop coverage below 80% and ask Claude to push
again, the hook blocks it (exit code 2, "Coverage gate FAILED — push blocked").

You can also exercise the hook script directly, without any real `git push`, by feeding it a
synthetic payload on stdin (this is how it was verified while building this project — no real
push to `origin` was made):

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin homework-6-submission"}}' \
  | .claude/hooks/check_coverage.sh; echo "exit code: $?"
```

## 5. Use the Claude Code skills

From an interactive Claude Code session with this directory open:

- `/run-pipeline` — clears `shared/`, runs `integrator.py`, and reports a results table plus any
  rejected transactions with their reasons.
- `/validate-transactions` — dry-run: validates every transaction in `sample-transactions.json`
  without running fraud detection, compliance, or settlement, and without touching `shared/`.
- `/write-spec` — regenerates `specification.md` from the template if the pipeline changes.

## 6. Query the pipeline via MCP

`mcp.json` configures two servers: `context7` (library docs, via `npx`) and `pipeline-status`
(this project's own FastMCP server, via `.venv/bin/python mcp/server.py`). With an MCP-aware
client (Claude Code, or any MCP client pointed at `mcp.json`), after running the pipeline at least
once you can call:

- `get_transaction_status(transaction_id="TXN002")` — full result for one transaction
- `list_pipeline_results()` — compact summary of every processed transaction
- resource `pipeline://summary` — the latest run's summary as text

To sanity-check the server manually without a full MCP client:

```bash
.venv/bin/python -c "
from fastmcp import Client
import asyncio

async def main():
    async with Client('mcp/server.py') as client:
        print(await client.call_tool('get_transaction_status', {'transaction_id': 'TXN002'}))

asyncio.run(main())
"
```

## 7. Clean up / re-run

`integrator.py` is safely re-runnable: it clears and rebuilds `shared/{input,processing,output}`
and `shared/results/*.json` on every run, but **never truncates** `shared/results/audit.log`
(the audit trail is meant to be durable across runs). To fully reset, delete `shared/results/`
and re-run `integrator.py`.
