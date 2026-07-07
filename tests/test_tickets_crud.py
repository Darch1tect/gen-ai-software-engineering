def test_create_ticket_returns_201_with_defaults(client, ticket_payload):
    response = client.post("/tickets", json=ticket_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["status"] == "new"
    assert body["priority"] == "high"
    assert body["resolved_at"] is None
    assert body["tags"] == ["login", "password"]
    assert body["metadata"]["source"] == "web_form"
    assert body["created_at"]


def test_create_ticket_rejects_invalid_email(client, ticket_payload):
    ticket_payload["customer_email"] = "not-an-email"
    response = client.post("/tickets", json=ticket_payload)
    assert response.status_code == 422


def test_create_ticket_rejects_short_description(client, ticket_payload):
    ticket_payload["description"] = "too short"
    response = client.post("/tickets", json=ticket_payload)
    assert response.status_code == 422


def test_create_ticket_rejects_bad_enum(client, ticket_payload):
    ticket_payload["category"] = "nonsense"
    response = client.post("/tickets", json=ticket_payload)
    assert response.status_code == 422


def test_get_ticket(client, ticket_payload):
    ticket_id = client.post("/tickets", json=ticket_payload).json()["id"]
    response = client.get(f"/tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json()["subject"] == ticket_payload["subject"]


def test_get_missing_ticket_returns_404(client):
    assert client.get("/tickets/no-such-id").status_code == 404


def test_list_tickets_with_filters(client, ticket_payload):
    client.post("/tickets", json=ticket_payload)
    other = dict(
        ticket_payload,
        subject="Invoice is wrong",
        category="billing_question",
        priority="low",
        description="The invoice for June charges me twice for the same subscription.",
        tags=["billing"],
    )
    client.post("/tickets", json=other)

    assert len(client.get("/tickets").json()) == 2
    billing = client.get("/tickets", params={"category": "billing_question"}).json()
    assert len(billing) == 1
    assert billing[0]["subject"] == "Invoice is wrong"
    assert len(client.get("/tickets", params={"priority": "high"}).json()) == 1
    assert len(client.get("/tickets", params={"search": "invoice"}).json()) == 1
    assert len(client.get("/tickets", params={"tag": "login"}).json()) == 1


def test_list_tickets_rejects_bad_filter_value(client):
    assert client.get("/tickets", params={"status": "bogus"}).status_code == 422


def test_update_ticket(client, ticket_payload):
    ticket_id = client.post("/tickets", json=ticket_payload).json()["id"]
    response = client.put(
        f"/tickets/{ticket_id}",
        json={"status": "resolved", "assigned_to": "agent.smith"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["assigned_to"] == "agent.smith"
    assert body["resolved_at"] is not None

    reopened = client.put(f"/tickets/{ticket_id}", json={"status": "in_progress"}).json()
    assert reopened["resolved_at"] is None


def test_update_missing_ticket_returns_404(client):
    assert client.put("/tickets/no-such-id", json={"priority": "low"}).status_code == 404


def test_update_rejects_unknown_field(client, ticket_payload):
    ticket_id = client.post("/tickets", json=ticket_payload).json()["id"]
    response = client.put(f"/tickets/{ticket_id}", json={"not_a_field": 1})
    assert response.status_code == 422


def test_delete_ticket(client, ticket_payload):
    ticket_id = client.post("/tickets", json=ticket_payload).json()["id"]
    assert client.delete(f"/tickets/{ticket_id}").status_code == 204
    assert client.get(f"/tickets/{ticket_id}").status_code == 404
    assert client.delete(f"/tickets/{ticket_id}").status_code == 404
