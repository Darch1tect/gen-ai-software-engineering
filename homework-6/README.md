# Multi-Agent Banking Transaction Processing Pipeline

Created by **Vitalii Roditieliev** — Homework 6 capstone, gen-ai-software-engineering course.

## What this is

This project processes a batch of raw bank transactions (`sample-transactions.json`) through a
chain of five cooperating agents — validation, configurable rule loading, fraud scoring,
compliance review, and settlement — that communicate exclusively by passing JSON message files
through a shared `shared/` directory tree. Each transaction ends up as an auditable JSON record in
`shared/results/`, alongside a pipeline summary report and a masked-PII audit log.

The pipeline has two ways in beyond the batch orchestrator: a custom
[FastMCP](https://gofastmcp.com) server (`mcp/server.py`) exposes the latest results to any MCP
client (including Claude Code itself, via `mcp.json`), and a [FastAPI](https://fastapi.tiangolo.com)
REST gateway (`api/app.py`) lets any HTTP client submit a transaction or query results —
`./demo.sh` starts the API, submits every sample transaction, and prints the results end to end
with zero manual steps. Two Claude Code slash commands (`/run-pipeline`, `/validate-transactions`)
drive the pipeline interactively, and a coverage-gate hook blocks `git push` whenever unit test
coverage for the core pipeline logic (agents, integrator, API) drops below 80%.

## Agent responsibilities

- **Transaction Validator** (`agents/transaction_validator.py`) — rejects a transaction if a
  required field is missing, the amount doesn't parse as a non-zero `Decimal` (negative only
  allowed for refunds), or the currency isn't a recognized ISO 4217 code.
- **Rule Engine** (`agents/rule_engine.py`) — loads and validates `rules.yaml` (fraud/compliance
  thresholds, weights, denylists) and stamps the active rule set onto the transaction, so
  downstream agents read config instead of hardcoded constants — edit `rules.yaml` to change
  business behavior, no code change needed.
- **Fraud Detector** (`agents/fraud_detector.py`) — scores every validated transaction 0-100 for
  risk based on high value, unusual timing, and a cross-border currency/country heuristic (all
  configurable via `rules.yaml`); never rejects on its own, always passes the score downstream.
- **Compliance Checker** (`agents/compliance_checker.py`) — rejects transactions from a
  configurable sanctioned-country denylist or with a disallowed transaction type, and flags
  (without rejecting) amounts sitting just under the reporting threshold as possible structuring.
- **Settlement Processor** (`agents/settlement_processor.py`) — finalizes every non-rejected
  transaction as `settled`, writes each transaction's result to `shared/results/`, and produces
  the run's `summary.json`.
- **Integrator** (`integrator.py`) — the batch orchestrator: loads `sample-transactions.json`,
  drives every transaction through the 5-stage chain (`agents/pipeline.py::process_transaction`,
  shared with the REST API), and prints a run summary.

Beyond the pipeline itself, this repo was built by four **meta-agents** per the assignment: a
specification agent (`specification.md` + the `/write-spec` skill), this code-generation agent,
a testing agent (`tests/` + the coverage-gate hook), and a documentation agent (this README +
`HOWTORUN.md`).

## Architecture

```
sample-transactions.json    demo.sh / curl / any HTTP client
          │                              │
          ▼                              ▼
   ┌──────────────┐            ┌───────────────────┐
   │  integrator   │            │  api/app.py        │
   │ (orchestrator)│            │  (FastAPI gateway)  │
   └──────┬───────┘            └─────────┬──────────┘
          │        shared/input/*.json    │
          └───────────────┬───────────────┘
                           ▼
                 agents/pipeline.py::process_transaction
                           │
                           ▼
                 ┌───────────────────────┐
                 │  Transaction Validator │
                 └───────────┬───────────┘
                  rejected │  │ validated
                           │  ▼
                 ┌───────────────────────┐        rules.yaml
                 │      Rule Engine       │◄───── (fraud/compliance
                 └───────────┬───────────┘        thresholds, denylists)
                              │ rules_applied
                              ▼
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
              ┌───────────────┴───────────────┐
              ▼                                ▼
   ┌───────────────────────┐       ┌───────────────────────┐
   │ mcp/server.py (FastMCP)│       │  api/app.py (FastAPI)  │
   │  get_transaction_status│       │  GET /transactions/{id}│
   │  list_pipeline_results │       │  GET /transactions     │
   │  pipeline://summary    │       │  POST /pipeline/run    │
   └───────────────────────┘       └───────────────────────┘
```

Both query surfaces read through the same `agents/results_query.py` helpers — no duplicated
read logic.

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 (`.venv`) |
| Money handling | `decimal.Decimal` (never `float`) |
| Agent messaging | JSON files over `shared/{input,processing,output,results}/` |
| Business rules | `rules.yaml` (`PyYAML`), loaded by the Rule Engine agent |
| REST API | `FastAPI` + `uvicorn`; tested via `httpx`/`TestClient` |
| Testing | `pytest` + `pytest-cov` |
| Coverage gate | Claude Code `PreToolUse` hook (`.claude/hooks/check_coverage.sh`) |
| MCP servers | `context7` (npx) + custom `pipeline-status` (`fastmcp`) |
| AI workflow | Claude Code skills (`/write-spec`, `/run-pipeline`, `/validate-transactions`) |
| Demo | `demo.sh` — bootstraps venv, starts the API, submits transactions, prints results |

## Project layout

```
homework-6/
├── specification.md, agents.md          # Agent 1 output
├── integrator.py, agents/, mcp/, api/    # Agent 2 output (+ Task-2 additions)
├── rules.yaml, demo.sh                   # Task-2: configurable rules, one-command demo
├── research-notes.md                     # context7 queries used while building Agent 2
├── .claude/commands/, .claude/hooks/, tests/   # Agent 3 output
├── README.md, HOWTORUN.md, docs/screenshots/   # Agent 4 output
└── shared/                               # runtime message bus (contents gitignored)
```

See [HOWTORUN.md](HOWTORUN.md) for step-by-step setup and demo instructions.
