from datetime import datetime, timezone, timedelta
import pytest
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource, ResourceClassification
from app.models.baseline import BehaviorBaseline
from app.models.event import AccessEvent
from ml.features.extractor import FeatureExtractor
from app.engines.anomaly_engine import AnomalyEngine
from app.engines.correlation_engine import CorrelationEngine


def test_feature_extractor_vector():
    baseline = BehaviorBaseline(
        typical_hours={"start": 9, "end": 18},
        avg_daily_volume=15728640,
        std_daily_volume=5242880,
        typical_devices=["dev-1"],
    )
    dt_day = datetime(2026, 9, 9, 14, 0, tzinfo=timezone.utc)
    vec = FeatureExtractor.extract_vector(
        user_department="ENGINEERING",
        user_baseline=baseline,
        device_id="dev-1",
        device_registered=True,
        device_owner_user_id="user-1",
        user_id="user-1",
        resource_classification_level="CONFIDENTIAL",
        resource_owner_dept="ENGINEERING",
        action="READ",
        timestamp=dt_day,
        data_volume=10485760,
    )

    assert len(vec) == 6
    assert vec[0] == 0.0  # hour_deviation
    assert vec[2] == 50.0 # CONFIDENTIAL sensitivity
    assert vec[3] == 0.0  # device_familiarity
    assert vec[4] == 0.0  # department_mismatch
    assert vec[5] == 10.0 # READ action severity


def test_anomaly_engine_evaluation():
    baseline = BehaviorBaseline(
        typical_hours={"start": 9, "end": 18},
        avg_daily_volume=15728640,
        std_daily_volume=5242880,
        typical_devices=["dev-1"],
    )

    # 1. Normal daytime reading
    dt_day = datetime(2026, 9, 9, 14, 0, tzinfo=timezone.utc)
    score_norm, factors_norm = AnomalyEngine.evaluate(
        user_department="ENGINEERING",
        user_baseline=baseline,
        device_id="dev-1",
        device_registered=True,
        device_owner_user_id="user-1",
        user_id="user-1",
        resource_classification_level="CONFIDENTIAL",
        resource_owner_dept="ENGINEERING",
        action="READ",
        timestamp=dt_day,
        data_volume=10485760,
        weight=0.10,
    )
    assert score_norm <= 30.0
    assert factors_norm[0].factor == "ML_BEHAVIORAL_ALIGNMENT"

    # 2. Extreme anomalous off-hours bulk export
    dt_night = datetime(2026, 9, 9, 2, 30, tzinfo=timezone.utc)
    score_anom, factors_anom = AnomalyEngine.evaluate(
        user_department="FINANCE",
        user_baseline=baseline,
        device_id="dev-unknown",
        device_registered=False,
        device_owner_user_id=None,
        user_id="user-1",
        resource_classification_level="CRITICAL",
        resource_owner_dept="DEFENSE_RD",
        action="EXPORT",
        timestamp=dt_night,
        data_volume=2147483648,  # 2 GB
        weight=0.10,
    )
    assert score_anom >= 70.0
    assert factors_anom[0].factor == "ML_ISOLATION_FOREST_ANOMALY"


def test_correlation_engine_kill_chain_detection():
    now = datetime(2026, 9, 9, 15, 0, tzinfo=timezone.utc)

    # 1. Isolated single event
    score_iso, mult_iso, factors_iso = CorrelationEngine.evaluate(
        current_action="READ",
        current_resource_id="repo-1",
        current_time=now,
        recent_events=[],
        weight=0.10,
    )
    assert score_iso == 0.0
    assert mult_iso == 1.0
    assert factors_iso[0].factor == "ISOLATED_EVENT"

    # 2. Multi-event chain: Rapid traversal across 3 distinct repositories followed by bulk export
    e1 = AccessEvent(
        id="e1", event_id="e1", timestamp=now - timedelta(minutes=10),
        user_id="u1", device_id="d1", resource_id="repo-a",
        action="READ", result="SUCCESS", data_volume=1000
    )
    e2 = AccessEvent(
        id="e2", event_id="e2", timestamp=now - timedelta(minutes=5),
        user_id="u1", device_id="d1", resource_id="repo-b",
        action="READ", result="SUCCESS", data_volume=2000
    )

    score_chain, mult_chain, factors_chain = CorrelationEngine.evaluate(
        current_action="EXPORT",
        current_resource_id="repo-c",
        current_time=now,
        recent_events=[e1, e2],
        weight=0.10,
    )

    assert score_chain >= 70.0
    assert mult_chain >= 1.25
    assert factors_chain[0].factor == "MULTI_EVENT_KILL_CHAIN_CORRELATION"
