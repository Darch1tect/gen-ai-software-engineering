"""Rule Engine agent: loads configurable business rules from rules.yaml and stamps them
onto the transaction as it flows through the pipeline, so downstream agents (Fraud Detector,
Compliance Checker) read thresholds from config instead of hardcoded constants.
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES_PATH = PROJECT_ROOT / "rules.yaml"

_REQUIRED_FRAUD_KEYS = {
    "high_value_threshold",
    "odd_hour_start",
    "odd_hour_end",
    "weights",
    "risk_level_bands",
    "currency_home_country",
}
_REQUIRED_COMPLIANCE_KEYS = {
    "sanctioned_countries",
    "allowed_transaction_types",
    "structuring_threshold",
    "structuring_band",
}


class RuleConfigError(ValueError):
    """Raised when rules.yaml is missing or malformed."""


def load_rules(path: Path | str | None = None) -> dict:
    """Load and validate the rules config. Raises RuleConfigError on a missing/malformed file."""
    rules_path = Path(path) if path is not None else DEFAULT_RULES_PATH
    if not rules_path.exists():
        raise RuleConfigError(f"rules config not found: {rules_path}")

    try:
        rules = yaml.safe_load(rules_path.read_text())
    except yaml.YAMLError as exc:
        raise RuleConfigError(f"rules config is not valid YAML: {rules_path}") from exc

    if not isinstance(rules, dict):
        raise RuleConfigError(f"rules config must be a mapping: {rules_path}")

    for key in ("version", "fraud", "compliance"):
        if key not in rules:
            raise RuleConfigError(f"rules config missing required top-level key: {key!r}")

    missing_fraud = _REQUIRED_FRAUD_KEYS - rules["fraud"].keys()
    if missing_fraud:
        raise RuleConfigError(f"rules config 'fraud' missing key(s): {sorted(missing_fraud)}")

    missing_compliance = _REQUIRED_COMPLIANCE_KEYS - rules["compliance"].keys()
    if missing_compliance:
        raise RuleConfigError(
            f"rules config 'compliance' missing key(s): {sorted(missing_compliance)}"
        )

    return rules


def apply_rule_engine(data: dict, rules: dict | None = None) -> dict:
    """Pipeline stage: load (or accept) the active rule set and stamp it onto the transaction."""
    rules = rules if rules is not None else load_rules()
    return {
        **data,
        "status": "rules_applied",
        "rules_version": rules.get("version"),
        "_rules": rules,
    }
