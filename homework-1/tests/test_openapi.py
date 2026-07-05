"""Contract tests for the generated OpenAPI schema.

These exist specifically to catch the schema/runtime mismatch a reviewer
flagged: FastAPI auto-documents a default 422 for request validation, but
this app's exception handler actually returns 400. See src/app.py's
`custom_openapi()`.
"""


def test_openapi_schema_does_not_advertise_422(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    offenders = []
    for path, methods in schema["paths"].items():
        for method, operation in methods.items():
            if "422" in operation.get("responses", {}):
                offenders.append(f"{method.upper()} {path}")
    assert offenders == [], f"these operations still document 422: {offenders}"


def test_openapi_documents_400_for_create_transaction(client):
    schema = client.get("/openapi.json").json()
    responses = schema["paths"]["/transactions"]["post"]["responses"]
    assert "400" in responses


def test_openapi_documents_400_for_list_transactions(client):
    schema = client.get("/openapi.json").json()
    responses = schema["paths"]["/transactions"]["get"]["responses"]
    assert "400" in responses


def test_openapi_documents_404_for_get_transaction_by_id(client):
    schema = client.get("/openapi.json").json()
    responses = schema["paths"]["/transactions/{transaction_id}"]["get"]["responses"]
    assert "404" in responses


def test_openapi_export_declares_csv_content_type(client):
    schema = client.get("/openapi.json").json()
    responses = schema["paths"]["/transactions/export"]["get"]["responses"]
    assert "200" in responses
    content = responses["200"].get("content", {})
    assert "text/csv" in content


def test_openapi_documents_400_and_404_for_account_routes(client):
    schema = client.get("/openapi.json").json()
    for suffix in ("balance", "summary", "interest"):
        responses = schema["paths"][f"/accounts/{{account_id}}/{suffix}"]["get"]["responses"]
        assert "400" in responses, f"{suffix} missing 400"
        assert "404" in responses, f"{suffix} missing 404"
