from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.models import utcnow
from app.parsers import FileParseError, detect_format, parse_file

router = APIRouter(prefix="/tickets", tags=["tickets"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _to_orm_kwargs(data: schemas.TicketCreate) -> dict:
    kwargs = data.model_dump(mode="json")
    kwargs["meta"] = kwargs.pop("metadata")
    return kwargs


@router.post("", response_model=schemas.TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: schemas.TicketCreate, db: Session = Depends(get_db)):
    ticket = models.Ticket(**_to_orm_kwargs(payload))
    if ticket.status in (schemas.Status.resolved, schemas.Status.closed):
        ticket.resolved_at = utcnow()
    db.add(ticket)
    db.commit()
    return ticket


@router.post("/import", response_model=schemas.ImportSummary)
async def import_tickets(file: UploadFile, db: Session = Depends(get_db)):
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
