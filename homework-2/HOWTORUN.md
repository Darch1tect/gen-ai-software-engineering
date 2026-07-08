# How to Run

**Author:** Vitalii Roditieliev

Step-by-step guide to run the Intelligent Customer Support System locally.
Every command below is meant to be executed from the `homework-2/` directory.

## 1. Install uv (one-time)

The project is managed by [uv](https://docs.astral.sh/uv/), which also
installs the required Python version itself — no system Python needed.

```bash
# macOS
brew install uv

# or the universal installer (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `uv --version`.

## 2. Install dependencies

```bash
uv sync
```

This creates `.venv/`, installs the exact locked dependency versions from
`uv.lock`, and installs the application package (`src/app`) in editable mode.

## 3. Start the server

```bash
uv run uvicorn app.main:app --reload
```

- The API is now at http://127.0.0.1:8000
- Health check: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`
- The SQLite database file `tickets.db` is created automatically on startup.

Need a different port? Add `--port 8080`.

## 4. Open the interactive API docs

Open http://127.0.0.1:8000/docs — Swagger UI with every endpoint, request
schema, and a "Try it out" button. The full written reference is in
[docs/API_REFERENCE.md](docs/API_REFERENCE.md).

## 5. Make your first requests

Create a ticket:

```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H 'Content-Type: application/json' \
  -d '{
    "customer_id": "CUST-1",
    "customer_email": "olena@example.com",
    "customer_name": "Olena K",
    "subject": "Cannot access my account",
    "description": "My password is rejected and the 2FA code never arrives."
  }'
```

Auto-classify it (paste the `id` from the previous response):

```bash
curl -X POST http://127.0.0.1:8000/tickets/<id>/auto-classify
```

List urgent tickets:

```bash
curl 'http://127.0.0.1:8000/tickets?priority=urgent'
```

## 6. Bulk import the sample data

100 ready-made tickets in three formats live in `samples/`:

```bash
curl -X POST 'http://127.0.0.1:8000/tickets/import?auto_classify=true' \
     -F 'file=@samples/sample_tickets.csv'
```

Negative-test files are in `samples/invalid/` — e.g. importing
`invalid_tickets.json` returns a per-record error summary instead of
failing the whole file.

## 7. Run the demo (optional, recommended)

A self-contained walkthrough of every feature — starts its own server on
port 8030 with a throwaway database and cleans up after itself:

```bash
./demo/demo.sh
```

Expected output of a full run: [demo/transcript.md](demo/transcript.md).

## 8. Run the tests

```bash
uv run pytest            # 58 tests + coverage gate (fails under 85%)
uv run pytest --no-cov   # faster, without coverage
```

Expected result: `58 passed`, total coverage ~96%. More in
[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv: command not found` | Re-open the terminal after installing uv, or add `~/.local/bin` to `PATH` |
| Server fails on startup after pulling schema changes | Delete the dev database: `rm tickets.db` (no migrations yet — it is recreated on startup) |
| `Address already in use` on port 8000 | Run with another port: `uv run uvicorn app.main:app --port 8080` |
| Import returns 400 `Unsupported file format` | Make sure the file has a `.csv`/`.json`/`.xml` extension or send a matching `Content-Type` |
| Want a clean slate | Stop the server and `rm tickets.db` — next start creates an empty database |
