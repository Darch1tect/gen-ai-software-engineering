"""Shared file-based messaging helpers for the banking pipeline agents.

Every agent communicates by reading and writing the standard JSON message
envelope to the shared/{input,processing,output,results} directories. This
module is the only place that touches those paths, timestamps, account
masking, and the audit log directly.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string, e.g. 2026-03-16T10:00:00Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mask_account(account: str) -> str:
    """Mask an account number to its last 4 characters, e.g. ACC-1001 -> ***1001."""
    if not account:
        return "***"
    return f"***{account[-4:]}"


def new_message(source_agent: str, target_agent: str, message_type: str, data: dict) -> dict:
    """Build a standard message envelope around a transaction payload."""
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "source_agent": source_agent,
        "target_agent": target_agent,
        "message_type": message_type,
        "data": data,
    }


def write_message(directory: Path, message: dict) -> Path:
    """Write a message envelope as JSON, named by transaction_id (or message_id)."""
    directory.mkdir(parents=True, exist_ok=True)
    tx_id = message.get("data", {}).get("transaction_id") or message["message_id"]
    path = directory / f"{tx_id}.json"
    path.write_text(json.dumps(message, indent=2, default=str))
    return path


def read_messages(directory: Path) -> list[dict]:
    """Read every message envelope JSON file from a shared directory."""
    if not directory.exists():
        return []
    return [json.loads(f.read_text()) for f in sorted(directory.glob("*.json"))]


def clear_directory(directory: Path) -> None:
    """Remove every JSON message file from a shared directory (creates it if missing)."""
    directory.mkdir(parents=True, exist_ok=True)
    for f in directory.glob("*.json"):
        f.unlink()


def strip_internal(data: dict) -> dict:
    """Drop any `_`-prefixed key (e.g. `_rules`) before a transaction is persisted or returned.

    Internal-only fields let agents thread working state (like the loaded rule set) through the
    pipeline via the same dict-merge pattern as everything else, without that state leaking into
    shared/results/ records or API responses.
    """
    return {k: v for k, v in data.items() if not k.startswith("_")}


def log_audit(audit_log_path: Path, agent: str, transaction_id: str, outcome: str) -> None:
    """Append one JSON-line audit record. Never pass full account numbers in `outcome`."""
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "agent": agent,
        "transaction_id": transaction_id,
        "outcome": outcome,
    }
    with audit_log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
