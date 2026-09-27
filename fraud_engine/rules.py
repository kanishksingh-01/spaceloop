"""
SpaceLoop Fraud Engine Rule Engine Layer
Deterministic, explainable rule evaluation gates against extracted feature vectors.
"""
from typing import List, Dict, Any
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudEventInput, FraudEventType
from fraud_engine.config import FraudEngineConfig


class RuleEngine:
    """
    Evaluates deterministic business integrity rules against an extracted feature vector.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        triggered_rules: List[RuleResult] = []

        # 1. Critical Rule: Self-Transaction Attempt
        if features.get("is_self_transaction"):
            triggered_rules.append(RuleResult(
                code="RULE_SELF_TRANSACTION",
                name="Self-Booking or Self-Transaction",
                category="coordinated_activity",
                severity=FraudSeverity.CRITICAL,
                weight=0.95,
                triggered=True,
                evidence="Seeker and space owner have the exact same authenticated user identifier."
            ))

        # 2. Critical Rule: Multi-Account Shared Device
        dev_overlap = features.get("device_user_overlap_count", 1)
        if dev_overlap >= 2:
            triggered_rules.append(RuleResult(
                code="RULE_SHARED_DEVICE_MULTI_ACCOUNT",
                name="Shared Hardware Device Collusion",
                category="coordinated_activity",
                severity=FraudSeverity.CRITICAL if dev_overlap >= 3 else FraudSeverity.HIGH,
                weight=0.85 if dev_overlap >= 3 else 0.70,
                triggered=True,
                evidence=f"Hardware fingerprint is shared across {dev_overlap} distinct user accounts."
            ))

        # 3. High Rule: Disposable / Burner Email
        if features.get("email_is_disposable"):
            triggered_rules.append(RuleResult(
                code="RULE_DISPOSABLE_EMAIL",
                name="Disposable Burner Email Address",
                category="identity_deception",
                severity=FraudSeverity.HIGH,
                weight=0.70,
                triggered=True,
                evidence=f"Account email domain '{features.get('email_domain')}' matches disposable email provider."
            ))

        # 4. High Rule: Account Creation Velocity Burst
        ip_velocity = features.get("ip_creation_velocity_1h", 0)
        if ip_velocity >= FraudEngineConfig.VELOCITY_CREATION_MAX_COUNT:
            triggered_rules.append(RuleResult(
                code="RULE_ACCOUNT_CREATION_BURST",
                name="Account Creation IP Velocity Burst",
                category="identity_deception",
                severity=FraudSeverity.HIGH,
                weight=0.65,
                triggered=True,
                evidence=f"{ip_velocity} account registrations observed from IP address within the last 1 hour."
            ))

        # 5. High Rule: Payment Failure Burst (Card/UPI Probing)
        fail_count = features.get("failed_payment_count_15m", 0)
        if fail_count >= FraudEngineConfig.PAYMENT_FAILURE_MAX_COUNT or event.event_type == FraudEventType.PAYMENT_FAILED and fail_count >= 2:
            triggered_rules.append(RuleResult(
                code="RULE_PAYMENT_FAILURE_BURST",
                name="Payment Gateway Failure Burst",
                category="payment_abuse",
                severity=FraudSeverity.HIGH,
                weight=0.75,
                triggered=True,
                evidence=f"{fail_count} failed payment attempts recorded within rolling 15-minute window."
            ))

        # 6. High Rule: High Booking Frequency Velocity
        b_count = features.get("user_booking_count_15m", 0)
        if b_count >= FraudEngineConfig.VELOCITY_BOOKING_MAX_COUNT:
            triggered_rules.append(RuleResult(
                code="RULE_HIGH_BOOKING_VELOCITY",
                name="Excessive Booking Velocity",
                category="inventory_blocking",
                severity=FraudSeverity.HIGH,
                weight=0.60,
                triggered=True,
                evidence=f"User initiated {b_count} space reservations within the last 15 minutes."
            ))

        # 7. High Rule: Rapid Cancellation Churn Ratio
        cancel_ratio = features.get("user_cancellation_ratio_7d", 0.0)
        if cancel_ratio >= FraudEngineConfig.CANCELLATION_RATIO_THRESHOLD:
            triggered_rules.append(RuleResult(
                code="RULE_RAPID_CANCELLATION_CHURN",
                name="Abnormal Reservation Cancellation Churn",
                category="inventory_blocking",
                severity=FraudSeverity.HIGH,
                weight=0.65,
                triggered=True,
                evidence=f"User has cancelled {int(cancel_ratio * 100)}% of recent reservations in the last 7 days."
            ))

        # 8. High Rule: Extreme Price Anomaly (Modified Z-Score)
        z_score = abs(features.get("price_zscore", 0.0))
        if z_score >= FraudEngineConfig.PRICE_OUTLIER_ZSCORE_THRESHOLD:
            triggered_rules.append(RuleResult(
                code="RULE_PRICE_OUTLIER",
                name="Extreme Transaction / Price Outlier",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                weight=0.60,
                triggered=True,
                evidence=f"Transaction rate of ₹{features.get('transaction_amount')} has modified Z-score of {z_score}."
            ))

        # 9. Medium Rule: Geo-Distance Discrepancy (Impossible Travel)
        geo_dist = features.get("geo_distance_km", 0.0)
        if geo_dist >= FraudEngineConfig.GEO_DISCREPANCY_KM_THRESHOLD:
            triggered_rules.append(RuleResult(
                code="RULE_IMPOSSIBLE_GEO_VELOCITY",
                name="Abnormal Geographic Velocity",
                category="account_takeover",
                severity=FraudSeverity.MEDIUM,
                weight=0.50,
                triggered=True,
                evidence=f"Booking client location is {int(geo_dist)} km away from premise coordinates."
            ))

        # 10. High Rule: Sudden Profile Mutation
        if features.get("is_sudden_profile_mutation"):
            triggered_rules.append(RuleResult(
                code="RULE_SUDDEN_PROFILE_MUTATION",
                name="Sudden Critical Profile Mutation",
                category="account_takeover",
                severity=FraudSeverity.HIGH,
                weight=0.60,
                triggered=True,
                evidence="Payout account or primary credentials altered immediately prior to transaction execution."
            ))

        # 11. Medium Rule: Unverified Host Luxury Rate
        if event.event_type in (FraudEventType.LISTING_CREATED, FraudEventType.LISTING_UPDATED):
            price = features.get("transaction_amount", 0.0)
            if price > 2500.0 and not features.get("is_host_verified"):
                triggered_rules.append(RuleResult(
                    code="RULE_UNVERIFIED_HOST_HIGH_RATE",
                    name="Unverified Host High-Rate Listing",
                    category="listing_integrity",
                    severity=FraudSeverity.MEDIUM,
                    weight=0.45,
                    triggered=True,
                    evidence=f"Host published premium rate of ₹{price}/hr without Discom electricity or DigiLocker verification."
                ))

        return triggered_rules
