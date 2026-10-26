from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerBase(BaseModel):
    external_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    tier: str = "Standard"


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    churn_risk_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    transactions_count: int = 0
    interactions_count: int = 0
    complaints_count: int = 0
    disputes_count: int = 0
