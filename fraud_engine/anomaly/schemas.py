"""
SpaceLoop Anomaly Detection Layer - Schemas & Data Structures
Defines normalized anomaly output, metadata storage, and neutral explainability payloads.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class AnomalyResult:
    """
    Structured outcome of an unsupervised Isolation Forest evaluation.
    Stores complete model metadata, versions, normalized score, and neutral explanation.
    """
    is_anomaly: bool
    anomaly_score: float                  # Normalized [0.0, 1.0], higher = more unusual
    raw_score: float                      # Scikit-learn decision_function signed distance
    model_version: str
    feature_version: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4),
            "raw_score": round(self.raw_score, 4),
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "timestamp": self.timestamp,
            "model_metadata": self.model_metadata,
            "evidence": self.evidence
        }
