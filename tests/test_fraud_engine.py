"""
SpaceLoop Fraud & Trust Engine Foundation Tests
Validates the FastAPI foundation endpoints, event ingestion flow,
feature extraction (Pandas/NumPy), rule engine, and risk engine.
"""
import unittest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from app import create_app
from models import db, User, Space, Booking, FraudEventRecord, FraudAlertRecord
from fraud_engine.db import SessionLocal
from fraud_engine.app import app as fraud_app
from fraud_engine.schemas import FraudEventType, FraudDecision, FraudRiskLevel


class TestFraudEngineFoundation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.flask_app = create_app()
        cls.flask_app.config["TESTING"] = True
        cls.client = TestClient(fraud_app)

        with cls.flask_app.app_context():
            db.create_all()
            user = User.query.filter_by(role="seeker").first() or User.query.first()
            if not user:
                user = User(
                    name="Fraud Test User",
                    email="fraud_test_user@spaceloop.in",
                    role="seeker",
                    is_email_verified=True
                )
                user.set_password("SecureTestPass123!")
                db.session.add(user)
                db.session.commit()
            cls.user_id = user.id

    def setUp(self):
        self.client = self.__class__.client
        self.user_id = self.__class__.user_id
        session = SessionLocal()
        session.query(FraudAlertRecord).delete()
        session.query(FraudEventRecord).delete()
        session.commit()
        session.close()

    def tearDown(self):
        session = SessionLocal()
        session.query(FraudAlertRecord).delete()
        session.query(FraudEventRecord).delete()
        session.commit()
        session.close()

    def test_01_health_check(self):
        """Test GET /fraud/health endpoint."""
        response = self.client.get("/fraud/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "SpaceLoop Fraud & Trust Engine")
        self.assertIn("FastAPI", data["framework"])

    def test_02_ingest_normal_account_created(self):
        """Test POST /fraud/events with normal account_created event."""
        payload = {
            "event_type": "account_created",
            "user_id": self.user_id,
            "entity_type": "user",
            "entity_id": self.user_id,
            "ip_address": "103.21.124.5",
            "device_fingerprint": "fp_test_device_001",
            "payload": {
                "email": "genuine.seeker@university.ac.in",
                "name": "Genuine Seeker"
            }
        }
        response = self.client.post("/fraud/events", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "ingested")
        self.assertEqual(data["event_type"], "account_created")
        self.assertEqual(data["decision"], "allow")
        self.assertEqual(data["risk_level"], "normal")
        self.assertLessEqual(data["risk_score"], 0.25)

    def test_03_ingest_disposable_email_account_created(self):
        """Test POST /fraud/events with disposable burner email triggering rule and alert."""
        payload = {
            "event_type": "account_created",
            "user_id": self.user_id,
            "entity_type": "user",
            "entity_id": self.user_id,
            "ip_address": "198.51.100.22",
            "device_fingerprint": "fp_burner_002",
            "payload": {
                "email": "burner_bot_8421@mailinator.com",
                "name": "Bot Tester"
            }
        }
        response = self.client.post("/fraud/events", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "ingested")
        self.assertGreaterEqual(data["risk_score"], 0.60)
        self.assertIn(data["decision"], ["hold", "review", "block"])
        self.assertIsNotNone(data["alert_id"])

    def test_04_ingest_all_required_event_types(self):
        """Test that all 13 canonical SpaceLoop event types can be successfully ingested."""
        event_types = [
            "account_created",
            "login",
            "profile_updated",
            "listing_created",
            "listing_updated",
            "booking_created",
            "booking_cancelled",
            "payment_failed",
            "payment_completed",
            "refund_requested",
            "refund_completed",
            "device_changed",
            "location_changed"
        ]

        for et in event_types:
            payload = {
                "event_type": et,
                "user_id": self.user_id,
                "entity_type": "booking" if "booking" in et or "payment" in et or "refund" in et else "user",
                "entity_id": 999,
                "ip_address": "127.0.0.1",
                "device_fingerprint": "fp_test_runner",
                "payload": {
                    "amount": 250.0,
                    "reason": "Test event verification"
                }
            }
            res = self.client.post("/fraud/events", json=payload)
            self.assertEqual(res.status_code, 201, f"Failed to ingest event {et}: {res.text}")
            body = res.json()
            self.assertEqual(body["event_type"], et)
            self.assertEqual(body["status"], "ingested")

    def test_05_score_prospective_transaction(self):
        """Test POST /fraud/score on-demand scoring."""
        payload = {
            "event_type": "booking_created",
            "user_id": self.user_id,
            "entity_type": "booking",
            "entity_id": 101,
            "ip_address": "127.0.0.1",
            "device_fingerprint": "fp_score_check",
            "payload": {
                "amount": 350.0,
                "space_id": 1
            }
        }
        response = self.client.post("/fraud/score", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("risk_score", data)
        self.assertIn("confidence", data)
        self.assertIn("risk_level", data)
        self.assertIn("decision", data)
        self.assertIn("triggered_rules", data)
        self.assertIn("features", data)

    def test_06_alerts_list_and_detail(self):
        """Test GET /fraud/alerts and GET /fraud/alerts/{id}."""
        # Ingest an event that triggers an alert (disposable email + high price)
        payload = {
            "event_type": "booking_created",
            "user_id": self.user_id,
            "entity_type": "booking",
            "entity_id": 102,
            "ip_address": "203.0.113.88",
            "device_fingerprint": "fp_alert_trigger",
            "payload": {
                "email": "scam_attempt@tempmail.com",
                "amount": 85000.0,
                "profile_mutated_recently": True
            }
        }
        ingest_res = self.client.post("/fraud/events", json=payload)
        self.assertEqual(ingest_res.status_code, 201)
        alert_id = ingest_res.json()["alert_id"]
        self.assertIsNotNone(alert_id)

        # 1. List alerts
        list_res = self.client.get("/fraud/alerts?limit=10")
        self.assertEqual(list_res.status_code, 200)
        alerts = list_res.json()
        self.assertIsInstance(alerts, list)
        self.assertGreaterEqual(len(alerts), 1)

        # 2. Detail alert by alert_id
        detail_res = self.client.get(f"/fraud/alerts/{alert_id}")
        self.assertEqual(detail_res.status_code, 200)
        alert_data = detail_res.json()
        self.assertEqual(alert_data["alert_id"], alert_id)
        self.assertIn(alert_data["decision"], ["hold", "block", "review", "challenge"])
        self.assertGreater(len(alert_data["triggered_rules"]), 0)


if __name__ == "__main__":
    unittest.main()
