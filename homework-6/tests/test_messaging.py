from __future__ import annotations

import json

from agents import messaging


def test_now_iso_format():
    ts = messaging.now_iso()
    assert ts.endswith("Z")
    assert "T" in ts


def test_mask_account_keeps_last_4_chars():
    assert messaging.mask_account("ACC-1001") == "***1001"


def test_mask_account_handles_empty():
    assert messaging.mask_account("") == "***"


def test_new_message_envelope_shape(make_transaction):
    msg = messaging.new_message("validator", "fraud_detector", "transaction", make_transaction())
    assert msg["source_agent"] == "validator"
    assert msg["target_agent"] == "fraud_detector"
    assert msg["message_type"] == "transaction"
    assert "message_id" in msg
    assert "timestamp" in msg


def test_write_and_read_messages_round_trip(tmp_path, make_transaction):
    directory = tmp_path / "input"
    msg = messaging.new_message("integrator", "validator", "transaction", make_transaction())

    path = messaging.write_message(directory, msg)
    assert path.exists()

    messages = messaging.read_messages(directory)
    assert len(messages) == 1
    assert messages[0]["data"]["transaction_id"] == msg["data"]["transaction_id"]


def test_read_messages_from_missing_directory_returns_empty(tmp_path):
    assert messaging.read_messages(tmp_path / "does-not-exist") == []


def test_clear_directory_removes_json_files(tmp_path, make_transaction):
    directory = tmp_path / "input"
    messaging.write_message(directory, messaging.new_message("a", "b", "transaction", make_transaction()))
    assert len(list(directory.glob("*.json"))) == 1

    messaging.clear_directory(directory)
    assert list(directory.glob("*.json")) == []


def test_log_audit_appends_json_lines(tmp_path):
    log_path = tmp_path / "results" / "audit.log"
    messaging.log_audit(log_path, "transaction_validator", "TXN001", "validated")
    messaging.log_audit(log_path, "fraud_detector", "TXN001", "risk_level=low")

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2
    entry = json.loads(lines[0])
    assert entry["agent"] == "transaction_validator"
    assert entry["transaction_id"] == "TXN001"
    assert entry["outcome"] == "validated"
