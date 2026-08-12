"""Custom FastMCP server exposing the banking pipeline's results.

Read-only against shared/results/ — this server never writes to the pipeline's shared
directories, it only queries what the agents already produced (via agents/results_query.py,
shared with the REST API in api/app.py). See research-notes.md ("Query 1: FastMCP server")
for the context7 research behind the decorator API used here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    # Run as `python mcp/server.py`, so the project root isn't on sys.path by default —
    # needed to import the sibling `agents` package.
    sys.path.insert(0, str(PROJECT_ROOT))

from fastmcp import FastMCP

from agents.results_query import list_results, load_result, load_summary

mcp = FastMCP(name="banking-pipeline-status")


@mcp.tool
def get_transaction_status(transaction_id: str) -> dict:
    """Return the current pipeline status/result for a single transaction, by its ID."""
    result = load_result(transaction_id)
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
        for result in list_results()
    ]


@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    """Return the latest pipeline run summary (shared/results/summary.json) as text."""
    summary = load_summary()
    if summary is None:
        return json.dumps({"error": "no pipeline run has produced a summary yet"})
    return json.dumps(summary)


if __name__ == "__main__":
    mcp.run()
