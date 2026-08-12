"""Orchestrator for the multi-agent banking transaction pipeline.

Loads sample-transactions.json into shared/input/, then runs each transaction through
transaction_validator -> rule_engine -> fraud_detector -> compliance_checker ->
settlement_processor (agents/pipeline.py::process_transaction), writing one result JSON
per transaction (plus a run summary) to shared/results/.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents import messaging
from agents.pipeline import process_transaction
from agents.rule_engine import load_rules
from agents.settlement_processor import write_summary

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_FILE = PROJECT_ROOT / "sample-transactions.json"
DEFAULT_SHARED_ROOT = PROJECT_ROOT / "shared"


def run_pipeline(input_file: Path = DEFAULT_INPUT_FILE, shared_root: Path = DEFAULT_SHARED_ROOT) -> dict:
    """Run the full pipeline once. Re-runnable: rebuilds input/processing/output/results each call,
    but appends (never truncates) the audit log, since that is meant to be a durable trail."""
    input_file = Path(input_file)
    shared_root = Path(shared_root)

    input_dir = shared_root / "input"
    processing_dir = shared_root / "processing"
    output_dir = shared_root / "output"
    results_dir = shared_root / "results"
    audit_log = results_dir / "audit.log"

    for directory in (input_dir, processing_dir, output_dir, results_dir):
        directory.mkdir(parents=True, exist_ok=True)

    messaging.clear_directory(input_dir)
    messaging.clear_directory(processing_dir)
    messaging.clear_directory(output_dir)
    for result_file in results_dir.glob("*.json"):
        result_file.unlink()

    raw_transactions = json.loads(input_file.read_text())
    for txn in raw_transactions:
        message = messaging.new_message("integrator", "transaction_validator", "transaction", txn)
        messaging.write_message(input_dir, message)

    rules = load_rules()
    results: list[dict] = [
        process_transaction(message["data"], rules=rules, audit_log=audit_log)
        for message in messaging.read_messages(input_dir)
    ]

    for result in results:
        tx_id = result.get("transaction_id") or "unknown"
        (results_dir / f"{tx_id}.json").write_text(json.dumps(result, indent=2, default=str))

    summary = write_summary(results)
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"Pipeline run complete: {len(results)} transactions processed")
    for status, count in summary["counts_by_status"].items():
        print(f"  {status}: {count}")
    print(f"Results written to {results_dir}")

    return summary


if __name__ == "__main__":
    run_pipeline()
