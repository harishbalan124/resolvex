#!/usr/bin/env python3
"""
ResolveX / LexIntel AI Model Training Pipeline
Trains:
  1. TF-IDF + Logistic Regression Sentiment Model (data/sentiment.csv)
  2. Random Forest Churn Risk Classifier (data/churn.csv)
Saves serialized model artifacts and metadata to backend/app/ml/artifacts/
"""
import os
import sys

# Ensure backend directory is in path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, BACKEND_DIR)

from app.ml.sentiment_model import SentimentModel
from app.ml.churn_model import ChurnModel


def train_all_models():
    print("=" * 60, flush=True)
    print("  LexIntel AI: Autonomous Intelligence Model Training Pipeline", flush=True)
    print("=" * 60, flush=True)

    sentiment_csv = os.path.join(DATA_DIR, "sentiment.csv")
    churn_csv = os.path.join(DATA_DIR, "churn.csv")

    if not os.path.exists(sentiment_csv) or not os.path.exists(churn_csv):
        print("\n[ERROR] Datasets not found in data/ directory.", flush=True)
        print("Please run `python scripts/seed_synthetic_data.py` first to generate synthetic datasets.", flush=True)
        sys.exit(1)

    # 1. Train Sentiment Model
    print("\n[1/2] Training LexIntel AI Customer Sentiment Model...", flush=True)
    sentiment_model = SentimentModel()
    sentiment_meta = sentiment_model.train(sentiment_csv)

    print(f" -> Artifact Saved: {sentiment_model.artifact_path}", flush=True)
    print(f" -> Training Samples: {sentiment_meta['samples_count']}", flush=True)
    print(f" -> Classes: {sentiment_meta['classes']}", flush=True)
    print(" -> Real Validation Metrics:", flush=True)
    for metric_name, val in sentiment_meta["metrics"].items():
        print(f"     * {metric_name.capitalize():<12}: {val:.4f}", flush=True)

    # 2. Train Churn Model
    print("\n[2/2] Training LexIntel AI Customer Churn Risk Model...", flush=True)
    churn_model = ChurnModel()
    churn_meta = churn_model.train(churn_csv)

    print(f" -> Artifact Saved: {churn_model.artifact_path}", flush=True)
    print(f" -> Training Samples: {churn_meta['samples_count']}", flush=True)
    print(" -> Top 5 Global Predictive Drivers:", flush=True)
    for feat, imp in list(churn_model.feature_importances.items())[:5]:
        print(f"     * {feat:<28}: {imp:.4f}", flush=True)
    print(" -> Real Validation Metrics:", flush=True)
    for metric_name, val in churn_meta["metrics"].items():
        print(f"     * {metric_name.upper():<12}: {val:.4f}", flush=True)

    print("\n" + "=" * 60, flush=True)
    print(" [SUCCESS] All LexIntel AI models trained and serialized successfully!", flush=True)
    print("=" * 60 + "\n", flush=True)


if __name__ == "__main__":
    train_all_models()
