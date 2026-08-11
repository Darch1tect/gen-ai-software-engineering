---
name: unit-tests-FIRST
description: Defines the FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely) that every generated unit test must satisfy. Use whenever writing or reviewing unit tests, especially in the Unit Test Generator agent.
---

# FIRST Principles for Unit Tests

The **Unit Test Generator** agent must apply this checklist to every test it
writes, and self-review the generated suite against it before running tests
and writing `test-report.md`.

## F — Fast

- A single test runs in milliseconds, not seconds. No `sleep`, no real
  network calls, no waiting on external services.
- Use in-memory fixtures (e.g. `sqlite3.connect(":memory:")`) instead of
  files or real databases/network I/O.
- **Check**: full generated suite runs in well under 1 second locally.

## I — Independent

- Each test sets up its own state (`setUp`/fixtures) and does not depend on
  execution order or on state left behind by another test.
- No shared mutable module-level state between tests; no test reads data
  written by a previous test.
- **Check**: running any single test in isolation (`-k test_name`) gives the
  same result as running the full suite.

## R — Repeatable

- Same result every run, in any environment (CI, local machine, offline).
- No dependence on wall-clock time, random seeds without fixing them,
  network availability, or machine-specific paths.
- **Check**: run the suite twice in a row; results must be identical.

## S — Self-validating

- Each test produces an unambiguous pass/fail via assertions — no tests that
  merely print output for a human to eyeball.
- One logical assertion focus per test (multiple related `assertEqual` calls
  for the same behavior are fine; testing unrelated behaviors in one test is
  not).
- **Check**: every test has at least one `assert*` call; test names describe
  the behavior being validated (`test_<unit>_<expected_behavior>`).

## T — Timely

- Tests are written alongside (immediately after, in this pipeline) the code
  change they cover, targeting the specific bug/change described in
  `fix-summary.md` — not written long after or for unrelated legacy code.
- Only new/changed code paths get new tests; do not regenerate the entire
  existing suite.
- **Check**: every generated test file/case traces back to a specific
  changed file:line in `fix-summary.md`.

## Reporting

`test-report.md` must include a short **FIRST Compliance** section
confirming each letter was checked, e.g.:

```
**FIRST Compliance**:
- Fast: suite runs in 0.01s (8 tests)
- Independent: each test uses its own in-memory DB/fixture via setUp
- Repeatable: no time/random/network dependencies
- Self-validating: all tests use assertEqual/assertRaises, no print-based checks
- Timely: every test maps to a changed function listed in fix-summary.md
```
