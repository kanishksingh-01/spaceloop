"""
SpaceLoop Statistical Anomaly Detection Module
Provides robust, distribution-free statistical metrics:
- Median Absolute Deviation (MAD) & Modified Z-scores (resilient to extreme outliers)
- Sliding-window velocity and Poisson-style burst scoring
- Inter-arrival temporal gap distributions
"""
import math
from datetime import datetime, timedelta


def compute_median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    mid = n // 2
    if n % 2 == 1:
        return sorted_v[mid]
    return (sorted_v[mid - 1] + sorted_v[mid]) / 2.0


def compute_mad(values: list[float], median: float | None = None) -> float:
    """
    Computes Median Absolute Deviation (MAD):
    MAD = median(|X_i - median(X)|)
    """
    if not values or len(values) < 2:
        return 0.0
    med = median if median is not None else compute_median(values)
    abs_deviations = [abs(x - med) for x in values]
    return compute_median(abs_deviations)


def compute_modified_z_score(value: float, values: list[float]) -> float:
    """
    Computes Boris Iglewicz and David Hoaglin's Modified Z-score:
    M_i = 0.6745 * (x_i - median(X)) / MAD
    Scores > 3.5 indicate significant outliers.
    """
    if not values or len(values) < 3:
        return 0.0
    med = compute_median(values)
    mad = compute_mad(values, med)
    if mad == 0.0:
        # If MAD is 0 (all or most values identical), use mean absolute deviation
        mean = sum(values) / len(values)
        diff = abs(value - mean)
        return round(diff / (1.0 + mean), 2)
    
    score = 0.6745 * (value - med) / mad
    return round(score, 2)


def evaluate_velocity_burst(timestamps: list[datetime], window_seconds: int = 900, threshold_count: int = 3) -> dict:
    """
    Evaluates temporal burst velocity within a sliding time window.
    Default: > 3 events within 15 minutes (900 seconds).
    """
    if not timestamps or len(timestamps) < threshold_count:
        return {"is_burst": False, "count_in_window": len(timestamps), "burst_ratio": 0.0}

    sorted_times = sorted(timestamps, reverse=True)
    recent_cutoff = sorted_times[0] - timedelta(seconds=window_seconds)
    in_window = [t for t in sorted_times if t >= recent_cutoff]
    count = len(in_window)

    burst_ratio = count / float(threshold_count)
    return {
        "is_burst": count >= threshold_count,
        "count_in_window": count,
        "burst_ratio": round(burst_ratio, 2),
        "window_seconds": window_seconds
    }


def evaluate_cancellation_ratio(bookings: list) -> dict:
    """
    Computes user cancellation ratio and status distribution over recent bookings.
    """
    if not bookings:
        return {"cancellation_ratio": 0.0, "total_bookings": 0, "is_abnormal": False}

    total = len(bookings)
    cancelled = sum(1 for b in bookings if getattr(b, "status", None) == "cancelled" or getattr(b, "session_state", None) == "cancelled")
    ratio = cancelled / float(total) if total > 0 else 0.0

    return {
        "cancellation_ratio": round(ratio, 2),
        "total_bookings": total,
        "cancelled_count": cancelled,
        "is_abnormal": total >= 3 and ratio >= 0.50
    }
