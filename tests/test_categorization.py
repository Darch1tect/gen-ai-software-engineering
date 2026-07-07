"""Classification tests: keyword classifier + auto-classify endpoints. (10 tests)"""

from app.classifier import classify

BILLING_TICKET = {
    "customer_id": "CUST-500",
    "customer_email": "dana@example.com",
    "customer_name": "Dana",
    "subject": "Question about my invoice",
    "description": "I was charged twice for my subscription, can I get a refund please?",
}


def test_classify_account_access_urgent():
    result = classify(
        "Can't access my account",
        "My password reset link is rejected and the 2FA code never arrives.",
    )
    assert result.category.value == "account_access"
    assert result.priority.value == "urgent"
    assert "password" in result.keywords_found
    assert "can't access" in result.keywords_found
    assert 0 < result.confidence <= 1
    assert "account_access" in result.reasoning


def test_classify_billing_medium_by_default():
    result = classify(
        "Question about my invoice",
        "I was charged twice for my subscription, can I get a refund please?",
    )
    assert result.category.value == "billing_question"
    assert result.priority.value == "medium"


def test_classify_feature_request_low():
    result = classify(
        "Suggestion: dark mode",
        "It would be nice to add support for dark mode. Just a minor idea.",
    )
    assert result.category.value == "feature_request"
    assert result.priority.value == "low"


def test_classify_bug_report_beats_technical_issue_with_repro_steps():
    result = classify(
        "App crashes on file upload",
        "Steps to reproduce:\n1. Open the app\n2. Upload any file\n"
        "Expected behavior: the file uploads.\n"
        "Actual behavior: the app crashes with an error.",
    )
    assert result.category.value == "bug_report"
    assert "steps to reproduce" in result.keywords_found


def test_classify_plain_crash_is_technical_issue():
    result = classify(
        "Constant error messages",
        "The dashboard shows an error and sometimes crashes, no idea why.",
    )
    assert result.category.value == "technical_issue"


def test_classify_priority_rules():
    urgent = classify("Production down", "Our production down since 9am, critical for us.")
    assert urgent.priority.value == "urgent"
    high = classify("Export is broken", "This is important and blocking our team, fix asap.")
    assert high.priority.value == "high"
    low = classify("Cosmetic issue", "There is a minor typo on the settings page somewhere.")
    assert low.priority.value == "low"


def test_classify_no_keywords_falls_back_to_other():
    result = classify("Hello there", "Just wanted to say thanks for everything you do.")
    assert result.category.value == "other"
    assert result.priority.value == "medium"
    assert result.confidence == 0.3
    assert result.keywords_found == []


def test_auto_classify_endpoint(client):
    created = client.post("/tickets", json=BILLING_TICKET).json()
    assert created["category"] == "other"  # default, not classified yet
    assert created["classification_source"] is None

    response = client.post(f"/tickets/{created['id']}/auto-classify")
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "billing_question"
    assert body["priority"] == "medium"
    assert 0 < body["confidence"] <= 1
    assert body["keywords_found"]
    assert "billing_question" in body["reasoning"]

    ticket = client.get(f"/tickets/{created['id']}").json()
    assert ticket["category"] == "billing_question"
    assert ticket["classification_source"] == "auto"
    assert ticket["classification_confidence"] == body["confidence"]
    assert ticket["classified_at"] is not None


def test_auto_classify_missing_ticket_returns_404(client):
    assert client.post("/tickets/no-such-id/auto-classify").status_code == 404
    assert client.get("/tickets/no-such-id/classification-log").status_code == 404


def test_manual_override_is_tracked_and_logged(client):
    ticket_id = client.post(
        "/tickets", params={"auto_classify": "true"}, json=BILLING_TICKET
    ).json()["id"]

    response = client.put(
        f"/tickets/{ticket_id}", json={"category": "other", "priority": "low"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "other"
    assert body["classification_source"] == "manual"
    assert body["classification_confidence"] == 1.0

    log = client.get(f"/tickets/{ticket_id}/classification-log").json()
    assert len(log) == 2
    assert log[0]["source"] == "auto"
    assert log[0]["category"] == "billing_question"
    assert log[0]["keywords"]
    assert log[1]["source"] == "manual"
    assert log[1]["category"] == "other"
    assert log[1]["priority"] == "low"
    assert log[1]["confidence"] == 1.0
    assert "Manual override" in log[1]["reasoning"]
