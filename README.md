# Intelligent Customer Support System

REST API for importing, classifying and prioritizing customer support tickets.

**Stack:** Python 3.12+ · FastAPI · Pydantic v2 · SQLAlchemy 2 · SQLite · pytest · uv

## Quick start

```bash
uv sync                          # install dependencies
uv run uvicorn app.main:app --reload
```

Interactive API docs: http://127.0.0.1:8000/docs

## Endpoints

| Method | Endpoint                            | Description                              |
|--------|-------------------------------------|------------------------------------------|
| POST   | `/tickets`                          | Create a new support ticket (201)        |
| POST   | `/tickets/import`                   | Bulk import from CSV / JSON / XML        |
| GET    | `/tickets`                          | List tickets with filtering & pagination |
| GET    | `/tickets/{id}`                     | Get a specific ticket (404 if missing)   |
| PUT    | `/tickets/{id}`                     | Partial update of a ticket               |
| DELETE | `/tickets/{id}`                     | Delete a ticket (204)                    |
| POST   | `/tickets/{id}/auto-classify`       | Classify the ticket and apply the result |
| GET    | `/tickets/{id}/classification-log`  | Audit trail of classification decisions  |

### Filtering (`GET /tickets`)

Query params: `status`, `priority`, `category`, `customer_id`, `assigned_to`,
`tag`, `search` (substring in subject/description), `limit` (default 50), `offset`.

### Bulk import (`POST /tickets/import`)

Multipart upload, field name `file`. Format is detected from the file extension
(`.csv`, `.json`, `.xml`) or Content-Type. Each record is validated
independently — one bad record never fails the whole file. Response:

```json
{
  "total_records": 3, "successful": 2, "failed": 1,
  "errors": [{"record": 2, "errors": ["customer_email: value is not a valid email address"]}],
  "created_ids": ["..."]
}
```

Malformed files (broken JSON/XML, non-UTF-8, empty, unsupported format) return
`400` with a message explaining what is wrong.

**CSV** — header row required; `tags` are `;`-separated; metadata is passed as
flat `source`, `browser`, `device_type` columns.
**JSON** — an array of ticket objects, or `{"tickets": [...]}`.
**XML** — `<tickets>` root with `<ticket>` children; `<tags><tag>…</tag></tags>`,
`<metadata><source>…</source></metadata>`.

## Auto-classification

`POST /tickets/{id}/auto-classify` runs a deterministic keyword classifier
([app/classifier.py](app/classifier.py)) and applies the result to the ticket:

```json
{
  "category": "billing_question",
  "priority": "medium",
  "confidence": 0.81,
  "reasoning": "Category 'billing_question' matched keywords: invoice, refund, charge (score 14 of 14 across all categories). No priority keywords matched; defaulting to 'medium'.",
  "keywords_found": ["invoice", "refund", "charge"]
}
```

- **Categories** are scored by weighted keyword matches (subject counts double).
  Reproduction signals (`steps to reproduce`, `expected/actual behavior`,
  numbered step lists) push a defect from `technical_issue` to `bug_report`.
  No matches → `other` with confidence 0.3.
- **Priority rules** (first match wins): urgent — `can't access`, `critical`,
  `production down`, `security`…; high — `important`, `blocking`, `asap`;
  low — `minor`, `cosmetic`, `suggestion`; default — `medium`.
- **Confidence** (0–1) grows with the winning category's dominance and the
  number of distinct keywords matched, capped at 0.95.
- **Auto-run on creation**: `POST /tickets?auto_classify=true` and
  `POST /tickets/import?auto_classify=true` classify on the fly (overriding
  any category/priority supplied in the payload/file).
- **Stored on the ticket**: `classification_confidence`,
  `classification_source` (`auto`/`manual`), `classified_at`.
- **Manual override**: updating `category`/`priority` via `PUT` marks the
  ticket `manual` with confidence 1.0.
- **Decision log**: every decision (auto and manual) is appended to the
  `classification_log` table — readable via
  `GET /tickets/{id}/classification-log` — and written to the app log.

## Ticket model

Validation rules: `customer_email` must be a valid email; `subject` 1–200 chars;
`description` 10–2000 chars; `category`, `priority`, `status`, `metadata.source`,
`metadata.device_type` are strict enums. Defaults: `category=other`,
`priority=medium`, `status=new`. `resolved_at` is set automatically when a
ticket transitions to `resolved`/`closed` and cleared when it is reopened.

## Sample data

`samples/` contains ready-to-import datasets for manual checks
(100 valid tickets total), regenerable with
`PYTHONPATH=. uv run python scripts/generate_samples.py`:

- `sample_tickets.csv` — 50 tickets
- `sample_tickets.json` — 20 tickets
- `sample_tickets.xml` — 30 tickets
- `invalid/` — negative-test files: records with broken fields
  (`invalid_tickets.csv/json/xml` → partial-import summaries with error
  details), plus structurally bad files (`malformed.json`, `malformed.xml`,
  `empty.csv`, `not_utf8.csv`, `unsupported.txt` → HTTP 400)

```bash
curl -X POST http://127.0.0.1:8000/tickets/import -F 'file=@samples/sample_tickets.csv'
```

## Tests

```bash
uv run pytest            # runs 56 tests with coverage (fails under 85%)
uv run pytest --no-cov   # without coverage
```

Coverage is enforced at **>85%** via `pytest-cov` (current: ~96%).

```
tests/
├── test_ticket_api.py       # API endpoints (11 tests)
├── test_ticket_model.py     # Data validation (9 tests)
├── test_import_csv.py       # CSV parsing (6 tests)
├── test_import_json.py      # JSON parsing (5 tests)
├── test_import_xml.py       # XML parsing (5 tests)
├── test_categorization.py   # Classification (10 tests)
├── test_integration.py      # End-to-end workflows (5 tests)
├── test_performance.py      # Benchmarks (5 tests)
└── fixtures/                # Sample data files (CSV/JSON/XML, valid + malformed)
```

## Project layout

```
app/
  main.py        # FastAPI app, lifespan (creates tables)
  database.py    # engine, session, Base
  models.py      # SQLAlchemy Ticket model
  schemas.py     # Pydantic schemas + enums
  parsers.py     # CSV / JSON / XML parsers
  routers/
    tickets.py   # all /tickets endpoints
tests/
```
