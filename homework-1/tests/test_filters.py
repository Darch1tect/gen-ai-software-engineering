from src.utils.storage import store

ACC_1 = "ACC-00001"
ACC_2 = "ACC-00002"
ACC_3 = "ACC-00003"


def _set_timestamp(transaction_id: str, iso_datetime: str) -> None:
    """Test helper: backdate a stored transaction's timestamp directly."""
    txn = store.get(transaction_id)
    txn.timestamp = iso_datetime


def test_filter_by_account(client):
    t1 = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    }).json()
    client.post("/transactions", json={
        "toAccount": ACC_2, "amount": 20, "currency": "USD", "type": "deposit",
    })
    t3 = client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_3, "amount": 5,
        "currency": "USD", "type": "transfer",
    }).json()

    resp = client.get(f"/transactions?accountId={ACC_1}")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert ids == {t1["id"], t3["id"]}


def test_filter_by_type(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    t2 = client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_2, "amount": 5,
        "currency": "USD", "type": "transfer",
    }).json()

    resp = client.get("/transactions?type=transfer")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == t2["id"]


def test_filter_by_date_range(client):
    t_jan = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    }).json()
    t_feb = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 20, "currency": "USD", "type": "deposit",
    }).json()
    _set_timestamp(t_jan["id"], "2024-01-15T10:00:00+00:00")
    _set_timestamp(t_feb["id"], "2024-02-15T10:00:00+00:00")

    resp = client.get("/transactions?from=2024-01-01&to=2024-01-31")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert ids == {t_jan["id"]}


def test_combine_multiple_filters(client):
    t1 = client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_2, "amount": 5,
        "currency": "USD", "type": "transfer",
    }).json()
    t2 = client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_3, "amount": 7,
        "currency": "USD", "type": "transfer",
    }).json()
    t3 = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    }).json()
    _set_timestamp(t1["id"], "2024-01-10T10:00:00+00:00")
    _set_timestamp(t2["id"], "2024-05-10T10:00:00+00:00")
    _set_timestamp(t3["id"], "2024-01-10T10:00:00+00:00")

    resp = client.get(
        f"/transactions?accountId={ACC_1}&type=transfer&from=2024-01-01&to=2024-01-31"
    )
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert ids == {t1["id"]}


def test_filter_invalid_account_format(client):
    resp = client.get("/transactions?accountId=bad-account")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"
    assert any(d["field"] == "accountId" for d in body["details"])


def test_filter_invalid_type(client):
    resp = client.get("/transactions?type=bogus")
    assert resp.status_code == 400


def test_filter_invalid_date_format(client):
    resp = client.get("/transactions?from=01-01-2024")
    assert resp.status_code == 400
    body = resp.json()
    assert any(d["field"] == "from" for d in body["details"])


def test_filter_from_after_to_rejected(client):
    resp = client.get("/transactions?from=2024-02-01&to=2024-01-01")
    assert resp.status_code == 400
    body = resp.json()
    assert any(d["field"] == "from" and "later than" in d["message"] for d in body["details"])


def test_no_filters_returns_all(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "toAccount": ACC_2, "amount": 20, "currency": "EUR", "type": "deposit",
    })
    resp = client.get("/transactions")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
