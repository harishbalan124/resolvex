from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    id: int
    dispute_id: Optional[int] = None
    complaint_id: Optional[int] = None
    suggested_action: str
    justification: str
    confidence_score: float
    status: str
    reviewed_by_user_id: Optional[int] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationReviewRequest(BaseModel):
    action: str  # "APPROVED" or "REJECTED"
    notes: Optional[str] = None
