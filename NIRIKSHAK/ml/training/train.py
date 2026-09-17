import os
import json
import logging
from datetime import datetime, timezone
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ml_trainer")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest_v1.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")


def generate_synthetic_training_data(n_samples: int = 2500, random_state: int = 42) -> np.ndarray:
    """Generates synthetic baseline features representing normal enterprise activity."""
    rng = np.random.default_rng(random_state)

    # 1. Hour deviation: Mostly 0.0 during working hours, small tail (0 to 1.0 hr)
    hour_dev = np.abs(rng.normal(loc=0.0, scale=0.3, size=n_samples))
    hour_dev = np.clip(hour_dev, 0.0, 4.0)

    # 2. Volume Z-score: mostly normal distribution bounded between 0 and 1.8
    vol_z = np.abs(rng.normal(loc=0.5, scale=0.4, size=n_samples))
    vol_z = np.clip(vol_z, 0.0, 2.5)

    # 3. Resource sensitivity: weighted towards INTERNAL (25) and CONFIDENTIAL (50)
    sens_choices = [10.0, 25.0, 50.0, 75.0]
    sens_probs = [0.25, 0.45, 0.25, 0.05]
    sensitivity = rng.choice(sens_choices, size=n_samples, p=sens_probs)

    # 4. Device familiarity: 98% registered regular device (0.0), 2% unfamiliar (0.5)
    dev_choices = [0.0, 0.5]
    dev_probs = [0.98, 0.02]
    device_fam = rng.choice(dev_choices, size=n_samples, p=dev_probs)

    # 5. Department mismatch: 95% same department (0.0), 5% cross department (1.0)
    dept_choices = [0.0, 1.0]
    dept_probs = [0.95, 0.05]
    dept_mismatch = rng.choice(dept_choices, size=n_samples, p=dept_probs)

    # 6. Action severity: READ (10.0: 70%), WRITE (30.0: 25%), EXPORT (80.0: 5%)
    act_choices = [10.0, 30.0, 80.0]
    act_probs = [0.70, 0.25, 0.05]
    action_sev = rng.choice(act_choices, size=n_samples, p=act_probs)

    X = np.column_stack([hour_dev, vol_z, sensitivity, device_fam, dept_mismatch, action_sev])
    return X


def train_and_save_model() -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)
    logger.info("Generating synthetic baseline activity telemetry...")
    X_train = generate_synthetic_training_data(n_samples=3000, random_state=42)

    logger.info(f"Training IsolationForest on {X_train.shape[0]} samples with 6 features...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.04,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train)

    # Evaluation on normal vs anomalous test points
    normal_sample = np.array([[0.0, 0.2, 25.0, 0.0, 0.0, 10.0]])
    anomaly_sample = np.array([[6.5, 7.8, 90.0, 1.0, 1.0, 80.0]])

    norm_score = float(model.decision_function(normal_sample)[0])
    anom_score = float(model.decision_function(anomaly_sample)[0])

    logger.info(f"Model evaluation -> Normal decision score: {norm_score:.4f} (expected > 0.0)")
    logger.info(f"Model evaluation -> Anomaly decision score: {anom_score:.4f} (expected < -0.1)")

    # Save model artifact
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Saved Isolation Forest artifact to: {MODEL_PATH}")

    metadata = {
        "model_type": "IsolationForest",
        "version": "v1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": X_train.shape[0],
        "n_features": 6,
        "feature_names": [
            "hour_deviation",
            "volume_z_score",
            "resource_sensitivity",
            "device_familiarity",
            "department_mismatch",
            "action_severity",
        ],
        "hyperparameters": {
            "n_estimators": 100,
            "contamination": 0.04,
            "random_state": 42,
        },
        "evaluation_check": {
            "normal_decision_score": norm_score,
            "anomaly_decision_score": anom_score,
            "separable": bool(norm_score > 0 and anom_score < 0),
        },
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to: {METADATA_PATH}")


if __name__ == "__main__":
    train_and_save_model()
