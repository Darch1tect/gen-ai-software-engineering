"""Settlement Processor agent: finalizes cleared transactions and builds the pipeline summary."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from agents.messaging import now_iso


def settle_transaction(data: dict) -> dict:
    """Mark a compliance-cleared transaction as settled."""
    return {**data, "status": "settled"}


def write_summary(results: list[dict]) -> dict:
    """Build the pipeline run summary backing the MCP pipeline://summary resource."""
    counts: dict[str, int] = defaultdict(int)
    totals_by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for result in results:
        counts[result["status"]] += 1
        if result["status"] == "settled":
            currency = result.get("currency", "UNKNOWN")
            totals_by_currency[currency] += Decimal(str(result["amount"])).copy_abs()

    return {
        "generated_at": now_iso(),
        "total_transactions": len(results),
        "counts_by_status": dict(counts),
        "settled_totals_by_currency": {k: str(v) for k, v in totals_by_currency.items()},
    }
