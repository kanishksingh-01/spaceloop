from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource, ResourceClassification
from app.models.baseline import BehaviorBaseline
from app.schemas.risk import RiskResult, FactorDetail
from app.engines.identity_engine import IdentityEngine
from app.engines.device_engine import DeviceEngine
from app.engines.sensitivity_engine import SensitivityEngine
from app.engines.behavior_engine import BehaviorEngine
from app.engines.anomaly_engine import AnomalyEngine
from app.engines.correlation_engine import CorrelationEngine
from app.engines.explanation_engine import ExplanationEngine


class RiskEngine:
    """Coordinates risk evaluation across Identity, Device, Sensitivity, Behavior, ML Anomaly, and Correlation dimensions."""

    @staticmethod
    def evaluate_event(
        user: User,
        device: Device,
        resource: Resource,
        classification: ResourceClassification,
        baseline: BehaviorBaseline | None,
        action: str,
        timestamp: datetime,
        data_volume: int,
        source_context: dict,
        custom_weights: Optional[Dict[str, float]] = None,
        custom_thresholds: Optional[Dict[str, float]] = None,
        recent_events: Optional[List[Any]] = None,
        enable_ml: bool = False,
    ) -> RiskResult:
        if custom_weights:
            w_identity = custom_weights.get("WEIGHT_IDENTITY", 0.20)
            w_device = custom_weights.get("WEIGHT_DEVICE", 0.20)
            w_sensitivity = custom_weights.get("WEIGHT_SENSITIVITY", 0.20)
            w_behavior = custom_weights.get("WEIGHT_BEHAVIOR", 0.20)
            w_anomaly = custom_weights.get("WEIGHT_ANOMALY", 0.10)
            w_correlation = custom_weights.get("WEIGHT_CORRELATION", 0.10)
            use_ml = (w_anomaly > 0.0 or w_correlation > 0.0)
        elif enable_ml:
            w_identity = 0.20
            w_device = 0.20
            w_sensitivity = 0.20
            w_behavior = 0.20
            w_anomaly = 0.10
            w_correlation = 0.10
            use_ml = True
        else:
            w_identity = settings.WEIGHT_IDENTITY
            w_device = settings.WEIGHT_DEVICE
            w_sensitivity = settings.WEIGHT_SENSITIVITY
            w_behavior = settings.WEIGHT_BEHAVIOR
            w_anomaly = 0.0
            w_correlation = 0.0
            use_ml = False

        all_factors: List[FactorDetail] = []

        # 1. Identity Signal
        identity_score, id_factors = IdentityEngine.evaluate(
            user=user,
            resource=resource,
            classification=classification,
            source_context=source_context,
            weight=w_identity,
        )
        all_factors.extend(id_factors)

        # 2. Device Trust Signal
        device_score, dev_factors = DeviceEngine.evaluate(
            user=user,
            device=device,
            source_context=source_context,
            weight=w_device,
        )
        all_factors.extend(dev_factors)

        # 3. Data Sensitivity Signal
        sensitivity_score, sens_factors = SensitivityEngine.evaluate(
            user=user,
            resource=resource,
            classification=classification,
            action=action,
            weight=w_sensitivity,
        )
        all_factors.extend(sens_factors)

        # 4. Behavioral Deviation Signal
        behavior_score, beh_factors = BehaviorEngine.evaluate(
            baseline=baseline,
            event_time=timestamp,
            data_volume=data_volume,
            resource=resource,
            device=device,
            weight=w_behavior,
        )
        all_factors.extend(beh_factors)

        # 5. ML Isolation Forest Anomaly Signal (if enabled)
        anomaly_score = 0.0
        if use_ml and w_anomaly > 0.0:
            anomaly_score, anom_factors = AnomalyEngine.evaluate(
                user_department=user.department,
                user_baseline=baseline,
                device_id=device.id,
                device_registered=device.registered,
                device_owner_user_id=device.owner_user_id,
                user_id=user.id,
                resource_classification_level=classification.level,
                resource_owner_dept=resource.owner_department,
                action=action,
                timestamp=timestamp,
                data_volume=data_volume,
                weight=w_anomaly,
            )
            all_factors.extend(anom_factors)

        # 6. Multi-Event Correlation Signal (if enabled)
        correlation_score = 0.0
        multiplier = 1.0
        if use_ml and w_correlation > 0.0:
            correlation_score, multiplier, corr_factors = CorrelationEngine.evaluate(
                current_action=action,
                current_resource_id=resource.id,
                current_time=timestamp,
                recent_events=recent_events or [],
                weight=w_correlation,
            )
            all_factors.extend(corr_factors)

        # 7. Composite Risk Calculation
        raw_composite = (
            (identity_score * w_identity)
            + (device_score * w_device)
            + (sensitivity_score * w_sensitivity)
            + (behavior_score * w_behavior)
            + (anomaly_score * w_anomaly)
            + (correlation_score * w_correlation)
        )
        # Apply correlation multiplier if sequence detected
        amplified = raw_composite * multiplier
        total_score = round(min(100.0, max(0.0, amplified)), 1)

        # 8. Threshold Evaluation
        th_crit = custom_thresholds.get("THRESHOLD_CRITICAL", settings.RISK_THRESHOLD_CRITICAL) if custom_thresholds else settings.RISK_THRESHOLD_CRITICAL
        th_high = custom_thresholds.get("THRESHOLD_HIGH", settings.RISK_THRESHOLD_HIGH) if custom_thresholds else settings.RISK_THRESHOLD_HIGH
        th_mod = custom_thresholds.get("THRESHOLD_MODERATE", settings.RISK_THRESHOLD_MODERATE) if custom_thresholds else settings.RISK_THRESHOLD_MODERATE

        if total_score >= th_crit:
            risk_level = "CRITICAL"
        elif total_score >= th_high:
            risk_level = "HIGH"
        elif total_score >= th_mod:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # 9. Factor synthesis
        synthesized_factors = ExplanationEngine.synthesize(
            factors=all_factors,
            total_score=total_score,
            risk_level=risk_level,
        )

        return RiskResult(
            total_score=total_score,
            risk_level=risk_level,
            identity_score=round(identity_score, 1),
            device_score=round(device_score, 1),
            sensitivity_score=round(sensitivity_score, 1),
            behavior_score=round(behavior_score, 1),
            anomaly_score=round(anomaly_score, 1),
            correlation_score=round(correlation_score, 1),
            factors=synthesized_factors,
        )
