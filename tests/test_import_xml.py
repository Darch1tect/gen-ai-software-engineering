"""XML parsing and import tests. (5 tests)"""


def test_import_xml_success_with_tags_and_metadata(client, upload_fixture):
    response = upload_fixture("sample.xml")
    assert response.status_code == 200
    summary = response.json()
    assert summary["successful"] == 1
    ticket = client.get(f"/tickets/{summary['created_ids'][0]}").json()
    assert ticket["subject"] == "Refund not received"
    assert ticket["tags"] == ["refund", "billing"]
    assert ticket["metadata"]["source"] == "phone"


def test_import_xml_single_ticket_root(upload):
    xml_content = """<ticket>
        <customer_id>CUST-31</customer_id>
        <customer_email>olga@example.com</customer_email>
        <customer_name>Olga</customer_name>
        <subject>Payment page timeout</subject>
        <description>The payment page times out every time I try to pay.</description>
    </ticket>"""
    response = upload("tickets.xml", xml_content)
    assert response.status_code == 200
    assert response.json()["successful"] == 1


def test_import_malformed_xml_returns_400(upload_fixture):
    response = upload_fixture("malformed.xml")
    assert response.status_code == 400
    assert "Malformed XML" in response.json()["detail"]


def test_import_xml_without_ticket_elements_returns_400(upload):
    response = upload("tickets.xml", "<tickets></tickets>")
    assert response.status_code == 400
    assert "<ticket>" in response.json()["detail"]


def test_import_xml_reports_invalid_records_with_details(upload):
    xml_content = """<tickets>
      <ticket>
        <customer_id>CUST-32</customer_id>
        <customer_email>bad-email</customer_email>
        <customer_name>Nina</customer_name>
        <subject>Broken record</subject>
        <description>This record has an invalid email and a bad priority.</description>
        <priority>mega-urgent</priority>
      </ticket>
    </tickets>"""
    summary = upload("tickets.xml", xml_content).json()
    assert summary["failed"] == 1
    messages = summary["errors"][0]["errors"]
    assert any("customer_email" in m for m in messages)
    assert any("priority" in m for m in messages)
