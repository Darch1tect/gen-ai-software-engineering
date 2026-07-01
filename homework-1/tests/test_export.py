import csv
import io

ACC_1 = "ACC-00001"
ACC_2 = "ACC-00002"


def _parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def test_export_default_format_is_csv(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    resp = client.get("/transactions/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    rows = _parse_csv(resp.text)
    assert len(rows) == 1
    assert rows[0]["toAccount"] == ACC_1
    assert rows[0]["amount"] == "10.00"
    assert rows[0]["currency"] == "USD"
    assert rows[0]["type"] == "deposit"
    assert rows[0]["status"] == "completed"
    assert rows[0]["id"]
    assert rows[0]["timestamp"]


def test_export_explicit_csv_format(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    resp = client.get("/transactions/export?format=csv")
    assert resp.status_code == 200
    assert len(_parse_csv(resp.text)) == 1


def test_export_unsupported_format_rejected(client):
    resp = client.get("/transactions/export?format=xml")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"


def test_export_empty_store_returns_header_only(client):
    resp = client.get("/transactions/export")
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert rows == []
    assert "id" in resp.text.splitlines()[0]


def test_export_filtered_by_account(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "toAccount": ACC_2, "amount": 20, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/transactions/export?accountId={ACC_1}")
    rows = _parse_csv(resp.text)
    assert len(rows) == 1
    assert rows[0]["toAccount"] == ACC_1


def test_export_filtered_by_type(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_2, "amount": 5,
        "currency": "USD", "type": "transfer",
    })
    resp = client.get("/transactions/export?type=transfer")
    rows = _parse_csv(resp.text)
    assert len(rows) == 1
    assert rows[0]["type"] == "transfer"


def test_export_filtered_by_invalid_account_rejected(client):
    resp = client.get("/transactions/export?accountId=bad-account")
    assert resp.status_code == 400
    body = resp.json()
    assert any(d["field"] == "accountId" for d in body["details"])


def test_export_invalid_date_format_rejected(client):
    resp = client.get("/transactions/export?from=not-a-date")
    assert resp.status_code == 400
