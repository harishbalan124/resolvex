from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.dispute import Dispute
from app.models.recommendation import Recommendation
from app.models.user import User, UserRole
from app.schemas.recommendation import RecommendationResponse, RecommendationReviewRequest
from app.services.recommendation_engine import recommendation_engine

router = APIRouter()

READ_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.ANALYST]
REVIEW_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT]


@router.get("/", response_model=List[RecommendationResponse])
def list_recommendations(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """List recommendations with status filter (e.g., PENDING for items awaiting human review)."""
    query = db.query(Recommendation)
    if status_filter:
        query = query.filter(Recommendation.status == status_filter.upper().strip())

    return query.order_by(Recommendation.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation_by_id(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """Retrieve recommendation details."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return rec


@router.post("/generate-for-dispute/{dispute_id}", response_model=RecommendationResponse)
def generate_recommendation_for_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(REVIEW_ROLES)),
):
    """Generate an explainable recommendation in PENDING status for a specific dispute."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    rec = recommendation_engine.generate_recommendation_for_dispute(
        db=db,
        dispute=dispute,
        user_id=current_user.id
    )
    db.commit()
    db.refresh(rec)
    return rec


@router.post("/{recommendation_id}/review", response_model=RecommendationResponse)
def review_recommendation(
    recommendation_id: int,
    payload: RecommendationReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(REVIEW_ROLES)),
):
    """
    Execute mandatory Human-in-the-Loop review (APPROVE or REJECT).
    Enforces Non-Negotiable Rule 2: A human must approve before actions proceed.
    """
    try:
        updated_rec = recommendation_engine.review_recommendation(
            db=db,
            recommendation_id=recommendation_id,
            reviewer_user=current_user,
            action=payload.action,
            notes=payload.notes,
        )
        return updated_rec
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
