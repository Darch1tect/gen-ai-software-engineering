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

| Method | Endpoint           | Description                              |
|--------|--------------------|------------------------------------------|
| POST   | `/tickets`         | Create a new support ticket (201)        |
| POST   | `/tickets/import`  | Bulk import from CSV / JSON / XML        |
| GET    | `/tickets`         | List tickets with filtering & pagination |
| GET    | `/tickets/{id}`    | Get a specific ticket (404 if missing)   |
| PUT    | `/tickets/{id}`    | Partial update of a ticket               |
| DELETE | `/tickets/{id}`    | Delete a ticket (204)                    |

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

## Ticket model

Validation rules: `customer_email` must be a valid email; `subject` 1–200 chars;
`description` 10–2000 chars; `category`, `priority`, `status`, `metadata.source`,
`metadata.device_type` are strict enums. Defaults: `category=other`,
`priority=medium`, `status=new`. `resolved_at` is set automatically when a
ticket transitions to `resolved`/`closed` and cleared when it is reopened.

## Tests

```bash
uv run pytest
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
