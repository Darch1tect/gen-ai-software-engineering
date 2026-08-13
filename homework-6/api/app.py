"""REST API gateway wrapping the file-based banking pipeline behind HTTP endpoints.

Reuses the same building blocks as the batch orchestrator and the MCP server rather than
duplicating pipeline or query logic:
- agents/pipeline.py::process_transaction — the 5-stage chain for one transaction.
- agents/results_query.py — read-only queries against shared/results/.
- integrator.py::run_pipeline — the full-batch orchestrator, for POST /pipeline/run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status

from agents.pipeline import process_transaction
from agents.results_query import list_results, load_result
from agents.rule_engine import load_rules
from integrator import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SHARED_ROOT = PROJECT_ROOT / "shared"

app = FastAPI(
    title="Banking Pipeline API",
    description="REST gateway over the file-based multi-agent transaction pipeline.",
    version="1.0.0",
)


def get_shared_root() -> Path:
    """FastAPI dependency for the shared/ root. Overridden in tests to isolate from the
    real shared/ tree — see tests/test_api.py."""
    return DEFAULT_SHARED_ROOT


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/transactions", status_code=status.HTTP_201_CREATED)
def submit_transaction(data: dict[str, Any], shared_root: Path = Depends(get_shared_root)) -> dict:
    """Submit and immediately process one transaction through all 5 pipeline stages.

    Returns 201 whether the transaction ends up settled or rejected — a business rejection
    is a normal, successfully-processed outcome, not an HTTP error. Malformed submissions
    (missing fields, bad currency, etc.) come back as `{"status": "rejected", "reason": ...}`,
    same as a batch run would produce.
    """
    results_dir = shared_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    audit_log = results_dir / "audit.log"

    result = process_transaction(data, rules=load_rules(), audit_log=audit_log)

    tx_id = result.get("transaction_id") or "unknown"
    (results_dir / f"{tx_id}.json").write_text(json.dumps(result, indent=2, default=str))
    return result


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, shared_root: Path = Depends(get_shared_root)) -> dict:
    result = load_result(transaction_id, results_dir=shared_root / "results")
    if result is None:
        raise HTTPException(status_code=404, detail=f"transaction '{transaction_id}' not found")
    return result


@app.get("/transactions")
def list_transactions(shared_root: Path = Depends(get_shared_root)) -> list[dict]:
    return list_results(results_dir=shared_root / "results")


@app.post("/pipeline/run")
def run_full_pipeline(shared_root: Path = Depends(get_shared_root)) -> dict:
    """Batch-run sample-transactions.json through the pipeline (used by demo.sh)."""
    return run_pipeline(shared_root=shared_root)
