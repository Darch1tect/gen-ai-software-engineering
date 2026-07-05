ACC_1 = "ACC-00001"
ACC_2 = "ACC-00002"


def test_create_deposit_returns_201(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 100,
        "currency": "USD",
        "type": "deposit",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["status"] == "completed"
    assert body["fromAccount"] is None
    assert body["toAccount"] == ACC_1
    assert body["amount"] == "100.00"
    assert body["currency"] == "USD"
    assert "timestamp" in body


def test_create_withdrawal_requires_from_account(client):
    resp = client.post("/transactions", json={
        "amount": 50,
        "currency": "USD",
        "type": "withdrawal",
    })
    assert resp.status_code == 400
    assert resp.json()["error"] == "Validation failed"


def test_create_transfer_requires_both_accounts(client):
    resp = client.post("/transactions", json={
        "fromAccount": ACC_1,
        "amount": 50,
        "currency": "EUR",
        "type": "transfer",
    })
    assert resp.status_code == 400


def test_create_transfer_same_account_rejected(client):
    resp = client.post("/transactions", json={
        "fromAccount": ACC_1,
        "toAccount": ACC_1,
        "amount": 50,
        "currency": "EUR",
        "type": "transfer",
    })
    assert resp.status_code == 400


def test_amount_must_be_positive(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": -10,
        "currency": "USD",
        "type": "deposit",
    })
    assert resp.status_code == 400
    details = resp.json()["details"]
    assert any(d["field"] == "amount" and d["message"] == "Amount must be a positive number" for d in details)

    resp_zero = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 0,
        "currency": "USD",
        "type": "deposit",
    })
    assert resp_zero.status_code == 400


def test_amount_max_two_decimal_places(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 10.999,
        "currency": "USD",
        "type": "deposit",
    })
    assert resp.status_code == 400
    details = resp.json()["details"]
    assert any(
        d["field"] == "amount" and d["message"] == "Amount must have at most 2 decimal places"
        for d in details
    )


def test_amount_with_two_decimal_places_accepted(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 99.99,
        "currency": "USD",
        "type": "deposit",
    })
    assert resp.status_code == 201
    assert resp.json()["amount"] == "99.99"


def test_invalid_currency_rejected(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 10,
        "currency": "XXX",
        "type": "deposit",
    })
    assert resp.status_code == 400
    details = resp.json()["details"]
    assert any(d["field"] == "currency" and d["message"] == "Invalid currency code" for d in details)


def test_valid_currency_jpy_accepted(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 10,
        "currency": "jpy",
        "type": "deposit",
    })
    assert resp.status_code == 201
    assert resp.json()["currency"] == "JPY"


def test_invalid_account_format_rejected(client):
    resp = client.post("/transactions", json={
        "toAccount": "acc-1",
        "amount": 10,
        "currency": "USD",
        "type": "deposit",
    })
    assert resp.status_code == 400
    details = resp.json()["details"]
    assert any(
        d["field"] == "toAccount" and "ACC-XXXXX" in d["message"]
        for d in details
    )


def test_invalid_type_rejected(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 10,
        "currency": "USD",
        "type": "bogus",
    })
    assert resp.status_code == 400


def test_multiple_validation_errors_reported_together(client):
    resp = client.post("/transactions", json={
        "toAccount": "bad-account",
        "amount": -5,
        "currency": "XXX",
        "type": "deposit",
    })
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"
    fields = {d["field"] for d in body["details"]}
    assert {"amount", "currency", "toAccount"}.issubset(fields)


def test_list_transactions(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "toAccount": ACC_2, "amount": 20, "currency": "EUR", "type": "deposit",
    })
    resp = client.get("/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["limit"] == 50
    assert body["offset"] == 0


def test_list_transactions_pagination(client):
    for i in range(5):
        client.post("/transactions", json={
            "toAccount": ACC_1, "amount": 10 + i, "currency": "USD", "type": "deposit",
        })

    resp = client.get("/transactions?limit=2&offset=0")
    body = resp.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert len(body["items"]) == 2

    resp2 = client.get("/transactions?limit=2&offset=4")
    body2 = resp2.json()
    assert body2["total"] == 5
    assert len(body2["items"]) == 1

    # No overlap between the two pages fetched above.
    first_page_ids = {t["id"] for t in body["items"]}
    last_page_ids = {t["id"] for t in body2["items"]}
    assert first_page_ids.isdisjoint(last_page_ids)


def test_list_transactions_invalid_pagination_rejected(client):
    resp = client.get("/transactions?limit=0")
    assert resp.status_code == 400

    resp2 = client.get("/transactions?limit=1000")
    assert resp2.status_code == 400

    resp3 = client.get("/transactions?offset=-1")
    assert resp3.status_code == 400


def test_create_transaction_rejects_unknown_fields(client):
    resp = client.post("/transactions", json={
        "toAccount": ACC_1,
        "amount": 10,
        "currency": "USD",
        "type": "deposit",
        "unexpectedField": "should not be accepted",
    })
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"
    assert any(d["field"] == "unexpectedField" for d in body["details"])


def test_amount_nan_and_infinity_rejected(client):
    for bad_amount in ["NaN", "Infinity", "-Infinity"]:
        resp = client.post("/transactions", json={
            "toAccount": ACC_1,
            "amount": bad_amount,
            "currency": "USD",
            "type": "deposit",
        })
        assert resp.status_code == 400, f"amount={bad_amount!r} should be rejected"


def test_get_transaction_by_id(client):
    created = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    }).json()
    resp = client.get(f"/transactions/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_transaction_not_found(client):
    resp = client.get("/transactions/does-not-exist")
    assert resp.status_code == 404
