"""
SpaceLoop Rule Engine - Account Rules
Evaluates multiple accounts sharing identifiers, abnormal login behavior,
unusual device changes, unusual location changes, and suspicious account creation patterns.
"""
from typing import Any, Dict, List
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudEventInput, FraudEventType
from fraud_engine.config import FraudEngineConfig
from fraud_engine.rules.base import BaseRuleGroup


class AccountRuleGroup(BaseRuleGroup):
    """
    Evaluates account integrity, identity reuse, device proliferation, and creation burst rules.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        triggered: List[RuleResult] = []

        # -------------------------------------------------------------
        # 1. Multiple Accounts Sharing Identifiers (Device & Hardware)
        # -------------------------------------------------------------
        dev_overlap = features.get("accounts_sharing_device_count") or features.get("device_user_overlap_count", 1)
        if dev_overlap >= 2:
            severity = FraudSeverity.CRITICAL if dev_overlap >= 3 else FraudSeverity.HIGH
            weight = 0.85 if dev_overlap >= 3 else 0.70
            triggered.append(cls.build_rule_result(
                rule_id="RULE_SHARED_DEVICE_MULTI_ACCOUNT",
                rule_name="Multiple Accounts Sharing Device Fingerprint",
                category="account_integrity",
                severity=severity,
                risk_contribution=weight,
                evidence=f"Suspicious activity detected: Hardware device fingerprint is associated with {dev_overlap} distinct user accounts.",
                feature_responsible="accounts_sharing_device_count",
                value_responsible=dev_overlap
            ))

        # Multiple Accounts Sharing Legal / Banking Identifiers (Phone, Aadhaar, UPI)
        shared_aadhaar = features.get("accounts_sharing_aadhaar_count", 1)
        shared_phone = features.get("accounts_sharing_phone_count", 1)
        shared_upi = features.get("accounts_sharing_upi_count", 1)
        max_shared_id = max(shared_aadhaar, shared_phone, shared_upi)

        if max_shared_id >= 2:
            detail = []
            if shared_aadhaar >= 2:
                detail.append(f"Aadhaar token hash shared across {shared_aadhaar} accounts")
            if shared_phone >= 2:
                detail.append(f"phone number shared across {shared_phone} accounts")
            if shared_upi >= 2:
                detail.append(f"UPI payment identifier shared across {shared_upi} accounts")

            triggered.append(cls.build_rule_result(
                rule_id="RULE_SHARED_IDENTITY_MULTI_ACCOUNT",
                rule_name="Multiple Accounts Sharing Primary Identifiers",
                category="account_integrity",
                severity=FraudSeverity.CRITICAL,
                risk_contribution=0.80,
                evidence=f"Suspicious activity detected: {'; '.join(detail)}.",
                feature_responsible="network_shared_identifiers_count",
                value_responsible=max_shared_id
            ))

        # -------------------------------------------------------------
        # 2. Abnormal Login Behavior (Frequency Burst)
        # -------------------------------------------------------------
        login_1h = features.get("login_frequency_1h", 0)
        if login_1h >= FraudEngineConfig.THRESHOLD_LOGIN_FREQUENCY_1H:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_ABNORMAL_LOGIN_FREQUENCY",
                rule_name="Abnormal Login Frequency Burst",
                category="account_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.60,
                evidence=f"Suspicious activity detected: {login_1h} authentication events recorded within rolling 1 hour.",
                feature_responsible="login_frequency_1h",
                value_responsible=login_1h
            ))

        # -------------------------------------------------------------
        # 3. Unusual Device Changes (Rapid Fingerprint Churn)
        # -------------------------------------------------------------
        dev_count_30d = features.get("device_changes_count_30d", 1)
        if dev_count_30d >= FraudEngineConfig.THRESHOLD_DEVICE_CHANGES_30D:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_UNUSUAL_DEVICE_CHANGES",
                rule_name="Unusual Device Proliferation",
                category="account_integrity",
                severity=FraudSeverity.MEDIUM,
                risk_contribution=0.50,
                evidence=f"Suspicious activity detected: User accessed platform from {dev_count_30d} distinct hardware fingerprints within 30 days.",
                feature_responsible="device_changes_count_30d",
                value_responsible=dev_count_30d
            ))

        # -------------------------------------------------------------
        # 4. Unusual Location Changes (Impossible Travel Speed)
        # -------------------------------------------------------------
        geo_velocity = features.get("impossible_geo_velocity_kmh", 0.0)
        geo_dist = features.get("geo_distance_km", 0.0)
        if geo_velocity >= FraudEngineConfig.THRESHOLD_IMPOSSIBLE_TRAVEL_KMH or geo_dist >= FraudEngineConfig.GEO_DISCREPANCY_KM_THRESHOLD:
            evidence_msg = (
                f"Suspicious activity detected: Consecutive geographic events indicate travel speed of {geo_velocity} km/h exceeding physical airline transit limits."
                if geo_velocity >= FraudEngineConfig.THRESHOLD_IMPOSSIBLE_TRAVEL_KMH
                else f"Suspicious activity detected: Physical distance of {geo_dist} km between client device and physical space location exceeds regional threshold."
            )
            triggered.append(cls.build_rule_result(
                rule_id="RULE_IMPOSSIBLE_GEO_VELOCITY",
                rule_name="Unusual Geographic Velocity (Impossible Travel)",
                category="account_integrity",
                severity=FraudSeverity.HIGH if geo_velocity >= 1000.0 else FraudSeverity.MEDIUM,
                risk_contribution=0.65 if geo_velocity >= 1000.0 else 0.50,
                evidence=evidence_msg,
                feature_responsible="impossible_geo_velocity_kmh" if geo_velocity >= FraudEngineConfig.THRESHOLD_IMPOSSIBLE_TRAVEL_KMH else "geo_distance_km",
                value_responsible=geo_velocity if geo_velocity >= FraudEngineConfig.THRESHOLD_IMPOSSIBLE_TRAVEL_KMH else geo_dist
            ))

        # -------------------------------------------------------------
        # 5. Suspicious Account Creation Patterns
        # -------------------------------------------------------------
        ip_velocity = features.get("ip_creation_velocity_1h") or features.get("account_creation_velocity_1h", 0)
        if ip_velocity >= FraudEngineConfig.VELOCITY_CREATION_MAX_COUNT:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_ACCOUNT_CREATION_BURST",
                rule_name="Account Creation IP Velocity Burst",
                category="account_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.65,
                evidence=f"Suspicious activity detected: {ip_velocity} account registrations observed from client IP address within rolling 1 hour.",
                feature_responsible="ip_creation_velocity_1h",
                value_responsible=ip_velocity
            ))

        if features.get("email_is_disposable"):
            domain = features.get("email_domain", "unknown")
            triggered.append(cls.build_rule_result(
                rule_id="RULE_DISPOSABLE_EMAIL",
                rule_name="Disposable Burner Email Address",
                category="account_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.70,
                evidence=f"Suspicious activity detected: User registration email domain '{domain}' matches disposable temporary mail service.",
                feature_responsible="email_is_disposable",
                value_responsible=domain
            ))

        if features.get("is_sudden_profile_mutation"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_SUDDEN_PROFILE_MUTATION",
                rule_name="Sudden Critical Profile Mutation",
                category="account_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.60,
                evidence="Suspicious activity detected: Payout account or primary credentials altered immediately prior to high-value transaction.",
                feature_responsible="is_sudden_profile_mutation",
                value_responsible=True
            ))

        return triggered
