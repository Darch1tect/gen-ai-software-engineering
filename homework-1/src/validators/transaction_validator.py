"""Standalone validation rules for transactions.

Kept separate from the Pydantic models so the rules themselves (currency
list, account number format, amount precision) are plain, independently
testable functions - the models module just wires them into field/model
validators.
"""

import re
from typing import Optional

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


def validate_amount(value: float) -> float:
    """Amount must be positive with at most 2 decimal places.

    Raises ValueError with a user-facing message on failure. Returns the
    value rounded to 2 decimal places on success.
    """
    if value <= 0:
        raise ValueError("Amount must be a positive number")
    # Compare against a fixed-precision string representation rather than
    # raw floats, to sidestep binary floating point rounding artifacts
    # (e.g. 0.1 + 0.2 == 0.30000000000000004).
    fixed = format(value, ".10f").rstrip("0")
    decimal_part = fixed.split(".")[1] if "." in fixed else ""
    if len(decimal_part) > 2:
        raise ValueError("Amount must have at most 2 decimal places")
    return round(value, 2)


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
