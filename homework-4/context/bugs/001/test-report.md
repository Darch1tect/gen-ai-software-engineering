# Test Report: 001

## Tests Added

### `calculate_total` (src/expense_tracker.py:55-59)
- **tests/test_expense_tracker.py:71** — `test_calculate_total_empty_list` — validates empty list returns 0.0 (edge case: empty input)
- **tests/test_expense_tracker.py:74** — `test_calculate_total_single_expense` — validates single-item list sums correctly (edge case: boundary)
- **tests/test_expense_tracker.py:77** — `test_calculate_total_includes_first_and_last` — validates first and last items are included, confirming off-by-one fix (edge case: comprehensive coverage)
- **tests/test_expense_tracker.py:80** — `test_calculate_total_with_decimal_precision` — validates decimal precision handling (edge case: floating-point accuracy)

### `apply_member_discount` (src/expense_tracker.py:71-75)
- **tests/test_expense_tracker.py:83** — `test_apply_member_discount_zero_total` — validates zero input with member=True returns 0.0 (edge case: zero boundary)
- **tests/test_expense_tracker.py:86** — `test_apply_member_discount_rounds_to_two_decimals` — validates rounding to 2 decimal places (edge case: precision)
- **tests/test_expense_tracker.py:89** — `test_apply_member_discount_large_amount` — validates large amount discounts correctly (edge case: upper bound)

### `search_expenses` (src/expense_tracker.py:78-84)
- **tests/test_expense_tracker.py:92** — `test_search_with_empty_keyword` — validates empty keyword matches all rows (edge case: empty input)
- **tests/test_expense_tracker.py:97** — `test_search_returns_multiple_matches` — validates parameterized query finds multiple matching results (edge case: validates query construction)
- **tests/test_expense_tracker.py:103** — `test_search_with_special_characters_in_keyword` — validates special SQL characters in normal keywords are handled safely (edge case: special characters)
- **tests/test_expense_tracker.py:107** — `test_search_case_insensitive` — validates LIKE search is case-insensitive (edge case: SQL LIKE behavior)

## Test Run Result

Command: `python3 -m unittest discover -s tests -v`

```
test_add_expense_persists_row (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_apply_member_discount_large_amount (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_apply_member_discount_rounds_to_two_decimals (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_apply_member_discount_zero_total (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_calculate_total_empty_list (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_calculate_total_includes_first_and_last (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_calculate_total_single_expense (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_calculate_total_sums_all_expenses (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_calculate_total_with_decimal_precision (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_list_expenses_returns_all_rows (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_member_discount_reduces_total (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_non_member_discount_is_unchanged (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_search_case_insensitive (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_search_does_not_leak_all_rows_on_injection_attempt (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_search_finds_matching_expense (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_search_returns_multiple_matches (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_search_with_empty_keyword (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_search_with_special_characters_in_keyword (test_expense_tracker.ExpenseTrackerTestCase) ... ok
test_total_for_category_includes_first_matching_row (test_expense_tracker.ExpenseTrackerTestCase) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.003s

OK
```

All 19 tests pass (8 original + 11 new). No failures or errors.

## FIRST Compliance

- **Fast**: All 19 tests complete in 0.003s using in-memory SQLite databases (`:memory:`) with no I/O, sleep, or network calls.
- **Independent**: Each test uses `setUp()` to create its own isolated in-memory database connection; tests run in any order with identical results via `tearDown()` cleanup.
- **Repeatable**: No time-dependent, random, network, or filesystem dependencies; suite produces identical results across runs and environments.
- **Self-validating**: All 11 new tests use `assertEqual()` or `assertAlmostEqual()` assertions with descriptive names (e.g., `test_calculate_total_empty_list`, `test_search_with_special_characters_in_keyword`); one logical focus per test.
- **Timely**: All 11 new tests directly target the 3 changed functions from `fix-summary.md` (4 for `calculate_total`, 3 for `apply_member_discount`, 4 for `search_expenses`), validating specific edge cases of the fixes (boundary inputs, precision, injection-resistant parameterization).

## References

- `src/expense_tracker.py:55-59` (`calculate_total`) — 4 new tests covering empty, single, comprehensive, and decimal-precision edge cases.
- `src/expense_tracker.py:71-75` (`apply_member_discount`) — 3 new tests covering zero, rounding, and large-amount edge cases.
- `src/expense_tracker.py:78-84` (`search_expenses`) — 4 new tests covering empty keyword, multiple matches, special characters, and case-insensitivity edge cases.

All changed code paths from `fix-summary.md` have received comprehensive edge case coverage. No code paths intentionally left uncovered.
