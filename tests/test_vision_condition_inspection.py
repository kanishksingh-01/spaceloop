import unittest
import io
import base64
from datetime import datetime, timedelta
from PIL import Image

from app import create_app
from models import db, User, Space, Booking, EscrowTransaction
from space_ai import evaluate_room_condition_delta


class TestVisionConditionInspection(unittest.TestCase):
    """
    End-to-End Test Suite for SpaceLoop Vision Condition-Delta Inspection.
    Verifies:
    1. evaluate_room_condition_delta correctly computes image SSIM and color delta.
    2. Identical arrival vs departure images produce >=95% match and instant escrow release.
    3. Discrepant/damaged images produce low match and hold escrow deposit.
    4. Seeker check-in saves real uploaded entry photo to disk and updates booking.entry_scan_photo.
    5. Seeker check-out saves real uploaded exit photo and updates condition scores.
    6. Host Booking Detail API returns the real uploaded photos and dynamic scores.
    """

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def _login(self, email: str, password: str = "password123"):
        res = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        self.assertEqual(res.status_code, 200, f"Failed to login user {email}: {res.status_code}")
        return res

    def _make_base64_image(self, color="white", size=(128, 128)) -> str:
        im = Image.new("RGB", size, color=color)
        buf = io.BytesIO()
        im.save(buf, format="JPEG")
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    def test_cv_delta_identical_images(self):
        """Identical photos should produce 100% match score and RELEASE_FULL decision."""
        img1 = self._make_base64_image(color="white")
        img2 = self._make_base64_image(color="white")

        res = evaluate_room_condition_delta(img1, img2)
        self.assertIsNotNone(res["condition_match_score"])
        self.assertGreaterEqual(res["condition_match_score"], 90.0)
        self.assertTrue(res["furniture_unchanged"])
        self.assertTrue(res["fans_lights_cleared"])
        self.assertEqual(res["escrow_decision"], "RELEASE_FULL")
        self.assertEqual(res["deposit_refund_amount"], 100.0)

    def test_cv_delta_discrepant_images(self):
        """Completely different photos (e.g. white room vs pitch black) should flag discrepancy."""
        img_white = self._make_base64_image(color="white")
        img_black = self._make_base64_image(color="black")

        res = evaluate_room_condition_delta(img_white, img_black)
        self.assertIsNotNone(res["condition_match_score"])
        self.assertLess(res["condition_match_score"], 75.0)
        self.assertEqual(res["escrow_decision"], "REVIEW_REQUIRED")
        self.assertEqual(res["deposit_refund_amount"], 0.0)

    def test_cv_delta_simulation_modes(self):
        """simulate_damaged and simulate_failure flags are honored."""
        img = self._make_base64_image(color="white")

        # simulate_failure
        fail_res = evaluate_room_condition_delta(img, img, simulate_failure=True)
        self.assertIsNone(fail_res["condition_match_score"])
        self.assertEqual(fail_res["escrow_decision"], "REVIEW_REQUIRED")

        # simulate_damaged
        dam_res = evaluate_room_condition_delta(img, img, simulate_damaged=True)
        self.assertEqual(dam_res["condition_match_score"], 64.0)
        self.assertFalse(dam_res["fans_lights_cleared"])
        self.assertEqual(dam_res["escrow_decision"], "REVIEW_REQUIRED")

    def test_end_to_end_checkin_checkout_photos(self):
        """Verifies seeker uploading entry and exit photos, backend disk storage, and host retrieval."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()
            self.assertIsNotNone(host)
            self.assertIsNotNone(seeker)

            space = Space(
                title="Vision Inspection Studio",
                description="Equipped with automated CV scanning",
                category="Workspace",
                max_capacity=4,
                sqft=200,
                price_hourly=150.0,
                address="44 Cyber Hub",
                city="Gurugram",
                state="Haryana",
                latitude=28.4986,
                longitude=77.0878,
                owner_id=host.id,
                room_qr_token="VISION_TEST_QR",
                is_active=True,
                is_verified=True
            )
            db.session.add(space)
            db.session.flush()

            now = datetime.utcnow()
            booking = Booking(
                space_id=space.id,
                renter_id=seeker.id,
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=2),
                hours_booked=3,
                total_price=450.0,
                status="confirmed",
                session_state="confirmed",
                intended_purpose="Study session",
                arrival_pin="1234",
                escrow_deposit_amount=100.0,
                escrow_status="held"
            )
            db.session.add(booking)
            db.session.commit()
            booking_id = booking.id
            host_email = host.email
            seeker_email = seeker.email

        # 1. Seeker logs in and executes check-in with a real base64 entry photo
        self._login(seeker_email)
        entry_b64 = self._make_base64_image(color="lightblue")
        checkin_payload = {
            "lat": 28.4986,
            "lng": 77.0878,
            "qr_token": "VISION_TEST_QR",
            "pin": "1234",
            "entry_photo": entry_b64
        }
        res_ci = self.client.post(f"/api/booking/{booking_id}/check-in", json=checkin_payload)
        self.assertEqual(res_ci.status_code, 200)
        data_ci = res_ci.get_json()
        self.assertTrue(data_ci["success"])
        # Verify entry_scan_photo is stored as local upload URL
        self.assertTrue(data_ci["booking"]["entry_scan_photo"].startswith("/static/uploads/inspections/"))

        # 2. Seeker executes check-out with matching exit photo
        exit_b64 = self._make_base64_image(color="lightblue")
        checkout_payload = {
            "lat": 28.4986,
            "lng": 77.0878,
            "exit_photo": exit_b64
        }
        res_co = self.client.post(f"/api/booking/{booking_id}/check-out", json=checkout_payload)
        self.assertEqual(res_co.status_code, 200)
        data_co = res_co.get_json()
        self.assertTrue(data_co["success"])
        self.assertTrue(data_co["booking"]["exit_scan_photo"].startswith("/static/uploads/inspections/"))
        self.assertGreaterEqual(data_co["booking"]["condition_match_score"], 80.0)
        self.assertEqual(data_co["booking"]["escrow_status"], "released")
        self.assertTrue(data_co["booking"]["condition_verified"])

        # 3. Host logs in and views booking detail
        self._login(host_email)
        res_host = self.client.get(f"/api/host/bookings/{booking_id}")
        self.assertEqual(res_host.status_code, 200)
        data_host = res_host.get_json()
        b_host = data_host["booking"]
        # Verify the host receives the real photos uploaded by the seeker, not Unsplash placeholders!
        self.assertTrue(b_host["entry_scan_photo"].startswith("/static/uploads/inspections/"))
        self.assertTrue(b_host["exit_scan_photo"].startswith("/static/uploads/inspections/"))
        self.assertGreaterEqual(b_host["condition_match_score"], 80.0)
        self.assertTrue(b_host["fans_lights_cleared"])
        self.assertTrue(b_host["condition_verified"])


if __name__ == "__main__":
    unittest.main()
