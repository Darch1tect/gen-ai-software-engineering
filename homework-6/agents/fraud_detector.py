"""Fraud Detector agent: risk score 0-100 from value, timing, and cross-border heuristics.

Never rejects a transaction outright — always passes it on with the score attached so
downstream compliance/settlement agents make the final accept/reject call.

Thresholds and weights come from the active rule set (see agents/rule_engine.py): if the
pipeline already ran the Rule Engine stage, `data["_rules"]` carries it; otherwise this agent
loads rules.yaml itself, so it stays independently callable/testable.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from agents.rule_engine import load_rules


def _is_odd_hour(timestamp: str, start: int, end: int) -> bool:
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    return start <= dt.hour < end


def _is_cross_border(data: dict, currency_home_country: dict) -> bool:
    currency = data.get("currency")
    country = (data.get("metadata") or {}).get("country")
    home = currency_home_country.get(currency)
    return bool(home and country and home != country)


def score_transaction(data: dict) -> dict:
    """Score a validated transaction for fraud risk. Always returns status 'risk_scored'."""
    rules = (data.get("_rules") or load_rules())["fraud"]

    amount = Decimal(str(data["amount"])).copy_abs()
    threshold = Decimal(str(rules["high_value_threshold"]))
    weights = rules["weights"]
    bands = rules["risk_level_bands"]

    factors: list[str] = []
    score = 0

    high_value = amount > threshold
    if high_value:
        factors.append("high_value")
        score += weights["high_value"]

    if _is_odd_hour(data.get("timestamp", ""), rules["odd_hour_start"], rules["odd_hour_end"]):
        factors.append("unusual_timing")
        score += weights["unusual_timing"]

    if _is_cross_border(data, rules["currency_home_country"]):
        factors.append("cross_border")
        score += weights["cross_border"]

    score = min(score, 100)

    if high_value or score >= bands["high"]:
        risk_level = "high"
    elif score >= bands["medium"]:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        **data,
        "status": "risk_scored",
        "risk_score": score,
        "risk_level": risk_level,
        "risk_factors": factors,
        "flagged_for_review": high_value,
    }
