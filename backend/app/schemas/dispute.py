from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DisputeBase(BaseModel):
    transaction_id: int
    customer_id: int
    complaint_id: Optional[int] = None
    reason: str
    status: str = "DETECTED"
    rule_triggered: str
    risk_score: float = 0.0


class DisputeResponse(DisputeBase):
    id: int
    dispute_reference: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisputeScanResponse(BaseModel):
    scanned_count: int
    disputes_detected: int
    dispute_ids: list[int]
