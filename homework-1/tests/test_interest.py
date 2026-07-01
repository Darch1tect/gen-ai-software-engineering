ACC_1 = "ACC-00001"


def test_interest_basic_calculation(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 1000, "currency": "USD", "type": "deposit",
    })

    resp = client.get(f"/accounts/{ACC_1}/interest?rate=0.05&days=30")
    assert resp.status_code == 200
    body = resp.json()
    assert body["accountId"] == ACC_1
    assert body["rate"] == 0.05
    assert body["days"] == 30
    assert body["principal"] == {"USD": 1000}
    # 1000 * 0.05 * (30 / 365) = 4.1095... -> rounded to 4.11
    assert body["interest"] == {"USD": 4.11}
    assert body["totalAmount"] == {"USD": 1004.11}


def test_interest_zero_rate_yields_zero_interest(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 500, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/interest?rate=0&days=30")
    assert resp.status_code == 200
    body = resp.json()
    assert body["interest"] == {"USD": 0}
    assert body["totalAmount"] == {"USD": 500}


def test_interest_zero_days_yields_zero_interest(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 500, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/interest?rate=0.1&days=0")
    assert resp.status_code == 200
    assert resp.json()["interest"] == {"USD": 0}


def test_interest_multi_currency(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 1000, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 2000, "currency": "EUR", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/interest?rate=0.1&days=365")
    body = resp.json()
    # rate=0.1, days=365 -> full year -> interest == 10% of principal exactly
    assert body["interest"] == {"USD": 100, "EUR": 200}
    assert body["totalAmount"] == {"USD": 1100, "EUR": 2200}


def test_interest_negative_rate_rejected(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/interest?rate=-0.05&days=30")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"
    assert any(d["field"] == "rate" for d in body["details"])


def test_interest_negative_days_rejected(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/interest?rate=0.05&days=-1")
    assert resp.status_code == 400
    body = resp.json()
    assert any(d["field"] == "days" for d in body["details"])


def test_interest_missing_query_params_rejected(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/interest")
    assert resp.status_code == 400


def test_interest_account_not_found(client):
    resp = client.get("/accounts/ACC-99999/interest?rate=0.05&days=30")
    assert resp.status_code == 404


def test_interest_invalid_account_format(client):
    resp = client.get("/accounts/not-an-account/interest?rate=0.05&days=30")
    assert resp.status_code == 400
    body = resp.json()
    assert any(d["field"] == "accountId" for d in body["details"])
