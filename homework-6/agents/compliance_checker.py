"""Compliance Checker agent: sanctioned-country denylist, allowed transaction types,
structuring detection just under the reporting threshold.

Thresholds/lists come from the active rule set (see agents/rule_engine.py): if the pipeline
already ran the Rule Engine stage, `data["_rules"]` carries it; otherwise this agent loads
rules.yaml itself, so it stays independently callable/testable.
"""

from __future__ import annotations

from decimal import Decimal

from agents.rule_engine import load_rules


def check_compliance(data: dict) -> dict:
    """Reject on sanctioned country / disallowed type; flag (not reject) structuring risk."""
    rules = (data.get("_rules") or load_rules())["compliance"]

    country = (data.get("metadata") or {}).get("country")
    if country in rules["sanctioned_countries"]:
        return {
            **data,
            "status": "rejected",
            "reason": f"country '{country}' is on the sanctioned-country denylist",
        }

    tx_type = data.get("transaction_type")
    if tx_type not in rules["allowed_transaction_types"]:
        return {
            **data,
            "status": "rejected",
            "reason": f"transaction_type '{tx_type}' is not permitted",
        }

    amount = Decimal(str(data["amount"])).copy_abs()
    threshold = Decimal(str(rules["structuring_threshold"]))
    band = Decimal(str(rules["structuring_band"]))
    is_structuring_risk = threshold - band <= amount < threshold

    result = {**data, "status": "compliance_cleared"}
    if is_structuring_risk:
        result["risk_factors"] = [*result.get("risk_factors", []), "structuring_suspected"]
        result["compliance_flag"] = "structuring_suspected"

    return result
