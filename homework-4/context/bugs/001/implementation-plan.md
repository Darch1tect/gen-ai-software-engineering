# Implementation Plan: 001

## Test Command

```
python3 -m unittest discover -s tests -v
```

Run this after each change (or once at the end, if applying all three
changes together — they are independent and non-overlapping). Before any
change, the suite fails 4/8:
`test_calculate_total_sums_all_expenses`,
`test_total_for_category_includes_first_matching_row`,
`test_member_discount_reduces_total`,
`test_search_does_not_leak_all_rows_on_injection_attempt`. All 8 must pass
after the fixes, with no new failures introduced.

## Planned Changes

### Change 1 — `calculate_total` off-by-one (Issue 1)

**File**: `src/expense_tracker.py`

**Before** (lines 55-64):
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

**After**:
```python
def calculate_total(expenses) -> float:
    """Sum the amount of every expense in the list."""
    total = 0.0
    for i in range(len(expenses)):
        total += expenses[i]["amount"]
    return total
```

**Why this fixes the root cause**: `verified-research.md` confirms (claim 3,
runtime confirmation) the loop range `range(1, len(expenses))` never visits
index 0, so the first expense's amount is silently dropped from every sum.
Changing the range to `range(len(expenses))` restores the missing index
without altering the summation logic, the function signature, or its return
type — it changes exactly the mechanism identified as the cause, nothing
else. The stale `BUG:` docstring note is removed since it would otherwise
describe code that no longer exists. This also fixes `total_for_category`
(`:67-72`) for free, since it calls `calculate_total` unmodified — no change
needed there.

### Change 2 — `apply_member_discount` inverted rate (Issue 2)

**File**: `src/expense_tracker.py`

**Before** (lines 75-83):
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

**After**:
```python
def apply_member_discount(total: float, is_member: bool) -> float:
    """Apply a 10% discount for members."""
    if is_member:
        return round(total * 0.9, 2)
    return total
```

**Why this fixes the root cause**: `verified-research.md` claim 10 confirms
the member branch multiplies by `1.1` (a 10% surcharge) instead of `0.9` (a
10% discount), while the non-member branch (`return total`, line 83, claim
11) is already correct and must stay untouched. Replacing `1.1` with `0.9`
is the exact, minimal correction to the multiplier; `round(..., 2)` and the
`if is_member` branching are preserved unchanged. The stale `BUG:` docstring
note is removed for the same reason as Change 1.

### Change 3 — SQL injection in `search_expenses` (Issue 3, CWE-89)

**File**: `src/expense_tracker.py`

**Before** (lines 86-96):
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

**After**:
```python
def search_expenses(conn: sqlite3.Connection, keyword: str):
    """Search expenses whose description contains the given keyword."""
    cursor = conn.execute(
        "SELECT id, description, amount, category FROM expenses WHERE description LIKE ?",
        (f"%{keyword}%",),
    )
    return cursor.fetchall()
```

**Why this fixes the root cause**: `verified-research.md` claim 17 identifies
the root cause as `+`-concatenating `keyword` directly into the SQL string
and passing the result to the single-argument `conn.execute(query)` form,
which lets a crafted keyword terminate the string literal and inject SQL
(claim 19, reproduced verbatim: `nonexistent' OR '1'='1' --`). Switching to
the `?` placeholder with `(f"%{keyword}%",)` as a bound parameter (the same
pattern already used safely in `add_expense` at `:42-45` and
`total_for_category` at `:68-70`, claim 18) means `keyword` is always treated
as literal data by SQLite's parameter binding, never as SQL syntax — this
closes the injection regardless of what characters `keyword` contains, not
just the specific payload in the test. The `%`-wildcard wrapping is moved
into the Python f-string so the LIKE pattern (`%<keyword>%`) is unchanged
from the original intent, and `test_search_finds_matching_expense`
(`tests/…:63-66`) continues to receive the same matching behavior.

## Out of Scope

- **LIKE-wildcard escaping for `%`/`_` inside `keyword`** — flagged as
  Advisory Observation 1 in `verified-research.md`'s Discrepancies section.
  The parameterized fix above fully closes the SQL injection (CWE-89), which
  is the seeded bug and the only behavior the test suite gates. A
  user-supplied `%` or `_` acting as a LIKE wildcard is a separate,
  pre-existing semantic quirk (broader-than-intended substring matching),
  not an injection risk, and no test in `tests/test_expense_tracker.py`
  exercises it. Adding `ESCAPE` handling would be effort beyond this bug's
  verified scope and risks changing `search`'s matching semantics without a
  test to pin the desired behavior.
- **Any change to `get_connection`, `init_db`, `add_expense`,
  `list_expenses`, `_print_rows`, `main`, or the CLI dispatch (`:136-141`)**
  — the completeness sweep (claims 23-24, and the verifier's independent
  grep/glob sweep) found these already correct and out of the bug's scope;
  the CLI dispatch lines call the three fixed functions with the same
  signatures, so no wiring changes are needed.
- **Cosmetic reference-range label** (Discrepancy Observation 2: `main` cited
  as `:107-148` vs. `main()` actually ending at `:144`) — not a code issue,
  no action needed.

## References

- `context/bugs/001/research/verified-research.md` — Verification Summary
  (PASS, EXCELLENT 12/12); Issue 1 table and source (`:17-63`); Issue 2 table
  and source (`:64-95`); Issue 3 table and source (`:97-134`); Completeness
  claims (`:136-156`); Runtime Confirmation (`:158-179`); Discrepancies Found
  (`:181-198`).
