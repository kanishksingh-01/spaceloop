"""
SpaceLoop Trust & Safety Package
Exports public interfaces for fraud prevention, device session tracking, and risk evaluation.
"""
from backend.modules.trust_safety.signals import SIGNALS, get_signal, ThreatCategory, SignalSeverity
from backend.modules.trust_safety.engine import (
    TrustSafetyEngine,
    record_device_session,
    generate_explainable_narrative
)
from backend.modules.trust_safety.graph import build_marketplace_graph, MarketplaceGraph
from backend.modules.trust_safety.rules import (
    evaluate_booking_rules,
    evaluate_listing_rules,
    evaluate_review_rules,
    evaluate_checkout_rules
)
from backend.modules.trust_safety.statistics import (
    compute_median,
    compute_mad,
    compute_modified_z_score,
    evaluate_velocity_burst,
    evaluate_cancellation_ratio
)
from backend.modules.trust_safety.content_similarity import (
    compute_semantic_content_similarity,
    check_listing_duplication
)

__all__ = [
    "TrustSafetyEngine",
    "SIGNALS",
    "get_signal",
    "ThreatCategory",
    "SignalSeverity",
    "record_device_session",
    "generate_explainable_narrative",
    "build_marketplace_graph",
    "MarketplaceGraph",
    "evaluate_booking_rules",
    "evaluate_listing_rules",
    "evaluate_review_rules",
    "evaluate_checkout_rules",
    "compute_median",
    "compute_mad",
    "compute_modified_z_score",
    "evaluate_velocity_burst",
    "evaluate_cancellation_ratio",
    "compute_semantic_content_similarity",
    "check_listing_duplication",
]
