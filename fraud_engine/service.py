"""
SpaceLoop Fraud Service Layer
Coordinates the core architecture flow:
SPACELOOP EVENT → FRAUD SERVICE → FEATURE EXTRACTION → RULE ENGINE → RISK ENGINE
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from models import FraudEventRecord, FraudAlertRecord
from fraud_engine.schemas import (
    FraudEventInput,
    ScoreRequest,
    FraudScoreResponse,
    EventIngestResponse,
    AlertResponse,
    FraudDecision,
    FraudRiskLevel,
    FraudSeverity
)
from fraud_engine.features import FeatureExtractor
from fraud_engine.rules import RuleEngine
from fraud_engine.risk import RiskEngine
from fraud_engine.anomaly import AnomalyPredictor


class FraudService:
    """
    Central orchestrator for the SpaceLoop Fraud & Trust Engine foundation.
    """

    @classmethod
    def ingest_event(cls, event: FraudEventInput, db: Session) -> EventIngestResponse:
        """
        Executes full pipeline on an incoming SpaceLoop event:
        SPACELOOP EVENT → FRAUD SERVICE → FEATURE EXTRACTION → RULE ENGINE → RISK ENGINE
        """
        event_id = event.event_id or str(uuid.uuid4())
        event.event_id = event_id
        if not event.timestamp:
            event.timestamp = datetime.utcnow()

        # Step 1: Feature Extraction (Pandas & NumPy)
        features = FeatureExtractor.extract(event, db)

        # Step 1b: Unsupervised Anomaly Scoring (Isolation Forest)
        anomaly_result = AnomalyPredictor.predict(features)

        # Step 2: Rule Engine Evaluation
        triggered_rules = RuleEngine.evaluate(features, event)

        # Step 3: Risk Engine Evaluation
        risk_score, confidence, risk_level, decision = RiskEngine.evaluate(triggered_rules, features, anomaly_result)

        # Step 4: Persist Normalized Fraud Event with Anomaly Lineage
        payload_data = dict(event.payload or {})
        payload_data["anomaly"] = anomaly_result.to_dict()

        event_record = FraudEventRecord(
            event_id=event_id,
            event_type=event.event_type.value,
            user_id=event.user_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            ip_address=event.ip_address or "",
            device_fingerprint=event.device_fingerprint or "",
            user_agent=event.user_agent or "",
            payload_json=payload_data,
            risk_score=risk_score,
            decision=decision.value,
            created_at=event.timestamp
        )
        db.add(event_record)

        # Step 5: Generate Fraud Alert if anomalous or high risk
        alert_id = None
        should_alert = (
            risk_level in (FraudRiskLevel.SUSPICIOUS, FraudRiskLevel.HIGH_RISK) or
            decision in (FraudDecision.HOLD, FraudDecision.BLOCK, FraudDecision.REVIEW, FraudDecision.CHALLENGE) or
            any(r.severity in (FraudSeverity.HIGH, FraudSeverity.CRITICAL) for r in triggered_rules)
        )

        if should_alert:
            alert_id = str(uuid.uuid4())
            severity_str = "critical" if any(r.severity == FraudSeverity.CRITICAL for r in triggered_rules) else (
                "high" if risk_level == FraudRiskLevel.HIGH_RISK else "medium"
            )
            rules_dump = [r.model_dump() for r in triggered_rules]

            alert_record = FraudAlertRecord(
                alert_id=alert_id,
                event_id=event_id,
                user_id=event.user_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                severity=severity_str,
                risk_score=risk_score,
                decision=decision.value,
                status="open",
                triggered_rules_json=rules_dump,
                features_snapshot_json={k: (v if isinstance(v, (int, float, str, bool, list, dict)) else str(v)) for k, v in features.items()},
                notes=f"Auto-generated alert for {event.event_type.value}. Triggered rules: {len(triggered_rules)}.",
                created_at=datetime.utcnow()
            )
            db.add(alert_record)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[FRAUD_SERVICE_COMMIT_ERROR] {e}")
            alert_id = None

        return EventIngestResponse(
            status="ingested",
            event_id=event_id,
            event_type=event.event_type,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            alert_id=alert_id,
            created_at=event.timestamp.isoformat()
        )

    @classmethod
    def score_event(cls, request: ScoreRequest, db: Session) -> FraudScoreResponse:
        """
        Calculates prospective risk score on-demand without persisting an uncommitted event.
        """
        # Convert to ephemeral FraudEventInput
        synthetic_event = FraudEventInput(
            event_id=str(uuid.uuid4()),
            event_type=request.event_type,
            user_id=request.user_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            ip_address=request.ip_address,
            device_fingerprint=request.device_fingerprint,
            location=request.location,
            payload=request.payload
        )

        # Step 1: Feature Extraction
        features = FeatureExtractor.extract(synthetic_event, db)

        # Step 1b: Unsupervised Anomaly Scoring (Isolation Forest)
        anomaly_result = AnomalyPredictor.predict(features)

        # Step 2: Rule Engine Evaluation
        triggered_rules = RuleEngine.evaluate(features, synthetic_event)

        # Step 3: Risk Engine Evaluation
        risk_score, confidence, risk_level, decision = RiskEngine.evaluate(triggered_rules, features, anomaly_result)

        safe_features = {k: (v if isinstance(v, (int, float, str, bool, list, dict)) else str(v)) for k, v in features.items()}

        return FraudScoreResponse(
            risk_score=risk_score,
            confidence=confidence,
            risk_level=risk_level,
            decision=decision,
            triggered_rules=triggered_rules,
            features=safe_features,
            anomaly=anomaly_result.to_dict()
        )

    @classmethod
    def get_alerts(cls, db: Session, status: Optional[str] = None, severity: Optional[str] = None, limit: int = 50) -> List[AlertResponse]:
        query = db.query(FraudAlertRecord)
        if status and status != "all":
            query = query.filter(FraudAlertRecord.status == status)
        if severity and severity != "all":
            query = query.filter(FraudAlertRecord.severity == severity)

        records = query.order_by(FraudAlertRecord.created_at.desc()).limit(limit).all()

        return [
            AlertResponse(
                id=r.id,
                alert_id=r.alert_id,
                event_id=r.event_id,
                user_id=r.user_id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                severity=FraudSeverity(r.severity) if r.severity in FraudSeverity._value2member_map_ else FraudSeverity.MEDIUM,
                risk_score=r.risk_score,
                decision=FraudDecision(r.decision) if r.decision in FraudDecision._value2member_map_ else FraudDecision.REVIEW,
                status=r.status,
                triggered_rules=r.triggered_rules_json or [],
                features_snapshot=r.features_snapshot_json or {},
                notes=r.notes or "",
                created_at=r.created_at.isoformat() if r.created_at else "",
                resolved_at=r.resolved_at.isoformat() if r.resolved_at else None
            )
            for r in records
        ]

    @classmethod
    def get_alert_by_id(cls, db: Session, alert_identifier: str) -> Optional[AlertResponse]:
        query = db.query(FraudAlertRecord)
        if alert_identifier.isdigit():
            rec = query.filter(FraudAlertRecord.id == int(alert_identifier)).first()
        else:
            rec = query.filter(FraudAlertRecord.alert_id == alert_identifier).first()

        if not rec:
            return None

        return AlertResponse(
            id=rec.id,
            alert_id=rec.alert_id,
            event_id=rec.event_id,
            user_id=rec.user_id,
            entity_type=rec.entity_type,
            entity_id=rec.entity_id,
            severity=FraudSeverity(rec.severity) if rec.severity in FraudSeverity._value2member_map_ else FraudSeverity.MEDIUM,
            risk_score=rec.risk_score,
            decision=FraudDecision(rec.decision) if rec.decision in FraudDecision._value2member_map_ else FraudDecision.REVIEW,
            status=rec.status,
            triggered_rules=rec.triggered_rules_json or [],
            features_snapshot=rec.features_snapshot_json or {},
            notes=rec.notes or "",
            created_at=rec.created_at.isoformat() if rec.created_at else "",
            resolved_at=rec.resolved_at.isoformat() if rec.resolved_at else None
        )
