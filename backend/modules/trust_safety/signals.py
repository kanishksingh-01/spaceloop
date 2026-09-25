"""
SpaceLoop Trust & Safety Canonical Signal Taxonomy
Defines standardized risk signals, severity weights, and threat categories.
"""
from dataclasses import dataclass
from enum import Enum


class SignalSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(str, Enum):
    LISTING_INTEGRITY = "listing_integrity"
    COORDINATED_ACTIVITY = "coordinated_activity"
    INVENTORY_BLOCKING = "inventory_blocking"
    PAYMENT_ABUSE = "payment_abuse"
    REVIEW_MANIPULATION = "review_manipulation"
    ACCOUNT_TAKEOVER = "account_takeover"
    IDENTITY_DECEPTION = "identity_deception"


@dataclass(frozen=True)
class SignalDefinition:
    code: str
    name: str
    category: ThreatCategory
    severity: SignalSeverity
    base_weight: float
    description: str


# Registry of canonical risk signals
SIGNALS = {
    # 1. Listing Integrity & Possession
    "SELF_BOOKING": SignalDefinition(
        code="SELF_BOOKING",
        name="Self-Booking Attempt",
        category=ThreatCategory.COORDINATED_ACTIVITY,
        severity=SignalSeverity.CRITICAL,
        base_weight=0.90,
        description="Seeker and Host are the exact same user account or share authenticated identity."
    ),
    "DUPLICATE_LISTING_CONTENT": SignalDefinition(
        code="DUPLICATE_LISTING_CONTENT",
        name="Duplicate or Cloned Listing",
        category=ThreatCategory.LISTING_INTEGRITY,
        severity=SignalSeverity.HIGH,
        base_weight=0.75,
        description="Listing description or attributes match another active property with >= 88% similarity."
    ),
    "PRICE_ANOMALY_EXTREME": SignalDefinition(
        code="PRICE_ANOMALY_EXTREME",
        name="Extreme Price Outlier",
        category=ThreatCategory.LISTING_INTEGRITY,
        severity=SignalSeverity.HIGH,
        base_weight=0.60,
        description="Hourly rate is wildly disconnected (> 3.0 IQR/Z-score) from neighborhood and category norms."
    ),
    "RAPID_PRICE_MUTATION": SignalDefinition(
        code="RAPID_PRICE_MUTATION",
        name="Rapid Price Mutation",
        category=ThreatCategory.LISTING_INTEGRITY,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.50,
        description="Listing price changed significantly within minutes prior to booking commitment."
    ),
    "UNVERIFIED_HOST_HIGH_RATE": SignalDefinition(
        code="UNVERIFIED_HOST_HIGH_RATE",
        name="Unverified Host High-Rate Listing",
        category=ThreatCategory.LISTING_INTEGRITY,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.45,
        description="Host lacks Discom electricity meter and DigiLocker verification but posted premium rates."
    ),

    # 2. Coordinated Activity & Shared Infrastructure
    "SHARED_DEVICE_COLLUSION": SignalDefinition(
        code="SHARED_DEVICE_COLLUSION",
        name="Shared Device Collusion",
        category=ThreatCategory.COORDINATED_ACTIVITY,
        severity=SignalSeverity.HIGH,
        base_weight=0.80,
        description="Seeker and Host have transacted or authenticated using the exact same physical device."
    ),
    "SHARED_NETWORK_BURST": SignalDefinition(
        code="SHARED_NETWORK_BURST",
        name="Shared Network Burst",
        category=ThreatCategory.COORDINATED_ACTIVITY,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.45,
        description="Seeker and Host share identical IP address during transaction execution."
    ),
    "GRAPH_CIRCULAR_LOOP": SignalDefinition(
        code="GRAPH_CIRCULAR_LOOP",
        name="Circular Transaction Loop",
        category=ThreatCategory.COORDINATED_ACTIVITY,
        severity=SignalSeverity.CRITICAL,
        base_weight=0.85,
        description="Multi-account cycle detected (e.g. A booked B, B booked C, C booked A) to inflate trust metrics."
    ),
    "MULTI_ACCOUNT_LINKAGE": SignalDefinition(
        code="MULTI_ACCOUNT_LINKAGE",
        name="Multi-Account Linkage",
        category=ThreatCategory.COORDINATED_ACTIVITY,
        severity=SignalSeverity.HIGH,
        base_weight=0.70,
        description="Device or payment infrastructure linked across 3 or more distinct user accounts."
    ),

    # 3. Inventory Blocking & Churn
    "INVENTORY_BLOCKING": SignalDefinition(
        code="INVENTORY_BLOCKING",
        name="Inventory Blocking Abuse",
        category=ThreatCategory.INVENTORY_BLOCKING,
        severity=SignalSeverity.HIGH,
        base_weight=0.75,
        description="User repeatedly books and immediately cancels or lets reservations expire on competing spaces."
    ),
    "HIGH_CANCELLATION_RATIO": SignalDefinition(
        code="HIGH_CANCELLATION_RATIO",
        name="Abnormal Cancellation Velocity",
        category=ThreatCategory.INVENTORY_BLOCKING,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.45,
        description="User has cancelled over 50% of all recent reservations in the last 7 days."
    ),
    "REPEATED_SLOT_RESERVATION": SignalDefinition(
        code="REPEATED_SLOT_RESERVATION",
        name="Rapid Consecutive Reservation Burst",
        category=ThreatCategory.INVENTORY_BLOCKING,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.50,
        description="Excessive booking velocity (> 3 reservations in < 15 minutes) by a new account."
    ),

    # 4. Payment Abuse & Financial Evacuation
    "PAYMENT_FAILURE_BURST": SignalDefinition(
        code="PAYMENT_FAILURE_BURST",
        name="Payment Failure Burst",
        category=ThreatCategory.PAYMENT_ABUSE,
        severity=SignalSeverity.HIGH,
        base_weight=0.70,
        description="3 or more failed payment attempts in 15 minutes indicating automated card/UPI testing."
    ),
    "UNUSUAL_TRANSACTION_SPIKE": SignalDefinition(
        code="UNUSUAL_TRANSACTION_SPIKE",
        name="Unusual Transaction Spike",
        category=ThreatCategory.PAYMENT_ABUSE,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.45,
        description="Booking value deviates by > 4.0x from the user's historical median spend."
    ),
    "REFUND_DISPUTE_CLUSTER": SignalDefinition(
        code="REFUND_DISPUTE_CLUSTER",
        name="Refund & Dispute Cluster",
        category=ThreatCategory.PAYMENT_ABUSE,
        severity=SignalSeverity.HIGH,
        base_weight=0.65,
        description="Frequent micro-escrow dispute triggers and condition damage claims."
    ),

    # 5. Review Manipulation & Artificial Reputation
    "UNVERIFIED_STAY_REVIEW": SignalDefinition(
        code="UNVERIFIED_STAY_REVIEW",
        name="Unverified Stay Review",
        category=ThreatCategory.REVIEW_MANIPULATION,
        severity=SignalSeverity.HIGH,
        base_weight=0.80,
        description="Review submitted without a completed, checked-out physical booking."
    ),
    "ZERO_STAY_CHECKOUT": SignalDefinition(
        code="ZERO_STAY_CHECKOUT",
        name="Zero-Duration Stay Check-Out",
        category=ThreatCategory.REVIEW_MANIPULATION,
        severity=SignalSeverity.HIGH,
        base_weight=0.70,
        description="Check-in and check-out timestamps are < 60 seconds apart, indicating paper reservation."
    ),
    "REVIEW_SIMILARITY_RING": SignalDefinition(
        code="REVIEW_SIMILARITY_RING",
        name="Review Text Similarity Ring",
        category=ThreatCategory.REVIEW_MANIPULATION,
        severity=SignalSeverity.HIGH,
        base_weight=0.65,
        description="Review text is identical or near-identical to reviews on other listings."
    ),
    "RECIPROCAL_REVIEW_COLLUSION": SignalDefinition(
        code="RECIPROCAL_REVIEW_COLLUSION",
        name="Reciprocal Review Collusion",
        category=ThreatCategory.REVIEW_MANIPULATION,
        severity=SignalSeverity.HIGH,
        base_weight=0.75,
        description="Host and seeker leave 5-star reviews on each other without genuine commercial usage."
    ),

    # 6. Account Takeover & Rapid Behavioral Shifts
    "ACCOUNT_TAKEOVER_RISK": SignalDefinition(
        code="ACCOUNT_TAKEOVER_RISK",
        name="Account Takeover Indicator",
        category=ThreatCategory.ACCOUNT_TAKEOVER,
        severity=SignalSeverity.CRITICAL,
        base_weight=0.85,
        description="High-risk action (payout change or large booking) immediately following password/email change from a novel device."
    ),
    "RAPID_DEVICE_SHIFT": SignalDefinition(
        code="RAPID_DEVICE_SHIFT",
        name="Rapid Device & IP Shift",
        category=ThreatCategory.ACCOUNT_TAKEOVER,
        severity=SignalSeverity.MEDIUM,
        base_weight=0.40,
        description="Authentication from an unrecognized device/IP with no prior history on this account."
    ),
}


def get_signal(code: str) -> SignalDefinition | None:
    return SIGNALS.get(code)
