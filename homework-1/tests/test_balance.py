ACC_1 = "ACC-00001"
ACC_2 = "ACC-00002"


def test_balance_after_deposit(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/balance")
    assert resp.status_code == 200
    assert resp.json()["balances"] == {"USD": 100}


def test_balance_after_withdrawal(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "fromAccount": ACC_1, "amount": 40, "currency": "USD", "type": "withdrawal",
    })
    resp = client.get(f"/accounts/{ACC_1}/balance")
    assert resp.json()["balances"] == {"USD": 60}


def test_balance_after_transfer(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 200, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_2, "amount": 75,
        "currency": "USD", "type": "transfer",
    })
    resp1 = client.get(f"/accounts/{ACC_1}/balance")
    resp2 = client.get(f"/accounts/{ACC_2}/balance")
    assert resp1.json()["balances"] == {"USD": 125}
    assert resp2.json()["balances"] == {"USD": 75}


def test_balance_multi_currency(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 50, "currency": "EUR", "type": "deposit",
    })
    resp = client.get(f"/accounts/{ACC_1}/balance")
    assert resp.json()["balances"] == {"USD": 100, "EUR": 50}


def test_balance_account_not_found(client):
    resp = client.get("/accounts/ACC-99999/balance")
    assert resp.status_code == 404


def test_balance_invalid_account_format(client):
    resp = client.get("/accounts/not-an-account/balance")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"
    assert any(d["field"] == "accountId" for d in body["details"])
