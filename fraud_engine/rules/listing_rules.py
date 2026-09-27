"""
SpaceLoop Rule Engine - Listing Rules
Evaluates duplicate listings, copied descriptions, repeated listings across accounts,
suspicious pricing, conflicting listing info, and unusual listing creation velocity.
"""
from typing import Any, Dict, List
from fraud_engine.schemas import RuleResult, FraudSeverity, FraudEventInput, FraudEventType
from fraud_engine.config import FraudEngineConfig
from fraud_engine.rules.base import BaseRuleGroup


class ListingRuleGroup(BaseRuleGroup):
    """
    Evaluates marketplace catalog integrity, content duplication, price manipulation, and geographic conflicts.
    """

    @classmethod
    def evaluate(cls, features: Dict[str, Any], event: FraudEventInput) -> List[RuleResult]:
        triggered: List[RuleResult] = []

        is_listing_context = (
            features.get("space_id") is not None or
            event.entity_type in ("space", "listing") or
            event.event_type in (FraudEventType.LISTING_CREATED, FraudEventType.LISTING_UPDATED) or
            features.get("listing_creation_velocity_1h", 0) > 0
        )
        if not is_listing_context:
            return triggered

        # -------------------------------------------------------------
        # 1. Duplicate Listings & Repeated Address
        # -------------------------------------------------------------
        dup_titles = features.get("duplicate_title_count", 0)
        dup_addrs = features.get("duplicate_address_count", 0)

        if dup_titles >= 1 and dup_addrs >= 1:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_DUPLICATE_LISTING",
                rule_name="Exact Duplicate Space Listing",
                category="listing_integrity",
                severity=FraudSeverity.CRITICAL,
                risk_contribution=0.85,
                evidence="Suspicious activity detected: Title and physical street address match an existing active marketplace listing.",
                feature_responsible="duplicate_title_count",
                value_responsible={"titles": dup_titles, "addresses": dup_addrs}
            ))
        elif dup_addrs >= 1:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_DUPLICATE_ADDRESS",
                rule_name="Duplicated Physical Premise Address",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.70,
                evidence=f"Suspicious activity detected: Physical address is already claimed by {dup_addrs} other space listings.",
                feature_responsible="duplicate_address_count",
                value_responsible=dup_addrs
            ))

        # -------------------------------------------------------------
        # 2. Copied Descriptions (Text Plagiarism)
        # -------------------------------------------------------------
        jaccard_sim = features.get("max_description_jaccard_similarity", 0.0)
        ngram_sim = features.get("max_description_ngram_similarity", 0.0)
        max_sim = max(jaccard_sim, ngram_sim)

        if max_sim >= FraudEngineConfig.THRESHOLD_LISTING_SIMILARITY_JACCARD:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_COPIED_DESCRIPTION",
                rule_name="High-Similarity Copied Listing Description",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.65,
                evidence=f"Suspicious activity detected: Space description exhibits {int(max_sim * 100)}% text overlap with an existing listing.",
                feature_responsible="max_description_jaccard_similarity",
                value_responsible=max_sim
            ))

        # -------------------------------------------------------------
        # 3. Repeated Listings Across Accounts (Hardware Token / Discom CA)
        # -------------------------------------------------------------
        if features.get("repeated_room_qr_token"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_REPEATED_ROOM_QR_TOKEN",
                rule_name="Duplicate Door Access Pass Token",
                category="listing_integrity",
                severity=FraudSeverity.CRITICAL,
                risk_contribution=0.90,
                evidence="Suspicious activity detected: Cryptographic door pass QR token is already registered to a separate physical space.",
                feature_responsible="repeated_room_qr_token",
                value_responsible=True
            ))

        if features.get("repeated_discom_ca"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_REPEATED_DISCOM_CA",
                rule_name="Duplicate Electricity Utility Identifier",
                category="listing_integrity",
                severity=FraudSeverity.CRITICAL,
                risk_contribution=0.85,
                evidence="Suspicious activity detected: Discom electricity consumer account number is already bound to another space premise.",
                feature_responsible="repeated_discom_ca",
                value_responsible=True
            ))

        # -------------------------------------------------------------
        # 4. Suspicious Pricing
        # -------------------------------------------------------------
        cat_zscore = abs(features.get("price_zscore_vs_category", 0.0))
        price = features.get("price_hourly", 0.0)

        if cat_zscore >= FraudEngineConfig.PRICE_OUTLIER_ZSCORE_THRESHOLD and price > 0:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_PRICE_OUTLIER",
                rule_name="Category Price Distribution Outlier",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.60,
                evidence=f"Suspicious activity detected: Hourly tariff of ₹{price:.2f} deviates from category median with modified Z-score of {cat_zscore:.2f}.",
                feature_responsible="price_zscore_vs_category",
                value_responsible=cat_zscore
            ))

        if features.get("is_extreme_price_low"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_EXTREME_LOW_PRICE",
                rule_name="Suspiciously Below-Market Hourly Rate",
                category="listing_integrity",
                severity=FraudSeverity.MEDIUM,
                risk_contribution=0.50,
                evidence=f"Suspicious activity detected: Published hourly tariff of ₹{price:.2f} is significantly below legitimate operational thresholds.",
                feature_responsible="is_extreme_price_low",
                value_responsible=price
            ))

        if features.get("is_extreme_price_high"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_EXTREME_HIGH_PRICE",
                rule_name="Anomalously High Commercial Tariff",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.70,
                evidence=f"Suspicious activity detected: Published hourly tariff of ₹{price:.2f} significantly exceeds category commercial medians.",
                feature_responsible="is_extreme_price_high",
                value_responsible=price
            ))

        # Unverified host listing high-value space
        if features.get("unverified_high_value_listing") or (
            not features.get("is_host_verified") and features.get("transaction_amount", 0) > 1000
        ):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_UNVERIFIED_HOST_HIGH_RATE",
                rule_name="Unverified Host Elevated Rate Listing",
                category="listing_integrity",
                severity=FraudSeverity.MEDIUM,
                risk_contribution=0.55,
                evidence="Suspicious activity detected: Host has not completed Discom or Aadhaar KYC verification while listing high-value commercial rates.",
                feature_responsible="unverified_high_value_listing",
                value_responsible=True
            ))

        # -------------------------------------------------------------
        # 5. Conflicting Listing Information
        # -------------------------------------------------------------
        if features.get("conflicting_geo_city"):
            diff_km = features.get("geo_city_discrepancy_km", 0.0)
            triggered.append(cls.build_rule_result(
                rule_id="RULE_CONFLICTING_GEO_CITY",
                rule_name="Geographic Coordinate Discrepancy",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.75,
                evidence=f"Suspicious activity detected: Listing GPS coordinates deviate by {diff_km:.1f} km from claimed city centroid.",
                feature_responsible="conflicting_geo_city",
                value_responsible=diff_km
            ))

        if features.get("impossible_sqft_capacity_ratio"):
            triggered.append(cls.build_rule_result(
                rule_id="RULE_IMPOSSIBLE_AREA_CAPACITY",
                rule_name="Physical Area and Capacity Inconsistency",
                category="listing_integrity",
                severity=FraudSeverity.MEDIUM,
                risk_contribution=0.50,
                evidence="Suspicious activity detected: Floor area and maximum guest occupancy metrics represent a physical impossibility.",
                feature_responsible="impossible_sqft_capacity_ratio",
                value_responsible=True
            ))

        # -------------------------------------------------------------
        # 6. Unusual Listing Creation Velocity
        # -------------------------------------------------------------
        list_velocity = features.get("listing_creation_velocity_1h", 0)
        if list_velocity >= FraudEngineConfig.THRESHOLD_LISTING_CREATION_VELOCITY_1H:
            triggered.append(cls.build_rule_result(
                rule_id="RULE_UNUSUAL_LISTING_VELOCITY",
                rule_name="Rapid-Fire Listing Creation Burst",
                category="listing_integrity",
                severity=FraudSeverity.HIGH,
                risk_contribution=0.65,
                evidence=f"Suspicious activity detected: Host published {list_velocity} space listings within rolling 1 hour.",
                feature_responsible="listing_creation_velocity_1h",
                value_responsible=list_velocity
            ))

        return triggered
