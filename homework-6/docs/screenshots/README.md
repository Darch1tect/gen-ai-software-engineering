# Screenshots checklist

All 5 required screenshots were captured from a real interactive Claude Code terminal session
(some split across two images where the output was longer than one screen).

| File(s) | What it shows |
|---|---|
| `pipeline-run.png` | Full terminal output of `.venv/bin/python integrator.py` — 8 transactions processed, 7 settled, 1 rejected. |
| `test-coverage.png` | `pytest --cov=agents --cov=integrator --cov-report=term-missing` — 31 tests passed, 98% coverage. |
| `skill-run-pipeline-1.png`, `skill-run-pipeline-2.png` | The `/run-pipeline` slash command executing end-to-end in Claude Code, including the full transaction summary table and rejected-transaction report. |
| `hook-trigger-1.png` | A **live** coverage-gate block: with `tests/` temporarily disabled (coverage at 0%), asking Claude Code to `git push` gets refused by the `PreToolUse` hook before the push runs. |
| `hook-trigger-2.png` | The same gate exercised directly via a synthetic hook payload on stdin, showing exit code 2 and the coverage report. |
| `mcp-interaction-1.png` | A real context7 query result (FastMCP's `@mcp.resource` API). |
| `mcp-interaction-2.png` | A real call to the custom `pipeline-status` MCP server's `get_transaction_status` tool for `TXN002`. |

These same images are embedded in the pull request description, per `TASKS.md`'s submission
checklist.
