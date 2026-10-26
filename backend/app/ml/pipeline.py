from typing import Any, Dict, Optional
from app.ml.churn_model import ChurnModel
from app.ml.sentiment_model import ModelNotTrainedError, SentimentModel


class LexIntelAIEngine:
    """Central AI engine gateway for ResolveX sentiment and churn intelligence."""

    def __init__(self):
        self.sentiment_model = SentimentModel()
        self.churn_model = ChurnModel()

    def reload_models(self) -> None:
        """Reload serialized model artifacts from disk."""
        self.sentiment_model.load()
        self.churn_model.load()

    def get_status(self) -> Dict[str, Any]:
        """Telemetry reporting on model training state and genuine validation metrics."""
        return {
            "engine": "LexIntel AI",
            "sentiment_model": {
                "trained": self.sentiment_model.is_trained,
                "version": self.sentiment_model.VERSION,
                "metadata": self.sentiment_model.metadata if self.sentiment_model.is_trained else None,
            },
            "churn_model": {
                "trained": self.churn_model.is_trained,
                "version": self.churn_model.VERSION,
                "metadata": self.churn_model.metadata if self.churn_model.is_trained else None,
            }
        }

    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """Run sentiment classification with explainable token drivers."""
        return self.sentiment_model.predict(text)

    def predict_churn(self, customer_features: Dict[str, Any]) -> Dict[str, Any]:
        """Run churn risk evaluation with explainable risk drivers."""
        return self.churn_model.predict(customer_features)


# Engine singleton
lex_intel_engine = LexIntelAIEngine()
