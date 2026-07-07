"""End-to-end workflow tests spanning several endpoints. (5 tests)"""

import json

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
