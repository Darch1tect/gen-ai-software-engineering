"""Shared per-transaction pipeline chain: Validator -> Rule Engine -> Fraud Detector ->
Compliance Checker -> Settlement Processor.

Used by both the batch orchestrator (integrator.py) and the REST API (api/app.py) so the
stage order and audit logging live in exactly one place.
"""

from __future__ import annotations

from pathlib import Path

from agents import messaging
from agents.compliance_checker import check_compliance
from agents.fraud_detector import score_transaction
from agents.rule_engine import apply_rule_engine, load_rules
from agents.settlement_processor import settle_transaction
from agents.transaction_validator import validate_transaction


def process_transaction(data: dict, rules: dict | None = None, audit_log: Path | None = None) -> dict:
    """Run one transaction through all 5 stages.

    Returns the final, persistable result (internal keys like `_rules` already stripped).
    If `audit_log` is given, appends one audit-log line per stage the transaction reaches.
    """
    rules = rules if rules is not None else load_rules()
    tx_id = data.get("transaction_id") or "unknown"
    masked_source = messaging.mask_account(data.get("source_account", ""))

    def _audit(agent: str, outcome: str) -> None:
        if audit_log is not None:
            messaging.log_audit(audit_log, agent, tx_id, outcome)

    validated = validate_transaction(data)
    _audit("transaction_validator", validated["status"])
    if validated["status"] == "rejected":
        return messaging.strip_internal(validated)

    ruled = apply_rule_engine(validated, rules)
    _audit("rule_engine", f"rules_version={ruled['rules_version']}")

    scored = score_transaction(ruled)
    _audit("fraud_detector", f"risk_level={scored['risk_level']} src={masked_source}")

    compliant = check_compliance(scored)
    _audit("compliance_checker", compliant["status"])
    if compliant["status"] == "rejected":
        return messaging.strip_internal(compliant)

    settled = settle_transaction(compliant)
    _audit("settlement_processor", settled["status"])
    return messaging.strip_internal(settled)
