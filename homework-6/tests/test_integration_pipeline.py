from __future__ import annotations

import json

from integrator import run_pipeline


def test_full_pipeline_processes_all_transactions_isolated(tmp_path):
    input_file = tmp_path / "sample-transactions.json"
    input_file.write_text(
        json.dumps(
            [
                {
                    "transaction_id": "TXN-A",
                    "timestamp": "2026-03-16T09:00:00Z",
                    "source_account": "ACC-1001",
                    "destination_account": "ACC-2001",
                    "amount": "1500.00",
                    "currency": "USD",
                    "transaction_type": "transfer",
                    "description": "Normal transfer",
                    "metadata": {"channel": "online", "country": "US"},
                },
                {
                    "transaction_id": "TXN-B",
                    "timestamp": "2026-03-16T09:00:00Z",
                    "source_account": "ACC-1002",
                    "destination_account": "ACC-2002",
                    "amount": "50.00",
                    "currency": "XYZ",
                    "transaction_type": "transfer",
                    "description": "Bad currency",
                    "metadata": {"channel": "online", "country": "US"},
                },
                {
                    "transaction_id": "TXN-C",
                    "timestamp": "2026-03-16T09:00:00Z",
                    "source_account": "ACC-1003",
                    "destination_account": "ACC-2003",
                    "amount": "9999.99",
                    "currency": "USD",
                    "transaction_type": "transfer",
                    "description": "Near threshold",
                    "metadata": {"channel": "online", "country": "US"},
                },
            ]
        )
    )
    shared_root = tmp_path / "shared"

    summary = run_pipeline(input_file=input_file, shared_root=shared_root)

    assert summary["total_transactions"] == 3
    assert summary["counts_by_status"] == {"settled": 2, "rejected": 1}

    results_dir = shared_root / "results"
    assert (results_dir / "TXN-A.json").exists()
    assert (results_dir / "TXN-B.json").exists()
    assert (results_dir / "TXN-C.json").exists()
    assert (results_dir / "summary.json").exists()

    txn_b = json.loads((results_dir / "TXN-B.json").read_text())
    assert txn_b["status"] == "rejected"
    assert "XYZ" in txn_b["reason"]

    txn_c = json.loads((results_dir / "TXN-C.json").read_text())
    assert txn_c["status"] == "settled"
    assert txn_c["compliance_flag"] == "structuring_suspected"

    audit_log = (results_dir / "audit.log").read_text()
    assert "ACC-1001" not in audit_log
    assert "ACC-1002" not in audit_log
    assert "ACC-1003" not in audit_log

    for stage_dir in ("input", "processing", "output"):
        assert (shared_root / stage_dir).exists()


def test_pipeline_is_rerunnable_and_rebuilds_results(tmp_path):
    input_file = tmp_path / "sample-transactions.json"
    input_file.write_text(
        json.dumps(
            [
                {
                    "transaction_id": "TXN-ONE",
                    "timestamp": "2026-03-16T09:00:00Z",
                    "source_account": "ACC-1001",
                    "destination_account": "ACC-2001",
                    "amount": "10.00",
                    "currency": "USD",
                    "transaction_type": "transfer",
                    "metadata": {"channel": "online", "country": "US"},
                }
            ]
        )
    )
    shared_root = tmp_path / "shared"

    run_pipeline(input_file=input_file, shared_root=shared_root)
    run_pipeline(input_file=input_file, shared_root=shared_root)

    results_dir = shared_root / "results"
    result_files = [f for f in results_dir.glob("*.json") if f.name != "summary.json"]
    assert len(result_files) == 1

    audit_lines = (results_dir / "audit.log").read_text().strip().splitlines()
    # 5 stages per settled transaction (validator, rule_engine, fraud, compliance, settlement) x 2 runs
    assert len(audit_lines) == 10
