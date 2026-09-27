"""
SpaceLoop Rule Engine Layer - Base Interfaces
Defines base class and standard creation helpers for deterministic rule evaluations.
Ensures objective, neutral evidence language without defamatory or speculative labeling.
"""
from typing import Any, Dict, List, Optional
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudEventInput


class BaseRuleGroup:
    """
    Abstract base class for modular rule groups.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        raise NotImplementedError("Subclasses must implement evaluate()")

    @staticmethod
    def build_rule_result(
        rule_id: str,
        rule_name: str,
        category: str,
        severity: FraudSeverity,
        risk_contribution: float,
        evidence: str,
        feature_responsible: str,
        value_responsible: Any
    ) -> RuleResult:
        """
        Creates a standardized RuleResult with neutral evidence language and complete attribution.
        """
        return RuleResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=severity,
            risk_contribution=risk_contribution,
            triggered=True,
            evidence=evidence,
            feature_responsible=feature_responsible,
            value_responsible=value_responsible,
            # Dual-compatibility aliases
            code=rule_id,
            name=rule_name,
            weight=risk_contribution
        )
