"""Data validation tests for the Pydantic ticket schemas. (9 tests)"""

import pytest
from pydantic import ValidationError

from app.schemas import TicketCreate, TicketMetadata, TicketUpdate

VALID = {
    "customer_id": "CUST-001",
    "customer_email": "jane@example.com",
    "customer_name": "Jane Doe",
    "subject": "Cannot log in",
    "description": "I keep getting an error after resetting my password.",
}


def test_valid_ticket_gets_defaults():
    ticket = TicketCreate(**VALID)
    assert ticket.category.value == "other"
    assert ticket.priority.value == "medium"
    assert ticket.status.value == "new"
    assert ticket.tags == []
    assert ticket.metadata is None
    assert ticket.assigned_to is None


def test_invalid_email_rejected():
    with pytest.raises(ValidationError) as exc:
        TicketCreate(**dict(VALID, customer_email="not-an-email"))
    assert "customer_email" in str(exc.value)


def test_subject_length_bounds():
    TicketCreate(**dict(VALID, subject="x" * 200))  # upper bound is allowed
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, subject=""))
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, subject="x" * 201))


def test_description_too_short_rejected():
    with pytest.raises(ValidationError) as exc:
        TicketCreate(**dict(VALID, description="too short"))
    assert "description" in str(exc.value)


def test_description_length_upper_bound():
    TicketCreate(**dict(VALID, description="x" * 2000))  # upper bound is allowed
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, description="x" * 2001))


def test_invalid_category_rejected():
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, category="nonsense"))


def test_invalid_priority_and_status_rejected():
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, priority="mega-urgent"))
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, status="sleeping"))


def test_metadata_enums_validated():
    ok = TicketMetadata(source="chat", device_type="mobile")
    assert ok.browser is None
    with pytest.raises(ValidationError):
        TicketMetadata(source="carrier_pigeon")
    with pytest.raises(ValidationError):
        TicketMetadata(source="chat", device_type="fridge")
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, metadata={"browser": "Chrome"}))  # source required


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        TicketCreate(**dict(VALID, surprise="field"))
    with pytest.raises(ValidationError):
        TicketUpdate(surprise="field")
