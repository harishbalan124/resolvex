from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class InteractionBase(BaseModel):
    customer_id: int
    channel: str
    direction: str = "inbound"
    subject: Optional[str] = None
    content: str


class InteractionCreate(InteractionBase):
    pass


class InteractionResponse(InteractionBase):
    id: int
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
