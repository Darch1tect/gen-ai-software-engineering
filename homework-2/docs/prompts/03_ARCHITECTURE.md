# Prompt: docs/ARCHITECTURE.md — for Technical Leads

**Run with:** Fable 5 (`claude-fable-5`), alternative: Opus 4.8 (`claude-opus-4-8`)

---

You are the architect of this system explaining it to **technical leads**
who must judge whether the design is sound, where it will break under
growth, and what to invest in next. They read code fluently but won't;
your document is their substitute. Honesty about limitations is the
whole value of this document — do not sell, assess.

## Read first

Entire `src/app/` package (it is small — read every file, don't skim),
`pyproject.toml`, `tests/test_performance.py`, and `git log --oneline`
for how the system evolved.

## Task

Write `docs/ARCHITECTURE.md` with:

1. **High-level architecture** — one Mermaid `flowchart` showing layers:
   HTTP/router → validation (Pydantic) → domain services (parsers,
   classifier) → persistence (SQLAlchemy → SQLite) and the audit side-channel
   (classification_log, app log). Follow with a one-paragraph narrative.
2. **Component descriptions** — for each module (`main`, `database`,
   `models`, `schemas`, `parsers`, `classifier`, `routers/tickets`): its
   single responsibility, key types, and what it deliberately does NOT do.
3. **Data flow diagrams** — two Mermaid `sequenceDiagram`s:
   a) bulk import: upload → format detection → parse → per-record validate
      → partial persist → summary (show the error-collection branch);
   b) auto-classification: request → keyword scoring → confidence → ticket
      update + audit log row; include the manual-override path via PUT.
4. **Design decisions and trade-offs** — table or subsections; at minimum:
   rule-based classifier vs LLM/ML (explainability, determinism, zero cost —
   vs recall ceiling); SQLite + create_all vs migrations (dev velocity vs
   schema-change pain, path to Alembic/Postgres); per-record import
   validation vs all-or-nothing transaction; append-only audit table without
   FK (survives ticket deletion) vs referential integrity; sync SQLAlchemy
   in async FastAPI (simplicity vs blocking under load); `tag` filter applied
   in Python after SQL pagination (correctness caveat — document it).
   For each: the decision, why, what it costs, and the trigger that should
   force revisiting it.
5. **Security considerations** — current posture is honest-by-omission:
   no auth/authz, no rate limiting, upload caps (10 MB / 10 000 records) as
   the only DoS guard, XML parsed with stdlib ElementTree (no external
   entities by default — state why that matters), email/PII stored in
   plaintext SQLite, no CORS policy. Rank what must change before any
   production exposure.
6. **Performance considerations** — measured envelope from the benchmark
   suite (cite thresholds from `tests/test_performance.py` and note real
   runs are ~10× under them); known ceilings: SQLite single-writer, O(n·k)
   regex classifier, in-process import loop; realistic scaling path
   (Postgres, background import jobs, classifier precompiled regex or
   vectorized/LLM stage).

## Style

- Written judgment, not a feature list: every section should answer
  "so what?" for a person allocating engineering time.
- ~3–5 pages. Diagrams small and legible; prose carries the argument.

## Verify before writing

- [ ] Every claim about behavior traced to a specific file/function
- [ ] Both sequence diagrams match the actual code paths (check
      `import_tickets` and `_auto_classify` line by line)
- [ ] Cited limits (10 MB, 10 000 records, 85% gate, thresholds) match code
- [ ] Mermaid syntax valid for GitHub rendering
