from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ComplaintStatusHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    changed_by_user_id: Optional[int] = None
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintBase(BaseModel):
    customer_id: int
    title: str
    description: str
    category: str
    priority: str = "MEDIUM"


class ComplaintCreate(ComplaintBase):
    assigned_user_id: Optional[int] = None


class ComplaintUpdateStatus(BaseModel):
    status: str
    comment: Optional[str] = None


class ComplaintResponse(ComplaintBase):
    id: int
    ticket_number: str
    assigned_user_id: Optional[int] = None
    status: str
    sla_deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    status_history: List[ComplaintStatusHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)
