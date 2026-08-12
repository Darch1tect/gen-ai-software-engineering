# Multi-Agent Banking Transaction Processing Pipeline Specification

> Ingest the information in this file, implement the Low-Level Tasks, and generate the code that
> will satisfy the High and Mid-Level Objectives.

## High-Level Objective

Process a batch of raw bank transactions through a chain of cooperating file-based agents —
validation, fraud scoring, compliance review, and settlement — producing an auditable, per-
transaction result and a pipeline summary report.

## Mid-Level Objectives

- Every transaction is validated for required fields, a parseable non-zero `Decimal` amount, and
  an ISO 4217 currency code before any further processing; invalid transactions are rejected
  immediately with a reason.
- Transactions with an amount over 10,000 (major units, in their own currency) are flagged for
  fraud review and carry a numeric risk score (0-100) built from value, timing, and cross-border
  heuristics.
- Fraud and compliance thresholds are configurable via `rules.yaml`, loaded and stamped onto each
  transaction by a dedicated Rule Engine agent — changing a threshold never requires a code change.
- Transactions are screened against a compliance policy (sanctioned-country denylist, structuring
  detection just under the $10,000 reporting threshold, disallowed transaction types) before
  settlement.
- Every rejected transaction is written to `shared/results/` with an explicit `reason` field; every
  processed transaction (settled or rejected) is written there too, so `shared/results/` is a
  complete record of the batch.
- All agent operations are logged to an append-only audit trail with ISO 8601 timestamps, the
  acting agent's name, the transaction ID, and the outcome — account numbers are masked to their
  last 4 characters and no full account number or name is ever written in plaintext.

## Implementation Notes

- **Monetary values**: always parsed and compared as `decimal.Decimal`; JSON in/out keeps amounts
  as strings to avoid float round-tripping. Never use `float` for money.
- **Currency codes**: validated against a fixed ISO 4217 allow-list (`USD`, `EUR`, `GBP`, `JPY`,
  `CHF`, `CAD`, `AUD`, and other common codes). Unknown codes (e.g. `XYZ`) are rejected by the
  Transaction Validator.
- **Fraud threshold simplification**: the $10,000 high-value threshold is applied to the raw major-
  unit amount in the transaction's own currency, with no FX conversion. This is a deliberate
  simplification for this capstone, not a production-grade rule — documented here so it isn't
  mistaken for an oversight.
- **Logging**: every agent writes one audit-log line (JSON) per transaction it touches to
  `shared/results/audit.log`, with fields `timestamp` (ISO 8601, UTC), `agent`, `transaction_id`,
  and `outcome`. No PII (full account numbers, names) is ever placed in log lines.
- **PII handling**: `source_account` / `destination_account` are treated as sensitive. Any account
  number that must appear in a log line or audit entry is masked to `***<last 4 chars>`. Full
  values may still appear in the per-transaction JSON result file in `shared/results/`, since that
  file plays the role of a compliance record, not a log stream.
- **Message protocol**: agents communicate exclusively via JSON files moved between
  `shared/{input,processing,output,results}/`, using the standard envelope
  (`message_id`, `timestamp`, `source_agent`, `target_agent`, `message_type`, `data`) defined in
  `TASKS.md`.
- **Rule configuration**: `rules.yaml` is the single source of truth for fraud/compliance
  thresholds. Agents thread the loaded config through the pipeline as an internal `_rules` key on
  the transaction dict; any key prefixed with `_` is stripped (`messaging.strip_internal`) before a
  result is persisted to `shared/results/` or returned from the API, so the full rule set never
  leaks into a compliance record.

## Context

### Beginning context
- `sample-transactions.json` — 8 raw transaction records (transfers, wire transfers, a refund),
  including deliberately awkward cases: a non-ISO currency (`XYZ`, TXN006), a negative-amount
  refund (TXN007), and an amount just under the $10,000 reporting threshold (`9999.99`, TXN003).
- No pipeline code exists yet.

### Ending context
- `agents/messaging.py`, `agents/transaction_validator.py`, `agents/rule_engine.py`,
  `agents/fraud_detector.py`, `agents/compliance_checker.py`, `agents/settlement_processor.py`,
  `agents/pipeline.py` (shared per-transaction chain), `agents/results_query.py` (shared read
  queries), `integrator.py`, `rules.yaml`, `api/app.py` (REST gateway), `demo.sh`.
- `shared/results/` populated with one JSON result per input transaction plus
  `shared/results/summary.json` (a pipeline run summary: counts by status, totals, timestamp) and
  `shared/results/audit.log`.
- `mcp/server.py` — a FastMCP server exposing the pipeline's results to MCP clients.
- `tests/` with unit tests per agent and one integration test, at ≥90% coverage (gate: 80%).

## Low-Level Tasks

### 1. Message bus / shared helpers

Task: Messaging helpers
Prompt: "Create a shared messaging module for the banking pipeline agents. It must write and read
the standard JSON message envelope (message_id, timestamp, source_agent, target_agent,
message_type, data) to/from shared/{input,processing,output,results}/, generate ISO 8601 UTC
timestamps, mask account numbers to their last 4 characters, and append JSON-line audit records to
shared/results/audit.log."
File to CREATE: `agents/messaging.py`
Function to CREATE: `write_message(directory: Path, message: dict) -> Path`,
`read_messages(directory: Path) -> list[dict]`, `mask_account(account: str) -> str`,
`log_audit(agent: str, transaction_id: str, outcome: str) -> None`
Details: No transaction_type/business logic here — this module only knows about file I/O,
timestamps, masking, and audit logging, so every agent below can reuse it without duplicating
those concerns.

### 2. Transaction Validator

Task: Transaction Validator
Prompt: "Create the Transaction Validator agent. It must reject a transaction if any required
field is missing (transaction_id, timestamp, source_account, destination_account, amount,
currency, transaction_type), if amount does not parse as a non-zero Decimal (negative only
allowed when transaction_type == 'refund'), or if currency is not in the ISO 4217 allow-list.
Valid transactions get status 'validated' and move to the fraud detector; invalid ones are written
directly to shared/results/ with status 'rejected' and a reason."
File to CREATE: `agents/transaction_validator.py`
Function to CREATE: `validate_transaction(data: dict) -> dict`
Details: Returns a result dict with `status` ('validated' | 'rejected') and, when rejected, a
`reason` string. Must not raise on malformed input — always returns a structured result.

### 3. Rule Engine

Task: Rule Engine
Prompt: "Create the Rule Engine agent. It must load and validate rules.yaml (version, fraud.*,
compliance.* keys — raising a clear error on a missing file, invalid YAML, or missing required
keys) and, as a pipeline stage, stamp the loaded rule set onto the transaction (status
'rules_applied', rules_version, and an internal _rules key) so downstream agents read thresholds
from config instead of hardcoded constants."
File to CREATE: `agents/rule_engine.py`
Function to CREATE: `load_rules(path: Path | None = None) -> dict`,
`apply_rule_engine(data: dict, rules: dict | None = None) -> dict`
Details: `load_rules()` with no argument reads `rules.yaml` at the project root; a custom path is
accepted so tests can exercise malformed-config error paths without touching the real file.

### 4. Fraud Detector

Task: Fraud Detector
Prompt: "Create the Fraud Detector agent. It must compute a risk score 0-100 from three factors:
high value (amount > threshold in the transaction's own currency), unusual timing (configurable
UTC hour window), and a currency/country mismatch heuristic (comparing currency's typical home
country to metadata.country) — all thresholds/weights read from data['_rules']['fraud'] (falling
back to loading rules.yaml directly if absent, so the agent stays independently callable). Score
at or above the configured 'high' band or high-value sets risk_level 'high' and flags the
transaction for review; otherwise 'low' or 'medium'. Never rejects a transaction outright — always
passes it on to the compliance checker with the score attached."
File to CREATE: `agents/fraud_detector.py`
Function to CREATE: `score_transaction(data: dict) -> dict`
Details: Returns the input data merged with `risk_score`, `risk_level`, and `risk_factors` (list
of triggered heuristic names) for downstream agents and the final result record.

### 5. Compliance Checker

Task: Compliance Checker
Prompt: "Create the Compliance Checker agent. It must reject (status 'rejected', with reason) any
transaction whose metadata.country is on the configured sanctioned-country denylist, or whose
transaction_type is not in the configured allowed set — read from data['_rules']['compliance']
(falling back to loading rules.yaml directly if absent). It must flag (not reject) structuring risk
when the amount is within the configured band below the configured reporting threshold. Everything
else passes through with status 'compliance_cleared'."
File to CREATE: `agents/compliance_checker.py`
Function to CREATE: `check_compliance(data: dict) -> dict`
Details: Denylist, allowed transaction types, and thresholds all come from `rules.yaml` via the
Rule Engine agent so tests can inject a custom rule set and exercise both the pass and reject
paths deterministically without editing the real config file.

### 6. Settlement Processor

Task: Settlement Processor
Prompt: "Create the Settlement Processor agent, the final pipeline stage. It must mark every
transaction that reached it (i.e. was not rejected upstream) as 'settled', write one JSON result
file per transaction to shared/results/{transaction_id}.json, and after all transactions in a run
are processed, write shared/results/summary.json with counts by status, total settled amount per
currency, and a run timestamp."
File to CREATE: `agents/settlement_processor.py`
Function to CREATE: `settle_transaction(data: dict) -> dict`, `write_summary(results: list[dict]) -> dict`
Details: `write_summary` is what backs the MCP `pipeline://summary` resource, so its output shape
must be stable and self-describing (include a `generated_at` timestamp).

### 7. Pipeline chain + Integrator / Orchestrator

Task: Pipeline chain + Integrator
Prompt: "Extract the per-transaction stage chain into a single reusable function so both the batch
orchestrator and any future entry point (e.g. a REST API) share it. Create the orchestrator that
ties the five agents together via that function. It must ensure the
shared/{input,processing,output,results} directories exist, load sample-transactions.json into
shared/input/ as standard-envelope messages, run each transaction through
validator -> rule engine -> fraud detector -> compliance checker -> settlement processor in order,
and print a run summary (counts by final status) to stdout."
File to CREATE: `agents/pipeline.py`, `integrator.py`
Function to CREATE: `process_transaction(data: dict, rules: dict | None = None, audit_log: Path | None = None) -> dict`,
`run_pipeline(input_file: Path = Path("sample-transactions.json")) -> dict`
Details: Must be safely re-runnable (clears/rewrites `shared/input,processing,output` between
runs) and must be importable by both `tests/test_integration_pipeline.py` and
`.claude/commands/run-pipeline.md`'s instructions without side effects at import time.

### 8. Custom MCP server

Task: Pipeline status MCP server
Prompt: "Create a FastMCP server exposing the banking pipeline's results: a get_transaction_status
tool that looks up one transaction by ID in shared/results/, a list_pipeline_results tool that
summarizes every processed transaction, and a pipeline://summary resource that returns
shared/results/summary.json as text."
File to CREATE: `mcp/server.py`
Function to CREATE: `get_transaction_status(transaction_id: str) -> dict`,
`list_pipeline_results() -> list[dict]`, `pipeline_summary() -> str`
Details: Read-only against `shared/results/` — the MCP server never writes to the pipeline's
shared directories, it only queries what the agents already produced.

### 9. REST API gateway

Task: REST API gateway
Prompt: "Create a FastAPI app wrapping the pipeline behind HTTP endpoints: GET /health,
POST /transactions (submit and synchronously process one transaction through
agents/pipeline.py::process_transaction, 201 with status settled/rejected either way — a
business rejection is not an HTTP error), GET /transactions/{id} (404 if unknown),
GET /transactions (list all results), and POST /pipeline/run (batch-run
sample-transactions.json via integrator.run_pipeline). Reuse agents/results_query.py for reads
so this doesn't duplicate mcp/server.py's query logic."
File to CREATE: `api/app.py`
Function to CREATE: `submit_transaction(data: dict) -> dict`, `get_transaction(transaction_id: str) -> dict`,
`list_transactions() -> list[dict]`, `run_full_pipeline() -> dict`
Details: The shared/ root is an injectable FastAPI dependency (`get_shared_root`) so
`tests/test_api.py` can isolate every test against a `tmp_path` instead of the real `shared/`
tree, matching the isolation pattern already used for `tests/test_integration_pipeline.py`.
