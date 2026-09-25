"""
SpaceLoop Deterministic Trust & Safety Rule Gates
Provides fast-path, transparent, deterministic abuse checks across:
- Self-booking and circular transactions
- Rapid reservation churn & inventory blocking
- Excessive cancellation ratios
- Unverified stay reviews & zero-duration stay checkouts
"""
from datetime import datetime, timedelta
from models import Booking, Space, Review, User, DeviceSession
from backend.modules.trust_safety.statistics import (
    evaluate_velocity_burst,
    evaluate_cancellation_ratio,
    compute_modified_z_score
)
from backend.modules.trust_safety.content_similarity import check_listing_duplication


def evaluate_booking_rules(
    seeker: User,
    space: Space,
    hours: float,
    total_price: float,
    device_fingerprint: str | None = None,
    ip_address: str | None = None,
    shared_infrastructure_data: dict | None = None
) -> list[dict]:
    """
    Evaluates deterministic rules on a proposed booking reservation.
    Returns a list of triggered signal dictionaries: {code, severity, weight, evidence}.
    """
    triggered = []

    # 1. Critical Rule: Self-Booking Attempt
    if seeker.id == space.owner_id:
        triggered.append({
            "code": "SELF_BOOKING",
            "evidence": f"Seeker '{seeker.name}' (ID: {seeker.id}) is the registered owner of Space '{space.title}' (ID: {space.id}).",
            "weight": 0.95
        })

    # 2. Shared Infrastructure Collusion Check
    has_shared_dev = False
    if shared_infrastructure_data and shared_infrastructure_data.get("has_shared_infrastructure"):
        dev_cnt = shared_infrastructure_data.get("shared_device_count", 0)
        ip_cnt = shared_infrastructure_data.get("shared_ip_count", 0)
        if dev_cnt > 0:
            has_shared_dev = True
            triggered.append({
                "code": "SHARED_DEVICE_COLLUSION",
                "evidence": f"Seeker and Host have authenticated using the same device fingerprint ({dev_cnt} shared device profile).",
                "weight": 0.80
            })
        elif ip_cnt > 0:
            triggered.append({
                "code": "SHARED_NETWORK_BURST",
                "evidence": f"Seeker and Host are transacting from the exact same client IP network address.",
                "weight": 0.45
            })

    # Direct match against Host's known devices/sessions
    if not has_shared_dev and device_fingerprint:
        host_device = DeviceSession.query.filter(
            DeviceSession.user_id == space.owner_id,
            DeviceSession.device_fingerprint == device_fingerprint
        ).first()
        if host_device:
            triggered.append({
                "code": "SHARED_DEVICE_COLLUSION",
                "evidence": f"Current seeker device fingerprint matches host's registered authentication device.",
                "weight": 0.80
            })

    # 3. Inventory Blocking & Rapid Reservation Velocity Check
    recent_seeker_bookings = Booking.query.filter(
        Booking.renter_id == seeker.id
    ).order_by(Booking.created_at.desc()).limit(15).all()

    if recent_seeker_bookings:
        # Check booking velocity (burst in last 15 min)
        b_times = [b.created_at for b in recent_seeker_bookings if b.created_at]
        burst_eval = evaluate_velocity_burst(b_times, window_seconds=900, threshold_count=3)
        if burst_eval["is_burst"]:
            triggered.append({
                "code": "REPEATED_SLOT_RESERVATION",
                "evidence": f"Seeker submitted {burst_eval['count_in_window']} bookings within the last 15 minutes.",
                "weight": 0.55
            })

        # Check cancellation churn ratio
        cancel_eval = evaluate_cancellation_ratio(recent_seeker_bookings)
        if cancel_eval["is_abnormal"]:
            triggered.append({
                "code": "HIGH_CANCELLATION_RATIO",
                "evidence": f"Seeker has cancelled {cancel_eval['cancelled_count']} of their last {cancel_eval['total_bookings']} bookings ({int(cancel_eval['cancellation_ratio'] * 100)}% cancellation rate).",
                "weight": 0.60
            })

    # 4. Same Listing Multiple Consecutive Bookings (Inventory Monopolization)
    consecutive_on_same = [b for b in recent_seeker_bookings[:5] if b.space_id == space.id and b.status in ("confirmed", "active")]
    if len(consecutive_on_same) >= 3:
        triggered.append({
            "code": "INVENTORY_BLOCKING",
            "evidence": f"Seeker currently holds {len(consecutive_on_same)} active reservations on this exact listing.",
            "weight": 0.70
        })

    # 5. Price Spike on Booking Total
    if total_price > 50000.0 and not seeker.is_student_verified and not seeker.is_aadhaar_verified:
        triggered.append({
            "code": "UNUSUAL_TRANSACTION_SPIKE",
            "evidence": f"High transaction value of ₹{total_price:,.0f} requested by unverified user.",
            "weight": 0.50
        })

    return triggered


def evaluate_listing_rules(space: Space, owner: User, existing_spaces: list) -> list[dict]:
    """
    Evaluates deterministic rules on a newly created or modified space listing.
    """
    triggered = []

    # 1. Duplicate Content Check
    dup_eval = check_listing_duplication(space, existing_spaces, threshold=0.88)
    if dup_eval["is_duplicate"]:
        triggered.append({
            "code": "DUPLICATE_LISTING_CONTENT",
            "evidence": f"Listing title/description is {int(dup_eval['similarity_score'] * 100)}% identical to existing Space #{dup_eval['matched_space_id']} ('{dup_eval['matched_space_title']}').",
            "weight": 0.75
        })

    # 2. Extreme Price Outlier Check
    all_prices = [s.price_hourly for s in existing_spaces if s.price_hourly and s.price_hourly > 0 and s.id != space.id]
    if len(all_prices) >= 5:
        z_score = compute_modified_z_score(space.price_hourly, all_prices)
        if abs(z_score) >= 3.5:
            triggered.append({
                "code": "PRICE_ANOMALY_EXTREME",
                "evidence": f"Hourly rate of ₹{space.price_hourly}/hr deviates significantly (Modified Z-score: {z_score}) from the platform median.",
                "weight": 0.60
            })

    # 3. Unverified Host Charging High Rates
    if space.price_hourly > 2500.0 and not (owner.is_host_verified or owner.is_aadhaar_verified):
        triggered.append({
            "code": "UNVERIFIED_HOST_HIGH_RATE",
            "evidence": f"Host is listing at ₹{space.price_hourly}/hr without Discom electricity or DigiLocker premise verification.",
            "weight": 0.45
        })

    return triggered


def evaluate_review_rules(user: User, space: Space, booking: Booking | None, comment: str) -> list[dict]:
    """
    Evaluates deterministic rules on a submitted review.
    """
    triggered = []

    # 1. Host Reviewing Own Property
    if user.id == space.owner_id:
        triggered.append({
            "code": "SELF_BOOKING",
            "evidence": f"Host '{user.name}' attempted to submit a review for their own listing '{space.title}'.",
            "weight": 0.95
        })

    # 2. Review Without Completed Booking
    if not booking or booking.space_id != space.id or booking.renter_id != user.id:
        triggered.append({
            "code": "UNVERIFIED_STAY_REVIEW",
            "evidence": "Review submitted without a valid completed reservation on this space.",
            "weight": 0.85
        })
    elif booking.status != "completed" and booking.session_state != "checked_out":
        triggered.append({
            "code": "UNVERIFIED_STAY_REVIEW",
            "evidence": f"Reservation #{booking.id} is in status '{booking.status}' (must be checked_out / completed).",
            "weight": 0.80
        })

    # 3. Zero-Duration Stay (Paper booking)
    if booking and booking.arrival_time and booking.departure_time:
        duration_sec = (booking.departure_time - booking.arrival_time).total_seconds()
        if 5.0 <= duration_sec < 60.0:
            triggered.append({
                "code": "ZERO_STAY_CHECKOUT",
                "evidence": f"Booking #{booking.id} duration was only {int(duration_sec)} seconds (paper check-in/out).",
                "weight": 0.70
            })

    # 4. Review text duplication check
    existing_reviews = Review.query.filter(Review.space_id == space.id).all()
    clean_comment = comment.strip().lower()
    for er in existing_reviews:
        if er.comment and er.comment.strip().lower() == clean_comment:
            triggered.append({
                "code": "REVIEW_SIMILARITY_RING",
                "evidence": "Review text is 100% identical to a previously posted review on this space.",
                "weight": 0.65
            })
            break

    return triggered


def evaluate_checkout_rules(booking: Booking) -> list[dict]:
    """
    Evaluates session telemetry at check-out for fraud / collateral damage abuse.
    """
    triggered = []

    if booking.arrival_time and booking.departure_time:
        duration_sec = (booking.departure_time - booking.arrival_time).total_seconds()
        if 5.0 <= duration_sec < 60.0:
            triggered.append({
                "code": "ZERO_STAY_CHECKOUT",
                "evidence": f"Reservation session lasted only {int(duration_sec)}s between check-in and check-out.",
                "weight": 0.70
            })

    # Discrepancy in room condition
    if getattr(booking, "condition_match_score", 100.0) < 50.0:
        triggered.append({
            "code": "REFUND_DISPUTE_CLUSTER",
            "evidence": f"Computer vision inspection detected significant premise condition delta (score: {booking.condition_match_score}%).",
            "weight": 0.60
        })

    return triggered
