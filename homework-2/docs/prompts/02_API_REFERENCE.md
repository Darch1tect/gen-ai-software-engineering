# Prompt: docs/API_REFERENCE.md — for API Consumers

**Run with:** Sonnet 5 (`claude-sonnet-5`), budget alternative: Haiku 4.5

---

You are writing the complete API reference for **external developers who
integrate with this service over HTTP**. They never see the Python code —
the document must stand entirely on its own.

## Context

REST API for support tickets: CRUD, bulk import (CSV/JSON/XML), automatic
classification. Base URL in examples: `http://localhost:8000`. No
authentication (development service).

## Source of truth (in this order)

1. **The live OpenAPI schema** — run the server and fetch it; this is the
   contract: `uv run uvicorn app.main:app --port 8000 &` then
   `curl http://localhost:8000/openapi.json`
2. `src/app/routers/tickets.py` — status codes and error branches
3. `src/app/schemas.py` — every field, constraint, enum, default
4. `samples/` — realistic payloads to borrow for examples

Do not document anything not present in the code. Do not omit any route.

## Task

Write `docs/API_REFERENCE.md` with:

1. **Overview** — base URL, content types, a 5-line quick start.
2. **Endpoints** — one subsection per route (9 total: 8 ticket routes +
   `GET /health`). For each: method + path, purpose (1–2 sentences), query
   parameters table (name / type / default / description), request body
   example (where applicable), **success response example with real JSON**
   (status code shown), and every error status it can return.
3. **Data models** — tables for Ticket (all fields incl.
   `classification_*`), TicketMetadata, ImportSummary, ClassificationResult,
   ClassificationLog entry; every enum with its allowed values; validation
   constraints (subject 1–200, description 10–2000, email format).
4. **Error response formats** — the three shapes a client will meet:
   FastAPI 422 validation body, `{"detail": "..."}` for 400/404/413, and
   per-record errors inside the import summary (with an example of each).
5. **cURL examples for each endpoint** — copy-pasteable, using
   `samples/sample_tickets.csv` for import, including one partial-failure
   import (`samples/invalid/invalid_tickets.json`) and one 404.
6. **Import file formats** — expected CSV columns (tags `;`-separated,
   flat `source`/`browser`/`device_type`), JSON array or `{"tickets": []}`
   wrapper, XML element structure; limits (10 MB, 10 000 records).

## Style

- Reference style: consistent, dense, zero narrative filler.
- All example JSON must be **actual responses** you got from the running
  server, lightly trimmed — not hand-written guesses.

## Verify before writing

- [ ] Every documented route exists in `openapi.json`; none missing
- [ ] Run each cURL example against the live server; paste real output
- [ ] Enum values match `src/app/schemas.py` letter-for-letter
- [ ] The three error-shape examples were actually provoked, not invented
- [ ] Stop the server and delete `tickets.db` when done
