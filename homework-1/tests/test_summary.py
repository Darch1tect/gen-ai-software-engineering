from datetime import datetime

from src.utils.storage import store

ACC_1 = "ACC-00001"
ACC_2 = "ACC-00002"


def _set_timestamp(transaction_id: str, iso_datetime: str) -> None:
    txn = store.get(transaction_id)
    txn.timestamp = datetime.fromisoformat(iso_datetime)


def _parse_api_datetime(value: str) -> datetime:
    """Parse a datetime string returned by the API.

    Pydantic v2 serializes UTC datetimes with a trailing "Z" (e.g.
    "2024-06-15T08:30:00Z"). `datetime.fromisoformat` only gained support
    for that suffix in Python 3.11, so normalize it to "+00:00" first to
    stay compatible with older Python versions too.
    """
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_summary_deposit_and_withdrawal(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 100, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "fromAccount": ACC_1, "amount": 30, "currency": "USD", "type": "withdrawal",
    })

    resp = client.get(f"/accounts/{ACC_1}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["accountId"] == ACC_1
    assert body["totalDeposits"] == {"USD": "100.00"}
    assert body["totalWithdrawals"] == {"USD": "30.00"}
    assert body["transactionCount"] == 2
    assert body["mostRecentTransactionDate"]


def test_summary_counts_transfer_in_both_directions(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 200, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "fromAccount": ACC_1, "toAccount": ACC_2, "amount": 50,
        "currency": "USD", "type": "transfer",
    })

    summary_1 = client.get(f"/accounts/{ACC_1}/summary").json()
    summary_2 = client.get(f"/accounts/{ACC_2}/summary").json()

    # ACC_1: 200 deposit in, 50 transferred out -> counts as a withdrawal for ACC_1
    assert summary_1["totalDeposits"] == {"USD": "200.00"}
    assert summary_1["totalWithdrawals"] == {"USD": "50.00"}
    assert summary_1["transactionCount"] == 2

    # ACC_2: received the transfer -> counts as a deposit for ACC_2
    assert summary_2["totalDeposits"] == {"USD": "50.00"}
    assert summary_2["totalWithdrawals"] == {}
    assert summary_2["transactionCount"] == 1


def test_summary_transaction_count_ignores_type_breakdown(client):
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    })
    client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 20, "currency": "EUR", "type": "deposit",
    })
    client.post("/transactions", json={
        "fromAccount": ACC_1, "amount": 5, "currency": "USD", "type": "withdrawal",
    })

    resp = client.get(f"/accounts/{ACC_1}/summary")
    body = resp.json()
    assert body["transactionCount"] == 3
    assert body["totalDeposits"] == {"USD": "10.00", "EUR": "20.00"}
    assert body["totalWithdrawals"] == {"USD": "5.00"}


def test_summary_most_recent_transaction_date(client):
    t1 = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 10, "currency": "USD", "type": "deposit",
    }).json()
    t2 = client.post("/transactions", json={
        "toAccount": ACC_1, "amount": 20, "currency": "USD", "type": "deposit",
    }).json()
    _set_timestamp(t1["id"], "2024-01-01T10:00:00+00:00")
    _set_timestamp(t2["id"], "2024-06-15T08:30:00+00:00")

    resp = client.get(f"/accounts/{ACC_1}/summary")
    most_recent = resp.json()["mostRecentTransactionDate"]
    # Compare as parsed datetimes rather than raw strings, so this test
    # doesn't depend on the exact ISO-8601 formatting Pydantic emits.
    assert _parse_api_datetime(most_recent) == datetime.fromisoformat("2024-06-15T08:30:00+00:00")


def test_summary_account_not_found(client):
    resp = client.get("/accounts/ACC-99999/summary")
    assert resp.status_code == 404


def test_summary_invalid_account_format(client):
    resp = client.get("/accounts/not-an-account/summary")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Validation failed"
    assert any(d["field"] == "accountId" for d in body["details"])
