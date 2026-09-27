"""
SpaceLoop Rule Engine - Master Orchestrator
Dispatches feature vectors and incoming events across all modular rule groups:
AccountRules, BookingRules, PaymentRules, and ListingRules.
"""
from typing import Any, Dict, List
from fraud_engine.schemas import RuleResult, FraudEventInput
from fraud_engine.rules.account_rules import AccountRuleGroup
from fraud_engine.rules.booking_rules import BookingRuleGroup
from fraud_engine.rules.payment_rules import PaymentRuleGroup
from fraud_engine.rules.listing_rules import ListingRuleGroup


class RuleEngine:
    """
    Master deterministic rule engine evaluating explainable integrity rules.
    Produces unambiguous evidence, attributed responsible features, and calibrated risk contributions.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        triggered_rules: List[RuleResult] = []

        # 1. Evaluate Account & Identity Rules
        triggered_rules.extend(AccountRuleGroup.evaluate(features, event))

        # 2. Evaluate Booking & Reservation Rules
        triggered_rules.extend(BookingRuleGroup.evaluate(features, event))

        # 3. Evaluate Payment & Transaction Rules
        triggered_rules.extend(PaymentRuleGroup.evaluate(features, event))

        # 4. Evaluate Listing & Catalog Rules
        triggered_rules.extend(ListingRuleGroup.evaluate(features, event))

        return triggered_rules
