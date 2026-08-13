from __future__ import annotations

from agents.compliance_checker import check_compliance


def test_normal_transaction_is_cleared(make_transaction):
    result = check_compliance(make_transaction(amount="100.00"))
    assert result["status"] == "compliance_cleared"
    assert "compliance_flag" not in result


def test_sanctioned_country_is_rejected(make_transaction):
    result = check_compliance(make_transaction(metadata={"country": "IR"}))
    assert result["status"] == "rejected"
    assert "IR" in result["reason"]


def test_disallowed_transaction_type_is_rejected(make_transaction):
    result = check_compliance(make_transaction(transaction_type="cash_withdrawal"))
    assert result["status"] == "rejected"
    assert "cash_withdrawal" in result["reason"]


def test_structuring_band_is_flagged_not_rejected(make_transaction):
    result = check_compliance(make_transaction(amount="9999.99"))
    assert result["status"] == "compliance_cleared"
    assert result["compliance_flag"] == "structuring_suspected"
    assert "structuring_suspected" in result["risk_factors"]


def test_amount_well_under_threshold_is_not_flagged(make_transaction):
    result = check_compliance(make_transaction(amount="500.00"))
    assert result["status"] == "compliance_cleared"
    assert "compliance_flag" not in result
