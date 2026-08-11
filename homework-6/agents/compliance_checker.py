"""Compliance Checker agent: sanctioned-country denylist, allowed transaction types,
structuring detection just under the reporting threshold.
"""

from __future__ import annotations

from decimal import Decimal

# Illustrative denylist for this capstone only — not an authoritative sanctions list.
SANCTIONED_COUNTRIES = {"KP", "IR", "SY", "CU"}
ALLOWED_TRANSACTION_TYPES = {"transfer", "wire_transfer", "refund"}
STRUCTURING_THRESHOLD = Decimal("10000")
STRUCTURING_BAND = Decimal("500")


def check_compliance(data: dict) -> dict:
    """Reject on sanctioned country / disallowed type; flag (not reject) structuring risk."""
    country = (data.get("metadata") or {}).get("country")
    if country in SANCTIONED_COUNTRIES:
        return {
            **data,
            "status": "rejected",
            "reason": f"country '{country}' is on the sanctioned-country denylist",
        }

    tx_type = data.get("transaction_type")
    if tx_type not in ALLOWED_TRANSACTION_TYPES:
        return {
            **data,
            "status": "rejected",
            "reason": f"transaction_type '{tx_type}' is not permitted",
        }

    amount = Decimal(str(data["amount"])).copy_abs()
    is_structuring_risk = STRUCTURING_THRESHOLD - STRUCTURING_BAND <= amount < STRUCTURING_THRESHOLD

    result = {**data, "status": "compliance_cleared"}
    if is_structuring_risk:
        result["risk_factors"] = [*result.get("risk_factors", []), "structuring_suspected"]
        result["compliance_flag"] = "structuring_suspected"

    return result
