"""Read-only queries against shared/results/, shared by the MCP server (mcp/server.py) and
the REST API (api/app.py) so the two entry points don't each keep their own copy of this logic.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "shared" / "results"


def load_result(transaction_id: str, results_dir: Path = DEFAULT_RESULTS_DIR) -> dict | None:
    """Return one transaction's persisted result, or None if it hasn't been processed."""
    path = results_dir / f"{transaction_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_results(results_dir: Path = DEFAULT_RESULTS_DIR) -> list[dict]:
    """Return every persisted transaction result (excludes summary.json and audit.log)."""
    if not results_dir.exists():
        return []
    return [
        json.loads(f.read_text())
        for f in sorted(results_dir.glob("*.json"))
        if f.name != "summary.json"
    ]


def load_summary(results_dir: Path = DEFAULT_RESULTS_DIR) -> dict | None:
    """Return the latest pipeline run summary, or None if no run has produced one yet."""
    path = results_dir / "summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())
