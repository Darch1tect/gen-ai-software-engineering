"""Routes for creating, listing, exporting, and fetching transactions."""

import csv
import io
from datetime import date, datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from src.models.transaction import Transaction, TransactionCreate, TransactionType
from src.utils.storage import store
from src.validators.transaction_validator import validate_account_number

router = APIRouter(tags=["transactions"])


@router.post(
    "/transactions",
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(payload: TransactionCreate) -> Transaction:
    """Create a new transaction. Amount must be positive (enforced by the model)."""
    transaction = Transaction.from_create(payload)
    store.add(transaction)
    return transaction


def _parse_filter_date(value: Optional[str], field: str, errors: list) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append({
            "field": field,
            "message": f"{field} must be a valid date in YYYY-MM-DD format",
        })
        return None


def _filter_transactions(
    accountId: Optional[str],
    type_: Optional[str],
    from_: Optional[str],
    to: Optional[str],
) -> list[Transaction]:
    """Shared filtering logic for listing and exporting transactions.

    Filters combine with AND semantics: accountId + type + date range all
    narrow the result set together. Raises 400 (with all field errors
    collected together) on bad accountId format, bad date format, or a
    `from` date later than `to`.
    """
    errors: list = []

    if accountId is not None and not validate_account_number(accountId):
        errors.append({
            "field": "accountId",
            "message": "Account number must follow format ACC-XXXXX (X is alphanumeric)",
        })

    from_date = _parse_filter_date(from_, "from", errors)
    to_date = _parse_filter_date(to, "to", errors)

    if from_date is not None and to_date is not None and from_date > to_date:
        errors.append({"field": "from", "message": "from must not be later than to"})

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Validation failed", "details": errors},
        )

    results = store.list_all()

    if accountId is not None:
        results = [t for t in results if t.fromAccount == accountId or t.toAccount == accountId]

    if type_ is not None:
        results = [t for t in results if t.type == type_]

    if from_date is not None:
        results = [t for t in results if datetime.fromisoformat(t.timestamp).date() >= from_date]

    if to_date is not None:
        results = [t for t in results if datetime.fromisoformat(t.timestamp).date() <= to_date]

    return results


@router.get("/transactions", response_model=list[Transaction])
def list_transactions(
    accountId: Optional[str] = Query(
        default=None, description="Filter by account (matches fromAccount or toAccount), e.g. ACC-12345"
    ),
    type: Optional[TransactionType] = Query(default=None, description="Filter by transaction type"),
    from_: Optional[str] = Query(
        default=None, alias="from", description="Start date, inclusive (YYYY-MM-DD), e.g. 2024-01-01"
    ),
    to: Optional[str] = Query(
        default=None, description="End date, inclusive (YYYY-MM-DD), e.g. 2024-01-31"
    ),
) -> list[Transaction]:
    """List transactions, optionally filtered by account, type, and/or date range.

    Filters combine with AND semantics: `?accountId=ACC-12345&type=transfer&from=2024-01-01&to=2024-01-31`
    returns only transfers involving ACC-12345 that happened between those two dates (inclusive).
    """
    return _filter_transactions(accountId, type, from_, to)


_CSV_COLUMNS = ["id", "fromAccount", "toAccount", "amount", "currency", "type", "timestamp", "status"]


# NOTE: this route must be registered before `/transactions/{transaction_id}`
# below, otherwise the dynamic route would match "export" as a transaction id.
@router.get("/transactions/export")
def export_transactions(
    format: Literal["csv"] = Query(
        default="csv", description="Export format. Only 'csv' is currently supported."
    ),
    accountId: Optional[str] = Query(
        default=None, description="Filter by account (matches fromAccount or toAccount), e.g. ACC-12345"
    ),
    type: Optional[TransactionType] = Query(default=None, description="Filter by transaction type"),
    from_: Optional[str] = Query(
        default=None, alias="from", description="Start date, inclusive (YYYY-MM-DD), e.g. 2024-01-01"
    ),
    to: Optional[str] = Query(
        default=None, description="End date, inclusive (YYYY-MM-DD), e.g. 2024-01-31"
    ),
) -> Response:
    """Export transactions as a downloadable file (currently CSV only).

    Accepts the same filters as `GET /transactions` (`accountId`, `type`,
    `from`, `to`) so the export can be narrowed down the same way. An
    unsupported `format` value returns 400.
    """
    transactions = _filter_transactions(accountId, type, from_, to)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_COLUMNS)
    for t in transactions:
        writer.writerow([
            t.id,
            t.fromAccount or "",
            t.toAccount or "",
            f"{t.amount:.2f}",
            t.currency,
            t.type,
            t.timestamp,
            t.status,
        ])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )


@router.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: str) -> Transaction:
    """Get a single transaction by id, or 404 if it doesn't exist."""
    transaction = store.get(transaction_id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found",
        )
    return transaction
