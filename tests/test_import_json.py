"""JSON parsing and import tests. (5 tests)"""

import json

from tests.conftest import FIXTURES_DIR


def test_import_json_array_success(client, upload_fixture):
    response = upload_fixture("sample.json")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_records"] == 2
    assert summary["successful"] == 2
    assert len(summary["created_ids"]) == 2

    ticket = client.get(f"/tickets/{summary['created_ids'][0]}").json()
    assert ticket["subject"] == "App crashes on start"
    assert ticket["tags"] == ["crash", "mobile"]
    assert ticket["metadata"]["source"] == "api"


def test_import_json_wrapped_in_tickets_key(upload):
    records = json.loads((FIXTURES_DIR / "sample.json").read_text())
    response = upload("tickets.json", json.dumps({"tickets": records}))
    assert response.json()["successful"] == 2


def test_import_malformed_json_returns_400(upload_fixture):
    response = upload_fixture("malformed.json")
    assert response.status_code == 400
    assert "Malformed JSON" in response.json()["detail"]


def test_import_json_non_array_returns_400(upload):
    response = upload("tickets.json", json.dumps({"just": "an object"}))
    assert response.status_code == 400
    assert "array" in response.json()["detail"]


def test_import_json_non_object_items_reported_as_failures(upload):
    records = json.loads((FIXTURES_DIR / "sample.json").read_text())
    response = upload("tickets.json", json.dumps([records[0], 42]))
    summary = response.json()
    assert summary["successful"] == 1
    assert summary["failed"] == 1
    assert summary["errors"][0]["record"] == 2
