"""
SpaceLoop Anomaly Detection Layer Unit Tests (Step 4)
Verifies Isolation Forest unsupervised anomaly model training, joblib serialization,
loader caching, inference score normalization, metadata lineage, and neutral evidence phrasing.
"""
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
import numpy as np
from sklearn.ensemble import IsolationForest

from app import create_app
from models import db, User, FraudEventRecord, FraudAlertRecord
from fraud_engine.db import SessionLocal
from fraud_engine.schemas import FraudEventInput, FraudEventType, ScoreRequest
from fraud_engine.service import FraudService
from fraud_engine.anomaly import (
    ANOMALY_FEATURE_KEYS,
    MODEL_VERSION,
    FEATURE_VERSION,
    MODEL_FILE_PATH,
    AnomalyResult,
    AnomalyModelTrainer,
    AnomalyModelLoader,
    AnomalyPredictor
)


class TestIsolationForestAnomalyDetection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.flask_app = create_app()
        cls.flask_app.config["TESTING"] = True
        cls.temp_dir = tempfile.mkdtemp()
        cls.temp_model_path = os.path.join(cls.temp_dir, "test_iforest.joblib")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        AnomalyModelLoader.clear_cache()
        self.db = SessionLocal()
        self.db.query(FraudAlertRecord).delete()
        self.db.query(FraudEventRecord).delete()
        self.db.commit()

    def tearDown(self):
        self.db.query(FraudAlertRecord).delete()
        self.db.query(FraudEventRecord).delete()
        self.db.commit()
        self.db.close()

    def test_01_training_and_joblib_persistence(self):
        """Verifies training pipeline, metadata capture, and joblib file creation."""
        metadata = AnomalyModelTrainer.train(model_path=self.temp_model_path)

        self.assertTrue(os.path.exists(self.temp_model_path))
        self.assertGreater(os.path.getsize(self.temp_model_path), 1000)

        # Verify metadata dictionary
        self.assertEqual(metadata["model_version"], MODEL_VERSION)
        self.assertEqual(metadata["feature_version"], FEATURE_VERSION)
        self.assertEqual(metadata["feature_names"], ANOMALY_FEATURE_KEYS)
        self.assertGreaterEqual(metadata["training_samples"], 1000)
        self.assertEqual(metadata["input_dimension"], len(ANOMALY_FEATURE_KEYS))
        self.assertIn("trained_at", metadata)

    def test_02_model_loader_and_caching(self):
        """Verifies joblib loading, memory caching, and thread-safe singleton access."""
        model_1, meta_1 = AnomalyModelLoader.load(model_path=self.temp_model_path)
        self.assertIsInstance(model_1, IsolationForest)
        self.assertEqual(meta_1["model_version"], MODEL_VERSION)

        # Second load should return cached object
        model_2, meta_2 = AnomalyModelLoader.load(model_path=self.temp_model_path)
        self.assertIs(model_1, model_2)

    def test_03_prediction_and_score_calibration(self):
        """Verifies prediction on normal baseline vs extreme multi-dimensional anomaly."""
        # 1. Normal typical user behaviour
        normal_features = {
            "bookings_count_24h": 1,
            "payment_failure_rate_24h": 0.0,
            "cancellations_count_24h": 0,
            "cancellation_ratio_7d": 0.0,
            "listing_creation_velocity_24h": 0,
            "account_age_hours": 350.0,
            "device_changes_count_30d": 1,
            "location_changes_count_30d": 1,
            "refund_requested_count_30d": 0,
            "booking_amount_zscore_vs_category": 0.15,
            "network_shared_device_degree": 0,
            "network_connected_accounts_count": 2
        }

        res_norm = AnomalyPredictor.predict(normal_features, model_path=self.temp_model_path)
        self.assertIsInstance(res_norm, AnomalyResult)
        self.assertFalse(res_norm.is_anomaly)
        self.assertLess(res_norm.anomaly_score, 0.50)
        self.assertGreater(res_norm.raw_score, 0.0)

        # 2. Extreme multidimensional outlier behaviour
        outlier_features = {
            "bookings_count_24h": 22,             # Burst bookings
            "payment_failure_rate_24h": 0.85,     # Severe decline rate
            "cancellations_count_24h": 8,         # Massive cancellations
            "cancellation_ratio_7d": 0.88,
            "listing_creation_velocity_24h": 12,
            "account_age_hours": 0.5,             # Brand new account
            "device_changes_count_30d": 7,        # Device hopping
            "location_changes_count_30d": 5,
            "refund_requested_count_30d": 6,
            "booking_amount_zscore_vs_category": 6.8,
            "network_shared_device_degree": 5,
            "network_connected_accounts_count": 14
        }

        res_outlier = AnomalyPredictor.predict(outlier_features, model_path=self.temp_model_path)
        self.assertTrue(res_outlier.is_anomaly)
        self.assertGreaterEqual(res_outlier.anomaly_score, 0.50)
        self.assertLess(res_outlier.raw_score, 0.0)

        # Normalization boundary guarantees
        self.assertGreaterEqual(res_norm.anomaly_score, 0.0)
        self.assertLessEqual(res_norm.anomaly_score, 1.0)
        self.assertGreaterEqual(res_outlier.anomaly_score, 0.0)
        self.assertLessEqual(res_outlier.anomaly_score, 1.0)

    def test_04_metadata_and_version_lineage(self):
        """Verifies anomaly output stores versions, timestamp, and model metadata."""
        features = {"bookings_count_24h": 2}
        result = AnomalyPredictor.predict(features, model_path=self.temp_model_path)

        self.assertEqual(result.model_version, MODEL_VERSION)
        self.assertEqual(result.feature_version, FEATURE_VERSION)
        self.assertTrue(len(result.timestamp) > 0)
        self.assertIn("hyperparameters", result.model_metadata)
        self.assertEqual(result.model_metadata["feature_count"], len(ANOMALY_FEATURE_KEYS))

        # Test dictionary serialization
        dump = result.to_dict()
        self.assertIsInstance(dump, dict)
        self.assertEqual(dump["model_version"], MODEL_VERSION)
        self.assertEqual(dump["feature_version"], FEATURE_VERSION)
        self.assertIn("anomaly_score", dump)

    def test_05_neutral_non_defamatory_language(self):
        """Verifies evidence is strictly objective and avoids defamatory labeling."""
        outlier_features = {
            "bookings_count_24h": 25,
            "payment_failure_rate_24h": 0.9,
            "cancellations_count_24h": 10,
            "cancellation_ratio_7d": 0.9,
            "listing_creation_velocity_24h": 15,
            "account_age_hours": 0.2,
            "device_changes_count_30d": 8,
            "location_changes_count_30d": 6,
            "refund_requested_count_30d": 7,
            "booking_amount_zscore_vs_category": 7.0,
            "network_shared_device_degree": 6,
            "network_connected_accounts_count": 15
        }
        res_anomaly = AnomalyPredictor.predict(outlier_features, model_path=self.temp_model_path)
        self.assertTrue(res_anomaly.evidence.startswith("Unusual behavioural pattern detected"))

        normal_features = {"bookings_count_24h": 1, "account_age_hours": 200.0}
        res_normal = AnomalyPredictor.predict(normal_features, model_path=self.temp_model_path)
        self.assertTrue(res_normal.evidence.startswith("Standard behavioural pattern observed"))

        prohibited_words = ["fraudster", "criminal", "scammer", "thief", "guilty", "fraudulent", "cheater"]
        for res in [res_anomaly, res_normal]:
            lower_evidence = res.evidence.lower()
            for word in prohibited_words:
                self.assertNotIn(word, lower_evidence, f"Defamatory word '{word}' found in anomaly evidence!")


    def test_06_end_to_end_pipeline_integration(self):
        """Verifies FraudService integrates anomaly scoring in prospective score and event ingestion."""
        # 1. On-demand prospective score request
        req = ScoreRequest(
            event_type=FraudEventType.BOOKING_CREATED,
            user_id=1,
            entity_type="booking",
            payload={"amount": 100.0, "hours_booked": 2.0}
        )
        score_res = FraudService.score_event(req, self.db)
        self.assertIsNotNone(score_res.anomaly)
        self.assertIn("anomaly_score", score_res.anomaly)
        self.assertIn("model_version", score_res.anomaly)
        self.assertIn("evidence", score_res.anomaly)

        # 2. Ingest event and verify anomaly stored in audit payload
        event = FraudEventInput(
            event_type=FraudEventType.LOGIN,
            user_id=1,
            device_fingerprint="test_fp_anomaly_pipeline"
        )
        ingest_res = FraudService.ingest_event(event, self.db)
        self.assertEqual(ingest_res.status, "ingested")

        record = self.db.query(FraudEventRecord).filter(FraudEventRecord.event_id == ingest_res.event_id).first()
        self.assertIsNotNone(record)
        self.assertIn("anomaly", record.payload_json)
        self.assertIn("anomaly_score", record.payload_json["anomaly"])
        self.assertEqual(record.payload_json["anomaly"]["model_version"], MODEL_VERSION)


if __name__ == "__main__":
    unittest.main()
