from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.ml.pipeline import lex_intel_engine
from app.ml.sentiment_model import ModelNotTrainedError
from app.models.customer import Customer
from app.models.interaction import Interaction
from app.models.user import User, UserRole
from app.schemas.interaction import InteractionCreate, InteractionResponse
from app.services.audit_service import log_audit_event

router = APIRouter()

READ_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.ANALYST]
WRITE_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT]


@router.get("/", response_model=List[InteractionResponse])
def list_interactions(
    customer_id: Optional[int] = None,
    channel: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """List customer interactions and feedback records."""
    query = db.query(Interaction)
    if customer_id:
        query = query.filter(Interaction.customer_id == customer_id)
    if channel:
        query = query.filter(Interaction.channel == channel)

    return query.order_by(Interaction.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
def log_interaction(
    interaction_in: InteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """
    Log an interaction and automatically score sentiment using LexIntel AI 
    if the trained model artifact is available.
    """
    customer = db.query(Customer).filter(Customer.id == interaction_in.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {interaction_in.customer_id} does not exist",
        )

    # Automatically run LexIntel AI sentiment classification if model is available
    sentiment_label = None
    sentiment_conf = None
    try:
        sentiment_res = lex_intel_engine.predict_sentiment(interaction_in.content)
        sentiment_label = sentiment_res["sentiment"]
        sentiment_conf = sentiment_res["confidence"]
    except ModelNotTrainedError:
        # Graceful fallback: unscored until model is trained
        pass

    interaction = Interaction(
        customer_id=interaction_in.customer_id,
        channel=interaction_in.channel.lower().strip(),
        direction=interaction_in.direction.lower().strip(),
        subject=interaction_in.subject.strip() if interaction_in.subject else None,
        content=interaction_in.content.strip(),
        sentiment=sentiment_label,
        sentiment_confidence=sentiment_conf,
        user_id=current_user.id,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    log_audit_event(
        db=db,
        action="INTERACTION_LOGGED",
        entity_type="interaction",
        entity_id=str(interaction.id),
        user_id=current_user.id,
        details={
            "customer_id": interaction.customer_id,
            "channel": interaction.channel,
            "sentiment": sentiment_label,
        }
    )

    return interaction
