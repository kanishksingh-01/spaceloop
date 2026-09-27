"""
SpaceLoop Fraud Engine - Anomaly Detection Package
Exposes scikit-learn Isolation Forest predictor, loader, trainer, and result schemas.
"""
from fraud_engine.anomaly.config import (
    ANOMALY_FEATURE_KEYS,
    MODEL_VERSION,
    FEATURE_VERSION,
    MODEL_FILE_PATH
)
from fraud_engine.anomaly.schemas import AnomalyResult
from fraud_engine.anomaly.training import AnomalyModelTrainer
from fraud_engine.anomaly.loader import AnomalyModelLoader
from fraud_engine.anomaly.predictor import AnomalyPredictor

__all__ = [
    "ANOMALY_FEATURE_KEYS",
    "MODEL_VERSION",
    "FEATURE_VERSION",
    "MODEL_FILE_PATH",
    "AnomalyResult",
    "AnomalyModelTrainer",
    "AnomalyModelLoader",
    "AnomalyPredictor"
]
