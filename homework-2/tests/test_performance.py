"""Performance benchmarks with generous thresholds to stay CI-stable. (5 tests)"""

import json
from time import perf_counter

from app.classifier import classify

SUBJECT_POOL = [
    "Can't access my account",
    "Invoice question about a refund",
    "App crashes with an error",
    "Feature request: please add dark mode",
    "Steps to reproduce a broken export",
]
DESCRIPTION_POOL = [
    "My password reset link is rejected and the 2FA code never arrives at all.",
    "I was charged twice for my subscription, can I get a refund please?",
    "The dashboard shows an error and sometimes crashes without warning.",
    "It would be nice to add support for a dark theme across the product.",
    "Expected behavior: export works. Actual behavior: the export fails.",
]


def _records(count):
    return [
        {
            "customer_id": f"CUST-{i}",
            "customer_email": f"user{i}@example.com",
            "customer_name": f"User {i}",
            "subject": SUBJECT_POOL[i % len(SUBJECT_POOL)],
            "description": DESCRIPTION_POOL[i % len(DESCRIPTION_POOL)],
        }
        for i in range(count)
    ]


def test_bulk_import_1000_records_under_5s(client, upload):
    payload = json.dumps(_records(1000))
    start = perf_counter()
    response = upload("tickets.json", payload)
    elapsed = perf_counter() - start
    assert response.json()["successful"] == 1000
    assert elapsed < 5, f"bulk import of 1000 records took {elapsed:.2f}s"


def test_list_with_filters_on_1000_tickets_under_1s(client, upload):
    upload("tickets.json", json.dumps(_records(1000)))
    start = perf_counter()
    listed = client.get("/tickets", params={"limit": 500, "search": "refund"}).json()
    elapsed = perf_counter() - start
    assert len(listed) > 0
    assert elapsed < 1, f"filtered listing took {elapsed:.2f}s"


def test_classifier_throughput_1000_calls_under_2s():
    start = perf_counter()
    for i in range(1000):
        classify(SUBJECT_POOL[i % len(SUBJECT_POOL)], DESCRIPTION_POOL[i % len(DESCRIPTION_POOL)])
    elapsed = perf_counter() - start
    assert elapsed < 2, f"1000 classifications took {elapsed:.2f}s"


def test_single_create_latency(client, ticket_payload):
    runs = 30
    start = perf_counter()
    for i in range(runs):
        response = client.post("/tickets", json=dict(ticket_payload, customer_id=f"C-{i}"))
        assert response.status_code == 201
    average = (perf_counter() - start) / runs
    assert average < 0.1, f"average create latency {average * 1000:.1f}ms exceeds 100ms"


def test_import_with_auto_classify_500_records_under_5s(client, upload):
    payload = json.dumps(_records(500))
    start = perf_counter()
    summary = upload("tickets.json", payload, auto_classify="true").json()
    elapsed = perf_counter() - start
    assert summary["successful"] == 500
    assert elapsed < 5, f"classified import of 500 records took {elapsed:.2f}s"
