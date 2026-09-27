"""
SpaceLoop Deterministic Rule Engine Unit Tests (Step 3)
Verifies all modular rule groups:
1. Account Rules
2. Booking Rules
3. Payment Rules
4. Listing Rules
Ensures explainable evidence, neutral non-defamatory language, and exact attribution.
"""
import unittest
from datetime import datetime

from fraud_engine.schemas import FraudEventInput, FraudEventType, FraudSeverity
from fraud_engine.rules import (
    RuleEngine,
    AccountRuleGroup,
    BookingRuleGroup,
    PaymentRuleGroup,
    ListingRuleGroup
)


class TestDeterministicRuleEngine(unittest.TestCase):

    def test_01_account_rules_shared_identifiers(self):
        """Validates detection of multi-account shared devices and shared legal IDs."""
        event = FraudEventInput(event_type=FraudEventType.LOGIN, user_id=101)

        # 1. Shared device fingerprint
        features_dev = {"accounts_sharing_device_count": 3}
        rules_dev = AccountRuleGroup.evaluate(features_dev, event)
        self.assertTrue(any(r.rule_id == "RULE_SHARED_DEVICE_MULTI_ACCOUNT" for r in rules_dev))
        r_dev = next(r for r in rules_dev if r.rule_id == "RULE_SHARED_DEVICE_MULTI_ACCOUNT")
        self.assertEqual(r_dev.severity, FraudSeverity.CRITICAL)
        self.assertEqual(r_dev.feature_responsible, "accounts_sharing_device_count")
        self.assertEqual(r_dev.value_responsible, 3)
        self.assertTrue(r_dev.evidence.startswith("Suspicious activity detected"))

        # 2. Shared phone / Aadhaar
        features_id = {"accounts_sharing_phone_count": 2, "accounts_sharing_aadhaar_count": 2}
        rules_id = AccountRuleGroup.evaluate(features_id, event)
        self.assertTrue(any(r.rule_id == "RULE_SHARED_IDENTITY_MULTI_ACCOUNT" for r in rules_id))
        r_id = next(r for r in rules_id if r.rule_id == "RULE_SHARED_IDENTITY_MULTI_ACCOUNT")
        self.assertEqual(r_id.severity, FraudSeverity.CRITICAL)
        self.assertTrue(r_id.evidence.startswith("Suspicious activity detected"))

    def test_02_account_rules_login_and_device_anomalies(self):
        """Validates abnormal login frequency, rapid device proliferation, and impossible travel."""
        event = FraudEventInput(event_type=FraudEventType.LOGIN, user_id=102)

        # Login burst
        features_login = {"login_frequency_1h": 12}
        rules_login = AccountRuleGroup.evaluate(features_login, event)
        self.assertTrue(any(r.rule_id == "RULE_ABNORMAL_LOGIN_FREQUENCY" for r in rules_login))

        # Device changes
        features_dev = {"device_changes_count_30d": 5}
        rules_dev = AccountRuleGroup.evaluate(features_dev, event)
        self.assertTrue(any(r.rule_id == "RULE_UNUSUAL_DEVICE_CHANGES" for r in rules_dev))

        # Impossible travel velocity
        features_geo = {"impossible_geo_velocity_kmh": 1200.0}
        rules_geo = AccountRuleGroup.evaluate(features_geo, event)
        self.assertTrue(any(r.rule_id == "RULE_IMPOSSIBLE_GEO_VELOCITY" for r in rules_geo))
        r_geo = next(r for r in rules_geo if r.rule_id == "RULE_IMPOSSIBLE_GEO_VELOCITY")
        self.assertIn("exceeding physical airline transit limits", r_geo.evidence)

    def test_03_account_rules_creation_patterns(self):
        """Validates account creation IP velocity burst and disposable email detection."""
        event = FraudEventInput(event_type=FraudEventType.ACCOUNT_CREATED, user_id=103)

        features = {
            "ip_creation_velocity_1h": 4,
            "email_is_disposable": True,
            "email_domain": "throwawaymail.com",
            "is_sudden_profile_mutation": True
        }
        rules = AccountRuleGroup.evaluate(features, event)
        rule_ids = {r.rule_id for r in rules}

        self.assertIn("RULE_ACCOUNT_CREATION_BURST", rule_ids)
        self.assertIn("RULE_DISPOSABLE_EMAIL", rule_ids)
        self.assertIn("RULE_SUDDEN_PROFILE_MUTATION", rule_ids)

    def test_04_booking_rules_frequency_and_cadence(self):
        """Validates unusually high booking frequency and rapid booking intervals."""
        event = FraudEventInput(event_type=FraudEventType.BOOKING_CREATED, user_id=201)

        features = {
            "user_booking_count_15m": 5,
            "bookings_count_1h": 8,
            "seconds_since_last_booking": 12.5
        }
        rules = BookingRuleGroup.evaluate(features, event)
        rule_ids = {r.rule_id for r in rules}

        self.assertIn("RULE_HIGH_BOOKING_VELOCITY", rule_ids)
        self.assertIn("RULE_RAPID_BOOKING_INTERVAL", rule_ids)

    def test_05_booking_rules_cancellation_churn_and_collusion(self):
        """Validates rapid booking/cancellation cycles and collusive self/wash bookings."""
        event = FraudEventInput(event_type=FraudEventType.BOOKING_CREATED, user_id=202)

        # Churn and cancellations
        features_churn = {
            "cancellation_ratio_7d": 0.75,
            "bookings_count_7d": 4,
            "cancellations_count_24h": 4
        }
        rules_churn = BookingRuleGroup.evaluate(features_churn, event)
        rule_ids_churn = {r.rule_id for r in rules_churn}
        self.assertIn("RULE_RAPID_CANCELLATION_CHURN", rule_ids_churn)
        self.assertIn("RULE_HIGH_CANCELLATION_FREQUENCY", rule_ids_churn)

        # Self-booking & Wash booking
        features_collusion = {
            "is_self_transaction": True,
            "network_shared_space_degree": 2
        }
        rules_collusion = BookingRuleGroup.evaluate(features_collusion, event)
        rule_ids_collusion = {r.rule_id for r in rules_collusion}
        self.assertIn("RULE_SELF_TRANSACTION", rule_ids_collusion)
        self.assertIn("RULE_RECIPROCAL_WASH_BOOKING", rule_ids_collusion)

    def test_06_payment_rules_failures_and_amounts(self):
        """Validates payment failure bursts, failure rate, and amount anomalies."""
        event = FraudEventInput(event_type=FraudEventType.PAYMENT_FAILED, user_id=301)

        features = {
            "failed_payment_count_15m": 3,
            "payment_failure_rate_24h": 0.67,
            "payment_attempts_24h": 6,
            "booking_amount_zscore_vs_category": 4.5,
            "transaction_amount": 25000.0
        }
        rules = PaymentRuleGroup.evaluate(features, event)
        rule_ids = {r.rule_id for r in rules}

        self.assertIn("RULE_PAYMENT_FAILURE_BURST", rule_ids)
        self.assertIn("RULE_HIGH_PAYMENT_FAILURE_RATE", rule_ids)
        self.assertIn("RULE_UNUSUAL_PAYMENT_AMOUNT", rule_ids)

    def test_07_payment_rules_micro_probing_and_refunds(self):
        """Validates sub-minimum probing amounts and excessive refund frequencies."""
        event = FraudEventInput(event_type=FraudEventType.REFUND_REQUESTED, user_id=302)

        # Micro-probing
        features_micro = {"transaction_amount": 1.50}
        rules_micro = PaymentRuleGroup.evaluate(features_micro, event)
        self.assertTrue(any(r.rule_id == "RULE_SUB_MINIMUM_TRANSACTION" for r in rules_micro))

        # Refund patterns
        features_refund = {
            "refund_requested_count_30d": 4,
            "refund_amount_total_30d": 15000.0
        }
        rules_refund = PaymentRuleGroup.evaluate(features_refund, event)
        rule_ids_refund = {r.rule_id for r in rules_refund}
        self.assertIn("RULE_FREQUENT_REFUND_REQUESTS", rule_ids_refund)
        self.assertIn("RULE_HIGH_REFUND_VOLUME", rule_ids_refund)

    def test_08_listing_rules_duplicate_and_copied_descriptions(self):
        """Validates duplicate listings, copied descriptions, and repeated hardware tokens."""
        event = FraudEventInput(event_type=FraudEventType.LISTING_CREATED, user_id=401)

        features = {
            "duplicate_title_count": 2,
            "duplicate_address_count": 2,
            "max_description_jaccard_similarity": 0.88,
            "repeated_room_qr_token": True,
            "repeated_discom_ca": True
        }
        rules = ListingRuleGroup.evaluate(features, event)
        rule_ids = {r.rule_id for r in rules}

        self.assertIn("RULE_DUPLICATE_LISTING", rule_ids)
        self.assertIn("RULE_COPIED_DESCRIPTION", rule_ids)
        self.assertIn("RULE_REPEATED_ROOM_QR_TOKEN", rule_ids)
        self.assertIn("RULE_REPEATED_DISCOM_CA", rule_ids)

    def test_09_listing_rules_pricing_conflicts_and_velocity(self):
        """Validates price anomalies, geo conflicts, physical impossibilities, and creation velocity."""
        event = FraudEventInput(event_type=FraudEventType.LISTING_CREATED, user_id=402)

        features = {
            "price_zscore_vs_category": 3.8,
            "price_hourly": 1800.0,
            "is_extreme_price_high": True,
            "conflicting_geo_city": True,
            "geo_city_discrepancy_km": 650.0,
            "impossible_sqft_capacity_ratio": True,
            "listing_creation_velocity_1h": 7,
            "unverified_high_value_listing": True
        }
        rules = ListingRuleGroup.evaluate(features, event)
        rule_ids = {r.rule_id for r in rules}

        self.assertIn("RULE_PRICE_OUTLIER", rule_ids)
        self.assertIn("RULE_EXTREME_HIGH_PRICE", rule_ids)
        self.assertIn("RULE_CONFLICTING_GEO_CITY", rule_ids)
        self.assertIn("RULE_IMPOSSIBLE_AREA_CAPACITY", rule_ids)
        self.assertIn("RULE_UNUSUAL_LISTING_VELOCITY", rule_ids)
        self.assertIn("RULE_UNVERIFIED_HOST_HIGH_RATE", rule_ids)

    def test_10_master_rule_engine_and_neutral_language_guarantee(self):
        """Validates master RuleEngine orchestration and strict adherence to neutral language."""
        event = FraudEventInput(event_type=FraudEventType.BOOKING_CREATED, user_id=501)

        features = {
            "space_id": 1,
            "is_self_transaction": True,
            "failed_payment_count_15m": 3,
            "email_is_disposable": True,
            "email_domain": "burnermail.io",
            "duplicate_title_count": 1,
            "duplicate_address_count": 1
        }
        all_rules = RuleEngine.evaluate(features, event)
        self.assertGreaterEqual(len(all_rules), 4)

        prohibited_words = ["fraudster", "criminal", "scammer", "thief", "guilty", "malicious user"]

        for rule in all_rules:
            # Check required fields
            self.assertTrue(rule.rule_id)
            self.assertTrue(rule.rule_name)
            self.assertTrue(rule.category)
            self.assertTrue(rule.severity)
            self.assertTrue(rule.risk_contribution > 0.0)
            self.assertTrue(rule.feature_responsible)
            self.assertIsNotNone(rule.value_responsible)
            self.assertTrue(rule.evidence)

            # Check neutral phrasing
            self.assertTrue(rule.evidence.startswith("Suspicious activity detected"))

            # Check no defamatory words
            lower_evidence = rule.evidence.lower()
            for bad_word in prohibited_words:
                self.assertNotIn(bad_word, lower_evidence, f"Prohibited word '{bad_word}' found in evidence!")


if __name__ == "__main__":
    unittest.main()
