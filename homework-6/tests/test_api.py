from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app, get_shared_root


@pytest.fixture
def client(tmp_path):
    app.dependency_overrides[get_shared_root] = lambda: tmp_path / "shared"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_submit_valid_transaction_returns_settled(client, make_transaction):
    resp = client.post("/transactions", json=make_transaction())
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "settled"
    assert "_rules" not in body


def test_submit_invalid_transaction_returns_201_with_rejected_status(client, make_transaction):
    """A business rejection is a normal outcome, not an HTTP error."""
    resp = client.post("/transactions", json=make_transaction(currency="XYZ"))
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "rejected"
    assert "XYZ" in body["reason"]


def test_get_transaction_after_submit(client, make_transaction):
    client.post("/transactions", json=make_transaction(transaction_id="TXN-API-1"))
    resp = client.get("/transactions/TXN-API-1")
    assert resp.status_code == 200
    assert resp.json()["transaction_id"] == "TXN-API-1"


def test_get_unknown_transaction_returns_404(client):
    resp = client.get("/transactions/DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_list_transactions(client, make_transaction):
    client.post("/transactions", json=make_transaction(transaction_id="TXN-L1"))
    client.post("/transactions", json=make_transaction(transaction_id="TXN-L2"))
    resp = client.get("/transactions")
    assert resp.status_code == 200
    ids = {r["transaction_id"] for r in resp.json()}
    assert {"TXN-L1", "TXN-L2"} <= ids


def test_pipeline_run_endpoint(client):
    resp = client.post("/pipeline/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_transactions"] == 8
    assert body["counts_by_status"]["rejected"] == 1
