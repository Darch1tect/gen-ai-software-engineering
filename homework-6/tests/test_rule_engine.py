from __future__ import annotations

import pytest

from agents.compliance_checker import check_compliance
from agents.fraud_detector import score_transaction
from agents.rule_engine import RuleConfigError, apply_rule_engine, load_rules

VALID_RULES = {
    "version": 7,
    "fraud": {
        "high_value_threshold": "100",
        "odd_hour_start": 0,
        "odd_hour_end": 5,
        "weights": {"high_value": 50, "unusual_timing": 25, "cross_border": 20},
        "risk_level_bands": {"high": 60, "medium": 25},
        "currency_home_country": {"USD": "US"},
    },
    "compliance": {
        "sanctioned_countries": ["KP"],
        "allowed_transaction_types": ["transfer"],
        "structuring_threshold": "100",
        "structuring_band": "10",
    },
}


def test_load_rules_default_path_is_valid():
    rules = load_rules()
    assert rules["version"] == 1
    assert "high_value_threshold" in rules["fraud"]
    assert "sanctioned_countries" in rules["compliance"]


def test_load_rules_missing_file_raises(tmp_path):
    with pytest.raises(RuleConfigError, match="not found"):
        load_rules(tmp_path / "does-not-exist.yaml")


def test_load_rules_malformed_yaml_raises(tmp_path):
    bad = tmp_path / "rules.yaml"
    bad.write_text("fraud: [unterminated\n  - broken: [")
    with pytest.raises(RuleConfigError, match="not valid YAML"):
        load_rules(bad)


def test_load_rules_non_mapping_raises(tmp_path):
    bad = tmp_path / "rules.yaml"
    bad.write_text("- just\n- a\n- list\n")
    with pytest.raises(RuleConfigError, match="must be a mapping"):
        load_rules(bad)


def test_load_rules_missing_top_level_key_raises(tmp_path):
    bad = tmp_path / "rules.yaml"
    bad.write_text("version: 1\nfraud: {}\n")
    with pytest.raises(RuleConfigError, match="missing required top-level key"):
        load_rules(bad)


def test_load_rules_missing_fraud_subkey_raises(tmp_path):
    bad = tmp_path / "rules.yaml"
    bad.write_text("version: 1\nfraud: {high_value_threshold: '10000'}\ncompliance: {}\n")
    with pytest.raises(RuleConfigError, match="'fraud' missing key"):
        load_rules(bad)


def test_load_rules_missing_compliance_subkey_raises(tmp_path):
    bad = tmp_path / "rules.yaml"
    bad.write_text(
        "version: 1\n"
        "fraud: {high_value_threshold: '10000', odd_hour_start: 0, odd_hour_end: 5, "
        "weights: {}, risk_level_bands: {}, currency_home_country: {}}\n"
        "compliance: {sanctioned_countries: []}\n"
    )
    with pytest.raises(RuleConfigError, match="'compliance' missing key"):
        load_rules(bad)


def test_apply_rule_engine_stamps_version_and_internal_rules(make_transaction):
    result = apply_rule_engine(make_transaction(), rules=VALID_RULES)
    assert result["status"] == "rules_applied"
    assert result["rules_version"] == 7
    assert result["_rules"] is VALID_RULES


def test_apply_rule_engine_defaults_to_load_rules(make_transaction):
    result = apply_rule_engine(make_transaction())
    assert result["rules_version"] == 1


def test_fraud_detector_honors_injected_rules(make_transaction):
    """Proof of configurability: a lower threshold flags a transaction the default rules wouldn't."""
    txn = make_transaction(amount="150.00")

    default_result = score_transaction(txn)
    assert default_result["risk_level"] == "low"

    ruled = apply_rule_engine(txn, rules=VALID_RULES)
    custom_result = score_transaction(ruled)
    assert custom_result["risk_level"] == "high"
    assert "high_value" in custom_result["risk_factors"]


def test_compliance_checker_honors_injected_rules(make_transaction):
    """Proof of configurability: a custom denylist rejects a country the default rules allow."""
    txn = make_transaction(metadata={"country": "US"})

    default_result = check_compliance(txn)
    assert default_result["status"] == "compliance_cleared"

    custom_rules = {**VALID_RULES, "compliance": {**VALID_RULES["compliance"], "sanctioned_countries": ["US"]}}
    ruled = apply_rule_engine(txn, rules=custom_rules)
    custom_result = check_compliance(ruled)
    assert custom_result["status"] == "rejected"
    assert "US" in custom_result["reason"]
