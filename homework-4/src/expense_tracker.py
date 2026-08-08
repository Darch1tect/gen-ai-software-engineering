"""
Expense Tracker CLI — a minimal personal expense tracking tool backed by SQLite.

Commands:
    add <description> <amount> <category>
    list
    total <category>
    discount <total> <is_member: 0|1>
    search <keyword>

Run: python3 src/expense_tracker.py <command> [args...]
"""
import argparse
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "expenses.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL
        )
        """
    )
    conn.commit()


def add_expense(conn: sqlite3.Connection, description: str, amount: float, category: str) -> int:
    cursor = conn.execute(
        "INSERT INTO expenses (description, amount, category) VALUES (?, ?, ?)",
        (description, amount, category),
    )
    conn.commit()
    return cursor.lastrowid


def list_expenses(conn: sqlite3.Connection):
    cursor = conn.execute("SELECT id, description, amount, category FROM expenses ORDER BY id")
    return cursor.fetchall()


def calculate_total(expenses) -> float:
    """Sum the amount of every expense in the list."""
    total = 0.0
    for i in range(len(expenses)):
        total += expenses[i]["amount"]
    return total


def total_for_category(conn: sqlite3.Connection, category: str) -> float:
    cursor = conn.execute(
        "SELECT amount FROM expenses WHERE category = ?", (category,)
    )
    expenses = [{"amount": row[0]} for row in cursor.fetchall()]
    return calculate_total(expenses)


def apply_member_discount(total: float, is_member: bool) -> float:
    """Apply a 10% discount for members."""
    if is_member:
        return round(total * 0.9, 2)
    return total


def search_expenses(conn: sqlite3.Connection, keyword: str):
    """Search expenses whose description contains the given keyword."""
    cursor = conn.execute(
        "SELECT id, description, amount, category FROM expenses WHERE description LIKE ?",
        (f"%{keyword}%",),
    )
    return cursor.fetchall()


def _print_rows(rows):
    if not rows:
        print("(no expenses)")
        return
    for row in rows:
        print(f"#{row[0]}: {row[1]} - {row[2]:.2f} [{row[3]}]")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Expense Tracker CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("description")
    p_add.add_argument("amount", type=float)
    p_add.add_argument("category")

    sub.add_parser("list")

    p_total = sub.add_parser("total")
    p_total.add_argument("category")

    p_discount = sub.add_parser("discount")
    p_discount.add_argument("total", type=float)
    p_discount.add_argument("is_member", type=int, choices=[0, 1])

    p_search = sub.add_parser("search")
    p_search.add_argument("keyword")

    args = parser.parse_args(argv)
    conn = get_connection()

    if args.command == "add":
        expense_id = add_expense(conn, args.description, args.amount, args.category)
        print(f"Added expense #{expense_id}")
    elif args.command == "list":
        _print_rows(list_expenses(conn))
    elif args.command == "total":
        print(f"{total_for_category(conn, args.category):.2f}")
    elif args.command == "discount":
        print(f"{apply_member_discount(args.total, bool(args.is_member)):.2f}")
    elif args.command == "search":
        _print_rows(search_expenses(conn, args.keyword))

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
