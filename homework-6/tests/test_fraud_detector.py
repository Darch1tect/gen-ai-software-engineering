from __future__ import annotations

from agents.fraud_detector import score_transaction


def test_low_value_daytime_domestic_is_low_risk(make_transaction):
    result = score_transaction(make_transaction(amount="100.00"))
    assert result["status"] == "risk_scored"
    assert result["risk_level"] == "low"
    assert result["risk_factors"] == []
    assert result["flagged_for_review"] is False


def test_high_value_is_flagged_high_risk(make_transaction):
    result = score_transaction(make_transaction(amount="25000.00"))
    assert result["risk_level"] == "high"
    assert "high_value" in result["risk_factors"]
    assert result["flagged_for_review"] is True


def test_odd_hour_timing_is_flagged(make_transaction):
    result = score_transaction(make_transaction(timestamp="2026-03-16T02:47:00Z", amount="500.00"))
    assert "unusual_timing" in result["risk_factors"]
    assert result["risk_level"] == "medium"


def test_cross_border_currency_country_mismatch_is_flagged(make_transaction):
    result = score_transaction(
        make_transaction(currency="USD", amount="500.00", metadata={"country": "DE"})
    )
    assert "cross_border" in result["risk_factors"]


def test_score_is_capped_at_100(make_transaction):
    result = score_transaction(
        make_transaction(
            amount="50000.00",
            timestamp="2026-03-16T02:00:00Z",
            currency="USD",
            metadata={"country": "DE"},
        )
    )
    assert result["risk_score"] <= 100
    assert result["risk_level"] == "high"


def test_malformed_timestamp_does_not_crash(make_transaction):
    result = score_transaction(make_transaction(timestamp="not-a-timestamp"))
    assert result["status"] == "risk_scored"
    assert "unusual_timing" not in result["risk_factors"]
