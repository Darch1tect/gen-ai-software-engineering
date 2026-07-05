"""Routes for account-level views: balance, summary, and simple interest."""

from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, HTTPException, Query, status

from src.models.transaction import (
    AccountSummary,
    BalanceResponse,
    InterestResponse,
    Transaction,
    ValidationErrorResponse,
)
from src.utils.storage import store
from src.validators.transaction_validator import validate_account_number

router = APIRouter(prefix="/accounts", tags=["accounts"])

DAYS_PER_YEAR = Decimal("365")
_TWO_PLACES = Decimal("0.01")

_VALIDATION_ERROR_RESPONSE = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ValidationErrorResponse,
        "description": "Validation failed - see `details` for the offending field(s).",
    }
}
_ACCOUNT_NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {"description": "Account has no transactions on record."}
}


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def _require_known_account(account_id: str) -> list[Transaction]:
    """Validate the account id format and look up its transactions.

    Raises 400 if the format is wrong, 404 if the account has never
    appeared in any transaction. Shared by the balance/summary/interest routes.
    """
    if not validate_account_number(account_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "details": [{
                    "field": "accountId",
                    "message": "Account number must follow format ACC-XXXXX (X is alphanumeric)",
                }],
            },
        )

    account_transactions = store.for_account(account_id)
    if not account_transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found",
        )
    return account_transactions


def _compute_balances(account_transactions: list[Transaction], account_id: str) -> dict[str, Decimal]:
    """Net balance per currency from completed transactions.

    deposit credits toAccount; withdrawal debits fromAccount; transfer debits
    fromAccount and credits toAccount. Only 'completed' transactions count.
    """
    balances: dict[str, Decimal] = {}
    for t in account_transactions:
        if t.status != "completed":
            continue
        if t.toAccount == account_id:
            balances[t.currency] = balances.get(t.currency, Decimal("0")) + t.amount
        if t.fromAccount == account_id:
            balances[t.currency] = balances.get(t.currency, Decimal("0")) - t.amount
    return {currency: _round_money(value) for currency, value in balances.items()}


@router.get("/{account_id}/balance", response_model=BalanceResponse, responses={
    **_VALIDATION_ERROR_RESPONSE, **_ACCOUNT_NOT_FOUND_RESPONSE,
})
def get_account_balance(account_id: str) -> BalanceResponse:
    """Compute an account's balance per currency from completed transactions.

    - deposit: credits toAccount
    - withdrawal: debits fromAccount
    - transfer: debits fromAccount, credits toAccount
    Only 'completed' transactions affect the balance. If the account has no
    transactions at all, 404 is returned.
    """
    account_transactions = _require_known_account(account_id)
    balances = _compute_balances(account_transactions, account_id)
    return BalanceResponse(accountId=account_id, balances=balances)


@router.get("/{account_id}/summary", response_model=AccountSummary, responses={
    **_VALIDATION_ERROR_RESPONSE, **_ACCOUNT_NOT_FOUND_RESPONSE,
})
def get_account_summary(account_id: str) -> AccountSummary:
    """Summarize an account's transaction history.

    - totalDeposits / totalWithdrawals: money in vs. money out per currency,
      from 'completed' transactions only. A 'transfer' counts as a deposit
      for the receiving account and a withdrawal for the sending account
      (same direction logic as the balance endpoint).
    - transactionCount: all transactions involving the account, any status.
    - mostRecentTransactionDate: timestamp of the latest one of those.
    404 if the account has never appeared in any transaction, 400 if the
    accountId doesn't match the ACC-XXXXX format.
    """
    account_transactions = _require_known_account(account_id)

    total_deposits: dict[str, Decimal] = {}
    total_withdrawals: dict[str, Decimal] = {}
    for t in account_transactions:
        if t.status != "completed":
            continue
        if t.toAccount == account_id:
            total_deposits[t.currency] = total_deposits.get(t.currency, Decimal("0")) + t.amount
        if t.fromAccount == account_id:
            total_withdrawals[t.currency] = total_withdrawals.get(t.currency, Decimal("0")) + t.amount

    total_deposits = {currency: _round_money(value) for currency, value in total_deposits.items()}
    total_withdrawals = {currency: _round_money(value) for currency, value in total_withdrawals.items()}

    most_recent = max((t.timestamp for t in account_transactions), default=None)

    return AccountSummary(
        accountId=account_id,
        totalDeposits=total_deposits,
        totalWithdrawals=total_withdrawals,
        transactionCount=len(account_transactions),
        mostRecentTransactionDate=most_recent,
    )


@router.get("/{account_id}/interest", response_model=InterestResponse, responses={
    **_VALIDATION_ERROR_RESPONSE, **_ACCOUNT_NOT_FOUND_RESPONSE,
})
def calculate_account_interest(
    account_id: str,
    rate: float = Query(
        ..., ge=0, description="Annual interest rate as a decimal, e.g. 0.05 for 5%"
    ),
    days: int = Query(
        ..., ge=0, description="Number of days to calculate interest over"
    ),
) -> InterestResponse:
    """Calculate simple interest on the account's current balance.

    For each currency the account holds a balance in:
        interest = principal * rate * (days / 365)
        totalAmount = principal + interest

    `principal` is the account's current balance (same computation as
    /balance), so the same 400 (bad accountId format) / 404 (unknown
    account) rules apply. `rate` and `days` must be non-negative.

    The calculation itself is done in `Decimal` (principal and the
    computed interest are money; `rate` stays a plain `float` ratio and is
    converted via `Decimal(str(rate))` - going through the same decimal
    string representation the client sent - rather than `Decimal(rate)`,
    which would bake in binary floating point noise).
    """
    account_transactions = _require_known_account(account_id)
    principal = _compute_balances(account_transactions, account_id)

    rate_decimal = Decimal(str(rate))
    time_fraction = Decimal(days) / DAYS_PER_YEAR

    interest = {
        currency: _round_money(amount * rate_decimal * time_fraction)
        for currency, amount in principal.items()
    }
    total_amount = {
        currency: _round_money(principal[currency] + interest[currency])
        for currency in principal
    }

    return InterestResponse(
        accountId=account_id,
        rate=rate,
        days=days,
        principal=principal,
        interest=interest,
        totalAmount=total_amount,
    )
