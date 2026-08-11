"""Custom FastMCP server exposing the banking pipeline's results.

Read-only against shared/results/ — this server never writes to the pipeline's shared
directories, it only queries what the agents already produced. See research-notes.md
("Query 1: FastMCP server") for the context7 research behind the decorator API used here.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "shared" / "results"

mcp = FastMCP(name="banking-pipeline-status")


def _load_result(transaction_id: str) -> dict | None:
    path = RESULTS_DIR / f"{transaction_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _all_results() -> list[dict]:
    results = []
    for f in sorted(RESULTS_DIR.glob("*.json")):
        if f.name == "summary.json":
            continue
        results.append(json.loads(f.read_text()))
    return results


@mcp.tool
def get_transaction_status(transaction_id: str) -> dict:
    """Return the current pipeline status/result for a single transaction, by its ID."""
    result = _load_result(transaction_id)
    if result is None:
        return {"transaction_id": transaction_id, "found": False}
    return {"found": True, **result}


@mcp.tool
def list_pipeline_results() -> list[dict]:
    """Return a compact summary (status, risk level, amount) for every processed transaction."""
    return [
        {
            "transaction_id": result.get("transaction_id"),
            "status": result.get("status"),
            "reason": result.get("reason"),
            "risk_level": result.get("risk_level"),
            "currency": result.get("currency"),
            "amount": result.get("amount"),
        }
        for result in _all_results()
    ]


@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    """Return the latest pipeline run summary (shared/results/summary.json) as text."""
    summary_path = RESULTS_DIR / "summary.json"
    if not summary_path.exists():
        return json.dumps({"error": "no pipeline run has produced a summary yet"})
    return summary_path.read_text()


if __name__ == "__main__":
    mcp.run()
