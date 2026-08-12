from __future__ import annotations

import json

from agents.results_query import list_results, load_result, load_summary


def test_load_result_missing_transaction_returns_none(tmp_path):
    assert load_result("TXN-MISSING", results_dir=tmp_path) is None


def test_load_result_returns_persisted_json(tmp_path):
    (tmp_path / "TXN001.json").write_text(json.dumps({"transaction_id": "TXN001", "status": "settled"}))
    result = load_result("TXN001", results_dir=tmp_path)
    assert result == {"transaction_id": "TXN001", "status": "settled"}


def test_list_results_missing_directory_returns_empty(tmp_path):
    assert list_results(results_dir=tmp_path / "does-not-exist") == []


def test_list_results_excludes_summary_json(tmp_path):
    (tmp_path / "TXN001.json").write_text(json.dumps({"transaction_id": "TXN001"}))
    (tmp_path / "TXN002.json").write_text(json.dumps({"transaction_id": "TXN002"}))
    (tmp_path / "summary.json").write_text(json.dumps({"total_transactions": 2}))

    results = list_results(results_dir=tmp_path)
    ids = {r["transaction_id"] for r in results}
    assert ids == {"TXN001", "TXN002"}


def test_load_summary_missing_returns_none(tmp_path):
    assert load_summary(results_dir=tmp_path) is None


def test_load_summary_returns_persisted_json(tmp_path):
    (tmp_path / "summary.json").write_text(json.dumps({"total_transactions": 5}))
    assert load_summary(results_dir=tmp_path) == {"total_transactions": 5}
