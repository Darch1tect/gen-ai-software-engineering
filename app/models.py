import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    customer_id: Mapped[str] = mapped_column(String(100), index=True)
    customer_email: Mapped[str] = mapped_column(String(320))
    customer_name: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    # attribute is `meta` because `metadata` is reserved by SQLAlchemy's DeclarativeBase
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(nullable=True)
    classification_source: Mapped[str | None] = mapped_column(String(10), nullable=True)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ClassificationLog(Base):
    """Audit trail of every classification decision, auto or manual.

    ticket_id is intentionally not a foreign key: audit rows must survive
    ticket deletion.
    """

    __tablename__ = "classification_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(36), index=True)
    source: Mapped[str] = mapped_column(String(10))  # "auto" | "manual"
    category: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    reasoning: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
