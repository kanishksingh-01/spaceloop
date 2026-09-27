"""
SpaceLoop Rule Engine - Booking Rules
Evaluates unusually high booking frequency, rapid booking/cancellation cycles,
and abnormal booking patterns (self-transactions, rapid-fire reservations, wash bookings).
"""
from typing import Any, Dict, List
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudEventInput, FraudEventType
from fraud_engine.config import FraudEngineConfig
from fraud_engine.rules.base import BaseRuleGroup


class BookingRuleGroup(BaseRuleGroup):
    """
    Evaluates reservation velocity, cancellation churn, and collusive transaction patterns.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        triggered: List[RuleResult] = []

        # -------------------------------------------------------------
        # 1. Unusually High Booking Frequency
        # -------------------------------------------------------------
        b_count_15m = features.get("user_booking_count_15m", 0)
        b_count_1h = features.get("bookings_count_1h", 0)

        if b_count_15m >= FraudEngineConfig.VELOCITY_BOOKING_MAX_COUNT or b_count_1h >= 5:
            count = b_count_15m if b_count_15m >= FraudEngineConfig.VELOCITY_BOOKING_MAX_COUNT else b_count_1h
            window_desc = "15 minutes" if b_count_15m >= FraudEngineConfig.VELOCITY_BOOKING_MAX_COUNT else "1 hour"
            triggered.append(cls.build_rule_result(
                rule_id="RULE_HIGH_BOOKING_VELOCITY",
                rule_name="Unusually High Booking Frequency",
                category="booking_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.60,
                evidence=f"Suspicious activity detected: User initiated {count} space reservations within {window_desc}.",
                feature_responsible="user_booking_count_15m" if b_count_15m >= FraudEngineConfig.VELOCITY_BOOKING_MAX_COUNT else "bookings_count_1h",
                value_responsible=count
            ))

        # Rapid fire booking interval (< 30s)
        sec_since_last = features.get("seconds_since_last_booking", 999999.0)
        if sec_since_last < 30.0 and b_count_1h >= 2 and event.event_type == FraudEventType.BOOKING_CREATED:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_RAPID_BOOKING_INTERVAL",
                rule_name="Automated High-Frequency Booking Cadence",
                category="booking_abuse",
                severity=FraudSeverity.MEDIUM,
                risk_contribution=0.55,
                evidence=f"Suspicious activity detected: Consecutive booking submitted within {sec_since_last:.1f} seconds of preceding booking.",
                feature_responsible="seconds_since_last_booking",
                value_responsible=sec_since_last
            ))

        # -------------------------------------------------------------
        # 2. Rapid Booking / Cancellation Cycles
        # -------------------------------------------------------------
        cancel_ratio = features.get("user_cancellation_ratio_7d") or features.get("cancellation_ratio_7d", 0.0)
        cancels_24h = features.get("cancellations_count_24h", 0)
        total_7d = features.get("user_total_bookings_7d") or features.get("bookings_count_7d", 0)

        if cancel_ratio >= FraudEngineConfig.CANCELLATION_RATIO_THRESHOLD and total_7d >= 2:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_RAPID_CANCELLATION_CHURN",
                rule_name="Abnormal Booking-to-Cancellation Ratio",
                category="booking_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.65,
                evidence=f"Suspicious activity detected: User has cancelled {int(cancel_ratio * 100)}% of reservations over the last 7 days.",
                feature_responsible="cancellation_ratio_7d",
                value_responsible=cancel_ratio
            ))

        if cancels_24h >= 3:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_HIGH_CANCELLATION_FREQUENCY",
                rule_name="Elevated Cancellation Frequency in 24 Hours",
                category="booking_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.60,
                evidence=f"Suspicious activity detected: {cancels_24h} reservation cancellations executed by user within rolling 24 hours.",
                feature_responsible="cancellations_count_24h",
                value_responsible=cancels_24h
            ))

        # -------------------------------------------------------------
        # 3. Abnormal Booking Patterns
        # -------------------------------------------------------------
        # Self-transaction booking
        if features.get("is_self_transaction"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_SELF_TRANSACTION",
                rule_name="Self-Booking Transaction Collusion",
                category="booking_abuse",
                severity=FraudSeverity.CRITICAL,
                risk_contribution=0.95,
                evidence="Suspicious activity detected: Authenticated seeker and listing premise host share identical account identifiers.",
                feature_responsible="is_self_transaction",
                value_responsible=True
            ))

        # Mutual wash booking cycles
        mutual_loops = features.get("network_shared_space_degree", 0)
        if mutual_loops >= 1:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_RECIPROCAL_WASH_BOOKING",
                rule_name="Reciprocal Booking Loop Detected",
                category="booking_abuse",
                severity=FraudSeverity.CRITICAL,
                risk_contribution=0.85,
                evidence=f"Suspicious activity detected: Reciprocal circular booking loop observed across {mutual_loops} counterparty host-renter pairings.",
                feature_responsible="network_shared_space_degree",
                value_responsible=mutual_loops
            ))

        return triggered
