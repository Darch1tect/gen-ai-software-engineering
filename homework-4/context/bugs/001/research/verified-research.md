# Verified Research: 001

## Verification Summary
- **Result**: PASS (per `skills/research-quality-measurement.md` gate: every cited `file:line` verified AND total score ≥ 8)
- **Research Quality**: EXCELLENT (12/12)
- **Claims checked**: 24 / **Verified**: 24 / **Discrepancies**: 0

Every `file:line` cited in `context/bugs/001/research/codebase-research.md` was
opened and compared against source. All three reported issues are real, present
at the claimed locations, and the quoted snippets match source **verbatim**
(character-for-character, including docstrings and indentation). The predicted
buggy return values were additionally confirmed by execution (see
*Runtime Confirmation* below), so no claim rests on reading alone.

## Verified Claims

### Issue 1 — `calculate_total` off-by-one

| # | Claim | Location | Result |
|---|---|---|---|
| 1 | Bug lives in `calculate_total` at `src/expense_tracker.py:55-64` | verified | **PASS** |
| 2 | Quoted snippet matches source | `src/expense_tracker.py:55-64` | **PASS** — verbatim |
| 3 | Root cause: `range(1, len(expenses))` never visits index `0` | `src/expense_tracker.py:62` | **PASS** |
| 4 | Caller `total_for_category` at `:67-72`, parameterized query at `:68-70` | verified | **PASS** |
| 5 | CLI `total` subcommand at `:136-137` | verified | **PASS** |
| 6 | `test_calculate_total_sums_all_expenses` (`tests/…:41-43`) expects `17.5`, gets `7.5` | verified | **PASS** |
| 7 | `test_total_for_category_includes_first_matching_row` (`tests/…:45-48`) expects `15.5`, gets `12.0` | verified | **PASS** |

Actual source read at `src/expense_tracker.py:55-64`:

```python
def calculate_total(expenses) -> float:
    """Sum the amount of every expense in the list.

    BUG: the loop starts at index 1 instead of 0, silently skipping the
    first expense in the list and undercounting the total.
    """
    total = 0.0
    for i in range(1, len(expenses)):
        total += expenses[i]["amount"]
    return total
```

Caller confirmed at `src/expense_tracker.py:67-72`:

```python
def total_for_category(conn: sqlite3.Connection, category: str) -> float:
    cursor = conn.execute(
        "SELECT amount FROM expenses WHERE category = ?", (category,)
    )
    expenses = [{"amount": row[0]} for row in cursor.fetchall()]
    return calculate_total(expenses)
```

The researcher's side-claim that this query is **not** an injection risk is
correct: it uses a `?` placeholder with a params tuple. CLI wiring confirmed at
`src/expense_tracker.py:136-137`:

```python
    elif args.command == "total":
        print(f"{total_for_category(conn, args.category):.2f}")
```

### Issue 2 — `apply_member_discount` inverted rate

| # | Claim | Location | Result |
|---|---|---|---|
| 8 | Bug lives in `apply_member_discount` at `src/expense_tracker.py:75-83` | verified | **PASS** |
| 9 | Quoted snippet matches source | `src/expense_tracker.py:75-83` | **PASS** — verbatim |
| 10 | Root cause: member branch multiplies by `1.1` (surcharge) not `0.9` | `src/expense_tracker.py:82` | **PASS** |
| 11 | Non-member branch (`return total`) is correct and untouched | `src/expense_tracker.py:83` | **PASS** |
| 12 | CLI `discount` subcommand at `:138-139` | verified | **PASS** |
| 13 | `test_member_discount_reduces_total` (`tests/…:50-51`) expects `90.0`, gets `110.0` | verified | **PASS** |
| 14 | `test_non_member_discount_is_unchanged` (`tests/…:53-54`) already passes | verified | **PASS** |

Actual source read at `src/expense_tracker.py:75-83`:

```python
def apply_member_discount(total: float, is_member: bool) -> float:
    """Apply a 10% discount for members.

    BUG: multiplies by 1.1 instead of 0.9, which *increases* the total for
    members instead of discounting it.
    """
    if is_member:
        return round(total * 1.1, 2)
    return total
```

CLI wiring confirmed at `src/expense_tracker.py:138-139`:

```python
    elif args.command == "discount":
        print(f"{apply_member_discount(args.total, bool(args.is_member)):.2f}")
```

### Issue 3 — SQL Injection in `search_expenses` (CWE-89)

| # | Claim | Location | Result |
|---|---|---|---|
| 15 | Bug lives in `search_expenses` at `src/expense_tracker.py:86-96` | verified | **PASS** |
| 16 | Quoted snippet matches source | `src/expense_tracker.py:86-96` | **PASS** — verbatim |
| 17 | Root cause: `keyword` concatenated with `+` into the SQL string; `conn.execute(query)` single-arg form | `src/expense_tracker.py:94-95` | **PASS** |
| 18 | Contrast pattern: `add_expense` `:42-45` and `total_for_category` `:68-70` correctly use `?` + params tuple | verified | **PASS** |
| 19 | Exploit `nonexistent' OR '1'='1' --` produces the stated concatenated query and returns every row | verified | **PASS** — string reproduced exactly |
| 20 | CLI `search` subcommand at `:140-141` | verified | **PASS** |
| 21 | `test_search_does_not_leak_all_rows_on_injection_attempt` (`tests/…:56-61`) expects `[]`, gets both rows | verified | **PASS** |
| 22 | `test_search_finds_matching_expense` (`tests/…:63-66`) defines the legitimate behavior a fix must preserve | verified | **PASS** |

Actual source read at `src/expense_tracker.py:86-96`:

```python
def search_expenses(conn: sqlite3.Connection, keyword: str):
    """Search expenses whose description contains the given keyword.

    SECURITY BUG (CWE-89, SQL Injection): the keyword is interpolated
    directly into the SQL string instead of using a parameterized query,
    so a crafted keyword such as `%' OR '1'='1` returns every row
    regardless of whether it matches.
    """
    query = "SELECT id, description, amount, category FROM expenses WHERE description LIKE '%" + keyword + "%'"
    cursor = conn.execute(query)
    return cursor.fetchall()
```

Reference (safe) pattern confirmed at `src/expense_tracker.py:41-47`:

```python
def add_expense(conn: sqlite3.Connection, description: str, amount: float, category: str) -> int:
    cursor = conn.execute(
        "INSERT INTO expenses (description, amount, category) VALUES (?, ?, ?)",
        (description, amount, category),
    )
```

### Completeness claims

| # | Claim | Result |
|---|---|---|
| 23 | The three issues are the full seeded scope per `bug-context.md:1-55` | **PASS** — file is exactly 55 lines and lists exactly these three |
| 24 | No additional injection or off-by-one patterns in `:18-53` / `:99-148` | **PASS** — independently re-checked (see below) |

Independent completeness sweep by the verifier:

- `Glob **/*.py` returns exactly two Python files (`src/expense_tracker.py`,
  `tests/test_expense_tracker.py`) — no second copy of the app to also fix.
- Grep for `conn.execute(` / SQL keywords across all `*.py` finds 8 call sites:
  lines 28, 42-43, 51, 68-69, 94-95. `:94` is the only string-concatenated
  query; every other is either a static literal or `?`-parameterized. The
  researcher's "only injection site" claim holds repo-wide.
- Grep for callers of the three buggy functions finds only `:72`, `:137`,
  `:139`, `:141` (plus the test file) — matching the researcher's call paths
  with no missed call site.
- `_print_rows` (`:99-104`), `get_connection` (`:21-24`), `init_db` (`:27-38`)
  and `main` (`:107-144`) contain no further off-by-one or injection pattern,
  as claimed.

### Runtime Confirmation

Every predicted value was reproduced by executing the code against an in-memory
SQLite DB, and the full suite was run:

```
calc_total([10.0, 5.0, 2.5])   -> 7.5      (research predicted 7.5, expected 17.5)
total_for_category("food")     -> 12.0     (research predicted 12.0, expected 15.5)
apply_member_discount(100,True)-> 110.0    (research predicted 110.0, expected 90.0)
apply_member_discount(100,False)->100.0    (research predicted unchanged — correct)
injected SQL: SELECT id, description, amount, category FROM expenses
              WHERE description LIKE '%nonexistent' OR '1'='1' --%'
injection results -> [(1,'Coffee',3.5,'food'), (2,'Secret gift',500.0,'personal')]
search("Coff")    -> [(1,'Coffee',3.5,'food')]   (legit behavior to preserve)
```

`python3 -m unittest discover -s tests` → **Ran 8 tests, FAILED (failures=4)**:
`test_calculate_total_sums_all_expenses`,
`test_total_for_category_includes_first_matching_row`,
`test_member_discount_reduces_total`,
`test_search_does_not_leak_all_rows_on_injection_attempt` — exactly the four the
research predicted would fail, and no others.

## Discrepancies Found

**None.** No claim in `codebase-research.md` contradicts the source. Two
non-blocking observations are recorded for the Bug Planner — neither is a
research error:

1. **Advisory (does not block planning)** — the proposed Issue 3 fix
   `... LIKE ?` with `(f"%{keyword}%",)` correctly closes CWE-89 and keeps
   `test_search_finds_matching_expense` passing, but a user-supplied `%` or `_`
   inside `keyword` still acts as a LIKE wildcard (broader-than-intended
   matching, not SQL injection). If the Planner wants strict substring
   semantics it should add `ESCAPE` handling. The research did not mention
   this; it is a property of the fix, not of a claimed finding.
2. **Cosmetic label, not line drift** — the reference list cites
   `src/expense_tracker.py:107-148` as "`main` / CLI wiring". `main()` itself
   ends at line 144; 147-148 is the `if __name__ == "__main__"` entrypoint
   guard. The range resolves and contains what is described; no correction
   needed.

## Research Quality Assessment

**Score**: Reference accuracy 3/3, Root cause identification 3/3,
Completeness 3/3, Actionability 3/3 — **Total 12/12**

**Level**: EXCELLENT

**Reasoning**:

- **Reference accuracy (3/3)** — All 20+ cited ranges were opened and matched
  exactly, with zero line drift: `calculate_total` really spans 55-64,
  `apply_member_discount` 75-83, `search_expenses` 86-96, and the CLI dispatch
  lines 136-137/138-139/140-141 are precisely where claimed. All three code
  snippets are verbatim reproductions of source including docstrings. Test
  ranges `41-43`, `45-48`, `50-51`, `53-54`, `56-61`, `63-66` all resolve to
  the named test methods.
- **Root cause identification (3/3)** — Each cause is mechanistic and
  code-backed rather than a symptom restatement: `range(1, len(expenses))`
  skipping index 0, the member branch applying a `1.1` surcharge while the
  non-member branch is correctly untouched, and `+` concatenation feeding the
  single-argument `conn.execute(query)` form. The injection explanation
  correctly identifies *why* the payload works (`--` comments out the trailing
  `%'`, `'1'='1'` short-circuits the `WHERE`), and I reproduced the resulting
  query string character-for-character.
- **Completeness (3/3)** — All three reported issues are covered with cause and
  location, plus related risk areas: the `total_for_category` → `calculate_total`
  call path, all three CLI entry points, and the contrasting *safe*
  parameterized queries at `:42-45` and `:68-70` used as the fix template. My
  independent grep/glob sweep found no additional call sites, no second copy of
  the module, and no other concatenated SQL — nothing relevant was missed.
- **Actionability (3/3)** — Every issue ships a concrete, drop-in fix
  (`range(len(expenses))` or the `sum(...)` generator; `total * 0.9`; the exact
  parameterized `execute` call), the tests that gate each fix, and the exact
  expected-vs-actual values. A fixer can implement all three without reopening
  the investigation; my run of the suite confirms exactly the four predicted
  failures and no unexpected ones.

## References

Files and ranges personally opened and checked during this verification pass:

- `context/bugs/001/research/codebase-research.md:1-156` — full research doc under verification.
- `skills/research-quality-measurement.md:1-59` — rubric, quality levels, pass/fail gate, required reporting format.
- `context/bugs/001/bug-context.md:1-55` — seeded scope cross-check (full file).
- `src/expense_tracker.py:1-149` — full file read.
  - `:1-18` — module docstring, imports, `DB_PATH`.
  - `:21-24` — `get_connection`.
  - `:27-38` — `init_db` (static DDL, no injection).
  - `:41-47` — `add_expense` (safe parameterized reference pattern).
  - `:50-52` — `list_expenses` (static literal).
  - `:55-64` — `calculate_total` (Issue 1).
  - `:67-72` — `total_for_category` (Issue 1 caller; safe `?` query).
  - `:75-83` — `apply_member_discount` (Issue 2).
  - `:86-96` — `search_expenses` (Issue 3).
  - `:99-104` — `_print_rows`.
  - `:107-144` — `main` / CLI dispatch; `:147-148` entrypoint guard.
- `tests/test_expense_tracker.py:1-71` — full file read.
  - `:1-26` — imports, `setUp`/`tearDown`.
  - `:41-48` — Issue 1 tests.
  - `:50-54` — Issue 2 tests.
  - `:56-66` — Issue 3 tests.
- Repo-wide `Grep` for `conn.execute(`/SQL keywords over `**/*.py`, `Grep` for
  callers of the three functions, and `Glob **/*.py` — completeness sweep.
- Executed `python3 -m unittest discover -s tests` and an in-memory reproduction
  script (read-only; no source modified).
