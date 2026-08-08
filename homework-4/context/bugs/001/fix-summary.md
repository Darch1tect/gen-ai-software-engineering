# Fix Summary: 001

## Changes Made

### Change 1 — `calculate_total` off-by-one

**File**: `src/expense_tracker.py:55-59`

**Before**:
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

**Test result after applying**: `python3 -m unittest discover -s tests -v`
→ 6 passed, 2 failed. Fixed `test_calculate_total_sums_all_expenses` and
`test_total_for_category_includes_first_matching_row` (the latter fixed for
free via `total_for_category`'s call to `calculate_total`, as predicted by
the plan). No new failures introduced. Remaining failures:
`test_member_discount_reduces_total`,
`test_search_does_not_leak_all_rows_on_injection_attempt`.

### Change 2 — `apply_member_discount` inverted rate

**File**: `src/expense_tracker.py:75-79`

**Before**:
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

**Test result after applying**: `python3 -m unittest discover -s tests -v`
→ 7 passed, 1 failed. Fixed `test_member_discount_reduces_total`. No new
failures introduced. Remaining failure:
`test_search_does_not_leak_all_rows_on_injection_attempt`.

### Change 3 — SQL injection in `search_expenses` (CWE-89)

**File**: `src/expense_tracker.py:86-91`

**Before**:
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

**Test result after applying**: `python3 -m unittest discover -s tests -v`
→ 8 passed, 0 failed. Fixed
`test_search_does_not_leak_all_rows_on_injection_attempt`. No new failures
introduced. Full suite green.

## Overall Status

COMPLETE

Final full test run: `python3 -m unittest discover -s tests -v`
```
Ran 8 tests in 0.002s

OK
```
All 8 tests pass, no failures, no errors.

## Manual Verification

Run from the `homework-4/` repository root:

1. **Total sums all expenses (Change 1)**:
   ```
   rm -f expenses.db
   python3 src/expense_tracker.py add "Coffee" 3.50 food
   python3 src/expense_tracker.py add "Lunch" 12.00 food
   python3 src/expense_tracker.py total food
   ```
   Expected: `15.50` (previously would have shown `12.00`, dropping the
   first-added row).

2. **Member discount reduces total (Change 2)**:
   ```
   python3 src/expense_tracker.py discount 100 1
   ```
   Expected: `90.00` (previously showed `110.00`, a surcharge instead of a
   discount).

3. **Search does not leak all rows on injection attempt (Change 3)**:
   ```
   python3 src/expense_tracker.py add "Secret gift" 500.00 personal
   python3 src/expense_tracker.py search "nonexistent' OR '1'='1' --"
   ```
   Expected: `(no expenses)` (previously returned every row in the table,
   including "Secret gift").

4. **Regression — normal search still matches (unchanged behavior)**:
   ```
   python3 src/expense_tracker.py search "Coffee"
   ```
   Expected: the `Coffee` row is printed.

5. **Full automated suite**:
   ```
   python3 -m unittest discover -s tests -v
   ```
   Expected: `Ran 8 tests ... OK`.

## References

- `src/expense_tracker.py:55-59` (`calculate_total`) —
  `implementation-plan.md` Change 1.
- `src/expense_tracker.py:75-79` (`apply_member_discount`) —
  `implementation-plan.md` Change 2.
- `src/expense_tracker.py:86-91` (`search_expenses`) —
  `implementation-plan.md` Change 3.
