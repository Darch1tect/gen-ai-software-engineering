# Multi-Agent Banking Transaction Processing Pipeline

Created by **Vitalii Roditieliev** — Homework 6 capstone, gen-ai-software-engineering course.

## What this is

This project processes a batch of raw bank transactions (`sample-transactions.json`) through a
chain of four cooperating agents — validation, fraud scoring, compliance review, and settlement —
that communicate exclusively by passing JSON message files through a shared `shared/` directory
tree. Each transaction ends up as an auditable JSON record in `shared/results/`, alongside a
pipeline summary report and a masked-PII audit log.

The pipeline is also queryable: a custom [FastMCP](https://gofastmcp.com) server
(`mcp/server.py`) exposes the latest results to any MCP client (including Claude Code itself, via
`mcp.json`), and two Claude Code slash commands (`/run-pipeline`, `/validate-transactions`) drive
the pipeline interactively. A coverage-gate hook blocks `git push` whenever unit test coverage for
the core pipeline logic drops below 80%.

## Agent responsibilities

- **Transaction Validator** (`agents/transaction_validator.py`) — rejects a transaction if a
  required field is missing, the amount doesn't parse as a non-zero `Decimal` (negative only
  allowed for refunds), or the currency isn't a recognized ISO 4217 code.
- **Fraud Detector** (`agents/fraud_detector.py`) — scores every validated transaction 0-100 for
  risk based on high value (>$10,000), unusual timing (00:00-05:00 UTC), and a cross-border
  currency/country heuristic; never rejects on its own, always passes the score downstream.
- **Compliance Checker** (`agents/compliance_checker.py`) — rejects transactions from a sanctioned
  country or with a disallowed transaction type, and flags (without rejecting) amounts sitting
  just under the $10,000 reporting threshold as possible structuring.
- **Settlement Processor** (`agents/settlement_processor.py`) — finalizes every non-rejected
  transaction as `settled`, writes each transaction's result to `shared/results/`, and produces
  the run's `summary.json`.
- **Integrator** (`integrator.py`) — the orchestrator: loads `sample-transactions.json`, drives
  every transaction through the four agents in order, and prints a run summary.

Beyond the pipeline itself, this repo was built by four **meta-agents** per the assignment: a
specification agent (`specification.md` + the `/write-spec` skill), this code-generation agent,
a testing agent (`tests/` + the coverage-gate hook), and a documentation agent (this README +
`HOWTORUN.md`).

## Architecture

```
sample-transactions.json
          │
          ▼
   ┌──────────────┐        shared/input/*.json
   │  integrator   │───────────────────────────┐
   │ (orchestrator)│                            │
   └──────────────┘                            ▼
                                    ┌───────────────────────┐
                                    │  Transaction Validator │
                                    └───────────┬───────────┘
                                     rejected │  │ validated
                                              │  ▼
                                    ┌───────────────────────┐
                                    │     Fraud Detector     │
                                    └───────────┬───────────┘
                                                 │ risk_scored
                                                 ▼
                                    ┌───────────────────────┐
                                    │   Compliance Checker   │
                                    └───────────┬───────────┘
                                     rejected │  │ compliance_cleared
                                              │  ▼
                                    ┌───────────────────────┐
                                    │  Settlement Processor  │
                                    └───────────┬───────────┘
                                                 ▼
                                     shared/results/*.json
                                     shared/results/summary.json
                                     shared/results/audit.log
                                                 │
                                                 ▼
                                    ┌───────────────────────┐
                                    │  mcp/server.py (FastMCP)│
                                    │  get_transaction_status │
                                    │  list_pipeline_results  │
                                    │  pipeline://summary     │
                                    └───────────────────────┘
```

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 (`.venv`) |
| Money handling | `decimal.Decimal` (never `float`) |
| Agent messaging | JSON files over `shared/{input,processing,output,results}/` |
| Testing | `pytest` + `pytest-cov` |
| Coverage gate | Claude Code `PreToolUse` hook (`.claude/hooks/check_coverage.sh`) |
| MCP servers | `context7` (npx) + custom `pipeline-status` (`fastmcp`) |
| AI workflow | Claude Code skills (`/write-spec`, `/run-pipeline`, `/validate-transactions`) |

## Project layout

```
homework-6/
├── specification.md, agents.md      # Agent 1 output
├── integrator.py, agents/, mcp/     # Agent 2 output
├── research-notes.md                # context7 queries used while building Agent 2
├── .claude/commands/, .claude/hooks/, tests/   # Agent 3 output
├── README.md, HOWTORUN.md, docs/screenshots/   # Agent 4 output
└── shared/                          # runtime message bus (contents gitignored)
```

See [HOWTORUN.md](HOWTORUN.md) for step-by-step setup and demo instructions.
