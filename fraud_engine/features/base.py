"""
SpaceLoop Feature Extraction Layer - Base Definitions & Traceability
Provides dataclasses and interfaces ensuring every feature has an explicit data origin.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from fraud_engine.schemas import FraudEventInput


@dataclass
class FeatureTrace:
    """
    Provenance and lineage tracking for a specific extracted feature.
    """
    name: str
    value: Any
    source: str          # e.g., 'db.users.created_at', 'db.fraud_events[window=1h]'
    category: str        # 'account', 'booking', 'listing', 'network'
    description: str     # Clear explanation of calculation method and parameters
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "source": self.source,
            "category": self.category,
            "description": self.description,
            "calculated_at": self.calculated_at.isoformat()
        }


@dataclass
class FeatureExtractionResult:
    """
    Container for extracted features and their full provenance traces.
    """
    features: Dict[str, Any] = field(default_factory=dict)
    traces: Dict[str, FeatureTrace] = field(default_factory=dict)

    def add(self, trace: FeatureTrace) -> None:
        self.features[trace.name] = trace.value
        self.traces[trace.name] = trace

    def get_value(self, name: str, default: Any = None) -> Any:
        return self.features.get(name, default)

    def get_trace(self, name: str) -> Optional[FeatureTrace]:
        return self.traces.get(name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "features": self.features,
            "traces": {k: v.to_dict() for k, v in self.traces.items()}
        }


class BaseFeatureExtractor:
    """
    Abstract interface for domain-specific feature extractors.
    """
    @classmethod
    def extract(cls, event: FraudEventInput, db: Session, result: FeatureExtractionResult) -> None:
        raise NotImplementedError("Subclasses must implement extract()")
