"""In-memory storage for transactions.

Data lives only for the lifetime of the running process - no database,
no persistence to disk. A dict keyed by transaction id gives O(1) lookups
by id while preserving insertion order for listing.
"""

from typing import Dict, List, Optional

from src.models.transaction import Transaction


class TransactionStore:
    def __init__(self) -> None:
        self._transactions: Dict[str, Transaction] = {}

    def add(self, transaction: Transaction) -> Transaction:
        self._transactions[transaction.id] = transaction
        return transaction

    def get(self, transaction_id: str) -> Optional[Transaction]:
        return self._transactions.get(transaction_id)

    def list_all(self) -> List[Transaction]:
        return list(self._transactions.values())

    def for_account(self, account_id: str) -> List[Transaction]:
        return [
            t for t in self._transactions.values()
            if t.fromAccount == account_id or t.toAccount == account_id
        ]

    def clear(self) -> None:
        """Reset storage. Mainly useful for tests."""
        self._transactions.clear()


# Single shared in-memory store used by the whole application.
store = TransactionStore()
