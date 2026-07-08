"""End-to-end workflow tests spanning several endpoints. (7 tests)"""

import json
from concurrent.futures import ThreadPoolExecutor

from tests.conftest import FIXTURES_DIR

NEUTRAL_TICKET = {
    "customer_id": "CUST-700",
    "customer_email": "lena@example.com",
    "customer_name": "Lena",
    "subject": "Problem with invoice",
    "description": "My latest invoice shows a double charge, I would like a refund.",
}


def test_full_ticket_lifecycle(client):
    assert client.get("/health").json() == {"status": "ok"}

    ticket_id = client.post("/tickets", json=NEUTRAL_TICKET).json()["id"]
    classification = client.post(f"/tickets/{ticket_id}/auto-classify").json()
    assert classification["category"] == "billing_question"

    client.put(f"/tickets/{ticket_id}", json={"assigned_to": "agent.o", "status": "in_progress"})
    resolved = client.put(f"/tickets/{ticket_id}", json={"status": "resolved"}).json()
    assert resolved["resolved_at"] is not None
    assert resolved["assigned_to"] == "agent.o"
    assert resolved["category"] == "billing_question"

    assert client.delete(f"/tickets/{ticket_id}").status_code == 204
    assert client.get(f"/tickets/{ticket_id}").status_code == 404


def test_import_all_three_formats_then_filter(client, upload_fixture):
    assert upload_fixture("sample.csv").json()["successful"] == 2
    assert upload_fixture("sample.json").json()["successful"] == 2
    assert upload_fixture("sample.xml").json()["successful"] == 1

    assert len(client.get("/tickets").json()) == 5
    billing = client.get("/tickets", params={"category": "billing_question"}).json()
    assert {t["subject"] for t in billing} == {"Billing double charge", "Refund not received"}
    urgent = client.get("/tickets", params={"priority": "urgent"}).json()
    assert len(urgent) == 2


def test_import_with_auto_classify_workflow(client, upload):
    records = [
        dict(NEUTRAL_TICKET, customer_id=f"CUST-70{i}", customer_email=f"user{i}@example.com")
        for i in range(3)
    ]
    summary = upload("tickets.json", json.dumps(records), auto_classify="true").json()
    assert summary["successful"] == 3

    for ticket_id in summary["created_ids"]:
        ticket = client.get(f"/tickets/{ticket_id}").json()
        assert ticket["category"] == "billing_question"
        assert ticket["classification_source"] == "auto"
        log = client.get(f"/tickets/{ticket_id}/classification-log").json()
        assert len(log) == 1
        assert log[0]["source"] == "auto"


def test_auto_create_then_manual_override_audit_trail(client):
    ticket_id = client.post(
        "/tickets", params={"auto_classify": "true"}, json=NEUTRAL_TICKET
    ).json()["id"]
    client.put(f"/tickets/{ticket_id}", json={"category": "other"})

    log = client.get(f"/tickets/{ticket_id}/classification-log").json()
    assert [e["source"] for e in log] == ["auto", "manual"]

    # updates that do not touch category/priority must not add audit entries
    client.put(f"/tickets/{ticket_id}", json={"assigned_to": "agent.k"})
    assert len(client.get(f"/tickets/{ticket_id}/classification-log").json()) == 2
    assert client.get(f"/tickets/{ticket_id}").json()["assigned_to"] == "agent.k"


def test_partial_import_then_fix_failed_record(client, upload_fixture):
    summary = upload_fixture("invalid_rows.csv").json()
    assert summary["successful"] == 1
    assert summary["failed"] == 1

    # resubmit the failed record with the email corrected
    fixed = client.post("/tickets", json={
        "customer_id": "CUST-11",
        "customer_email": "petro@example.com",
        "customer_name": "Petro",
        "subject": "Broken row",
        "description": "This row has an invalid email and must be rejected",
        "category": "technical_issue",
        "priority": "low",
    })
    assert fixed.status_code == 201
    assert len(client.get("/tickets").json()) == 2


def test_concurrent_operations(file_client):
    """20+ simultaneous requests: parallel creates, then mixed reads/updates."""
    client = file_client
    workers = 20
    total = 24

    def create(i):
        return client.post("/tickets", json={
            "customer_id": f"CUST-C{i}",
            "customer_email": f"concurrent{i}@example.com",
            "customer_name": f"Concurrent User {i}",
            "subject": f"Concurrent ticket {i}",
            "description": "Created from a concurrent worker to test simultaneous requests.",
        }).status_code

    with ThreadPoolExecutor(max_workers=workers) as pool:
        create_codes = list(pool.map(create, range(total)))
    assert create_codes == [201] * total

    tickets = client.get("/tickets", params={"limit": 100}).json()
    assert len(tickets) == total
    ids = [t["id"] for t in tickets]

    # interleaved reads and writes against the same set of tickets
    with ThreadPoolExecutor(max_workers=workers) as pool:
        read_futures = [pool.submit(client.get, f"/tickets/{tid}") for tid in ids]
        update_futures = [
            pool.submit(client.put, f"/tickets/{tid}", json={"status": "in_progress"})
            for tid in ids
        ]
    assert all(f.result().status_code == 200 for f in read_futures)
    assert all(f.result().status_code == 200 for f in update_futures)

    final = client.get("/tickets", params={"limit": 100}).json()
    assert len(final) == total
    assert all(t["status"] == "in_progress" for t in final)


def test_combined_filtering_by_category_and_priority(client, ticket_payload):
    combos = [
        ("billing_question", "high"),
        ("billing_question", "low"),
        ("technical_issue", "high"),
        ("feature_request", "medium"),
        ("billing_question", "high"),
    ]
    for i, (category, priority) in enumerate(combos):
        response = client.post("/tickets", json=dict(
            ticket_payload,
            customer_id=f"CUST-F{i}",
            subject=f"{category} / {priority} ticket {i}",
            category=category,
            priority=priority,
        ))
        assert response.status_code == 201

    matched = client.get(
        "/tickets", params={"category": "billing_question", "priority": "high"}
    ).json()
    assert len(matched) == 2
    assert all(
        t["category"] == "billing_question" and t["priority"] == "high" for t in matched
    )

    # each filter alone is wider than the combination
    assert len(client.get("/tickets", params={"category": "billing_question"}).json()) == 3
    assert len(client.get("/tickets", params={"priority": "high"}).json()) == 3
    # combination with no matches is empty, not an error
    none = client.get(
        "/tickets", params={"category": "feature_request", "priority": "urgent"}
    )
    assert none.status_code == 200
    assert none.json() == []
