"""
SpaceLoop Feature Extraction Layer Unit Tests (Step 2)
Verifies feature calculations, provenance traces, and source tracking across all 4 domains:
1. Account Features
2. Booking Features
3. Listing Features
4. Network Features
"""
import unittest
import uuid
from datetime import datetime, timedelta
import numpy as np

from app import create_app
from models import db, User, Space, Booking, DeviceSession, FraudEventRecord, FraudAlertRecord
from fraud_engine.db import SessionLocal
from fraud_engine.schemas import FraudEventInput, FraudEventType, GeoLocation
from fraud_engine.features import (
    FeatureExtractor,
    AccountFeatureExtractor,
    BookingFeatureExtractor,
    ListingFeatureExtractor,
    NetworkFeatureExtractor,
    FeatureExtractionResult,
    is_disposable_email,
    compute_haversine_distance_km,
    calculate_jaccard_similarity,
    calculate_ngram_similarity,
    calculate_modified_zscore,
    check_conflicting_city_coordinates
)


class TestFeatureExtractionLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.flask_app = create_app()
        cls.flask_app.config["TESTING"] = True

        with cls.flask_app.app_context():
            db.create_all()

            # Ensure test seeker user
            seeker = User.query.filter_by(email="feature_seeker@spaceloop.in").first()
            if not seeker:
                seeker = User(
                    name="Feature Seeker",
                    email="feature_seeker@spaceloop.in",
                    role="seeker",
                    phone="+919811122233",
                    is_email_verified=True,
                    is_student_verified=True,
                    created_at=datetime.utcnow() - timedelta(days=10)
                )
                seeker.set_password("SecurePass123!")
                db.session.add(seeker)

            # Ensure test host user
            host = User.query.filter_by(email="feature_host@spaceloop.in").first()
            if not host:
                host = User(
                    name="Feature Host",
                    email="feature_host@spaceloop.in",
                    role="host",
                    phone="+919822233344",
                    is_email_verified=True,
                    is_host_verified=True,
                    upi_vpa_masked="host@okhdfcbank",
                    created_at=datetime.utcnow() - timedelta(days=45)
                )
                host.set_password("SecurePass123!")
                db.session.add(host)

            db.session.commit()
            cls.seeker_id = seeker.id
            cls.host_id = host.id

            # Ensure a test space exists
            test_space = Space.query.filter_by(owner_id=host.id).first()
            if not test_space:
                test_space = Space(
                    owner_id=host.id,
                    title="Acoustic Sound Studio Hauz Khas",
                    description="Professional soundproof acoustic studio with high-end microphones and audio workstation.",
                    category="Studio",
                    address="Hauz Khas Village, New Delhi",
                    city="New Delhi",
                    state="Delhi",
                    latitude=28.5494,
                    longitude=77.1945,
                    price_hourly=40.0,
                    price_daily=250.0,
                    sqft=250,
                    max_capacity=5,
                    is_active=True,
                    room_qr_token="qr_token_hk_studio_01",
                    discom_ca_number="CA_DELHI_100982"
                )
                db.session.add(test_space)
                db.session.commit()
            cls.space_id = test_space.id

    def setUp(self):
        self.db = SessionLocal()
        # Clean up any test events
        self.db.query(FraudEventRecord).delete()
        self.db.query(FraudAlertRecord).delete()
        self.db.commit()

    def tearDown(self):
        self.db.query(FraudEventRecord).delete()
        self.db.query(FraudAlertRecord).delete()
        self.db.commit()
        self.db.close()

    def test_01_similarity_and_math_utilities(self):
        """Validates pure mathematical and NLP helper functions."""
        # Disposable email
        self.assertTrue(is_disposable_email("tester@mailinator.com"))
        self.assertTrue(is_disposable_email("burner@tempmail.com"))
        self.assertFalse(is_disposable_email("student@iitd.ac.in"))
        self.assertFalse(is_disposable_email("owner@gmail.com"))

        # Haversine distance
        # Delhi (28.6139, 77.2090) to Mumbai (19.0760, 72.8777) is ~1148 km
        dist = compute_haversine_distance_km(28.6139, 77.2090, 19.0760, 72.8777)
        self.assertGreater(dist, 1100.0)
        self.assertLess(dist, 1200.0)

        # Text similarities
        text_a = "Spacious quiet desk for coding and study"
        text_b = "Spacious quiet desk for study and reading"
        text_c = "Heavy mechanical industrial workshop with lathe machines"

        j_sim_high = calculate_jaccard_similarity(text_a, text_b)
        j_sim_low = calculate_jaccard_similarity(text_a, text_c)
        self.assertGreater(j_sim_high, 0.5)
        self.assertLess(j_sim_low, 0.2)

        ng_sim = calculate_ngram_similarity(text_a, text_a)
        self.assertEqual(ng_sim, 1.0)

        # Modified Z-score
        prices = [25.0, 30.0, 28.0, 26.0, 32.0, 27.0]
        z_normal = calculate_modified_zscore(29.0, prices)
        z_outlier = calculate_modified_zscore(500.0, prices)
        self.assertLess(abs(z_normal), 2.0)
        self.assertGreater(abs(z_outlier), 5.0)

        # Conflicting city coordinates
        # Bangalore coords with city 'New Delhi' -> conflict
        is_conf, diff_km = check_conflicting_city_coordinates("New Delhi", 12.9716, 77.5946)
        self.assertTrue(is_conf)
        self.assertGreater(diff_km, 500.0)

        # Delhi coords with city 'New Delhi' -> no conflict
        is_conf_ok, _ = check_conflicting_city_coordinates("New Delhi", 28.5494, 77.1945)
        self.assertFalse(is_conf_ok)

    def test_02_account_feature_extraction_and_traceability(self):
        """Validates AccountFeatureExtractor calculations and provenance lineage."""
        event = FraudEventInput(
            event_type=FraudEventType.LOGIN,
            user_id=self.seeker_id,
            ip_address="103.25.14.88",
            device_fingerprint="device_fp_seeker_alpha",
            payload={"email": "feature_seeker@spaceloop.in"}
        )

        res = FeatureExtractionResult()
        AccountFeatureExtractor.extract(event, self.db, res)

        # Check calculated values
        self.assertGreater(res.get_value("account_age_days"), 5.0)
        self.assertGreater(res.get_value("account_age_hours"), 120.0)
        self.assertEqual(res.get_value("email_is_disposable"), False)
        self.assertEqual(res.get_value("email_domain"), "spaceloop.in")
        self.assertEqual(res.get_value("is_student_verified"), True)

        # Verify every trace has valid metadata
        for trace_name, trace in res.traces.items():
            self.assertEqual(trace.category, "account")
            self.assertTrue(len(trace.source) > 0, f"Missing source for {trace_name}")
            self.assertTrue(len(trace.description) > 0, f"Missing description for {trace_name}")

    def test_03_booking_feature_extraction(self):
        """Validates BookingFeatureExtractor calculations (frequency, churn, price deviation)."""
        # Create 2 cancelled bookings and 1 confirmed booking for seeker
        b1 = Booking(
            space_id=self.space_id,
            renter_id=self.seeker_id,
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=2),
            hours_booked=2.0,
            total_price=80.0,
            status="cancelled",
            intended_purpose="Exam prep",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        b2 = Booking(
            space_id=self.space_id,
            renter_id=self.seeker_id,
            start_time=datetime.utcnow() + timedelta(days=2),
            end_time=datetime.utcnow() + timedelta(days=2, hours=2),
            hours_booked=2.0,
            total_price=80.0,
            status="cancelled",
            intended_purpose="Quiet study",
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        b3 = Booking(
            space_id=self.space_id,
            renter_id=self.seeker_id,
            start_time=datetime.utcnow() + timedelta(days=3),
            end_time=datetime.utcnow() + timedelta(days=3, hours=2),
            hours_booked=2.0,
            total_price=80.0,
            status="confirmed",
            intended_purpose="Group project",
            created_at=datetime.utcnow() - timedelta(minutes=20)
        )
        self.db.add_all([b1, b2, b3])
        self.db.commit()

        event = FraudEventInput(
            event_type=FraudEventType.BOOKING_CREATED,
            user_id=self.seeker_id,
            entity_type="booking",
            payload={"space_id": self.space_id, "amount": 80.0, "hours_booked": 2.0}
        )

        res = FeatureExtractionResult()
        BookingFeatureExtractor.extract(event, self.db, res)

        self.assertGreaterEqual(res.get_value("bookings_count_24h"), 3)
        self.assertGreaterEqual(res.get_value("cancellations_count_24h"), 2)
        self.assertGreater(res.get_value("cancellation_ratio_7d"), 0.5)
        self.assertEqual(res.get_value("booking_amount"), 80.0)

        # Check booking traces
        for name, trace in res.traces.items():
            self.assertEqual(trace.category, "booking")
            self.assertTrue(len(trace.source) > 0)
            self.assertTrue(len(trace.description) > 0)

    def test_04_listing_feature_extraction(self):
        """Validates ListingFeatureExtractor duplicate detection, similarity, and conflict signals."""
        event = FraudEventInput(
            event_type=FraudEventType.LISTING_CREATED,
            user_id=self.host_id,
            entity_type="listing",
            payload={
                "title": "Acoustic Sound Studio Hauz Khas",  # Exact duplicate title
                "description": "Professional soundproof acoustic studio with high-end microphones and audio workstation.", # Exact duplicate description
                "address": "Hauz Khas Village, New Delhi",  # Exact duplicate address
                "city": "New Delhi",
                "price_hourly": 40.0,
                "price_daily": 250.0,
                "sqft": 250,
                "max_capacity": 5,
                "room_qr_token": "qr_token_hk_studio_01",   # Repeated token
                "discom_ca_number": "CA_DELHI_100982",       # Repeated CA
                "latitude": 28.5494,
                "longitude": 77.1945
            }
        )

        res = FeatureExtractionResult()
        ListingFeatureExtractor.extract(event, self.db, res)

        self.assertGreaterEqual(res.get_value("duplicate_title_count"), 1)
        self.assertGreaterEqual(res.get_value("duplicate_address_count"), 1)
        self.assertGreaterEqual(res.get_value("max_description_jaccard_similarity"), 0.9)
        self.assertTrue(res.get_value("repeated_room_qr_token"))
        self.assertTrue(res.get_value("repeated_discom_ca"))
        self.assertFalse(res.get_value("conflicting_geo_city"))

        # Test conflicting city coordinates
        event_conflict = FraudEventInput(
            event_type=FraudEventType.LISTING_CREATED,
            user_id=self.host_id,
            entity_type="listing",
            payload={
                "title": "Conflicting Location Listing",
                "city": "New Delhi",
                "latitude": 12.9716, # Bangalore coords!
                "longitude": 77.5946,
                "price_hourly": 50.0
            }
        )
        res_conf = FeatureExtractionResult()
        ListingFeatureExtractor.extract(event_conflict, self.db, res_conf)
        self.assertTrue(res_conf.get_value("conflicting_geo_city"))
        self.assertGreater(res_conf.get_value("geo_city_discrepancy_km"), 500.0)

    def test_05_network_feature_extraction(self):
        """Validates NetworkFeatureExtractor multi-account sharing, graph degrees, and clusters."""
        # Create second user sharing the same device fingerprint as seeker
        shared_fp = "device_fp_colleague_shared"
        sess1 = DeviceSession(
            user_id=self.seeker_id,
            device_fingerprint=shared_fp,
            ip_address="103.25.14.88",
            ip_hash="hash_88"
        )
        sess2 = DeviceSession(
            user_id=self.host_id,
            device_fingerprint=shared_fp,
            ip_address="103.25.14.88",
            ip_hash="hash_88"
        )
        self.db.add_all([sess1, sess2])
        self.db.commit()

        event = FraudEventInput(
            event_type=FraudEventType.LOGIN,
            user_id=self.seeker_id,
            device_fingerprint=shared_fp
        )

        res = FeatureExtractionResult()
        NetworkFeatureExtractor.extract(event, self.db, res)

        self.assertGreaterEqual(res.get_value("network_shared_device_degree"), 1)
        self.assertGreaterEqual(res.get_value("network_connected_accounts_count"), 1)
        self.assertGreaterEqual(res.get_value("network_cluster_size"), 2)

    def test_06_unified_feature_extractor_facade(self):
        """Validates the master FeatureExtractor combining all domains and producing flat dict."""
        event = FraudEventInput(
            event_type=FraudEventType.BOOKING_CREATED,
            user_id=self.seeker_id,
            entity_type="booking",
            payload={"space_id": self.space_id, "amount": 80.0, "hours_booked": 2.0}
        )

        # 1. Traceable result
        traceable = FeatureExtractor.extract_traceable(event, self.db)
        self.assertIsInstance(traceable, FeatureExtractionResult)
        self.assertIn("account_age_hours", traceable.features)
        self.assertIn("bookings_count_24h", traceable.features)
        self.assertIn("duplicate_title_count", traceable.features)
        self.assertIn("network_shared_device_degree", traceable.features)

        # 2. Flat dict result
        flat = FeatureExtractor.extract(event, self.db)
        self.assertIsInstance(flat, dict)
        self.assertEqual(flat["account_age_hours"], traceable.features["account_age_hours"])
        self.assertEqual(flat["bookings_count_24h"], traceable.features["bookings_count_24h"])
        self.assertIn("price_zscore", flat)
        self.assertIn("is_self_transaction", flat)
        self.assertIn("device_user_overlap_count", flat)


if __name__ == "__main__":
    unittest.main()
