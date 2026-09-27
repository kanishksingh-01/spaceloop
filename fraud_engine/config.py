"""
SpaceLoop Fraud Engine Configuration
Settings and thresholds for the foundation fraud engine layer.
"""
import os

class FraudEngineConfig:
    # Risk decision thresholds
    THRESHOLD_ALLOW = float(os.environ.get("FRAUD_THRESHOLD_ALLOW", "0.25"))
    THRESHOLD_REVIEW = float(os.environ.get("FRAUD_THRESHOLD_REVIEW", "0.45"))
    THRESHOLD_HOLD = float(os.environ.get("FRAUD_THRESHOLD_HOLD", "0.65"))
    THRESHOLD_BLOCK = float(os.environ.get("FRAUD_THRESHOLD_BLOCK", "0.85"))

    # Velocity window limits
    VELOCITY_CREATION_WINDOW_SECONDS = 3600  # 1 hour
    VELOCITY_CREATION_MAX_COUNT = 3

    VELOCITY_BOOKING_WINDOW_SECONDS = 900   # 15 minutes
    VELOCITY_BOOKING_MAX_COUNT = 3

    PAYMENT_FAILURE_WINDOW_SECONDS = 900    # 15 minutes
    PAYMENT_FAILURE_MAX_COUNT = 3

    CANCELLATION_RATIO_THRESHOLD = 0.50     # 50%
    PRICE_OUTLIER_ZSCORE_THRESHOLD = 3.0    # 3.0 Modified Z-score
    GEO_DISCREPANCY_KM_THRESHOLD = 1000.0   # 1,000 km
