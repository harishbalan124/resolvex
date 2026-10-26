from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SentimentPredictRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000, description="Customer feedback or interaction text")


class SentimentPredictResponse(BaseModel):
    sentiment: str
    confidence: float
    probabilities: Dict[str, float]
    key_drivers: List[str]
    model_version: str


class ChurnPredictResponse(BaseModel):
    customer_id: str
    churn_risk_score: float
    risk_label: str
    top_drivers: List[Dict[str, str]]
    model_version: str


class ModelStatusResponse(BaseModel):
    engine: str
    sentiment_model: Dict[str, Any]
    churn_model: Dict[str, Any]
