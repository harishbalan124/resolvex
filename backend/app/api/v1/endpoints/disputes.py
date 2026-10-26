from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.dispute import Dispute
from app.models.user import User, UserRole
from app.schemas.dispute import DisputeResponse, DisputeScanResponse
from app.services.dispute_engine import dispute_engine
from app.services.recommendation_engine import recommendation_engine

router = APIRouter()

READ_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.ANALYST]
WRITE_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT]


@router.get("/", response_model=List[DisputeResponse])
def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    rule: Optional[str] = None,
    customer_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """List detected disputes with status and rule filters."""
    query = db.query(Dispute)
    if status_filter:
        query = query.filter(Dispute.status == status_filter)
    if rule:
        query = query.filter(Dispute.rule_triggered == rule)
    if customer_id:
        query = query.filter(Dispute.customer_id == customer_id)

    return query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{dispute_id}", response_model=DisputeResponse)
def get_dispute_by_id(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """Get dispute details by ID."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")
    return dispute


@router.post("/scan-batch", response_model=DisputeScanResponse)
def trigger_batch_dispute_scan(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """
    Scan completed transactions against explainable dispute detection rules.
    Generates recommendations in PENDING status for human agent review.
    """
    new_disputes = dispute_engine.scan_unflagged_transactions(db, limit=limit)

    # For each detected dispute, generate autonomous recommendation in PENDING status
    for dispute in new_disputes:
        recommendation_engine.generate_recommendation_for_dispute(
            db=db,
            dispute=dispute,
            user_id=current_user.id
        )

    db.commit()

    return DisputeScanResponse(
        scanned_count=limit,
        disputes_detected=len(new_disputes),
        dispute_ids=[d.id for d in new_disputes],
    )
