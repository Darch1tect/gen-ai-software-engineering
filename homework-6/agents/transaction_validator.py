"""Transaction Validator agent: required fields, decimal amount, ISO 4217 currency."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

REQUIRED_FIELDS = [
    "transaction_id",
    "timestamp",
    "source_account",
    "destination_account",
    "amount",
    "currency",
    "transaction_type",
]

# Illustrative ISO 4217 allow-list for this capstone — not the full standard.
ISO_4217_CODES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "CNY", "INR",
    "SEK", "NOK", "DKK", "SGD", "HKD", "MXN", "BRL", "ZAR", "PLN", "AED",
}


def validate_transaction(data: dict) -> dict:
    """Validate a raw transaction dict. Always returns a structured result, never raises."""
    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        return {
            **data,
            "status": "rejected",
            "reason": f"missing required field(s): {', '.join(missing)}",
        }

    currency = data["currency"]
    if currency not in ISO_4217_CODES:
        return {
            **data,
            "status": "rejected",
            "reason": f"unsupported/invalid ISO 4217 currency code: {currency}",
        }

    try:
        amount = Decimal(str(data["amount"]))
    except (InvalidOperation, TypeError, ValueError):
        return {
            **data,
            "status": "rejected",
            "reason": f"amount is not a valid decimal: {data.get('amount')!r}",
        }

    if amount == 0:
        return {**data, "status": "rejected", "reason": "amount must be non-zero"}

    if amount < 0 and data.get("transaction_type") != "refund":
        return {
            **data,
            "status": "rejected",
            "reason": "negative amount only allowed for transaction_type 'refund'",
        }

    return {**data, "status": "validated"}
