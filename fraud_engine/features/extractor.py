"""
SpaceLoop Feature Extraction Layer - Master Orchestrator
Coordinates domain-specific feature extractors across Account, Booking, Listing, and Network domains.
"""
from typing import Any, Dict
from sqlalchemy.orm import Session

from fraud_engine.schemas import FraudEventInput
from fraud_engine.features.base import FeatureExtractionResult, FeatureTrace
from fraud_engine.features.account import AccountFeatureExtractor
from fraud_engine.features.booking import BookingFeatureExtractor
from fraud_engine.features.listing import ListingFeatureExtractor
from fraud_engine.features.network import NetworkFeatureExtractor


class FeatureExtractor:
    """
    Master feature orchestrator extracting high-dimensional, traceable risk vectors.
    """

    @classmethod
    def extract_traceable(cls, event: FraudEventInput, db: Session) -> FeatureExtractionResult:
        """
        Extracts all domain features along with complete provenance metadata traces.
        """
        result = FeatureExtractionResult()

        # Step 1: Account & Identity Features
        AccountFeatureExtractor.extract(event, db, result)

        # Step 2: Booking & Payment Features
        BookingFeatureExtractor.extract(event, db, result)

        # Step 3: Listing & Catalog Features
        ListingFeatureExtractor.extract(event, db, result)

        # Step 4: Network & Graph Relationship Features
        NetworkFeatureExtractor.extract(event, db, result)

        # Step 5: Global Rolling Event Velocity
        user_events_15m = result.get_value("user_booking_count_15m", 0) + result.get_value("failed_payment_count_15m", 0)
        result.add(FeatureTrace(
            name="user_event_count_15m",
            value=user_events_15m,
            source="user_booking_count_15m + failed_payment_count_15m",
            category="account",
            description="Combined aggregate velocity of user state actions over rolling 15 minutes."
        ))

        return result

    @classmethod
    def extract(cls, event: FraudEventInput, db: Session) -> Dict[str, Any]:
        """
        Standard feature extraction returning a flat, JSON-serializable dictionary.
        Preserves 100% backward compatibility with downstream RuleEngine and RiskEngine.
        """
        res = cls.extract_traceable(event, db)
        return res.features
