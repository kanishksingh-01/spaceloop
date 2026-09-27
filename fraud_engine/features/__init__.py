"""
SpaceLoop Fraud Engine Feature Extraction Package
Exports master FeatureExtractor, domain-specific extractors, and similarity utilities.
"""
from fraud_engine.features.base import FeatureTrace, FeatureExtractionResult, BaseFeatureExtractor
from fraud_engine.features.similarity import (
    is_disposable_email,
    compute_haversine_distance_km,
    calculate_jaccard_similarity,
    calculate_ngram_similarity,
    calculate_modified_zscore,
    check_conflicting_city_coordinates
)
from fraud_engine.features.account import AccountFeatureExtractor
from fraud_engine.features.booking import BookingFeatureExtractor
from fraud_engine.features.listing import ListingFeatureExtractor
from fraud_engine.features.network import NetworkFeatureExtractor
from fraud_engine.features.extractor import FeatureExtractor

__all__ = [
    "FeatureTrace",
    "FeatureExtractionResult",
    "BaseFeatureExtractor",
    "FeatureExtractor",
    "AccountFeatureExtractor",
    "BookingFeatureExtractor",
    "ListingFeatureExtractor",
    "NetworkFeatureExtractor",
    "is_disposable_email",
    "compute_haversine_distance_km",
    "calculate_jaccard_similarity",
    "calculate_ngram_similarity",
    "calculate_modified_zscore",
    "check_conflicting_city_coordinates"
]
