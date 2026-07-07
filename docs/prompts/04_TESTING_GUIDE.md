# Prompt: docs/TESTING_GUIDE.md — for QA Engineers

**Run with:** Sonnet 5 (`claude-sonnet-5`)

---

You are writing the testing handbook for **QA engineers** joining the
project: they must be able to run the suite, understand what is covered,
test the API manually with prepared data, and add new tests that fit the
existing conventions.

## Read first

1. `pyproject.toml` — pytest/coverage configuration (85% gate in `addopts`)
2. `tests/conftest.py` — the `client`, `upload`, `upload_fixture`,
   `ticket_payload` fixtures (in-memory SQLite per test, full isolation)
3. All 8 test files in `tests/` and `tests/fixtures/`
4. `samples/` and `samples/invalid/` — manual-testing datasets
5. `scripts/generate_samples.py` — how samples are produced

## Task

Write `docs/TESTING_GUIDE.md` with:

1. **Test pyramid** — Mermaid diagram mapping the actual suite to levels:
   unit (model validation 9, classifier unit portion of categorization),
   service/API (endpoint + import tests), integration workflows (7,
   incl. a 20-worker concurrency test on a file-backed DB), performance
   (5); 58 tests total. Note what is intentionally absent (no UI layer →
   no E2E browser tier).
2. **How to run tests** — full suite (coverage gate fails under 85%),
   `--no-cov`, single file, single test, verbose benchmark run
   (`uv run pytest tests/test_performance.py -v --no-cov`); how to read the
   coverage table and the current ~96% baseline; what to do when the gate
   trips.
3. **Test suite map** — table: file → scope → count → what it protects
   (11/9/6/5/5/10/7/5), plus `fixtures/` contents and the conftest fixtures
   (incl. `file_client` for concurrency) with one line on when to use each.
   Embed the coverage screenshot `docs/screenshots/test_coverage.png`.
4. **Sample test data locations** — `tests/fixtures/` (small, wired into
   automated tests) vs `samples/` (large, for manual/exploratory work:
   50 CSV / 20 JSON / 30 XML valid; `invalid/` with per-record-broken and
   structurally-broken files and the exact failure each must produce);
   regeneration command.
5. **Manual testing checklist** — step-by-step scripted pass over the live
   server (start command included): create → get → list with each filter →
   update/resolve → delete → 404s; import each of the three sample files
   and check the summary counts (50/20/30, 0 failed); import each
   `samples/invalid/*` file and check the expected outcome (which give
   partial summaries with which counts, which give 400 and with what
   message, 413 case); auto-classify flow incl. manual override and
   audit-log verification; Swagger UI spot-check. Format as checkboxes
   with expected results — an engineer ticks them off.
6. **Performance benchmarks table** — columns: scenario / dataset /
   threshold / typical actual / test name. Thresholds from
   `tests/test_performance.py`; fill "typical actual" by running the
   benchmarks and recording real numbers. State the flakiness policy
   (thresholds are deliberately ~10× above typical).
7. **Adding new tests** — conventions: which file a new test belongs in,
   using the fixtures instead of raw TestClient, fixtures vs samples,
   keeping the coverage gate green.

## Style

- Handbook tone: imperative, checklist-heavy, zero theory beyond the
  pyramid section.

## Verify before writing

- [ ] Run the full suite; every count and the coverage % you cite are real
- [ ] Run the performance tests; record actual timings for the table
- [ ] Walk the manual checklist yourself against a live server once —
      every expected result in the doc is something you observed
