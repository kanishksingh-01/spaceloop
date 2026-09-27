"""
SpaceLoop Fraud & Trust Engine Foundation Package
Modular hybrid fraud prevention and risk evaluation service.
"""

from fraud_engine.schemas import (
    FraudEventType,
    FraudEventInput,
    ScoreRequest,
    FraudScoreResponse,
    EventIngestResponse,
    AlertResponse,
    HealthResponse,
)
from fraud_engine.service import FraudService
from fraud_engine.features import FeatureExtractor
from fraud_engine.rules import RuleEngine
from fraud_engine.risk import RiskEngine
from fraud_engine.app import app

__all__ = [
    "FraudEventType",
    "FraudEventInput",
    "ScoreRequest",
    "FraudScoreResponse",
    "EventIngestResponse",
    "AlertResponse",
    "HealthResponse",
    "FraudService",
    "FeatureExtractor",
    "RuleEngine",
    "RiskEngine",
    "app",
]
