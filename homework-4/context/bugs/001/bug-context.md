# Bug Context: 001 — Expense Tracker CLI

## Application

`src/expense_tracker.py` — a minimal SQLite-backed expense tracker CLI
(`add`, `list`, `total`, `discount`, `search`). See root `README.md` for run
instructions.

## Seeded Issues

### Bug 1 (functional) — `calculate_total` off-by-one

- **File**: `src/expense_tracker.py`
- **Function**: `calculate_total(expenses)`
- **Symptom**: The running total silently excludes the first expense in the
  list because the summation loop starts at index `1` instead of `0`
  (`for i in range(1, len(expenses))`).
- **Impact**: `total_for_category` (and any caller of `calculate_total`)
  under-reports totals by the amount of the first matching expense.
- **Detected by**: `tests/test_expense_tracker.py::test_calculate_total_sums_all_expenses`
  and `::test_total_for_category_includes_first_matching_row` (both fail on
  current code).

### Bug 2 (functional) — `apply_member_discount` inverted rate

- **File**: `src/expense_tracker.py`
- **Function**: `apply_member_discount(total, is_member)`
- **Symptom**: Members should receive a 10% discount (`total * 0.9`), but the
  code multiplies by `1.1`, *increasing* the price for members instead of
  discounting it.
- **Impact**: Members are overcharged 10% instead of receiving a discount.
- **Detected by**: `tests/test_expense_tracker.py::test_member_discount_reduces_total`
  (fails on current code).

### Security Issue 1 — SQL Injection in `search_expenses` (CWE-89)

- **File**: `src/expense_tracker.py`
- **Function**: `search_expenses(conn, keyword)`
- **Symptom**: The search keyword is concatenated directly into the SQL
  string (`"... LIKE '%" + keyword + "%'"`) instead of being passed as a
  bound parameter.
- **Impact**: A crafted keyword such as `nonexistent' OR '1'='1' --` causes
  the query to return every row in the table regardless of whether it
  matches, bypassing the intended filter. In a real deployment this class of
  bug allows arbitrary data exfiltration or query manipulation.
- **Detected by**: `tests/test_expense_tracker.py::test_search_does_not_leak_all_rows_on_injection_attempt`
  (fails on current code — the malicious keyword returns all rows instead of
  none).

## Status

Seeded prior to the agent pipeline run. All three issues are expected to be
found by **Bug Research Verifier**, fixed by **Bug Fixer**, checked by
**Security Verifier**, and covered by new tests from **Unit Test Generator**.
