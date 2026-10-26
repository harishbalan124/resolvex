import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


class ModelNotTrainedError(Exception):
    """Raised when inference is requested on an uninitialized/untrained model."""
    pass


class SentimentModel:
    VERSION = "1.0.0"

    def __init__(self, artifact_path: Optional[str] = None):
        if artifact_path is None:
            base_dir = os.path.dirname(__file__)
            artifact_path = os.path.join(base_dir, "artifacts", "sentiment_model.joblib")
        self.artifact_path = artifact_path
        self.pipeline: Optional[Pipeline] = None
        self.metadata: Dict = {}
        self.is_trained: bool = False
        self.load()

    def load(self) -> bool:
        if os.path.exists(self.artifact_path):
            try:
                data = joblib.load(self.artifact_path)
                self.pipeline = data["pipeline"]
                self.metadata = data.get("metadata", {})
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
        if "text" not in df.columns or "sentiment" not in df.columns:
            raise ValueError("CSV must contain 'text' and 'sentiment' columns")

        df = df.dropna(subset=["text", "sentiment"])
        X = df["text"].astype(str)
        y = df["sentiment"].astype(str)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")),
            ("clf", LogisticRegression(C=1.2, max_iter=1000, random_state=42))
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        accuracy = float(accuracy_score(y_test, y_pred))
        precision = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        recall = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

        metadata = {
            "version": self.VERSION,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "samples_count": len(df),
            "classes": list(pipeline.classes_),
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            }
        }

        os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
        joblib.dump({"pipeline": pipeline, "metadata": metadata}, self.artifact_path)

        self.pipeline = pipeline
        self.metadata = metadata
        self.is_trained = True

        return metadata

    def predict(self, text: str) -> Dict:
        if not self.is_trained or self.pipeline is None:
            raise ModelNotTrainedError(
                "LexIntel AI: Sentiment analysis model is not trained. "
                "Train the model using scripts/train_models.py before requesting inference."
            )

        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "probabilities": {"negative": 0.33, "neutral": 0.34, "positive": 0.33},
                "key_drivers": [],
                "model_version": self.VERSION,
            }

        probabilities = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        prob_dict = {cls_name: round(float(prob), 4) for cls_name, prob in zip(classes, probabilities)}

        predicted_idx = int(np.argmax(probabilities))
        predicted_sentiment = classes[predicted_idx]
        confidence = float(probabilities[predicted_idx])

        # Explainability: Extract key token drivers for the predicted class
        key_drivers = self._extract_explainable_drivers(text, predicted_sentiment)

        return {
            "sentiment": predicted_sentiment,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "key_drivers": key_drivers,
            "model_version": self.VERSION,
        }

    def _extract_explainable_drivers(self, text: str, predicted_sentiment: str, top_k: int = 5) -> List[str]:
        """Extract top feature terms that contributed to this specific prediction."""
        try:
            tfidf: TfidfVectorizer = self.pipeline.named_steps["tfidf"]
            clf: LogisticRegression = self.pipeline.named_steps["clf"]

            feature_names = tfidf.get_feature_names_out()
            class_idx = list(clf.classes_).index(predicted_sentiment)
            coefficients = clf.coef_[class_idx]

            # Transform single text to token vector
            transformed = tfidf.transform([text]).toarray()[0]
            non_zero_indices = np.where(transformed > 0)[0]

            contributions = []
            for idx in non_zero_indices:
                score = transformed[idx] * coefficients[idx]
                if score > 0:  # Positively contributed to the chosen label
                    contributions.append((feature_names[idx], float(score)))

            contributions.sort(key=lambda x: x[1], reverse=True)
            return [term for term, score in contributions[:top_k]]
        except Exception:
            return []
