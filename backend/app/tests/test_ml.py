import os
import pytest
from fastapi import status

from app.ml.churn_model import ChurnModel
from app.ml.pipeline import lex_intel_engine
from app.ml.sentiment_model import ModelNotTrainedError, SentimentModel
from app.models import Customer, Prediction


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))


def test_untrained_model_raises_clear_error(tmp_path):
    """Enforces Non-Negotiable Rule 1: Clear 'model not trained' message if missing."""
    empty_path = str(tmp_path / "missing_sentiment.joblib")
    model = SentimentModel(artifact_path=empty_path)
    assert model.is_trained is False

    with pytest.raises(ModelNotTrainedError) as exc_info:
        model.predict("The service was terrible and I was overcharged.")
    assert "not trained" in str(exc_info.value).lower()

    empty_churn_path = str(tmp_path / "missing_churn.joblib")
    churn_model = ChurnModel(artifact_path=empty_churn_path)
    assert churn_model.is_trained is False

    with pytest.raises(ModelNotTrainedError) as exc_info2:
        churn_model.predict({"tenure_months": 12})
    assert "not trained" in str(exc_info2.value).lower()


def test_sentiment_model_train_and_predict(tmp_path):
    sentiment_csv = os.path.join(DATA_DIR, "sentiment.csv")
    assert os.path.exists(sentiment_csv), "sentiment.csv must exist"

    artifact_path = str(tmp_path / "sentiment_test.joblib")
    model = SentimentModel(artifact_path=artifact_path)
    meta = model.train(sentiment_csv)

    assert meta["metrics"]["accuracy"] > 0.70
    assert "negative" in meta["classes"]
    assert "positive" in meta["classes"]
    assert os.path.exists(artifact_path)

    # Test negative prediction with explainability
    neg_res = model.predict("I was charged twice for transaction TXN-123456 and want an immediate refund.")
    assert neg_res["sentiment"] == "negative"
    assert neg_res["confidence"] > 0.50
    assert len(neg_res["key_drivers"]) > 0

    # Test positive prediction
    pos_res = model.predict("Exceptional service! The support agent resolved my dispute in minutes.")
    assert pos_res["sentiment"] == "positive"
    assert pos_res["confidence"] > 0.50


def test_churn_model_train_and_predict(tmp_path):
    churn_csv = os.path.join(DATA_DIR, "churn.csv")
    assert os.path.exists(churn_csv), "churn.csv must exist"

    artifact_path = str(tmp_path / "churn_test.joblib")
    model = ChurnModel(artifact_path=artifact_path)
    meta = model.train(churn_csv)

    assert meta["metrics"]["accuracy"] > 0.70
    assert meta["metrics"]["roc_auc"] > 0.70
    assert len(model.feature_importances) > 0
    assert os.path.exists(artifact_path)

    # High risk profile
    high_risk_input = {
        "tenure_months": 2,
        "monthly_charges": 199.99,
        "total_charges": 399.98,
        "contract_type": "Month-to-Month",
        "payment_method": "Electronic Check",
        "tier": "Standard",
        "num_complaints": 5,
        "num_disputes": 3,
        "avg_sentiment_score": -0.85,
        "support_interactions_count": 14,
    }
    high_res = model.predict(high_risk_input)
    assert high_res["churn_risk_score"] > 0.50
    assert len(high_res["top_drivers"]) > 0

    # Low risk loyal profile
    low_risk_input = {
        "tenure_months": 48,
        "monthly_charges": 49.99,
        "total_charges": 2399.52,
        "contract_type": "Two-Year",
        "payment_method": "Bank Transfer",
        "tier": "Platinum",
        "num_complaints": 0,
        "num_disputes": 0,
        "avg_sentiment_score": 0.80,
        "support_interactions_count": 2,
    }
    low_res = model.predict(low_risk_input)
    assert low_res["churn_risk_score"] < 0.40
    assert low_res["risk_label"] == "LOW_RISK"


def test_analytics_api_endpoints(client, analyst_token_headers, db_session):
    # Ensure LexIntel AI engine is trained and loaded
    sentiment_csv = os.path.join(DATA_DIR, "sentiment.csv")
    churn_csv = os.path.join(DATA_DIR, "churn.csv")
    lex_intel_engine.sentiment_model.train(sentiment_csv)
    lex_intel_engine.churn_model.train(churn_csv)
    lex_intel_engine.reload_models()

    # 1. GET /analytics/status
    res_status = client.get("/api/v1/analytics/status", headers=analyst_token_headers)
    assert res_status.status_code == status.HTTP_200_OK
    status_data = res_status.json()
    assert status_data["engine"] == "LexIntel AI"
    assert status_data["sentiment_model"]["trained"] is True
    assert status_data["churn_model"]["trained"] is True

    # 2. POST /analytics/sentiment
    payload = {"text": "I received an unexpected fee and terrible support when asking for clarification."}
    res_sent = client.post("/api/v1/analytics/sentiment", json=payload, headers=analyst_token_headers)
    assert res_sent.status_code == status.HTTP_200_OK
    sent_data = res_sent.json()
    assert sent_data["sentiment"] == "negative"
    assert "confidence" in sent_data
    assert "key_drivers" in sent_data

    # 3. Create a test customer in DB to evaluate churn
    customer = Customer(
        external_id="CUST-TEST-ML",
        name="ML Test Customer",
        email="test.ml@example.com",
        tier="Gold",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    # 4. POST /analytics/churn/customer/{id}
    res_churn = client.post(
        f"/api/v1/analytics/churn/customer/{customer.id}",
        headers=analyst_token_headers
    )
    assert res_churn.status_code == status.HTTP_200_OK
    churn_data = res_churn.json()
    assert churn_data["customer_id"] == "CUST-TEST-ML"
    assert "churn_risk_score" in churn_data
    assert "risk_label" in churn_data
    assert len(churn_data["top_drivers"]) > 0

    # Verify prediction persisted in DB
    db_pred = db_session.query(Prediction).filter(Prediction.customer_id == customer.id).first()
    assert db_pred is not None
    assert db_pred.model_type == "CHURN"
    assert customer.churn_risk_score is not None
