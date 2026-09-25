import unittest
import json
from datetime import datetime, timedelta
from app import create_app
from models import db, Space, User, Booking, Review, RiskAssessment, DeviceSession
from backend.modules.trust_safety import (
    TrustSafetyEngine,
    MarketplaceGraph,
    compute_median,
    compute_mad,
    compute_modified_z_score,
    evaluate_velocity_burst,
    check_listing_duplication,
)
from space_ai import set_simulate_ai_failure


class TestTrustSafety(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        set_simulate_ai_failure(False)

        with self.app.app_context():
            # Setup test users
            self.host = User.query.filter_by(email="ts_host@spaceloop.in").first()
            if not self.host:
                self.host = User(
                    name="TS Host Aarav",
                    email="ts_host@spaceloop.in",
                    role="host",
                    is_host=True,
                    is_host_verified=True,
                    is_email_verified=True
                )
                self.host.set_password("SecurePass123!")
                db.session.add(self.host)
                db.session.commit()

            self.seeker = User.query.filter_by(email="ts_seeker@spaceloop.in").first()
            if not self.seeker:
                self.seeker = User(
                    name="TS Seeker Priya",
                    email="ts_seeker@spaceloop.in",
                    role="seeker",
                    is_email_verified=True
                )
                self.seeker.set_password("SecurePass123!")
                db.session.add(self.seeker)
                db.session.commit()

            self.admin = User.query.filter_by(email="ts_admin@spaceloop.in").first()
            if not self.admin:
                self.admin = User(
                    name="TS Security Admin",
                    email="ts_admin@spaceloop.in",
                    role="admin",
                    is_admin=True,
                    is_email_verified=True
                )
                self.admin.set_password("SecurePass123!")
                db.session.add(self.admin)
            else:
                self.admin.role = "admin"
                self.admin.is_admin = True
                self.admin.set_password("SecurePass123!")
            db.session.commit()

            # Create test space
            self.space = Space.query.filter_by(title="TS Kharadi Study Nook").first()
            if not self.space:
                self.space = Space(
                    owner_id=self.host.id,
                    title="TS Kharadi Study Nook",
                    category="Study",
                    address="Tower 2, World Trade Center",
                    city="Pune",
                    neighborhood="Kharadi",
                    price_hourly=150.0,
                    price_daily=750.0,
                    sqft=120,
                    max_capacity=4,
                    is_active=True,
                    description="Quiet ergonomic study desks with dedicated high speed Wi-Fi and power outlets."
                )
                db.session.add(self.space)
                db.session.commit()

            self.host_id = self.host.id
            self.seeker_id = self.seeker.id
            self.admin_id = self.admin.id
            self.space_id = self.space.id

    def tearDown(self):
        set_simulate_ai_failure(False)
        with self.app.app_context():
            # Clean up test-created bookings & assessments
            RiskAssessment.query.filter(RiskAssessment.evidence_text.ilike("%TS %")).delete()
            DeviceSession.query.filter(DeviceSession.user_id.in_([self.host_id, self.seeker_id, self.admin_id])).delete()
            Review.query.filter(Review.user_id.in_([self.host_id, self.seeker_id])).delete()
            Booking.query.filter(Booking.renter_id.in_([self.host_id, self.seeker_id])).delete()
            db.session.commit()

    # =========================================================================
    # 1. Statistical Anomaly & Math Primitives
    # =========================================================================
    def test_statistical_mad_and_modified_z_score(self):
        """Validates robust Median Absolute Deviation and modified Z-score computation."""
        values = [100.0, 105.0, 98.0, 102.0, 101.0, 104.0, 5000.0]  # 5000 is extreme outlier
        med = compute_median(values)
        self.assertEqual(med, 102.0)

        mad = compute_mad(values, med)
        self.assertGreater(mad, 0.0)

        z_normal = compute_modified_z_score(105.0, values)
        z_outlier = compute_modified_z_score(5000.0, values)

        self.assertLess(abs(z_normal), 2.0)
        self.assertGreater(abs(z_outlier), 10.0)

    # =========================================================================
    # 2. Legitimate Booking Evaluation
    # =========================================================================
    def test_legitimate_booking_low_risk(self):
        """Normal reservation between distinct verified accounts has low risk and allow action."""
        with self.app.app_context():
            seeker = User.query.get(self.seeker_id)
            space = Space.query.get(self.space_id)

            assessment = TrustSafetyEngine.evaluate_booking(
                seeker=seeker,
                space=space,
                hours=3.0,
                total_price=572.5,
                device_fingerprint="fp_seeker_legit_macbook_01",
                ip_address="49.37.112.55"
            )

            self.assertIn(assessment.risk_level, ["normal", "unusual"])
            self.assertIn(assessment.recommended_action, ["allow", "monitor"])
            self.assertLess(assessment.risk_score, 0.5)

    # =========================================================================
    # 3. Threat: Self-Booking Collusion
    # =========================================================================
    def test_self_booking_detected_and_blocked(self):
        """Host attempting to book their own listing is deterministically flagged and restricted."""
        with self.app.app_context():
            host = User.query.get(self.host_id)
            space = Space.query.get(self.space_id)

            assessment = TrustSafetyEngine.evaluate_booking(
                seeker=host,
                space=space,
                hours=2.0,
                total_price=415.0
            )

            self.assertEqual(assessment.risk_level, "high_risk")
            self.assertEqual(assessment.recommended_action, "restrict_action")
            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("SELF_BOOKING", signals)

    # =========================================================================
    # 4. Threat: Shared Device Collusion
    # =========================================================================
    def test_shared_device_collusion_detected(self):
        """Seeker and host sharing the exact same hardware fingerprint triggers SHARED_DEVICE_COLLUSION."""
        with self.app.app_context():
            shared_fp = "hardware_hash_shared_between_host_and_seeker"

            # Host logged in on this device earlier
            TrustSafetyEngine.record_device_session(
                user_id=self.host_id,
                device_fingerprint=shared_fp,
                ip_address="122.161.45.10"
            )

            seeker = User.query.get(self.seeker_id)
            space = Space.query.get(self.space_id)

            assessment = TrustSafetyEngine.evaluate_booking(
                seeker=seeker,
                space=space,
                hours=2.0,
                total_price=415.0,
                device_fingerprint=shared_fp,
                ip_address="122.161.45.10"
            )

            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("SHARED_DEVICE_COLLUSION", signals)
            self.assertGreaterEqual(assessment.risk_score, 0.70)
            self.assertIn(assessment.risk_level, ["suspicious", "high_risk"])

    # =========================================================================
    # 5. Threat: Rapid Inventory Blocking Velocity
    # =========================================================================
    def test_inventory_blocking_velocity(self):
        """Burst of unpaid/unconfirmed bookings from same seeker triggers INVENTORY_BLOCKING."""
        with self.app.app_context():
            now = datetime.utcnow()
            # Seed 5 recent pending bookings in the last 15 minutes
            for i in range(5):
                b = Booking(
                    space_id=self.space_id,
                    renter_id=self.seeker_id,
                    start_time=now + timedelta(days=i + 1),
                    end_time=now + timedelta(days=i + 1, hours=2),
                    hours_booked=2.0,
                    total_price=300.0,
                    status="pending",
                    session_state="pending",
                    intended_purpose="Study session",
                    created_at=now - timedelta(minutes=i * 2)
                )
                db.session.add(b)
            db.session.commit()

            seeker = User.query.get(self.seeker_id)
            space = Space.query.get(self.space_id)

            assessment = TrustSafetyEngine.evaluate_booking(
                seeker=seeker,
                space=space,
                hours=2.0,
                total_price=315.0
            )

            signals = [s["code"] for s in assessment.signals_list]
            self.assertTrue("REPEATED_SLOT_RESERVATION" in signals or "INVENTORY_BLOCKING" in signals)

    # =========================================================================
    # 6. Threat: Listing Content Duplication
    # =========================================================================
    def test_listing_content_duplication_detected(self):
        """Verbatim copied space description triggers DUPLICATE_LISTING_CONTENT."""
        with self.app.app_context():
            # Create a second space by another host with verbatim same text
            fraud_host = User.query.filter_by(email="scam_ts_host@spaceloop.in").first()
            if not fraud_host:
                fraud_host = User(name="Scam Host", email="scam_ts_host@spaceloop.in", role="host")
                fraud_host.set_password("SecurePass123!")
                db.session.add(fraud_host)
                db.session.commit()

            duplicate_space = Space(
                owner_id=fraud_host.id,
                title="Exact Copy Nook TS",
                category="Study",
                address="Another Address",
                city="Pune",
                price_hourly=150.0,
                description="Quiet ergonomic study desks with dedicated high speed Wi-Fi and power outlets."
            )
            db.session.add(duplicate_space)
            db.session.commit()

            assessment = TrustSafetyEngine.evaluate_listing(duplicate_space, fraud_host)
            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("DUPLICATE_LISTING_CONTENT", signals)

            # Cleanup
            db.session.delete(duplicate_space)
            db.session.commit()

    # =========================================================================
    # 7. Threat: Extreme Price Anomaly
    # =========================================================================
    def test_extreme_price_anomaly_detected(self):
        """Listing priced at ₹4,500/hr in a ₹150/hr area triggers PRICE_ANOMALY_EXTREME."""
        with self.app.app_context():
            host = User.query.get(self.host_id)
            price_outlier_space = Space(
                owner_id=host.id,
                title="Suspicious Expensive Closet TS",
                category="Study",
                address="Kharadi IT Park",
                city="Pune",
                price_hourly=4500.0,
                description="A tiny desk for urgent needs."
            )
            db.session.add(price_outlier_space)
            db.session.commit()

            assessment = TrustSafetyEngine.evaluate_listing(price_outlier_space, host)
            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("PRICE_ANOMALY_EXTREME", signals)
            self.assertIn(assessment.risk_level, ["suspicious", "high_risk"])

            # Cleanup
            db.session.delete(price_outlier_space)
            db.session.commit()

    # =========================================================================
    # 8. Threat: Zero-Duration Stay Checkout
    # =========================================================================
    def test_zero_stay_checkout_detected(self):
        """Checkout triggered immediately (<60s) after arrival triggers ZERO_STAY_CHECKOUT."""
        with self.app.app_context():
            now = datetime.utcnow()
            rapid_booking = Booking(
                space_id=self.space_id,
                renter_id=self.seeker_id,
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=1),
                hours_booked=2.0,
                total_price=300.0,
                status="active",
                session_state="checked_in",
                intended_purpose="Study session",
                arrival_time=now - timedelta(seconds=20),  # Arrived 20 seconds ago
                departure_time=now,
                escrow_status="held"
            )
            db.session.add(rapid_booking)
            db.session.commit()

            assessment = TrustSafetyEngine.evaluate_checkout(rapid_booking)
            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("ZERO_STAY_CHECKOUT", signals)
            self.assertEqual(assessment.recommended_action, "hold_transaction")

    # =========================================================================
    # 9. Threat: Unverified Stay Review Blocked
    # =========================================================================
    def test_unverified_stay_review_blocked(self):
        """User cannot post a review without a completed, checked-out stay on that space."""
        with self.app.app_context():
            seeker = User.query.get(self.seeker_id)
            space = Space.query.get(self.space_id)

            # No completed booking passed
            assessment = TrustSafetyEngine.evaluate_review(
                reviewer=seeker,
                space=space,
                booking=None,
                rating=5,
                comment="Incredible place! 5 stars highly recommended!"
            )

            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("UNVERIFIED_STAY_REVIEW", signals)
            self.assertEqual(assessment.recommended_action, "restrict_action")

    # =========================================================================
    # 10. Threat: Duplicate Review Ring
    # =========================================================================
    def test_duplicate_review_ring_detected(self):
        """Identical review text duplicated on space triggers REVIEW_SIMILARITY_RING."""
        with self.app.app_context():
            now = datetime.utcnow()
            # Verified completed booking
            booking = Booking(
                space_id=self.space_id,
                renter_id=self.seeker_id,
                start_time=now - timedelta(days=1, hours=3),
                end_time=now - timedelta(days=1),
                hours_booked=3.0,
                total_price=450.0,
                status="completed",
                session_state="checked_out",
                intended_purpose="Study session",
                departure_time=now - timedelta(days=1)
            )
            db.session.add(booking)

            # Pre-existing review with specific phrase
            existing_rev = Review(
                space_id=self.space_id,
                user_id=self.host_id,
                booking_id=None,
                rating=5,
                comment="Absolutely flawless pristine room, great coffee machine and zero noise."
            )
            db.session.add(existing_rev)
            db.session.commit()

            seeker = User.query.get(self.seeker_id)
            space = Space.query.get(self.space_id)

            # New review with verbatim copy
            assessment = TrustSafetyEngine.evaluate_review(
                reviewer=seeker,
                space=space,
                booking=booking,
                rating=5,
                comment="Absolutely flawless pristine room, great coffee machine and zero noise."
            )

            signals = [s["code"] for s in assessment.signals_list]
            self.assertIn("REVIEW_SIMILARITY_RING", signals)

    # =========================================================================
    # 11. Graph Analytics: Cyclic Collusion Ring
    # =========================================================================
    def test_entity_graph_cycle_detection(self):
        """MarketplaceGraph detects circular A -> B -> C -> A transaction loop."""
        graph = MarketplaceGraph()
        # Add nodes
        graph.add_node("user_1", "User")
        graph.add_node("user_2", "User")
        graph.add_node("user_3", "User")

        # Directed circular cycle
        graph.add_edge("user_1", "user_2", "BOOKED_HOST")
        graph.add_edge("user_2", "user_3", "BOOKED_HOST")
        graph.add_edge("user_3", "user_1", "BOOKED_HOST")

        cycles = graph.detect_directed_cycles()
        self.assertGreater(len(cycles), 0)
        first_cycle = cycles[0]
        self.assertEqual(len(set(first_cycle)), 3)

    # =========================================================================
    # 12. Explainability & Multi-Tier AI Fallback
    # =========================================================================
    def test_explainable_narrative_and_deterministic_fallback(self):
        """Validates AI forensic narrative generation and resilient fallback when simulation is forced offline."""
        with self.app.app_context():
            host = User.query.get(self.host_id)
            space = Space.query.get(self.space_id)

            # Case A: Normal engine explainability
            normal_assessment = TrustSafetyEngine.evaluate_booking(seeker=host, space=space)
            self.assertTrue(len(normal_assessment.evidence_text) > 20)

            # Case B: AI services offline / failure simulation
            set_simulate_ai_failure(True)
            fallback_assessment = TrustSafetyEngine.evaluate_booking(seeker=host, space=space)

            # Fallback must succeed deterministically without raising exceptions
            self.assertIsNotNone(fallback_assessment)
            self.assertEqual(fallback_assessment.risk_level, "high_risk")
            self.assertIn("Forensic Rule Synthesis", fallback_assessment.evidence_text)

    # =========================================================================
    # 13. API Endpoints: Assessments, Stats, Triage
    # =========================================================================
    def test_admin_trust_safety_api_endpoints(self):
        """Validates /api/v1/trust-safety REST endpoints."""
        # Authenticate as admin
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "ts_admin@spaceloop.in",
            "password": "SecurePass123!"
        })
        self.assertEqual(login_res.status_code, 200)

        # 1. Trigger an assessment via evaluate
        eval_resp = self.client.post("/api/v1/trust-safety/evaluate", json={
            "entity_type": "space",
            "entity_id": self.space_id
        })
        self.assertEqual(eval_resp.status_code, 200)
        eval_data = eval_resp.get_json()
        assessment_id = eval_data["assessment"]["id"]

        # 2. Query assessments list
        list_resp = self.client.get("/api/v1/trust-safety/assessments")
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.get_json()
        self.assertTrue(list_data["success"])
        self.assertGreaterEqual(list_data["total"], 1)

        # 3. Query stats
        stats_resp = self.client.get("/api/v1/trust-safety/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = stats_resp.get_json()
        self.assertIn("total_assessments", stats_data["stats"])

        # 4. Take action
        action_resp = self.client.post(f"/api/v1/trust-safety/assessments/{assessment_id}/action", json={
            "action": "escrow_held",
            "notes": "Held pending ID re-verification"
        })
        self.assertEqual(action_resp.status_code, 200)
        action_data = action_resp.get_json()
        self.assertEqual(action_data["assessment"]["action_taken"], "escrow_held")

        # 5. Query entity subgraph
        graph_resp = self.client.get(f"/api/v1/trust-safety/graph/space/{self.space_id}")
        self.assertEqual(graph_resp.status_code, 200)
        graph_data = graph_resp.get_json()
        self.assertTrue(graph_data["success"])
        self.assertIn("subgraph_size", graph_data["graph"])


if __name__ == "__main__":
    unittest.main()
