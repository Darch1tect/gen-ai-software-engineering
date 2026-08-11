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

## Context

### Beginning context
- `sample-transactions.json` — 8 raw transaction records (transfers, wire transfers, a refund),
  including deliberately awkward cases: a non-ISO currency (`XYZ`, TXN006), a negative-amount
  refund (TXN007), and an amount just under the $10,000 reporting threshold (`9999.99`, TXN003).
- No pipeline code exists yet.

### Ending context
- `agents/messaging.py`, `agents/transaction_validator.py`, `agents/fraud_detector.py`,
  `agents/compliance_checker.py`, `agents/settlement_processor.py`, `integrator.py`.
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

### 3. Fraud Detector

Task: Fraud Detector
Prompt: "Create the Fraud Detector agent. It must compute a risk score 0-100 from three factors:
high value (amount > 10,000 in the transaction's own currency), unusual timing (UTC hour in
00:00-05:00), and a currency/country mismatch heuristic (comparing currency's typical home
country to metadata.country). Score >= 60 or high-value sets risk_level 'high' and flags the
transaction for review; otherwise 'low' or 'medium'. Never rejects a transaction outright — always
passes it on to the compliance checker with the score attached."
File to CREATE: `agents/fraud_detector.py`
Function to CREATE: `score_transaction(data: dict) -> dict`
Details: Returns the input data merged with `risk_score`, `risk_level`, and `risk_factors` (list
of triggered heuristic names) for downstream agents and the final result record.

### 4. Compliance Checker

Task: Compliance Checker
Prompt: "Create the Compliance Checker agent. It must reject (status 'rejected', with reason) any
transaction whose metadata.country is on a small sanctioned-country denylist, or whose
transaction_type is not in the allowed set. It must flag (not reject) structuring risk when the
amount is within $500 of the $10,000 reporting threshold from below. Everything else passes
through with status 'compliance_cleared'."
File to CREATE: `agents/compliance_checker.py`
Function to CREATE: `check_compliance(data: dict) -> dict`
Details: Denylist and allowed transaction types are simple module-level constants so tests can
exercise both the pass and reject paths deterministically.

### 5. Settlement Processor

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

### 6. Integrator / Orchestrator

Task: Integrator
Prompt: "Create the orchestrator that ties the four agents together. It must ensure the
shared/{input,processing,output,results} directories exist, load sample-transactions.json into
shared/input/ as standard-envelope messages, run each transaction through
validator -> fraud detector -> compliance checker -> settlement processor in order, and print a
run summary (counts by final status) to stdout."
File to CREATE: `integrator.py`
Function to CREATE: `run_pipeline(input_file: Path = Path("sample-transactions.json")) -> dict`
Details: Must be safely re-runnable (clears/rewrites `shared/input,processing,output` between
runs) and must be importable by both `tests/test_integration_pipeline.py` and
`.claude/commands/run-pipeline.md`'s instructions without side effects at import time.

### 7. Custom MCP server

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
