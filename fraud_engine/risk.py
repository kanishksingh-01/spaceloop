"""
SpaceLoop Fraud Engine Risk Engine Layer
Calculates non-linear composite risk scores, statistical confidence, and automated policy actions.
"""
from typing import List, Dict, Any, Tuple
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudRiskLevel, FraudDecision
from fraud_engine.config import FraudEngineConfig


class RiskEngine:
    """
    Computes calibrated composite risk scores and policy actions using non-linear diminishing marginal risk accumulation:
    R = 1.0 - ∏ (1.0 - w_i)
    """

    @classmethod
    def evaluate(
        cls,
        triggered_rules: List[RuleResult],
        features: Dict[str, Any],
        anomaly_result: Optional[Any] = None
    ) -> Tuple[float, float, FraudRiskLevel, FraudDecision]:
        # If unsupervised anomaly model detected unusual pattern, integrate explainable signal
        if anomaly_result and getattr(anomaly_result, "is_anomaly", False):
            a_score = float(anomaly_result.anomaly_score)
            anomaly_contribution = round(min(0.40, max(0.15, 0.15 + (0.35 * (a_score - 0.50) / 0.50))), 2)
            rule_res = RuleResult(
                rule_id="RULE_UNSUPERVISED_ANOMALY_SIGNAL",
                rule_name="Unsupervised Statistical Behavioural Outlier",
                category="anomaly_detection",
                severity=FraudSeverity.MEDIUM if a_score < 0.80 else FraudSeverity.HIGH,
                risk_contribution=anomaly_contribution,
                triggered=True,
                evidence=anomaly_result.evidence,
                feature_responsible="isolation_forest_anomaly_score",
                value_responsible=round(a_score, 4),
                code="RULE_UNSUPERVISED_ANOMALY_SIGNAL",
                name="Unsupervised Statistical Behavioural Outlier",
                weight=anomaly_contribution
            )
            triggered_rules.append(rule_res)

        if not triggered_rules:
            return 0.05, 0.95, FraudRiskLevel.NORMAL, FraudDecision.ALLOW

        # 1. Independent probability accumulation
        combined_prob = 1.0
        has_critical = False
        has_high = False

        for r in triggered_rules:
            w = float(r.risk_contribution if r.risk_contribution else (r.weight or 0.0))
            combined_prob *= (1.0 - w)
            if r.severity == FraudSeverity.CRITICAL:
                has_critical = True
            elif r.severity == FraudSeverity.HIGH:
                has_high = True

        raw_score = 1.0 - combined_prob
        risk_score = round(min(1.0, max(0.0, raw_score)), 4)

        # 2. Statistical certainty scaling
        confidence = round(min(0.98, 0.65 + (0.08 * len(triggered_rules))), 4)

        # 3. Risk Tier assignment
        if risk_score >= FraudEngineConfig.THRESHOLD_BLOCK or has_critical:
            risk_level = FraudRiskLevel.HIGH_RISK
        elif risk_score >= FraudEngineConfig.THRESHOLD_HOLD or has_high:
            risk_level = FraudRiskLevel.SUSPICIOUS
        elif risk_score >= FraudEngineConfig.THRESHOLD_REVIEW:
            risk_level = FraudRiskLevel.UNUSUAL
        else:
            risk_level = FraudRiskLevel.NORMAL

        # 4. Action decision mapping
        critical_codes = ("RULE_SELF_TRANSACTION", "RULE_SHARED_DEVICE_MULTI_ACCOUNT", "RULE_DUPLICATE_LISTING")
        challenge_codes = ("RULE_IMPOSSIBLE_GEO_VELOCITY", "RULE_SUDDEN_PROFILE_MUTATION", "RULE_DISPOSABLE_EMAIL")

        if has_critical or any(r.rule_id in critical_codes or r.code in critical_codes for r in triggered_rules):
            decision = FraudDecision.BLOCK
        elif risk_score >= FraudEngineConfig.THRESHOLD_HOLD:
            decision = FraudDecision.HOLD
        elif any(r.rule_id in challenge_codes or r.code in challenge_codes for r in triggered_rules):
            decision = FraudDecision.CHALLENGE
        elif risk_score >= FraudEngineConfig.THRESHOLD_REVIEW:
            decision = FraudDecision.REVIEW
        else:
            decision = FraudDecision.ALLOW

        return risk_score, confidence, risk_level, decision
