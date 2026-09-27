"""
SpaceLoop Rule Engine - Payment Rules
Evaluates repeated failed payments, unusual payment amounts, and suspicious refund patterns.
"""
from typing import Any, Dict, List
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudEventInput, FraudEventType
from fraud_engine.config import FraudEngineConfig
from fraud_engine.rules.base import BaseRuleGroup


class PaymentRuleGroup(BaseRuleGroup):
    """
    Evaluates payment gateway failures, card/UPI probing, amount anomalies, and refund abuse.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        triggered: List[RuleResult] = []

        # -------------------------------------------------------------
        # 1. Repeated Failed Payments (Probing / Gateway Abuse)
        # -------------------------------------------------------------
        fail_count_15m = features.get("failed_payment_count_15m", 0)
        is_pay_event = event.event_type == FraudEventType.PAYMENT_FAILED

        if fail_count_15m >= FraudEngineConfig.PAYMENT_FAILURE_MAX_COUNT or (is_pay_event and fail_count_15m >= 2):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_PAYMENT_FAILURE_BURST",
                rule_name="Payment Gateway Failure Burst",
                category="payment_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.75,
                evidence=f"Suspicious activity detected: {fail_count_15m} failed payment transactions recorded within rolling 15 minutes.",
                feature_responsible="failed_payment_count_15m",
                value_responsible=fail_count_15m
            ))

        fail_rate_24h = features.get("payment_failure_rate_24h", 0.0)
        attempts_24h = features.get("payment_attempts_24h", 0)
        if fail_rate_24h >= FraudEngineConfig.THRESHOLD_PAYMENT_FAILURE_RATE and attempts_24h >= 3:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_HIGH_PAYMENT_FAILURE_RATE",
                rule_name="Elevated Payment Decline Ratio",
                category="payment_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.65,
                evidence=f"Suspicious activity detected: {int(fail_rate_24h * 100)}% of payment transactions failed over 24 hours ({attempts_24h} total attempts).",
                feature_responsible="payment_failure_rate_24h",
                value_responsible=fail_rate_24h
            ))

        # -------------------------------------------------------------
        # 2. Unusual Payment Amounts
        # -------------------------------------------------------------
        z_score = abs(features.get("price_zscore") or features.get("booking_amount_zscore_vs_category", 0.0))
        amount = features.get("booking_amount") or features.get("transaction_amount", 0.0)

        if z_score >= FraudEngineConfig.PRICE_OUTLIER_ZSCORE_THRESHOLD and amount > 0:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_UNUSUAL_PAYMENT_AMOUNT",
                rule_name="Extreme Transaction Amount Anomaly",
                category="payment_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.60,
                evidence=f"Suspicious activity detected: Transaction rate of ₹{amount:.2f} deviates from category median with modified Z-score of {z_score:.2f}.",
                feature_responsible="booking_amount_zscore_vs_category",
                value_responsible=z_score
            ))

        if 0.0 < amount < 5.0:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_SUB_MINIMUM_TRANSACTION",
                rule_name="Sub-Minimum Micro-Probing Amount",
                category="payment_abuse",
                severity=FraudSeverity.MEDIUM,
                risk_contribution=0.50,
                evidence=f"Suspicious activity detected: Nominal transaction value of ₹{amount:.2f} is suspiciously below minimum viable reservation thresholds.",
                feature_responsible="transaction_amount",
                value_responsible=amount
            ))

        # -------------------------------------------------------------
        # 3. Suspicious Refund Patterns
        # -------------------------------------------------------------
        refund_req_count = features.get("refund_requested_count_30d", 0)
        refund_amt_30d = features.get("refund_amount_total_30d", 0.0)

        if refund_req_count >= FraudEngineConfig.THRESHOLD_REFUND_FREQUENCY_30D:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_FREQUENT_REFUND_REQUESTS",
                rule_name="Excessive Refund Request Frequency",
                category="payment_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.65,
                evidence=f"Suspicious activity detected: User submitted {refund_req_count} refund requests within rolling 30 days.",
                feature_responsible="refund_requested_count_30d",
                value_responsible=refund_req_count
            ))

        if refund_amt_30d >= 10000.0:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_HIGH_REFUND_VOLUME",
                rule_name="Elevated Cumulative Refund Volume",
                category="payment_abuse",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.70,
                evidence=f"Suspicious activity detected: Cumulative 30-day refund amount reached ₹{refund_amt_30d:.2f}.",
                feature_responsible="refund_amount_total_30d",
                value_responsible=refund_amt_30d
            ))

        return triggered
