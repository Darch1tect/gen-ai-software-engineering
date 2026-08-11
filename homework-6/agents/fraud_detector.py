"""Fraud Detector agent: risk score 0-100 from value, timing, and cross-border heuristics.

Never rejects a transaction outright — always passes it on with the score attached so
downstream compliance/settlement agents make the final accept/reject call.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

HIGH_VALUE_THRESHOLD = Decimal("10000")
ODD_HOUR_START = 0
ODD_HOUR_END = 5  # UTC hours [0, 5) are treated as unusual timing

# Simplified currency -> "home" country heuristic for the cross-border check.
# Illustrative only (e.g. EUR has no single home country in reality).
CURRENCY_HOME_COUNTRY = {
    "USD": "US", "EUR": "DE", "GBP": "GB", "JPY": "JP", "CHF": "CH", "CAD": "CA",
    "AUD": "AU", "NZD": "NZ", "CNY": "CN", "INR": "IN", "SEK": "SE", "NOK": "NO",
    "DKK": "DK", "SGD": "SG", "HKD": "HK", "MXN": "MX", "BRL": "BR", "ZAR": "ZA",
    "PLN": "PL", "AED": "AE",
}


def _is_odd_hour(timestamp: str) -> bool:
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    return ODD_HOUR_START <= dt.hour < ODD_HOUR_END


def _is_cross_border(data: dict) -> bool:
    currency = data.get("currency")
    country = (data.get("metadata") or {}).get("country")
    home = CURRENCY_HOME_COUNTRY.get(currency)
    return bool(home and country and home != country)


def score_transaction(data: dict) -> dict:
    """Score a validated transaction for fraud risk. Always returns status 'risk_scored'."""
    amount = Decimal(str(data["amount"])).copy_abs()
    factors: list[str] = []
    score = 0

    high_value = amount > HIGH_VALUE_THRESHOLD
    if high_value:
        factors.append("high_value")
        score += 50

    if _is_odd_hour(data.get("timestamp", "")):
        factors.append("unusual_timing")
        score += 25

    if _is_cross_border(data):
        factors.append("cross_border")
        score += 20

    score = min(score, 100)

    if high_value or score >= 60:
        risk_level = "high"
    elif score >= 25:
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
