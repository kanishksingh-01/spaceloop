import os
import sys
import logging
from typing import List, Tuple, Optional
import numpy as np
import joblib

# Ensure repository root and workspace are discoverable on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from app.schemas.risk import FactorDetail
from ml.features.extractor import FeatureExtractor, FEATURE_NAMES

logger = logging.getLogger(__name__)

possible_paths = [
    os.path.join(root_dir, "ml", "models", "isolation_forest_v1.joblib"),
    os.path.join(workspace_dir, "ml", "models", "isolation_forest_v1.joblib"),
    "/workspace/ml/models/isolation_forest_v1.joblib",
]
MODEL_PATH = next((p for p in possible_paths if os.path.exists(p)), possible_paths[0])


class AnomalyEngine:
    """Evaluates access events using a trained Isolation Forest model."""

    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            if os.path.exists(MODEL_PATH):
                try:
                    cls._model = joblib.load(MODEL_PATH)
                    logger.info("Loaded Isolation Forest model from disk.")
                except Exception as e:
                    logger.warning(f"Failed to load Isolation Forest artifact: {e}")
            else:
                logger.warning(f"Isolation Forest model not found at {MODEL_PATH}")
        return cls._model

    @classmethod
    def evaluate(
        cls,
        user_department: str,
        user_baseline: Optional[object],
        device_id: str,
        device_registered: bool,
        device_owner_user_id: Optional[str],
        user_id: str,
        resource_classification_level: str,
        resource_owner_dept: str,
        action: str,
        timestamp,
        data_volume: int,
        weight: float = 0.10,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []
        model = cls.get_model()

        # Extract 6D feature vector
        vec = FeatureExtractor.extract_vector(
            user_department=user_department,
            user_baseline=user_baseline,
            device_id=device_id,
            device_registered=device_registered,
            device_owner_user_id=device_owner_user_id,
            user_id=user_id,
            resource_classification_level=resource_classification_level,
            resource_owner_dept=resource_owner_dept,
            action=action,
            timestamp=timestamp,
            data_volume=data_volume,
        )

        if model is None:
            # Fallback heuristic if ML model artifact is missing
            sub = 15.0
            return sub, factors

        # Reshape for single sample prediction
        X = vec.reshape(1, -1)
        # decision_function: positive indicates inlier/normal; negative indicates outlier/anomaly
        decision_score = float(model.decision_function(X)[0])

        # Map decision score (-0.25 to +0.25) to [0, 100] subscore
        # score <= -0.15 => 85..95
        # score == 0.0 => 50
        # score >= +0.15 => 10..15
        if decision_score <= -0.15:
            normalized_sub = 85.0 + min(15.0, abs(decision_score + 0.15) * 80.0)
        elif decision_score <= -0.05:
            normalized_sub = 65.0 + ((-0.05 - decision_score) / 0.10) * 20.0
        elif decision_score <= 0.05:
            normalized_sub = 40.0 + ((0.05 - decision_score) / 0.10) * 25.0
        elif decision_score <= 0.15:
            normalized_sub = 20.0 + ((0.15 - decision_score) / 0.10) * 20.0
        else:
            normalized_sub = max(5.0, 20.0 - (decision_score - 0.15) * 50.0)

        normalized_sub = round(min(100.0, max(0.0, normalized_sub)), 1)

        # Highlight prominent feature deviations
        deviations = []
        if vec[0] > 0.5:
            deviations.append(f"time offset {vec[0]:.1f}h")
        if vec[1] > 2.0:
            deviations.append(f"volume z-score {vec[1]:.1f}")
        if vec[2] >= 75.0:
            deviations.append(f"high sensitivity {vec[2]:.0f}")
        if vec[3] > 0.0:
            deviations.append("unfamiliar endpoint")
        if vec[4] > 0.0:
            deviations.append("cross-department access")
        if vec[5] >= 80.0:
            deviations.append(f"high-impact action severity {vec[5]:.0f}")

        explanation_suffix = f" (Key deviations: {', '.join(deviations)})" if deviations else ""

        if normalized_sub >= 50.0:
            factor_name = "ML_ISOLATION_FOREST_ANOMALY"
            explanation = f"Unsupervised Isolation Forest flagged vector as an anomaly with decision score {decision_score:.3f}{explanation_suffix}."
        else:
            factor_name = "ML_BEHAVIORAL_ALIGNMENT"
            explanation = f"Isolation Forest confirms vector aligns with normal organizational cluster (decision score: +{decision_score:.3f})."

        factors.append(
            FactorDetail(
                factor=factor_name,
                subscore=normalized_sub,
                weight=weight,
                contribution=round(normalized_sub * weight, 2),
                explanation=explanation,
                details={
                    "decision_score": round(decision_score, 4),
                    "features": {name: round(float(val), 2) for name, val in zip(FEATURE_NAMES, vec)},
                    "deviations": deviations,
                },
            )
        )

        return normalized_sub, factors
