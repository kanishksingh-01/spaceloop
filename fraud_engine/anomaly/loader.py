"""
SpaceLoop Anomaly Detection Layer - Model Loader
Handles loading, joblib deserialization, in-memory caching, and lazy provisioning of model artifacts.
"""
import os
import threading
from typing import Any, Dict, Optional, Tuple
import joblib
from sklearn.ensemble import IsolationForest

from fraud_engine.anomaly.config import MODEL_FILE_PATH
from fraud_engine.anomaly.training import AnomalyModelTrainer


class AnomalyModelLoader:
    """
    Thread-safe model loader ensuring cached, high-throughput model access.
    """
    _cache: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()

    @classmethod
    def load(cls, model_path: Optional[str] = None) -> Tuple[IsolationForest, Dict[str, Any]]:
        """
        Loads the Isolation Forest model artifact.
        If the file does not exist, automatically bootstraps and trains a fresh baseline model.
        """
        raw_path = model_path or MODEL_FILE_PATH
        resolved_path = os.path.abspath(raw_path)

        with cls._lock:
            if resolved_path in cls._cache:
                cached = cls._cache[resolved_path]
                return cached["model"], cached["metadata"]

            if not os.path.exists(resolved_path):
                # Lazy bootstrap if no model has been persisted yet
                AnomalyModelTrainer.train(model_path=resolved_path)

            artifact = joblib.load(resolved_path)
            if not isinstance(artifact, dict) or "model" not in artifact:
                raise ValueError(f"Corrupted anomaly model artifact at {resolved_path}")

            cls._cache[resolved_path] = artifact
            return artifact["model"], artifact.get("metadata", {})

    @classmethod
    def clear_cache(cls) -> None:
        """Clears in-memory cached model artifacts."""
        with cls._lock:
            cls._cache.clear()

