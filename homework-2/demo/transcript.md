# Demo transcript

**Author:** Vitalii Roditieliev

Captured output of one full `./demo/demo.sh` run (2026-07-08). IDs and timestamps will differ between runs.

```text

════ Starting server on port 8030 (throwaway DB) ════
server is up: {"status":"ok"}

════ 1. Create a single ticket (as if from a web form) ════
{
    "id": "199a5045-8c86-4304-965a-0c847b3f0dc8",
    "customer_id": "CUST-DEMO-1",
    "customer_email": "olena@example.com",
    "customer_name": "Olena K",
    "subject": "Cannot access my account since yesterday",
    "description": "My password is rejected and the 2FA code never arrives. This is urgent, I am locked out.",
    "category": "other",
    "priority": "medium",
    "status": "new",
    "created_at": "2026-07-08T16:24:38.319703Z",
    "updated_at": "2026-07-08T16:24:38.319706Z",
    "resolved_at": null,
    "assigned_to": null,
    "tags": [],
    "metadata": {
        "source": "web_form",
        "browser": "Chrome 126",
        "device_type": "desktop"
    },
    "classification_confidence": null,
    "classification_source": null,
    "classified_at": null
}

════ 2. Auto-classify it — note the reasoning, keywords and confidence ════
{
    "category": "account_access",
    "priority": "urgent",
    "confidence": 0.87,
    "reasoning": "Category 'account_access' matched keywords: password, 2fa, locked out, access my account (score 14 of 14 across all categories). Priority 'urgent' matched keywords: cannot access, urgent.",
    "keywords_found": [
        "password",
        "2fa",
        "locked out",
        "access my account",
        "cannot access",
        "urgent"
    ]
}

════ 3. Bulk import 50 tickets from CSV with auto-classification ════
total=50  successful=50  failed=0

════ 4. Import a file with broken records — per-record error reporting ════
{
    "total_records": 5,
    "successful": 1,
    "failed": 4,
    "errors": [
        {
            "record": 2,
            "errors": [
                "customer_email: value is not a valid email address: An email address must have an @-sign."
            ]
        },
        {
            "record": 3,
            "errors": [
                "priority: Input should be 'urgent', 'high', 'medium' or 'low'",
                "status: Input should be 'new', 'in_progress', 'waiting_customer', 'resolved' or 'closed'"
            ]
        },
        {
            "record": 4,
            "errors": [
                "customer_email: Field required",
                "customer_name: Field required",
                "description: Field required"
            ]
        },
        {
            "record": 5,
            "errors": [
                "customer_id: Field required",
                "customer_email: Field required",
                "customer_name: Field required",
                "subject: Field required",
                "description: Field required",
                "_raw: Extra inputs are not permitted"
            ]
        }
    ],
    "created_ids": [
        "641612fa-0a10-463d-bb1d-79dc123c9d68"
    ]
}

════ 5. A malformed file never crashes the API ════
{"detail":"Malformed XML: no element found: line 2, column 0"}
HTTP 400

════ 6. Filtering: urgent tickets first ════
- [urgent] Cannot access my account since yesterday  (account_access)

════ 7. Combined filter: medium-priority billing questions ════
- [medium] Refund still not received
- [medium] Question about renewal price
- [medium] Charged twice this month
- [medium] General question about limits
- [medium] Update payment method

════ 8. A human disagrees: manual override of category and priority ════
category=technical_issue  priority=high  source=manual  confidence=1.0

════ 9. The audit log remembers every decision — auto and manual ════
#1 [auto] account_access/urgent conf=0.87
    Category 'account_access' matched keywords: password, 2fa, locked out, access my account (score 14 of 14 across all cate
#52 [manual] technical_issue/high conf=1.0
    Manual override via PUT /tickets/199a5045-8c86-4304-965a-0c847b3f0dc8: category=technical_issue, priority=high

════ Demo finished — server stopped, throwaway DB removed ════
```
