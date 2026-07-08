"""CSV parsing and import tests. (6 tests)"""

from tests.conftest import FIXTURES_DIR


def test_import_csv_success_with_tags_and_metadata(client, upload_fixture):
    response = upload_fixture("sample.csv")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_records"] == 2
    assert summary["successful"] == 2
    assert summary["failed"] == 0

    tickets = {t["subject"]: t for t in client.get("/tickets").json()}
    assert tickets["Login broken"]["tags"] == ["login", "urgent-fix"]
    assert tickets["Login broken"]["metadata"]["device_type"] == "desktop"
    assert tickets["Billing double charge"]["metadata"]["source"] == "email"
    assert tickets["Billing double charge"]["metadata"]["browser"] is None


def test_import_csv_reports_invalid_rows_with_details(client, upload_fixture):
    summary = upload_fixture("invalid_rows.csv").json()
    assert summary["total_records"] == 2
    assert summary["successful"] == 1
    assert summary["failed"] == 1
    assert summary["errors"][0]["record"] == 2
    assert any("customer_email" in msg for msg in summary["errors"][0]["errors"])
    assert len(client.get("/tickets").json()) == 1  # only the valid row persisted


def test_import_csv_without_header_reports_row_errors(upload):
    # the first data row is consumed as the header, remaining rows fail validation
    response = upload("tickets.csv", "just,some,random,cells\n1,2,3,4\n")
    assert response.status_code == 200
    summary = response.json()
    assert summary["failed"] == summary["total_records"]


def test_import_empty_csv_returns_400(upload):
    response = upload("tickets.csv", "")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_import_non_utf8_csv_returns_400(upload):
    response = upload("tickets.csv", b"\xff\xfe\x00broken")
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_import_csv_detected_by_content_type_without_extension(upload):
    content = (FIXTURES_DIR / "sample.csv").read_bytes()
    response = upload("upload-without-extension", content, content_type="text/csv")
    assert response.status_code == 200
    assert response.json()["successful"] == 2
