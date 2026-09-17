from datetime import datetime, timezone
import pytest
from app.models.user import User, Role
from app.models.device import Device
from app.models.resource import Resource, ResourceClassification
from app.models.baseline import BehaviorBaseline
from app.engines.risk_engine import RiskEngine
from app.engines.identity_engine import IdentityEngine
from app.engines.device_engine import DeviceEngine
from app.engines.sensitivity_engine import SensitivityEngine
from app.engines.behavior_engine import BehaviorEngine


@pytest.fixture
def mock_entities():
    """Provides a consistent set of synthetic entities for testing."""
    role = Role(id="role-1", name="USER", description="Employee")
    user = User(
        id="user-1",
        external_identifier="USER-001",
        username="user_001",
        hashed_password="hash",
        role_id=role.id,
        department="DEFENSE_RD",
        status="ACTIVE",
    )
    user_eng = User(
        id="user-2",
        external_identifier="USER-002",
        username="user_002",
        hashed_password="hash",
        role_id=role.id,
        department="ENGINEERING",
        status="ACTIVE",
    )
    device_trusted = Device(
        id="dev-1",
        device_identifier="DEV-101",
        owner_user_id=user.id,
        device_type="LAPTOP",
        registered=True,
        trust_level="TRUSTED",
    )
    device_unregistered = Device(
        id="dev-999",
        device_identifier="DEV-999",
        owner_user_id=None,
        device_type="UNKNOWN_WORKSTATION",
        registered=False,
        trust_level="LOW",
    )
    class_critical = ResourceClassification(
        id="class-crit",
        level="CRITICAL",
        base_sensitivity_score=90,
    )
    class_confidential = ResourceClassification(
        id="class-conf",
        level="CONFIDENTIAL",
        base_sensitivity_score=50,
    )
    repo_operational = Resource(
        id="repo-1",
        name="Operational Repository A",
        category="OPERATIONAL_DEFENSE",
        classification_id=class_critical.id,
        owner_department="DEFENSE_RD",
    )
    baseline = BehaviorBaseline(
        id="base-1",
        user_id=user.id,
        typical_hours={"start": 9, "end": 18},
        typical_devices=[device_trusted.id],
        typical_resources=[repo_operational.id],
        avg_daily_volume=15728640,  # 15 MB
        std_daily_volume=5242880,   # 5 MB
    )
    return {
        "user": user,
        "user_eng": user_eng,
        "device_trusted": device_trusted,
        "device_unregistered": device_unregistered,
        "class_critical": class_critical,
        "class_confidential": class_confidential,
        "repo_operational": repo_operational,
        "baseline": baseline,
    }


def test_scenario_normal_activity(mock_entities):
    """Scenario 1: Daytime access from registered device to departmental repo with MFA -> LOW."""
    m = mock_entities
    daytime = datetime(2026, 9, 9, 11, 30, tzinfo=timezone.utc)
    source_context = {"mfa_verified": True, "corporate_network": True, "client_ip": "10.0.1.5"}

    result = RiskEngine.evaluate_event(
        user=m["user"],
        device=m["device_trusted"],
        resource=m["repo_operational"],
        classification=m["class_critical"],
        baseline=m["baseline"],
        action="READ",
        timestamp=daytime,
        data_volume=10485760,  # 10 MB
        source_context=source_context,
    )

    # Identity=0 (MFA active), Device=0 (trusted registered), Sensitivity=90 (CRITICAL, same dept), Behavior=0
    # Composite = 0.25*0 + 0.25*0 + 0.25*90 + 0.25*0 = 22.5
    assert result.total_score == 22.5
    assert result.risk_level == "LOW"
    assert result.identity_score == 0.0
    assert result.device_score == 0.0
    assert result.sensitivity_score == 90.0
    assert result.behavior_score == 0.0


def test_scenario_off_hours_cross_department(mock_entities):
    """Scenario 2: 02:30 AM access from Engineering user to Defense repo without MFA -> HIGH/CRITICAL."""
    m = mock_entities
    night_time = datetime(2026, 9, 9, 2, 30, tzinfo=timezone.utc)
    source_context = {"mfa_verified": False, "corporate_network": True, "client_ip": "10.0.1.20"}

    result = RiskEngine.evaluate_event(
        user=m["user_eng"],  # Engineering user
        device=m["device_trusted"],
        resource=m["repo_operational"],  # Defense R&D repo (Cross-dept!)
        classification=m["class_critical"],
        baseline=m["baseline"],
        action="READ",
        timestamp=night_time,
        data_volume=12000000,
        source_context=source_context,
    )

    assert result.risk_level in ["HIGH", "CRITICAL"]
    assert result.total_score >= 61.0
    assert result.identity_score >= 70.0  # Missing MFA on sensitive
    assert result.sensitivity_score == 100.0  # 90 base + 25 cross dept capped at 100
    assert result.behavior_score >= 50.0  # Off-hours + unfamiliar resource

    # Verify factor breakdown presence
    factor_names = [f.factor for f in result.factors]
    assert "MISSING_MFA_SENSITIVE_ACCESS" in factor_names
    assert "CROSS_DEPARTMENT_RESOURCE_ACCESS" in factor_names
    assert "OFF_HOURS_ACCESS_DEVIATION" in factor_names


def test_scenario_bulk_exfiltration(mock_entities):
    """Scenario 3: Unregistered device, off-hours, 2.5 GB download (>3 sigma) -> CRITICAL."""
    m = mock_entities
    night_time = datetime(2026, 9, 9, 3, 15, tzinfo=timezone.utc)
    source_context = {"mfa_verified": False, "corporate_network": False, "client_ip": "203.0.113.88"}

    result = RiskEngine.evaluate_event(
        user=m["user_eng"],
        device=m["device_unregistered"],
        resource=m["repo_operational"],
        classification=m["class_critical"],
        baseline=m["baseline"],
        action="EXPORT",
        timestamp=night_time,
        data_volume=2684354560,  # 2.5 GB (far exceeds 15 MB baseline)
        source_context=source_context,
    )

    assert result.risk_level == "CRITICAL"
    assert result.total_score >= 81.0
    assert result.device_score == 100.0  # Unregistered + low trust
    assert result.behavior_score >= 90.0  # Off hours + volume > 3 sigma

    factor_names = [f.factor for f in result.factors]
    assert "UNREGISTERED_DEVICE" in factor_names
    assert "VOLUME_EXCEEDS_3_SIGMA" in factor_names
    assert "HIGH_IMPACT_ACTION_EXPORT" in factor_names


def test_score_bounds_and_contribution_sum(mock_entities):
    """Verifies that all sub-scores and composite scores are strictly within [0.0, 100.0]."""
    m = mock_entities
    result = RiskEngine.evaluate_event(
        user=m["user"],
        device=m["device_unregistered"],
        resource=m["repo_operational"],
        classification=m["class_critical"],
        baseline=m["baseline"],
        action="WRITE",
        timestamp=datetime(2026, 9, 9, 14, 0, tzinfo=timezone.utc),
        data_volume=50000000,
        source_context={"mfa_verified": True},
    )

    assert 0.0 <= result.total_score <= 100.0
    assert 0.0 <= result.identity_score <= 100.0
    assert 0.0 <= result.device_score <= 100.0
    assert 0.0 <= result.sensitivity_score <= 100.0
    assert 0.0 <= result.behavior_score <= 100.0

    # Ensure every factor has non-negative contribution
    for factor in result.factors:
        assert factor.contribution >= 0.0
        assert len(factor.explanation) > 0
