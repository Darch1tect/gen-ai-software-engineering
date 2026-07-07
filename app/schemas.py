from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Category(str, Enum):
    account_access = "account_access"
    technical_issue = "technical_issue"
    billing_question = "billing_question"
    feature_request = "feature_request"
    bug_report = "bug_report"
    other = "other"


class Priority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class Status(str, Enum):
    new = "new"
    in_progress = "in_progress"
    waiting_customer = "waiting_customer"
    resolved = "resolved"
    closed = "closed"


class Source(str, Enum):
    web_form = "web_form"
    email = "email"
    api = "api"
    chat = "chat"
    phone = "phone"


class DeviceType(str, Enum):
    desktop = "desktop"
    mobile = "mobile"
    tablet = "tablet"


class TicketMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Source
    browser: str | None = None
    device_type: DeviceType | None = None


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1, max_length=100)
    customer_email: EmailStr
    customer_name: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    category: Category = Category.other
    priority: Priority = Priority.medium
    status: Status = Status.new
    assigned_to: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: TicketMetadata | None = None


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str | None = Field(default=None, min_length=1, max_length=100)
    customer_email: EmailStr | None = None
    customer_name: str | None = Field(default=None, min_length=1, max_length=200)
    subject: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    category: Category | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: str | None = None
    tags: list[str] | None = None
    metadata: TicketMetadata | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    customer_email: str
    customer_name: str
    subject: str
    description: str
    category: Category
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    assigned_to: str | None
    tags: list[str]
    metadata: TicketMetadata | None = Field(default=None, validation_alias="meta")


class ImportError_(BaseModel):
    record: int = Field(description="1-based index of the record in the source file")
    errors: list[str]


class ImportSummary(BaseModel):
    total_records: int
    successful: int
    failed: int
    errors: list[ImportError_]
    created_ids: list[str]
