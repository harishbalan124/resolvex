import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.sentiment_model import ModelNotTrainedError


class ChurnModel:
    VERSION = "1.0.0"

    NUMERICAL_FEATURES = [
        "tenure_months",
        "monthly_charges",
        "total_charges",
        "num_complaints",
        "num_disputes",
        "avg_sentiment_score",
        "support_interactions_count",
    ]

    CATEGORICAL_FEATURES = [
        "contract_type",
        "payment_method",
        "tier",
    ]

    ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

    def __init__(self, artifact_path: Optional[str] = None):
        if artifact_path is None:
            base_dir = os.path.dirname(__file__)
            artifact_path = os.path.join(base_dir, "artifacts", "churn_model.joblib")
        self.artifact_path = artifact_path
        self.pipeline: Optional[Pipeline] = None
        self.metadata: Dict = {}
        self.is_trained: bool = False
        self.feature_importances: Dict[str, float] = {}
        self.load()

    def load(self) -> bool:
        if os.path.exists(self.artifact_path):
            try:
                data = joblib.load(self.artifact_path)
                self.pipeline = data["pipeline"]
                self.metadata = data.get("metadata", {})
                self.feature_importances = data.get("feature_importances", {})
                self.is_trained = True
                return True
            except Exception:
                self.is_trained = False
                return False
        self.is_trained = False
        return False

    def train(self, csv_path: str) -> Dict:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Training dataset not found: {csv_path}")

        df = pd.read_csv(csv_path)
        required_cols = self.ALL_FEATURES + ["churned"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required feature column in CSV: {col}")

        df = df.dropna(subset=required_cols)
        X = df[self.ALL_FEATURES]
        y = df["churned"].astype(int)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.NUMERICAL_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.CATEGORICAL_FEATURES),
            ]
        )

        clf = RandomForestClassifier(
            n_estimators=80,
            max_depth=6,
            min_samples_split=4,
            random_state=42,
            n_jobs=1
        )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", clf)
        ])

        pipeline.fit(X_train, y_train)

        # Evaluate performance
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_test, y_prob))

        # Extract feature importances
        feature_names = self._get_transformed_feature_names(preprocessor)
        raw_importances = clf.feature_importances_
        feature_importance_map = {
            name: round(float(imp), 4) for name, imp in zip(feature_names, raw_importances)
        }
        # Sort by importance descending
        sorted_importance = dict(sorted(feature_importance_map.items(), key=lambda x: x[1], reverse=True))

        metadata = {
            "version": self.VERSION,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "samples_count": len(df),
            "metrics": {
                "accuracy": round(acc, 4),
                "roc_auc": round(auc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
            }
        }

        os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
        joblib.dump({
            "pipeline": pipeline,
            "metadata": metadata,
            "feature_importances": sorted_importance,
        }, self.artifact_path)

        self.pipeline = pipeline
        self.metadata = metadata
        self.feature_importances = sorted_importance
        self.is_trained = True

        return metadata

    def _get_transformed_feature_names(self, preprocessor: ColumnTransformer) -> List[str]:
        output_features = list(self.NUMERICAL_FEATURES)
        cat_encoder = preprocessor.named_transformers_["cat"]
        encoded_cats = cat_encoder.get_feature_names_out(self.CATEGORICAL_FEATURES)
        output_features.extend(list(encoded_cats))
        return output_features

    def predict(self, customer_features: Dict[str, Any]) -> Dict:
        if not self.is_trained or self.pipeline is None:
            raise ModelNotTrainedError(
                "LexIntel AI: Churn prediction model is not trained. "
                "Train the model using scripts/train_models.py before requesting inference."
            )

        # Prepare single record DataFrame with expected defaults
        row = {}
        for feature in self.NUMERICAL_FEATURES:
            val = customer_features.get(feature, 0.0)
            try:
                row[feature] = [float(val) if val is not None else 0.0]
            except (ValueError, TypeError):
                row[feature] = [0.0]

        for feature in self.CATEGORICAL_FEATURES:
            row[feature] = [str(customer_features.get(feature, "Standard"))]

        input_df = pd.DataFrame(row)

        churn_probability = float(self.pipeline.predict_proba(input_df)[0][1])
        churn_risk_score = round(churn_probability, 4)

        if churn_risk_score >= 0.70:
            risk_label = "HIGH_RISK"
        elif churn_risk_score >= 0.40:
            risk_label = "MEDIUM_RISK"
        else:
            risk_label = "LOW_RISK"

        # Generate explainable drivers based on input values and global importances
        explainable_drivers = self._build_explainable_drivers(customer_features, churn_risk_score)

        return {
            "churn_risk_score": churn_risk_score,
            "risk_label": risk_label,
            "top_drivers": explainable_drivers,
            "model_version": self.VERSION,
        }

    def _build_explainable_drivers(self, features: Dict[str, Any], score: float) -> List[Dict[str, str]]:
        drivers = []
        complaints = features.get("num_complaints", 0)
        disputes = features.get("num_disputes", 0)
        tenure = features.get("tenure_months", 12)
        sentiment = features.get("avg_sentiment_score", 0.0)
        contract = features.get("contract_type", "Standard")

        if complaints > 2:
            drivers.append({
                "factor": "Elevated Complaints",
                "detail": f"{complaints} unresolved complaints logged",
                "impact": "HIGH_NEGATIVE"
            })
        if disputes > 1:
            drivers.append({
                "factor": "Frequent Transaction Disputes",
                "detail": f"{disputes} payment disputes filed",
                "impact": "HIGH_NEGATIVE"
            })
        if sentiment < -0.1:
            drivers.append({
                "factor": "Negative Sentiment Trend",
                "detail": f"Average sentiment score: {sentiment}",
                "impact": "MODERATE_NEGATIVE"
            })
        if tenure > 24:
            drivers.append({
                "factor": "Long-Term Loyalty",
                "detail": f"{tenure} months established relationship",
                "impact": "POSITIVE_RETENTION"
            })
        if contract == "Month-to-Month":
            drivers.append({
                "factor": "Flexible Contract",
                "detail": "Month-to-month commitment has higher switching velocity",
                "impact": "MODERATE_NEGATIVE"
            })
        elif contract in ["One-Year", "Two-Year"]:
            drivers.append({
                "factor": "Contract Lock-In",
                "detail": f"Secured under {contract} agreement",
                "impact": "POSITIVE_RETENTION"
            })

        if not drivers:
            drivers.append({
                "factor": "Standard Profile",
                "detail": "Customer metrics within regular baseline thresholds",
                "impact": "NEUTRAL"
            })

        return drivers
