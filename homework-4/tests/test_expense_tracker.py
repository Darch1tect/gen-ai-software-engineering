import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from expense_tracker import (  # noqa: E402
    add_expense,
    apply_member_discount,
    calculate_total,
    init_db,
    list_expenses,
    search_expenses,
    total_for_category,
)


class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    # --- baseline coverage (already passing) ---------------------------

    def test_add_expense_persists_row(self):
        expense_id = add_expense(self.conn, "Coffee", 3.5, "food")
        self.assertEqual(expense_id, 1)

    def test_list_expenses_returns_all_rows(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        add_expense(self.conn, "Bus ticket", 2.0, "transport")
        rows = list_expenses(self.conn)
        self.assertEqual(len(rows), 2)

    # --- bug coverage (fail on current buggy code) ----------------------

    def test_calculate_total_sums_all_expenses(self):
        expenses = [{"amount": 10.0}, {"amount": 5.0}, {"amount": 2.5}]
        self.assertEqual(calculate_total(expenses), 17.5)

    def test_total_for_category_includes_first_matching_row(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        add_expense(self.conn, "Lunch", 12.0, "food")
        self.assertEqual(total_for_category(self.conn, "food"), 15.5)

    def test_member_discount_reduces_total(self):
        self.assertEqual(apply_member_discount(100.0, True), 90.0)

    def test_non_member_discount_is_unchanged(self):
        self.assertEqual(apply_member_discount(100.0, False), 100.0)

    def test_search_does_not_leak_all_rows_on_injection_attempt(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        add_expense(self.conn, "Secret gift", 500.0, "personal")
        malicious_keyword = "nonexistent' OR '1'='1' --"
        results = search_expenses(self.conn, malicious_keyword)
        self.assertEqual(results, [])

    def test_search_finds_matching_expense(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        results = search_expenses(self.conn, "Coff")
        self.assertEqual(len(results), 1)

    # --- edge case coverage for fixed code ----------------------------

    def test_calculate_total_empty_list(self):
        expenses = []
        self.assertEqual(calculate_total(expenses), 0.0)

    def test_calculate_total_single_expense(self):
        expenses = [{"amount": 42.5}]
        self.assertEqual(calculate_total(expenses), 42.5)

    def test_calculate_total_includes_first_and_last(self):
        expenses = [{"amount": 1.0}, {"amount": 2.0}, {"amount": 3.0}]
        self.assertEqual(calculate_total(expenses), 6.0)

    def test_calculate_total_with_decimal_precision(self):
        expenses = [{"amount": 0.1}, {"amount": 0.2}, {"amount": 0.3}]
        self.assertAlmostEqual(calculate_total(expenses), 0.6, places=2)

    def test_apply_member_discount_zero_total(self):
        self.assertEqual(apply_member_discount(0.0, True), 0.0)

    def test_apply_member_discount_rounds_to_two_decimals(self):
        self.assertEqual(apply_member_discount(99.99, True), 89.99)

    def test_apply_member_discount_large_amount(self):
        self.assertEqual(apply_member_discount(10000.0, True), 9000.0)

    def test_search_with_empty_keyword(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        add_expense(self.conn, "Tea", 2.5, "food")
        results = search_expenses(self.conn, "")
        self.assertEqual(len(results), 2)

    def test_search_returns_multiple_matches(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        add_expense(self.conn, "Iced coffee", 4.0, "food")
        add_expense(self.conn, "Tea", 2.5, "food")
        results = search_expenses(self.conn, "coffee")
        self.assertEqual(len(results), 2)

    def test_search_with_special_characters_in_keyword(self):
        add_expense(self.conn, "50% off shirt", 25.0, "clothing")
        results = search_expenses(self.conn, "50%")
        self.assertEqual(len(results), 1)

    def test_search_case_insensitive(self):
        add_expense(self.conn, "Coffee", 3.5, "food")
        results = search_expenses(self.conn, "coffee")
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
