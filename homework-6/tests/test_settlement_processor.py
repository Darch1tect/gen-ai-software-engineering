from __future__ import annotations

from agents.settlement_processor import settle_transaction, write_summary


def test_settle_transaction_marks_settled(make_transaction):
    result = settle_transaction(make_transaction())
    assert result["status"] == "settled"


def test_write_summary_counts_and_totals(make_transaction):
    results = [
        settle_transaction(make_transaction(transaction_id="TXN1", amount="100.00", currency="USD")),
        settle_transaction(make_transaction(transaction_id="TXN2", amount="200.00", currency="USD")),
        {**make_transaction(transaction_id="TXN3"), "status": "rejected", "reason": "bad currency"},
    ]

    summary = write_summary(results)

    assert summary["total_transactions"] == 3
    assert summary["counts_by_status"] == {"settled": 2, "rejected": 1}
    assert summary["settled_totals_by_currency"] == {"USD": "300.00"}
    assert "generated_at" in summary


def test_write_summary_handles_empty_results():
    summary = write_summary([])
    assert summary["total_transactions"] == 0
    assert summary["counts_by_status"] == {}
    assert summary["settled_totals_by_currency"] == {}
