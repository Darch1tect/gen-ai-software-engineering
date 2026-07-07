# Prompt: README.md — for Developers

**Run with:** Fable 5 (`claude-fable-5`), alternative: Opus 4.8 (`claude-opus-4-8`)

---

You are a senior engineer writing the front-door document of this repository
for **developers who will clone, run, and extend the project**. Assume they
know Python and REST but have never seen this codebase.

## Context

Intelligent Customer Support System: a FastAPI service that imports support
tickets from CSV/JSON/XML, validates them, auto-classifies category and
priority with an explainable keyword engine, and keeps an audit log of every
classification decision. Stack: Python 3.12+, FastAPI, Pydantic v2,
SQLAlchemy 2, SQLite, pytest (+pytest-cov, 85% gate), uv.

## Read first (source of truth — do not invent anything)

1. Current `README.md` — reuse what is still accurate, restructure freely
2. `app/main.py`, `app/routers/tickets.py` — app wiring and all endpoints
3. `app/schemas.py`, `app/models.py` — domain model
4. `app/classifier.py`, `app/parsers.py` — the two core mechanisms
5. `pyproject.toml` — dependencies, test configuration
6. `tests/` and `samples/` directory listings

## Task

Rewrite `README.md` (repo root) with exactly these sections:

1. **Project overview and features** — 2–3 paragraphs: what it does, for
   whom; then a feature bullet list (import formats, validation, per-record
   error reporting, auto-classification with confidence + reasoning, manual
   override tracking, audit log, filtering/pagination, coverage gate).
2. **Architecture diagram** — one Mermaid `flowchart` (graph TD or LR):
   client → FastAPI router → Pydantic validation → parsers (CSV/JSON/XML) /
   classifier → SQLAlchemy → SQLite; show the classification_log table and
   the audit path. Max ~15 nodes, label the edges.
3. **Installation and setup** — prerequisites (uv; note it can install
   Python itself), `uv sync`, run server, where Swagger UI lives, note that
   `tickets.db` is created on startup and must be deleted after schema
   changes (no migrations yet).
4. **How to run tests** — `uv run pytest` (coverage gate at 85%),
   `--no-cov` variant, how to run a single file; current suite: 56 tests,
   ~96% coverage.
5. **Project structure** — annotated tree of `app/`, `tests/`, `samples/`,
   `scripts/`; one line per entry saying *why it exists*, not just what it is.

## Style

- Practical and terse; a developer should go from clone to green tests by
  copy-pasting commands top to bottom.
- Keep the endpoint summary table (method / path / description) — it earns
  its place in a README.
- No marketing language. No sections beyond the five above (plus the
  endpoint table wherever it fits best).

## Verify before writing

- [ ] `uv sync && uv run pytest -q` — confirm the test count and coverage
      number you cite are what actually prints
- [ ] Endpoint list matches `app/routers/tickets.py` exactly (8 routes + `/health`)
- [ ] Every command in the doc has been executed successfully in this repo
- [ ] Mermaid renders (mentally trace the syntax; no orphan nodes)
