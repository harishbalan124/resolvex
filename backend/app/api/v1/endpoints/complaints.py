from datetime import datetime, timezone
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.schemas.complaint import ComplaintCreate, ComplaintResponse, ComplaintUpdateStatus
from app.services.audit_service import log_audit_event

router = APIRouter()

READ_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.ANALYST]
WRITE_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT]


def generate_ticket_number() -> str:
    year = datetime.now(timezone.utc).year
    suffix = secrets.token_hex(3).upper()
    return f"CMP-{year}-{suffix}"


@router.get("/", response_model=List[ComplaintResponse])
def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_to_me: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """List customer complaints with RBAC and assignment filters."""
    query = db.query(Complaint)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    # Support agents can filter to their assigned tickets
    if assigned_to_me and current_user.role == UserRole.SUPPORT_AGENT:
        query = query.filter(Complaint.assigned_user_id == current_user.id)

    return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    complaint_in: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """Log a new complaint ticket with initial status history."""
    customer = db.query(Customer).filter(Customer.id == complaint_in.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {complaint_in.customer_id} does not exist",
        )

    ticket_number = generate_ticket_number()
    assigned_user_id = complaint_in.assigned_user_id or (
        current_user.id if current_user.role == UserRole.SUPPORT_AGENT else None
    )

    complaint = Complaint(
        ticket_number=ticket_number,
        customer_id=complaint_in.customer_id,
        assigned_user_id=assigned_user_id,
        title=complaint_in.title.strip(),
        description=complaint_in.description.strip(),
        category=complaint_in.category,
        priority=complaint_in.priority,
        status="OPEN",
    )
    db.add(complaint)
    db.flush()

    # Initial status history
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        changed_by_user_id=current_user.id,
        old_status=None,
        new_status="OPEN",
        comment=f"Complaint created by {current_user.full_name} ({current_user.role.value}).",
    )
    db.add(history)

    log_audit_event(
        db=db,
        action="COMPLAINT_CREATED",
        entity_type="complaint",
        entity_id=str(complaint.id),
        user_id=current_user.id,
        details={
            "ticket_number": ticket_number,
            "category": complaint.category,
            "priority": complaint.priority,
        }
    )

    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_detail(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """Retrieve detailed complaint and timeline history."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return complaint


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: int,
    payload: ComplaintUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """Update complaint status (Open, In Investigation, Pending Approval, Resolved, Closed)."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    old_status = complaint.status
    new_status = payload.status.upper().strip()

    if old_status == new_status:
        return complaint

    complaint.status = new_status
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        changed_by_user_id=current_user.id,
        old_status=old_status,
        new_status=new_status,
        comment=payload.comment.strip() if payload.comment else f"Status changed from {old_status} to {new_status}.",
    )
    db.add(history)

    log_audit_event(
        db=db,
        action="COMPLAINT_STATUS_UPDATED",
        entity_type="complaint",
        entity_id=str(complaint.id),
        user_id=current_user.id,
        details={"old_status": old_status, "new_status": new_status, "comment": payload.comment}
    )

    db.commit()
    db.refresh(complaint)
    return complaint
