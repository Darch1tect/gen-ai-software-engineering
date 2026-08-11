from __future__ import annotations

from agents.transaction_validator import validate_transaction


def test_valid_transaction_passes(make_transaction):
    result = validate_transaction(make_transaction())
    assert result["status"] == "validated"


def test_missing_required_field_is_rejected(make_transaction):
    txn = make_transaction()
    del txn["destination_account"]
    result = validate_transaction(txn)
    assert result["status"] == "rejected"
    assert "destination_account" in result["reason"]


def test_invalid_currency_is_rejected(make_transaction):
    result = validate_transaction(make_transaction(currency="XYZ"))
    assert result["status"] == "rejected"
    assert "XYZ" in result["reason"]


def test_non_decimal_amount_is_rejected(make_transaction):
    result = validate_transaction(make_transaction(amount="not-a-number"))
    assert result["status"] == "rejected"
    assert "decimal" in result["reason"]


def test_zero_amount_is_rejected(make_transaction):
    result = validate_transaction(make_transaction(amount="0.00"))
    assert result["status"] == "rejected"
    assert "non-zero" in result["reason"]


def test_negative_amount_rejected_for_non_refund(make_transaction):
    result = validate_transaction(make_transaction(amount="-50.00", transaction_type="transfer"))
    assert result["status"] == "rejected"
    assert "refund" in result["reason"]


def test_negative_amount_allowed_for_refund(make_transaction):
    result = validate_transaction(make_transaction(amount="-50.00", transaction_type="refund"))
    assert result["status"] == "validated"
