"""
SpaceLoop Anomaly Detection Layer - Training Module
Trains scikit-learn Isolation Forest on baseline behavioural vectors and serializes using joblib.
"""
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from fraud_engine.anomaly.config import (
    ANOMALY_FEATURE_KEYS,
    IFOREST_PARAMS,
    MODEL_FILE_PATH,
    MODEL_VERSION,
    FEATURE_VERSION,
    MODELS_DIR
)


class AnomalyModelTrainer:
    """
    Handles fitting and persistence of the Isolation Forest unsupervised anomaly model.
    """

    @staticmethod
    def generate_baseline_data(n_samples: int = 1200) -> np.ndarray:
        """
        Generates realistic baseline distribution for the 12 SpaceLoop anomaly features:
        Represents typical platform usage (low velocity, low failure rates, occasional churn)
        with a calibrated 5% tail of anomalous behavioral bursts.
        """
        np.random.seed(42)

        # 1. bookings_count_24h (typical: 0-3, rare burst: 8-15)
        norm_b = np.random.poisson(lam=1.0, size=n_samples)
        # 2. payment_failure_rate_24h (typical: 0.0 - 0.10, rare: 0.6 - 1.0)
        norm_pay_fail = np.random.beta(a=0.5, b=10.0, size=n_samples)
        # 3. cancellations_count_24h (typical: 0, rare: 3-5)
        norm_canc = np.random.poisson(lam=0.2, size=n_samples)
        # 4. cancellation_ratio_7d (typical: 0.0 - 0.15)
        norm_canc_ratio = np.random.beta(a=0.5, b=5.0, size=n_samples)
        # 5. listing_creation_velocity_24h (typical: 0-1)
        norm_list_vel = np.random.poisson(lam=0.1, size=n_samples)
        # 6. account_age_hours (typical: 24 - 2000 hours)
        norm_age = np.random.exponential(scale=500.0, size=n_samples) + 24.0
        # 7. device_changes_count_30d (typical: 1-2)
        norm_dev = np.random.choice([1, 2, 3], size=n_samples, p=[0.80, 0.17, 0.03])
        # 8. location_changes_count_30d (typical: 1-2)
        norm_loc = np.random.choice([1, 2, 3], size=n_samples, p=[0.75, 0.20, 0.05])
        # 9. refund_requested_count_30d (typical: 0)
        norm_refund = np.random.poisson(lam=0.1, size=n_samples)
        # 10. booking_amount_zscore_vs_category (typical: ~0, Gaussian)
        norm_z = np.random.normal(loc=0.0, scale=1.0, size=n_samples)
        # 11. network_shared_device_degree (typical: 0-1)
        norm_net_dev = np.random.poisson(lam=0.05, size=n_samples)
        # 12. network_connected_accounts_count (typical: 1-4)
        norm_net_conn = np.random.poisson(lam=1.5, size=n_samples)

        X = np.column_stack([
            norm_b, norm_pay_fail, norm_canc, norm_canc_ratio,
            norm_list_vel, norm_age, norm_dev, norm_loc,
            norm_refund, norm_z, norm_net_dev, norm_net_conn
        ])

        # Inject 5% deliberate multidimensional extreme outliers
        n_outliers = int(n_samples * 0.05)
        outlier_indices = np.random.choice(n_samples, size=n_outliers, replace=False)

        X[outlier_indices, 0] = np.random.randint(10, 25, size=n_outliers)    # High bookings
        X[outlier_indices, 1] = np.random.uniform(0.7, 1.0, size=n_outliers)  # High payment failure
        X[outlier_indices, 2] = np.random.randint(4, 10, size=n_outliers)     # High cancellations
        X[outlier_indices, 3] = np.random.uniform(0.6, 1.0, size=n_outliers)  # High churn ratio
        X[outlier_indices, 6] = np.random.randint(4, 8, size=n_outliers)      # Many devices
        X[outlier_indices, 9] = np.random.uniform(4.0, 8.0, size=n_outliers)  # Extreme price Z-score
        X[outlier_indices, 10] = np.random.randint(3, 7, size=n_outliers)     # High device sharing

        return X

    @classmethod
    def train(
        cls,
        X: Optional[np.ndarray] = None,
        model_path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trains Isolation Forest and persists model and metadata via joblib.
        """
        save_path = model_path or MODEL_FILE_PATH
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        if X is None:
            X = cls.generate_baseline_data()

        hyperparams = params or IFOREST_PARAMS.copy()
        model = IsolationForest(**hyperparams)
        model.fit(X)

        metadata = {
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "feature_names": ANOMALY_FEATURE_KEYS,
            "hyperparameters": hyperparams,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "training_samples": len(X),
            "input_dimension": X.shape[1]
        }

        artifact = {
            "model": model,
            "metadata": metadata
        }

        joblib.dump(artifact, save_path, compress=3)
        return metadata
