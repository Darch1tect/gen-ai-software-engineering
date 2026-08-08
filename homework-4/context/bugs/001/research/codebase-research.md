# Codebase Research: 001

## Issues Investigated

### Issue 1 — `calculate_total` off-by-one (functional)

- **File**: `src/expense_tracker.py:55-64`
- **Snippet**:
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
- **Root cause**: The summation loop is built with `range(1, len(expenses))`,
  which in Python starts at index `1` and never visits index `0`. Since
  `expenses[0]` is skipped, its `"amount"` is never added to `total`. The
  function's own docstring already documents this as an intentional seeded
  bug.
- **Call path**: `total_for_category` (`src/expense_tracker.py:67-72`) builds
  a list of `{"amount": row[0]}` dicts from a `SELECT amount FROM expenses
  WHERE category = ?` query (line 68-70, correctly parameterized — no
  injection risk here) and passes it straight to `calculate_total`. Any
  caller of either function inherits the under-count, e.g. the CLI `total`
  subcommand at `src/expense_tracker.py:136-137`.
- **Confirms test expectations**: `tests/test_expense_tracker.py:41-43`
  (`test_calculate_total_sums_all_expenses`) expects `calculate_total([{"amount":
  10.0}, {"amount": 5.0}, {"amount": 2.5}])` to equal `17.5`; with the current
  loop it sums only indices 1 and 2 (`5.0 + 2.5 = 7.5`), so the test fails.
  `tests/test_expense_tracker.py:45-48`
  (`test_total_for_category_includes_first_matching_row`) adds two "food"
  expenses (3.5, 12.0, expected total 15.5) and would get 12.0 instead,
  confirming the impact described in the bug context.
- **Fix**: change `range(1, len(expenses))` to `range(len(expenses))` (or
  equivalently `sum(e["amount"] for e in expenses)`).
- **Confidence**: high — directly observed in code, matches an explicit
  in-code `BUG:` comment, and matches the failing-test description in
  `bug-context.md`.

### Issue 2 — `apply_member_discount` inverted rate (functional)

- **File**: `src/expense_tracker.py:75-83`
- **Snippet**:
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
- **Root cause**: For members (`is_member` truthy) the total is multiplied by
  `1.1` (a 10% surcharge) instead of `0.9` (a 10% discount). Non-members are
  unaffected (`return total` unchanged), which is correct. The docstring
  again explicitly flags this as the seeded bug.
- **Call path**: invoked directly from the CLI `discount` subcommand
  (`src/expense_tracker.py:138-139`), so any member-flagged CLI invocation
  is overcharged.
- **Confirms test expectations**: `tests/test_expense_tracker.py:50-51`
  (`test_member_discount_reduces_total`) expects
  `apply_member_discount(100.0, True) == 90.0`; current code returns `110.0`,
  so the test fails. `test_non_member_discount_is_unchanged`
  (`tests/test_expense_tracker.py:53-54`) already passes since the
  non-member branch is untouched by the bug.
- **Fix**: change `total * 1.1` to `total * 0.9`.
- **Confidence**: high — directly observed in code, matches in-code `BUG:`
  comment and bug-context description.

### Issue 3 — SQL Injection in `search_expenses` (CWE-89, security)

- **File**: `src/expense_tracker.py:86-96`
- **Snippet**:
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
- **Root cause**: `keyword` is concatenated directly into the SQL string via
  `+`, with no escaping, quoting, or parameter binding. `conn.execute` is
  called with a single fully-formed string, not the `(query, params)` form
  used elsewhere in this same file (contrast with `add_expense` at line 42-45
  and `total_for_category` at line 68-70, both of which correctly use `?`
  placeholders and a params tuple). A keyword containing a single quote can
  break out of the intended `LIKE '%...%'` literal and inject arbitrary SQL
  fragments into the `WHERE` clause.
- **Concrete exploit**: keyword `nonexistent' OR '1'='1' --` produces:
  `SELECT id, description, amount, category FROM expenses WHERE description LIKE '%nonexistent' OR '1'='1' --%'`.
  The `--` comments out the trailing `%'`, and `'1'='1'` is always true, so
  the `WHERE` clause matches every row regardless of the `nonexistent`
  keyword — full data exfiltration of the `expenses` table via the `search`
  CLI command (`src/expense_tracker.py:140-141`).
- **Confirms test expectations**:
  `tests/test_expense_tracker.py:56-61`
  (`test_search_does_not_leak_all_rows_on_injection_attempt`) inserts two
  rows, searches with the exact malicious keyword above, and asserts
  `results == []`; against current code the query matches both rows so the
  test fails. `test_search_finds_matching_expense`
  (`tests/test_expense_tracker.py:63-66`) shows the legitimate substring-match
  behavior that any fix must preserve.
- **Fix**: use a parameterized query, e.g.
  `conn.execute("SELECT id, description, amount, category FROM expenses WHERE description LIKE ?", (f"%{keyword}%",))`,
  mirroring the pattern already used by `add_expense` and
  `total_for_category` in the same file.
- **Confidence**: high — directly observed in code, matches in-code
  `SECURITY BUG` comment, bug-context description, and the exact malicious
  payload used by the corresponding test.

## Open Questions

- None of the three issues required inference beyond reading the code — each
  is additionally documented by an explicit in-code comment (`BUG:` /
  `SECURITY BUG`) that matches `bug-context.md` verbatim, and each has a
  corresponding failing test in `tests/test_expense_tracker.py` whose
  expected value was hand-verified above. No unconfirmed claims remain.
- Not investigated (out of scope per `bug-context.md`, which lists exactly
  these three issues): `main()`'s argument parsing, `get_connection`/`init_db`
  connection handling, and `_print_rows` formatting — a quick read of these
  (`src/expense_tracker.py:18-53`, `99-148`) showed no additional injection
  or off-by-one patterns, but they were not exhaustively test-driven here.

## References

- `src/expense_tracker.py:1-18` — module docstring, imports, `DB_PATH`.
- `src/expense_tracker.py:21-24` — `get_connection`.
- `src/expense_tracker.py:27-38` — `init_db`.
- `src/expense_tracker.py:41-47` — `add_expense` (correct parameterized query, used as the reference pattern for fixing Issue 3).
- `src/expense_tracker.py:50-52` — `list_expenses`.
- `src/expense_tracker.py:55-64` — `calculate_total` (Issue 1).
- `src/expense_tracker.py:67-72` — `total_for_category` (caller of Issue 1; correct parameterized query).
- `src/expense_tracker.py:75-83` — `apply_member_discount` (Issue 2).
- `src/expense_tracker.py:86-96` — `search_expenses` (Issue 3).
- `src/expense_tracker.py:99-104` — `_print_rows`.
- `src/expense_tracker.py:107-148` — `main` / CLI wiring (calls into all three buggy functions).
- `tests/test_expense_tracker.py:1-26` — imports and `setUp`/`tearDown`.
- `tests/test_expense_tracker.py:41-48` — tests for Issue 1.
- `tests/test_expense_tracker.py:50-54` — tests for Issue 2.
- `tests/test_expense_tracker.py:56-66` — tests for Issue 3.
- `context/bugs/001/bug-context.md:1-55` — seeded bug context (full file read).
