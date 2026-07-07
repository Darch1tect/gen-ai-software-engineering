import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.classifier import classify
from app.database import get_db
from app.models import utcnow
from app.parsers import FileParseError, detect_format, parse_file

logger = logging.getLogger("app.tickets")

router = APIRouter(prefix="/tickets", tags=["tickets"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

MANUAL_OVERRIDE_CONFIDENCE = 1.0


def _to_orm_kwargs(data: schemas.TicketCreate) -> dict:
    kwargs = data.model_dump(mode="json")
    kwargs["meta"] = kwargs.pop("metadata")
    return kwargs


def _auto_classify(ticket: models.Ticket, db: Session) -> schemas.ClassificationResult:
    """Classify the ticket, apply the result and append an audit log row."""
    result = classify(ticket.subject, ticket.description)
    ticket.category = result.category.value
    ticket.priority = result.priority.value
    ticket.classification_confidence = result.confidence
    ticket.classification_source = schemas.ClassificationSource.auto.value
    ticket.classified_at = utcnow()
    db.add(models.ClassificationLog(
        ticket_id=ticket.id,
        source=schemas.ClassificationSource.auto.value,
        category=result.category.value,
        priority=result.priority.value,
        confidence=result.confidence,
        reasoning=result.reasoning,
        keywords=result.keywords_found,
    ))
    return schemas.ClassificationResult(
        category=result.category,
        priority=result.priority,
        confidence=result.confidence,
        reasoning=result.reasoning,
        keywords_found=result.keywords_found,
    )


def _log_manual_override(ticket: models.Ticket, overridden: list[str], db: Session) -> None:
    reasoning = (
        f"Manual override via PUT /tickets/{ticket.id}: "
        + ", ".join(f"{f}={getattr(ticket, f)}" for f in overridden)
    )
    ticket.classification_source = schemas.ClassificationSource.manual.value
    ticket.classification_confidence = MANUAL_OVERRIDE_CONFIDENCE
    ticket.classified_at = utcnow()
    db.add(models.ClassificationLog(
        ticket_id=ticket.id,
        source=schemas.ClassificationSource.manual.value,
        category=ticket.category,
        priority=ticket.priority,
        confidence=MANUAL_OVERRIDE_CONFIDENCE,
        reasoning=reasoning,
        keywords=[],
    ))
    logger.info(reasoning)


@router.post("", response_model=schemas.TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: schemas.TicketCreate,
    auto_classify: bool = Query(
        default=False,
        description="Classify the ticket on creation; overrides any category/priority in the body",
    ),
    db: Session = Depends(get_db),
):
    ticket = models.Ticket(**_to_orm_kwargs(payload))
    if ticket.status in (schemas.Status.resolved, schemas.Status.closed):
        ticket.resolved_at = utcnow()
    db.add(ticket)
    if auto_classify:
        db.flush()  # assign the id used in the audit log row
        _auto_classify(ticket, db)
    db.commit()
    return ticket


@router.post("/import", response_model=schemas.ImportSummary)
async def import_tickets(
    file: UploadFile,
    auto_classify: bool = Query(
        default=False,
        description="Classify every imported ticket; overrides category/priority from the file",
    ),
    db: Session = Depends(get_db),
):
    file_format = detect_format(file.filename, file.content_type)
    if file_format is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. Upload a .csv, .json or .xml file "
                "(or set a matching Content-Type)."
            ),
        )

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB upload limit")
    if not data.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        records = parse_file(data, file_format)
    except FileParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    successful_ids: list[str] = []
    errors: list[schemas.ImportError_] = []
    for index, record in enumerate(records, start=1):
        try:
            payload = schemas.TicketCreate.model_validate(record)
        except ValidationError as exc:
            messages = [
                f"{'.'.join(str(loc) for loc in err['loc']) or 'record'}: {err['msg']}"
                for err in exc.errors()
            ]
            errors.append(schemas.ImportError_(record=index, errors=messages))
            continue
        ticket = models.Ticket(**_to_orm_kwargs(payload))
        if ticket.status in (schemas.Status.resolved, schemas.Status.closed):
            ticket.resolved_at = utcnow()
        db.add(ticket)
        db.flush()
        if auto_classify:
            _auto_classify(ticket, db)
        successful_ids.append(ticket.id)

    db.commit()
    return schemas.ImportSummary(
        total_records=len(records),
        successful=len(successful_ids),
        failed=len(errors),
        errors=errors,
        created_ids=successful_ids,
    )


@router.get("", response_model=list[schemas.TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    status_: schemas.Status | None = Query(default=None, alias="status"),
    priority: schemas.Priority | None = None,
    category: schemas.Category | None = None,
    customer_id: str | None = None,
    assigned_to: str | None = None,
    tag: str | None = Query(default=None, description="Return tickets carrying this tag"),
    search: str | None = Query(default=None, description="Substring match in subject/description"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = select(models.Ticket)
    if status_ is not None:
        query = query.where(models.Ticket.status == status_.value)
    if priority is not None:
        query = query.where(models.Ticket.priority == priority.value)
    if category is not None:
        query = query.where(models.Ticket.category == category.value)
    if customer_id is not None:
        query = query.where(models.Ticket.customer_id == customer_id)
    if assigned_to is not None:
        query = query.where(models.Ticket.assigned_to == assigned_to)
    if search is not None:
        pattern = f"%{search}%"
        query = query.where(
            or_(models.Ticket.subject.ilike(pattern), models.Ticket.description.ilike(pattern))
        )
    query = query.order_by(models.Ticket.created_at.desc()).limit(limit).offset(offset)
    tickets = db.scalars(query).all()
    if tag is not None:
        tickets = [t for t in tickets if tag in (t.tags or [])]
    return tickets


@router.post("/{ticket_id}/auto-classify", response_model=schemas.ClassificationResult)
def auto_classify_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    result = _auto_classify(ticket, db)
    ticket.updated_at = utcnow()
    db.commit()
    return result


@router.get("/{ticket_id}/classification-log", response_model=list[schemas.ClassificationLogOut])
def get_classification_log(ticket_id: str, db: Session = Depends(get_db)):
    if db.get(models.Ticket, ticket_id) is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return db.scalars(
        select(models.ClassificationLog)
        .where(models.ClassificationLog.ticket_id == ticket_id)
        .order_by(models.ClassificationLog.id)
    ).all()


@router.get("/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.put("/{ticket_id}", response_model=schemas.TicketOut)
def update_ticket(ticket_id: str, payload: schemas.TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    changes = payload.model_dump(mode="json", exclude_unset=True)
    if "metadata" in changes:
        changes["meta"] = changes.pop("metadata")
    for field, value in changes.items():
        setattr(ticket, field, value)

    if "status" in changes:
        if changes["status"] in (schemas.Status.resolved, schemas.Status.closed):
            if ticket.resolved_at is None:
                ticket.resolved_at = utcnow()
        else:
            ticket.resolved_at = None

    overridden = [f for f in ("category", "priority") if f in changes]
    if overridden:
        _log_manual_override(ticket, overridden, db)
    ticket.updated_at = utcnow()

    db.commit()
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    db.delete(ticket)
    db.commit()
