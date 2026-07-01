"""Pydantic models for the Transactions API."""

import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.validators.transaction_validator import (
    validate_account_field,
    validate_amount,
    validate_currency_code,
)

TransactionType = Literal["deposit", "withdrawal", "transfer"]
TransactionStatus = Literal["pending", "completed", "failed"]


class TransactionCreate(BaseModel):
    """Request body for creating a new transaction."""

    fromAccount: Optional[str] = Field(
        default=None, description="Source account. Required for withdrawal/transfer."
    )
    toAccount: Optional[str] = Field(
        default=None, description="Destination account. Required for deposit/transfer."
    )
    amount: float = Field(
        ..., description="Transaction amount, must be positive with at most 2 decimal places."
    )
    currency: str = Field(..., description="ISO 4217 currency code, e.g. USD, EUR, GBP.")
    type: TransactionType

    @field_validator("amount")
    @classmethod
    def _validate_amount(cls, value: float) -> float:
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
    amount: float
    currency: str
    type: TransactionType
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: TransactionStatus = "completed"

    @classmethod
    def from_create(cls, data: TransactionCreate) -> "Transaction":
        return cls(
            fromAccount=data.fromAccount,
            toAccount=data.toAccount,
            amount=data.amount,
            currency=data.currency,
            type=data.type,
        )


class BalanceResponse(BaseModel):
    """Response for the account balance endpoint."""

    accountId: str
    balances: dict[str, float] = Field(
        description="Balance per currency, e.g. {'USD': 120.5, 'EUR': -30.0}"
    )


class AccountSummary(BaseModel):
    """Response for the account transaction summary endpoint."""

    accountId: str
    totalDeposits: dict[str, float] = Field(
        description=(
            "Total amount credited to the account per currency - 'deposit' "
            "transactions plus the incoming side of 'transfer' transactions, "
            "e.g. {'USD': 250.0}"
        )
    )
    totalWithdrawals: dict[str, float] = Field(
        description=(
            "Total amount debited from the account per currency - 'withdrawal' "
            "transactions plus the outgoing side of 'transfer' transactions, "
            "e.g. {'USD': 40.0}"
        )
    )
    transactionCount: int = Field(description="Number of transactions involving this account.")
    mostRecentTransactionDate: Optional[str] = Field(
        default=None, description="ISO 8601 timestamp of the most recent transaction, if any."
    )


class InterestResponse(BaseModel):
    """Response for the simple-interest calculation endpoint."""

    accountId: str
    rate: float = Field(description="Annual interest rate used in the calculation, e.g. 0.05 for 5%.")
    days: int = Field(description="Number of days the interest was calculated over.")
    principal: dict[str, float] = Field(
        description="Current balance per currency, used as principal, e.g. {'USD': 1000.0}"
    )
    interest: dict[str, float] = Field(
        description="Simple interest per currency: principal * rate * (days / 365)."
    )
    totalAmount: dict[str, float] = Field(
        description="principal + interest per currency."
    )


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
