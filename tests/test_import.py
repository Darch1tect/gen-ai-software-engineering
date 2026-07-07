import json

VALID_ROW = {
    "customer_id": "CUST-100",
    "customer_email": "alice@example.com",
    "customer_name": "Alice",
    "subject": "App crashes on start",
    "description": "The mobile app crashes immediately after the splash screen.",
    "category": "bug_report",
    "priority": "urgent",
    "status": "new",
}


def _upload(client, filename, content, content_type):
    return client.post(
        "/tickets/import", files={"file": (filename, content, content_type)}
    )


def test_import_json_success(client):
    records = [
        VALID_ROW,
        dict(
            VALID_ROW,
            customer_email="bob@example.com",
            subject="Feature: dark mode",
            category="feature_request",
            tags=["ui", "dark-mode"],
            metadata={"source": "api"},
        ),
    ]
    response = _upload(client, "tickets.json", json.dumps(records), "application/json")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_records"] == 2
    assert summary["successful"] == 2
    assert summary["failed"] == 0
    assert len(summary["created_ids"]) == 2
    assert len(client.get("/tickets").json()) == 2


def test_import_json_wrapped_in_tickets_key(client):
    payload = {"tickets": [VALID_ROW]}
    response = _upload(client, "tickets.json", json.dumps(payload), "application/json")
    assert response.json()["successful"] == 1


def test_import_csv_success_with_tags_and_metadata(client):
    csv_content = (
        "customer_id,customer_email,customer_name,subject,description,"
        "category,priority,status,tags,source,browser,device_type\n"
        "CUST-1,a@example.com,Anna,Login broken,Cannot sign in since the last update happened,"
        "account_access,high,new,login;urgent-fix,web_form,Firefox 127,desktop\n"
        "CUST-2,b@example.com,Ben,Billing double charge,I was charged twice for my subscription,"
        "billing_question,medium,new,,email,,\n"
    )
    response = _upload(client, "tickets.csv", csv_content, "text/csv")
    assert response.status_code == 200
    summary = response.json()
    assert summary["successful"] == 2
    tickets = {t["subject"]: t for t in client.get("/tickets").json()}
    assert tickets["Login broken"]["tags"] == ["login", "urgent-fix"]
    assert tickets["Login broken"]["metadata"]["device_type"] == "desktop"
    assert tickets["Billing double charge"]["metadata"]["source"] == "email"
    assert tickets["Billing double charge"]["metadata"]["browser"] is None


def test_import_xml_success(client):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <tickets>
      <ticket>
        <customer_id>CUST-10</customer_id>
        <customer_email>carol@example.com</customer_email>
        <customer_name>Carol</customer_name>
        <subject>Password reset email never arrives</subject>
        <description>I requested a password reset three times and got nothing.</description>
        <category>account_access</category>
        <priority>high</priority>
        <status>new</status>
        <tags><tag>password</tag><tag>email</tag></tags>
        <metadata><source>phone</source></metadata>
      </ticket>
    </tickets>"""
    response = _upload(client, "tickets.xml", xml_content, "application/xml")
    assert response.status_code == 200
    summary = response.json()
    assert summary["successful"] == 1
    ticket = client.get(f"/tickets/{summary['created_ids'][0]}").json()
    assert ticket["tags"] == ["password", "email"]
    assert ticket["metadata"]["source"] == "phone"


def test_import_reports_partial_failures_with_details(client):
    records = [
        VALID_ROW,
        dict(VALID_ROW, customer_email="not-an-email"),
        dict(VALID_ROW, description="short", priority="mega-urgent"),
    ]
    response = _upload(client, "tickets.json", json.dumps(records), "application/json")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_records"] == 3
    assert summary["successful"] == 1
    assert summary["failed"] == 2

    by_record = {e["record"]: e["errors"] for e in summary["errors"]}
    assert 2 in by_record and 3 in by_record
    assert any("customer_email" in msg for msg in by_record[2])
    assert any("description" in msg for msg in by_record[3])
    assert any("priority" in msg for msg in by_record[3])
    # only the valid record was persisted
    assert len(client.get("/tickets").json()) == 1


def test_import_malformed_json_returns_400(client):
    response = _upload(client, "tickets.json", '[{"customer_id": ', "application/json")
    assert response.status_code == 400
    assert "Malformed JSON" in response.json()["detail"]


def test_import_malformed_xml_returns_400(client):
    response = _upload(client, "tickets.xml", "<tickets><ticket>", "application/xml")
    assert response.status_code == 400
    assert "Malformed XML" in response.json()["detail"]


def test_import_csv_without_header_reports_row_errors(client):
    # first data row is consumed as the header, remaining rows fail validation
    response = _upload(client, "tickets.csv", "just,some,random,cells\n1,2,3,4\n", "text/csv")
    assert response.status_code == 200
    assert response.json()["failed"] == response.json()["total_records"]


def test_import_unsupported_format_returns_400(client):
    response = _upload(client, "tickets.pdf", "%PDF-1.4", "application/pdf")
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_import_empty_file_returns_400(client):
    response = _upload(client, "tickets.csv", "", "text/csv")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_import_non_utf8_returns_400(client):
    response = _upload(client, "tickets.csv", b"\xff\xfe\x00broken", "text/csv")
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_import_json_with_non_object_items_reports_errors(client):
    response = _upload(client, "tickets.json", json.dumps([VALID_ROW, 42]), "application/json")
    summary = response.json()
    assert summary["successful"] == 1
    assert summary["failed"] == 1
