from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    customer_id: int
    external_txn_id: str
    amount: Decimal
    currency: str = "USD"
    merchant: str
    category: str
    txn_timestamp: datetime
    status: str = "COMPLETED"


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
