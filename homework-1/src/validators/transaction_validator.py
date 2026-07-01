"""Standalone validation rules for transactions.

Kept separate from the Pydantic models so the rules themselves (currency
list, account number format, amount precision) are plain, independently
testable functions - the models module just wires them into field/model
validators.
"""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

TWO_PLACES = Decimal("0.01")

# Active ISO 4217 alphabetic currency codes.
VALID_CURRENCIES = {
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL",
    "BSD", "BTN", "BWP", "BYN", "BZD", "CAD", "CDF", "CHF", "CLP", "CNY",
    "COP", "CRC", "CUP", "CVE", "CZK", "DJF", "DKK", "DOP", "DZD", "EGP",
    "ERN", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL", "GHS", "GIP", "GMD",
    "GNF", "GTQ", "GYD", "HKD", "HNL", "HTG", "HUF", "IDR", "ILS", "INR",
    "IQD", "IRR", "ISK", "JMD", "JOD", "JPY", "KES", "KGS", "KHR", "KMF",
    "KPW", "KRW", "KWD", "KYD", "KZT", "LAK", "LBP", "LKR", "LRD", "LSL",
    "LYD", "MAD", "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRU", "MUR",
    "MVR", "MWK", "MXN", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR",
    "NZD", "OMR", "PAB", "PEN", "PGK", "PHP", "PKR", "PLN", "PYG", "QAR",
    "RON", "RSD", "RUB", "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD",
    "SHP", "SLE", "SOS", "SRD", "SSP", "STN", "SYP", "SZL", "THB", "TJS",
    "TMT", "TND", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH", "UGX", "USD",
    "UYU", "UZS", "VES", "VND", "VUV", "WST", "XAF", "XCD", "XOF", "XPF",
    "YER", "ZAR", "ZMW", "ZWL",
}

# Account numbers must look like ACC-XXXXX, where X is any alphanumeric
# character (letters and/or digits), exactly 5 of them.
ACCOUNT_PATTERN = re.compile(r"^ACC-[A-Za-z0-9]{5}$")


def validate_account_number(value: str) -> bool:
    """True if `value` matches the ACC-XXXXX format. Reused by path/query params too."""
    return bool(ACCOUNT_PATTERN.match(value))


def validate_amount(value: Decimal) -> Decimal:
    """Amount must be a finite positive number with at most 2 decimal places.

    `value` arrives already coerced to `Decimal` by Pydantic (from a JSON
    number or string). Using `Decimal` end-to-end - rather than `float` -
    avoids binary floating point artifacts (e.g. 0.1 + 0.2 ==
    0.30000000000000004) when amounts are later summed for balances,
    summaries, and interest.

    Raises ValueError with a user-facing message on failure. Returns the
    value quantized to exactly 2 decimal places on success.
    """
    if not value.is_finite():
        raise ValueError("Amount must be a finite number")
    if value <= 0:
        raise ValueError("Amount must be a positive number")
    # normalize() strips insignificant trailing zeros first, so "10.50" and
    # "10.990" are judged by their *significant* decimal places (1 and 2
    # respectively), not by however many digits happened to be typed.
    exponent = value.normalize().as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise ValueError("Amount must have at most 2 decimal places")
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def validate_currency_code(value: str) -> str:
    """Normalize and validate a currency code against the ISO 4217 list."""
    normalized = value.upper().strip() if isinstance(value, str) else value
    if not isinstance(normalized, str) or len(normalized) != 3 or not normalized.isalpha():
        raise ValueError("Invalid currency code")
    if normalized not in VALID_CURRENCIES:
        raise ValueError("Invalid currency code")
    return normalized


def validate_account_field(value: Optional[str]) -> Optional[str]:
    """Trim and validate an optional fromAccount/toAccount field."""
    if value is None:
        return value
    value = value.strip()
    if not value:
        return None
    if not validate_account_number(value):
        raise ValueError("Account number must follow format ACC-XXXXX (X is alphanumeric)")
    return value
