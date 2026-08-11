from __future__ import annotations

import copy

import pytest

BASE_TRANSACTION = {
    "transaction_id": "TXN900",
    "timestamp": "2026-03-16T12:00:00Z",
    "source_account": "ACC-1900",
    "destination_account": "ACC-2900",
    "amount": "100.00",
    "currency": "USD",
    "transaction_type": "transfer",
    "description": "Test transaction",
    "metadata": {"channel": "online", "country": "US"},
}


@pytest.fixture
def make_transaction():
    def _make(**overrides):
        txn = copy.deepcopy(BASE_TRANSACTION)
        metadata_override = overrides.pop("metadata", None)
        txn.update(overrides)
        if metadata_override is not None:
            txn["metadata"] = {**txn["metadata"], **metadata_override}
        return txn

    return _make
