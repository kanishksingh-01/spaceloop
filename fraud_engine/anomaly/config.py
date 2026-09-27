"""
SpaceLoop Anomaly Detection Layer - Configuration
Specifies feature vector schema, hyperparameters, model artifact paths, and versions.
"""
import os

# Base directory for persisted model artifacts
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(BASE_DIR, "artifacts")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_FILE_PATH = os.path.join(MODELS_DIR, "isolation_forest_v1.joblib")

# Versions
MODEL_VERSION = "iforest-v1.0.0"
FEATURE_VERSION = "feat-v1.0.0"

# Canonical feature keys selected for Isolation Forest model input
ANOMALY_FEATURE_KEYS = [
    "bookings_count_24h",               # booking frequency
    "payment_failure_rate_24h",          # payment failure rate
    "cancellations_count_24h",           # cancellation frequency
    "cancellation_ratio_7d",             # cancellation ratio
    "listing_creation_velocity_24h",     # listing creation velocity
    "account_age_hours",                 # account age
    "device_changes_count_30d",          # device changes
    "location_changes_count_30d",        # location changes
    "refund_requested_count_30d",        # refund frequency
    "booking_amount_zscore_vs_category", # booking amount deviation
    "network_shared_device_degree",      # network behavior (shared devices)
    "network_connected_accounts_count"   # network behavior (graph density)
]

# Isolation Forest Hyperparameters
IFOREST_PARAMS = {
    "n_estimators": 100,
    "contamination": 0.05,
    "max_samples": "auto",
    "random_state": 42,
    "n_jobs": -1
}

# Score Calibration Constant for Sigmoid Normalization
# sigmoid(k * -decision_function): maps decision boundary 0.0 to 0.50
SIGMOID_K = 4.0
