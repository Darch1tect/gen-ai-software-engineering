"""Pydantic models for the Transactions API."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from src.validators.transaction_validator import (
    validate_account_field,
    validate_amount,
    validate_currency_code,
)

TransactionType = Literal["deposit", "withdrawal", "transfer"]
TransactionStatus = Literal["pending", "completed", "failed"]


def _serialize_money_dict(value: Dict[str, Decimal]) -> Dict[str, str]:
    """Render a currency -> Decimal mapping as currency -> fixed-2-decimal string.

    Money is serialized as a string (not a JSON number) so exact precision
    survives the wire format regardless of client-side float handling -
    the same reasoning that keeps `Decimal` (not `float`) in the Python
    models in the first place.
    """
    return {currency: format(amount, ".2f") for currency, amount in value.items()}


class TransactionCreate(BaseModel):
    """Request body for creating a new transaction."""

    # Unknown fields are rejected rather than silently ignored - important
    # for a financial API where a typo'd field name should never be dropped
    # on the floor without the caller finding out.
    model_config = ConfigDict(extra="forbid")

    fromAccount: Optional[str] = Field(
        default=None, description="Source account. Required for withdrawal/transfer."
    )
    toAccount: Optional[str] = Field(
        default=None, description="Destination account. Required for deposit/transfer."
    )
    amount: Decimal = Field(
        ..., description="Transaction amount, must be positive with at most 2 decimal places."
    )
    currency: str = Field(..., description="ISO 4217 currency code, e.g. USD, EUR, GBP.")
    type: TransactionType

    @field_validator("amount")
    @classmethod
    def _validate_amount(cls, value: Decimal) -> Decimal:
        return validate_amount(value)

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        return validate_currency_code(value)

    @field_validator("fromAccount", "toAccount")
    @classmethod
    def _validate_account(cls, value: Optional[str]) -> Optional[str]:
        return validate_account_field(value)

    @model_validator(mode="after")
    def _validate_accounts_for_type(self) -> "TransactionCreate":
        if self.type == "deposit" and not self.toAccount:
            raise ValueError("toAccount is required for a deposit transaction")
        if self.type == "withdrawal" and not self.fromAccount:
            raise ValueError("fromAccount is required for a withdrawal transaction")
        if self.type == "transfer" and (not self.fromAccount or not self.toAccount):
            raise ValueError("both fromAccount and toAccount are required for a transfer transaction")
        if self.type == "transfer" and self.fromAccount == self.toAccount:
            raise ValueError("fromAccount and toAccount must be different for a transfer transaction")
        return self


class Transaction(BaseModel):
    """Full transaction record as stored and returned by the API."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fromAccount: Optional[str] = None
    toAccount: Optional[str] = None
    amount: Decimal
    currency: str
    type: TransactionType
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: TransactionStatus = "completed"

    @field_serializer("amount", when_used="json")
    def _serialize_amount(self, value: Decimal) -> str:
        return format(value, ".2f")

    @classmethod
    def from_create(cls, data: TransactionCreate) -> "Transaction":
        return cls(
            fromAccount=data.fromAccount,
            toAccount=data.toAccount,
            amount=data.amount,
            currency=data.currency,
            type=data.type,
        )


class TransactionPage(BaseModel):
    """Paginated response for GET /transactions."""

    items: List[Transaction]
    total: int = Field(description="Total number of transactions matching the filters (before pagination).")
    limit: int = Field(description="Page size that was applied.")
    offset: int = Field(description="Number of matching transactions skipped before this page.")


class BalanceResponse(BaseModel):
    """Response for the account balance endpoint."""

    accountId: str
    balances: Dict[str, Decimal] = Field(
        description="Balance per currency, e.g. {'USD': '120.50', 'EUR': '-30.00'}"
    )

    @field_serializer("balances", when_used="json")
    def _serialize_balances(self, value: Dict[str, Decimal]) -> Dict[str, str]:
        return _serialize_money_dict(value)


class AccountSummary(BaseModel):
    """Response for the account transaction summary endpoint."""

    accountId: str
    totalDeposits: Dict[str, Decimal] = Field(
        description=(
            "Total amount credited to the account per currency - 'deposit' "
            "transactions plus the incoming side of 'transfer' transactions, "
            "e.g. {'USD': '250.00'}"
        )
    )
    totalWithdrawals: Dict[str, Decimal] = Field(
        description=(
            "Total amount debited from the account per currency - 'withdrawal' "
            "transactions plus the outgoing side of 'transfer' transactions, "
            "e.g. {'USD': '40.00'}"
        )
    )
    transactionCount: int = Field(description="Number of transactions involving this account.")
    mostRecentTransactionDate: Optional[datetime] = Field(
        default=None, description="Timestamp of the most recent transaction, if any."
    )

    @field_serializer("totalDeposits", "totalWithdrawals", when_used="json")
    def _serialize_money(self, value: Dict[str, Decimal]) -> Dict[str, str]:
        return _serialize_money_dict(value)


class InterestResponse(BaseModel):
    """Response for the simple-interest calculation endpoint."""

    accountId: str
    rate: float = Field(description="Annual interest rate used in the calculation, e.g. 0.05 for 5%.")
    days: int = Field(description="Number of days the interest was calculated over.")
    principal: Dict[str, Decimal] = Field(
        description="Current balance per currency, used as principal, e.g. {'USD': '1000.00'}"
    )
    interest: Dict[str, Decimal] = Field(
        description="Simple interest per currency: principal * rate * (days / 365)."
    )
    totalAmount: Dict[str, Decimal] = Field(
        description="principal + interest per currency."
    )

    @field_serializer("principal", "interest", "totalAmount", when_used="json")
    def _serialize_money(self, value: Dict[str, Decimal]) -> Dict[str, str]:
        return _serialize_money_dict(value)


class ValidationErrorDetail(BaseModel):
    """One field-level validation failure."""

    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Response body for 400 validation failures.

    Example:
        {
          "error": "Validation failed",
          "details": [
            {"field": "amount", "message": "Amount must be a positive number"},
            {"field": "currency", "message": "Invalid currency code"}
          ]
        }
    """

    error: str = "Validation failed"
    details: List[ValidationErrorDetail]


class ErrorResponse(BaseModel):
    """Generic error response (e.g. 404 not found)."""

    error: str
