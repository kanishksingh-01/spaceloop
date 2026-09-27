"""
SpaceLoop Anomaly Detection Layer - Predictor Module
Executes inference on extracted feature vectors using calibrated Isolation Forest.
Normalizes output and enforces non-defamatory, objective evidence reporting.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import numpy as np

from fraud_engine.anomaly.config import (
    ANOMALY_FEATURE_KEYS,
    SIGMOID_K,
    MODEL_VERSION,
    FEATURE_VERSION
)
from fraud_engine.anomaly.loader import AnomalyModelLoader
from fraud_engine.anomaly.schemas import AnomalyResult


class AnomalyPredictor:
    """
    Inference orchestrator for unsupervised behavioural anomaly scoring.
    """

    @classmethod
    def extract_vector(cls, features: Dict[str, Any]) -> np.ndarray:
        """
        Extracts ordered numerical feature vector matching model schema.
        Fills missing signals with robust neutral zero defaults.
        """
        row = []
        for key in ANOMALY_FEATURE_KEYS:
            val = features.get(key)
            if val is None:
                val = 0.0
            try:
                row.append(float(val))
            except (ValueError, TypeError):
                row.append(0.0)
        return np.array([row], dtype=np.float64)

    @classmethod
    def predict(
        cls,
        features: Dict[str, Any],
        model_path: Optional[str] = None
    ) -> AnomalyResult:
        """
        Evaluates input feature vector against trained Isolation Forest.
        Normalizes signed decision_function score into a calibrated [0.0, 1.0] anomaly metric.
        IMPORTANT: An anomaly is NOT proof of fraud; all explanations use strictly neutral phrasing.
        """
        model, metadata = AnomalyModelLoader.load(model_path=model_path)
        X = cls.extract_vector(features)

        # Raw signed decision function: negative values indicate outliers/anomalies
        raw_score = float(model.decision_function(X)[0])

        # Calibrated Sigmoid Normalization: maps decision boundary 0.0 -> 0.50
        # raw_score > 0 (inliers)  -> anomaly_score < 0.50
        # raw_score < 0 (outliers) -> anomaly_score > 0.50
        anomaly_score = float(1.0 / (1.0 + np.exp(SIGMOID_K * raw_score)))
        anomaly_score = float(round(min(1.0, max(0.0, anomaly_score)), 4))

        is_anomaly = bool(raw_score < 0.0 or anomaly_score >= 0.50)

        # Factual, non-defamatory evidence phrasing
        if is_anomaly:
            evidence = (
                f"Unusual behavioural pattern detected: Multi-dimensional feature vector deviates "
                f"from baseline distribution (Isolation Forest score: {anomaly_score:.2f}, "
                f"raw metric: {raw_score:.3f})."
            )
        else:
            evidence = (
                f"Standard behavioural pattern observed: Feature vector conforms to normal "
                f"operational parameters (Isolation Forest score: {anomaly_score:.2f})."
            )

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            raw_score=raw_score,
            model_version=metadata.get("model_version", MODEL_VERSION),
            feature_version=metadata.get("feature_version", FEATURE_VERSION),
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_metadata={
                "hyperparameters": metadata.get("hyperparameters", {}),
                "trained_at": metadata.get("trained_at", ""),
                "training_samples": metadata.get("training_samples", 0),
                "feature_count": len(ANOMALY_FEATURE_KEYS)
            },
            evidence=evidence
        )
