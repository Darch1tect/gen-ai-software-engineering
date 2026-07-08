# API Reference

**Author:** Vitalii Roditieliev

REST API for support tickets: CRUD, bulk import (CSV/JSON/XML), and automatic
classification.

- **Base URL:** `http://localhost:8000`
- **Content type:** `application/json` for all endpoints except
  `POST /tickets/import`, which takes `multipart/form-data`.
- **Authentication:** none (development service).

**Quick start**

```bash
uv run uvicorn app.main:app --port 8000
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-001","customer_email":"jane@example.com","customer_name":"Jane Doe","subject":"Cannot log in","description":"Login keeps failing after password reset."}'
```

---

## Endpoints

### `GET /health`

Liveness check.

**Response `200`**

```json
{"status": "ok"}
```

---

### `POST /tickets`

Create a single ticket.

**Query parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `auto_classify` | bool | `false` | Classify the ticket on creation; overrides any `category`/`priority` in the body |

**Request body** — `TicketCreate` (see [Data models](#data-models))

```json
{
  "customer_id": "cust-001",
  "customer_email": "jane.doe@example.com",
  "customer_name": "Jane Doe",
  "subject": "Cannot log into my account",
  "description": "I keep getting an invalid password error even though I reset it twice.",
  "tags": ["login", "urgent"],
  "metadata": {"source": "web_form", "browser": "Chrome 126", "device_type": "desktop"}
}
```

**Response `201`** — `TicketOut`

```json
{
  "id": "01a91d65-2764-4e47-8074-67e565279638",
  "customer_id": "cust-001",
  "customer_email": "jane.doe@example.com",
  "customer_name": "Jane Doe",
  "subject": "Cannot log into my account",
  "description": "I keep getting an invalid password error even though I reset it twice.",
  "category": "other",
  "priority": "medium",
  "status": "new",
  "created_at": "2026-07-07T23:57:03.427899Z",
  "updated_at": "2026-07-07T23:57:03.427902Z",
  "resolved_at": null,
  "assigned_to": null,
  "tags": ["login", "urgent"],
  "metadata": {"source": "web_form", "browser": "Chrome 126", "device_type": "desktop"},
  "classification_confidence": null,
  "classification_source": null,
  "classified_at": null
}
```

With `?auto_classify=true`, `category`/`priority` are overwritten by the
classifier and the classification fields are populated:

```json
{
  "id": "157f1123-f106-4798-b11d-478dc681a9d0",
  "category": "billing_question",
  "priority": "medium",
  "classification_confidence": 0.9,
  "classification_source": "auto",
  "classified_at": "2026-07-07T23:57:10.624902Z",
  "...": "remaining fields as above"
}
```

If `status` is set to `resolved` or `closed` on creation, `resolved_at` is
stamped immediately.

**Errors:** `422` (validation — see [Error response formats](#error-response-formats))

---

### `POST /tickets/import`

Bulk-import tickets from a `.csv`, `.json`, or `.xml` file. Records are
validated independently — one bad record does not fail the whole import.

**Query parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `auto_classify` | bool | `false` | Classify every imported ticket; overrides `category`/`priority` from the file |

**Body:** `multipart/form-data` with a `file` field. Format is detected from
the filename extension first, then the `Content-Type` header.

**Response `200`** — `ImportSummary`

```json
{
  "total_records": 3,
  "successful": 3,
  "failed": 0,
  "errors": [],
  "created_ids": [
    "3a6c1541-28dd-4914-ad13-b90b207f0c7b",
    "516df4e6-9259-4855-aeb2-a83cec607ba0",
    "e4203f4a-0c68-4e41-8a05-a4ce5f6e9d81"
  ]
}
```

Partial-failure example (5 records, 4 invalid — see
[Error response formats](#error-response-formats) for the per-record shape).

**Errors**

| Status | Cause |
|---|---|
| `400` | Unsupported file extension/content type, empty file, or malformed CSV/JSON/XML |
| `413` | File exceeds the 10 MB upload limit |

Limits: **10 MB** max file size, **10,000** records max per import
(a larger file raises the `400` "limit per import" error, since the record
count is only known after parsing).

---

### `GET /tickets`

List tickets with optional filters, sorted by `created_at` descending.

**Query parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `status` | enum `Status` | — | Filter by status |
| `priority` | enum `Priority` | — | Filter by priority |
| `category` | enum `Category` | — | Filter by category |
| `customer_id` | string | — | Filter by exact customer ID |
| `assigned_to` | string | — | Filter by exact assignee |
| `tag` | string | — | Return tickets carrying this tag |
| `search` | string | — | Case-insensitive substring match in subject/description |
| `limit` | int | `50` | Page size, `1`–`500` |
| `offset` | int | `0` | Pagination offset |

**Response `200`** — `array<TicketOut>`

```json
[
  {
    "id": "157f1123-f106-4798-b11d-478dc681a9d0",
    "customer_id": "cust-002",
    "customer_email": "bob@example.com",
    "customer_name": "Bob Smith",
    "subject": "Billing charge is wrong",
    "description": "I was charged twice for my subscription this month, please refund the duplicate charge.",
    "category": "billing_question",
    "priority": "medium",
    "status": "new",
    "created_at": "2026-07-07T23:57:10.623510",
    "updated_at": "2026-07-07T23:57:10.626144",
    "resolved_at": null,
    "assigned_to": null,
    "tags": [],
    "metadata": {"source": "email", "browser": null, "device_type": null},
    "classification_confidence": 0.9,
    "classification_source": "auto",
    "classified_at": "2026-07-07T23:57:10.624902"
  }
]
```

**Errors:** `422` if `limit`/`offset`/enum query params are out of range or invalid.

---

### `GET /tickets/{ticket_id}`

Fetch a single ticket.

**Response `200`** — `TicketOut` (same shape as above)

**Errors:** `404` if the ticket does not exist.

---

### `PUT /tickets/{ticket_id}`

Partially update a ticket. Only fields present in the body are changed
(`TicketUpdate`, all fields optional).

**Request body**

```json
{"priority": "high", "status": "in_progress", "assigned_to": "agent-42"}
```

**Response `200`** — `TicketOut`

```json
{
  "id": "01a91d65-2764-4e47-8074-67e565279638",
  "priority": "high",
  "status": "in_progress",
  "assigned_to": "agent-42",
  "classification_confidence": 1.0,
  "classification_source": "manual",
  "classified_at": "2026-07-07T23:57:20.702162Z",
  "...": "remaining fields unchanged"
}
```

**Side effects**

- Setting `category` and/or `priority` logs a `manual` classification-log
  entry with `confidence = 1.0` and a `reasoning` string naming the
  overridden field(s), e.g.
  `"Manual override via PUT /tickets/{id}: priority=high"`.
- Setting `status` to `resolved`/`closed` stamps `resolved_at` (if not
  already set); setting it to any other status clears `resolved_at`.

**Errors:** `404` (not found), `422` (validation).

---

### `DELETE /tickets/{ticket_id}`

Delete a ticket.

**Response:** `204 No Content` (empty body).

**Errors:** `404` if the ticket does not exist.

---

### `POST /tickets/{ticket_id}/auto-classify`

Run the classifier against the ticket's current `subject`/`description` and
apply the result (`category`, `priority`, `classification_confidence`,
`classification_source = "auto"`, `classified_at`), appending an `auto`
classification-log entry.

**Response `200`** — `ClassificationResult`

```json
{
  "category": "account_access",
  "priority": "medium",
  "confidence": 0.43,
  "reasoning": "Category 'account_access' matched keywords: password (score 2 of 4 across all categories). No priority keywords matched; defaulting to 'medium'.",
  "keywords_found": ["password"]
}
```

**Errors:** `404` if the ticket does not exist.

---

### `GET /tickets/{ticket_id}/classification-log`

Return the full classification audit trail for a ticket (both `auto` runs
and `manual` overrides), ordered oldest to newest.

**Response `200`** — `array<ClassificationLogOut>`

```json
[
  {
    "id": 2,
    "ticket_id": "01a91d65-2764-4e47-8074-67e565279638",
    "source": "manual",
    "category": "other",
    "priority": "high",
    "confidence": 1.0,
    "reasoning": "Manual override via PUT /tickets/01a91d65-2764-4e47-8074-67e565279638: priority=high",
    "keywords": [],
    "created_at": "2026-07-07T23:57:20.702372"
  },
  {
    "id": 3,
    "ticket_id": "01a91d65-2764-4e47-8074-67e565279638",
    "source": "auto",
    "category": "account_access",
    "priority": "medium",
    "confidence": 0.43,
    "reasoning": "Category 'account_access' matched keywords: password (score 2 of 4 across all categories). No priority keywords matched; defaulting to 'medium'.",
    "keywords": ["password"],
    "created_at": "2026-07-07T23:57:20.714729"
  }
]
```

**Errors:** `404` if the ticket does not exist.

---

## Data models

### Ticket (`TicketOut`)

| Field | Type | Notes |
|---|---|---|
| `id` | string (UUID) | Server-generated |
| `customer_id` | string | 1–100 chars |
| `customer_email` | string | Valid email address |
| `customer_name` | string | 1–200 chars |
| `subject` | string | 1–200 chars |
| `description` | string | 10–2000 chars |
| `category` | `Category` | Default `other` |
| `priority` | `Priority` | Default `medium` |
| `status` | `Status` | Default `new` |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `resolved_at` | datetime \| null | Set when status becomes `resolved`/`closed` |
| `assigned_to` | string \| null | |
| `tags` | string[] | Default `[]` |
| `metadata` | `TicketMetadata` \| null | |
| `classification_confidence` | float \| null | `0`–`1` |
| `classification_source` | `ClassificationSource` \| null | |
| `classified_at` | datetime \| null | |

### TicketMetadata

| Field | Type | Notes |
|---|---|---|
| `source` | `Source` | Required |
| `browser` | string \| null | |
| `device_type` | `DeviceType` \| null | |

### ImportSummary

| Field | Type |
|---|---|
| `total_records` | int |
| `successful` | int |
| `failed` | int |
| `errors` | `ImportError_[]` |
| `created_ids` | string[] |

`ImportError_`: `{"record": int (1-based index in the source file), "errors": string[]}`

### ClassificationResult

| Field | Type |
|---|---|
| `category` | `Category` |
| `priority` | `Priority` |
| `confidence` | float (`0`–`1`) |
| `reasoning` | string |
| `keywords_found` | string[] |

### ClassificationLog entry (`ClassificationLogOut`)

| Field | Type |
|---|---|
| `id` | int |
| `ticket_id` | string |
| `source` | `ClassificationSource` |
| `category` | `Category` |
| `priority` | `Priority` |
| `confidence` | float \| null |
| `reasoning` | string |
| `keywords` | string[] |
| `created_at` | datetime |

### Enums

| Enum | Values |
|---|---|
| `Category` | `account_access`, `technical_issue`, `billing_question`, `feature_request`, `bug_report`, `other` |
| `Priority` | `urgent`, `high`, `medium`, `low` |
| `Status` | `new`, `in_progress`, `waiting_customer`, `resolved`, `closed` |
| `Source` | `web_form`, `email`, `api`, `chat`, `phone` |
| `DeviceType` | `desktop`, `mobile`, `tablet` |
| `ClassificationSource` | `auto`, `manual` |

### Validation constraints

- `subject`: 1–200 characters
- `description`: 10–2000 characters
- `customer_id`: 1–100 characters
- `customer_name`: 1–200 characters
- `customer_email`: must be a valid email address
- All request schemas use `extra="forbid"` — unknown fields are rejected.

---

## Error response formats

**1. FastAPI `422` validation error** (`POST /tickets`, `PUT /tickets/{id}`, invalid query params)

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "customer_id"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    },
    {
      "type": "value_error",
      "loc": ["body", "customer_email"],
      "msg": "value is not a valid email address: An email address must have an @-sign.",
      "input": "not-an-email",
      "ctx": {"reason": "An email address must have an @-sign."}
    }
  ]
}
```

**2. `{"detail": "..."}` string** (`400`, `404`, `413`)

```json
{"detail": "Ticket does-not-exist not found"}
```

```json
{"detail": "File exceeds the 10 MB upload limit"}
```

**3. Per-record errors inside an import summary** (`200`, embedded in `ImportSummary.errors`)

```json
{
  "record": 2,
  "errors": ["customer_email: value is not a valid email address: An email address must have an @-sign."]
}
```

A record can fail with multiple errors at once, e.g. an invalid enum plus a
missing field:

```json
{
  "record": 3,
  "errors": [
    "priority: Input should be 'urgent', 'high', 'medium' or 'low'",
    "status: Input should be 'new', 'in_progress', 'waiting_customer', 'resolved' or 'closed'"
  ]
}
```

---

## cURL examples

**Health check**

```bash
curl http://localhost:8000/health
```

**Create a ticket**

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-001",
    "customer_email": "jane.doe@example.com",
    "customer_name": "Jane Doe",
    "subject": "Cannot log into my account",
    "description": "I keep getting an invalid password error even though I reset it twice.",
    "tags": ["login", "urgent"],
    "metadata": {"source": "web_form", "browser": "Chrome 126", "device_type": "desktop"}
  }'
```

**Create and auto-classify in one call**

```bash
curl -X POST "http://localhost:8000/tickets?auto_classify=true" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-002",
    "customer_email": "bob@example.com",
    "customer_name": "Bob Smith",
    "subject": "Billing charge is wrong",
    "description": "I was charged twice for my subscription this month, please refund the duplicate charge.",
    "metadata": {"source": "email"}
  }'
```

**Bulk import from CSV**

```bash
curl -X POST http://localhost:8000/tickets/import \
  -F "file=@samples/sample_tickets.csv;type=text/csv"
```

**Bulk import with a partial failure** (2 of 5 records are valid — malformed
email, invalid enum values, and missing required fields in the rest)

```bash
curl -X POST http://localhost:8000/tickets/import \
  -F "file=@samples/invalid/invalid_tickets.json;type=application/json"
```

**List tickets with filters**

```bash
curl "http://localhost:8000/tickets?status=new&priority=high&limit=20"
```

**Get a ticket**

```bash
curl http://localhost:8000/tickets/01a91d65-2764-4e47-8074-67e565279638
```

**Get a nonexistent ticket (404)**

```bash
curl http://localhost:8000/tickets/does-not-exist
# {"detail":"Ticket does-not-exist not found"}
```

**Update a ticket (manual category/priority override)**

```bash
curl -X PUT http://localhost:8000/tickets/01a91d65-2764-4e47-8074-67e565279638 \
  -H "Content-Type: application/json" \
  -d '{"priority": "high", "status": "in_progress", "assigned_to": "agent-42"}'
```

**Run the classifier on a ticket**

```bash
curl -X POST http://localhost:8000/tickets/01a91d65-2764-4e47-8074-67e565279638/auto-classify
```

**Get a ticket's classification log**

```bash
curl http://localhost:8000/tickets/01a91d65-2764-4e47-8074-67e565279638/classification-log
```

**Delete a ticket**

```bash
curl -X DELETE http://localhost:8000/tickets/01a91d65-2764-4e47-8074-67e565279638
```

---

## Import file formats

All three formats validate identically once parsed — invalid or missing
fields produce a per-record error in `ImportSummary.errors` rather than
failing the whole import.

**Limits:** 10 MB max file size, 10,000 records max per file.

### CSV

Header row required. Recognized columns match the `TicketCreate` field
names, plus:

- `tags` — `;`-separated list, e.g. `2fa;login`
- `source`, `browser`, `device_type` — flat columns that get folded into a
  nested `metadata` object during parsing

```csv
customer_id,customer_email,customer_name,subject,description,category,priority,status,assigned_to,tags,source,browser,device_type
CUST-1000,ann@example.com,Ann Shevchenko,Can't log in,After the last password reset my login attempts fail.,account_access,low,resolved,agent.olha,2fa;login,email,Firefox 127,desktop
```

Empty cells are omitted from the record (so schema defaults apply). A blank
file (header only or truly empty) raises a `400`.

### JSON

Either a top-level array of ticket objects, or an object with a `tickets`
array:

```json
[{"customer_id": "CUST-1210", "customer_email": "roman@example.com", "customer_name": "Roman Lysenko", "subject": "Refund still not received", "description": "I cancelled two weeks ago and the promised refund has not reached my credit card.", "category": "billing_question", "priority": "medium", "status": "resolved", "tags": ["refund", "invoice"], "metadata": {"source": "api", "browser": "Chrome 126"}, "assigned_to": "agent.smith"}]
```

```json
{"tickets": [ /* same ticket objects */ ]}
```

`tags` and `metadata` are already nested — no flattening. Non-object array
entries (e.g. a bare string) are wrapped as `{"_raw": <value>}`, which fails
validation with an `"Extra inputs are not permitted"` error since `_raw`
isn't a real field.

### XML

A `<tickets>` root with `<ticket>` children (a lone `<ticket>` root is also
accepted). Child elements map directly to fields; `<tags>` holds repeated
`<tag>` elements, `<metadata>` holds `<source>`/`<browser>`/`<device_type>`.

```xml
<?xml version='1.0' encoding='utf-8'?>
<tickets>
  <ticket>
    <customer_id>CUST-1070</customer_id>
    <customer_email>nina@example.com</customer_email>
    <customer_name>Nina Shevchenko</customer_name>
    <subject>Refund still not received</subject>
    <description>I cancelled two weeks ago and the promised refund has not reached my credit card.</description>
    <category>billing_question</category>
    <priority>medium</priority>
    <status>closed</status>
    <assigned_to>agent.kova</assigned_to>
    <tags>
      <tag>refund</tag>
    </tags>
    <metadata>
      <source>email</source>
      <browser>Edge 125</browser>
      <device_type>mobile</device_type>
    </metadata>
  </ticket>
</tickets>
```
</content>
