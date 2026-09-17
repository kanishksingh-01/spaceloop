import unittest
from app import create_app
from models import db, User, Space, Booking


class TestIDORSecurity(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_space_modification_idor_prevented(self):
        """Host A cannot edit Host B's space listing."""
        # Find space owned by Sunita (id=1)
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            vikram = User.query.filter_by(email="vikram@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()
            self.assertIsNotNone(sunita_space)
            sunita_space_id = sunita_space.id

        # Login as Vikram
        self.client.post("/api/v1/auth/login", json={
            "email": "vikram@spaceloop.in",
            "password": "password123"
        })

        # Vikram attempts to edit Sunita's space
        res = self.client.post(f"/api/spaces/{sunita_space_id}/edit", json={
            "title": "Hacked Title By Another Host",
            "price_hourly": 999.0
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("permission", res.get_json()["error"].lower())

        # Vikram attempts to toggle status of Sunita's space
        res_toggle = self.client.post(f"/api/spaces/{sunita_space_id}/toggle-status", json={})
        self.assertEqual(res_toggle.status_code, 403)

    def test_space_owner_can_modify_own_space(self):
        """Space owner can modify and toggle status of their own space."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()
            sunita_space_id = sunita_space.id

        # Login as Sunita
        self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })

        # Sunita toggles status of her own space
        res_toggle = self.client.post(f"/api/spaces/{sunita_space_id}/toggle-status", json={})
        self.assertEqual(res_toggle.status_code, 200)
        self.assertTrue(res_toggle.get_json()["success"])

        # Toggle back
        self.client.post(f"/api/spaces/{sunita_space_id}/toggle-status", json={})

    def test_booking_actions_idor_prevented(self):
        """User B cannot check in, check out, or cancel User A's booking."""
        with self.app.app_context():
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()
            self.assertIsNotNone(aarav_booking)
            booking_id = aarav_booking.id

        # Login as Priya (unrelated seeker)
        self.client.post("/api/v1/auth/login", json={
            "email": "priya@coep.ac.in",
            "password": "password123"
        })

        # Priya attempts check-in on Aarav's booking
        res_checkin = self.client.post(f"/api/booking/{booking_id}/check-in", json={
            "qr_token": "SPACELOOP_QR_IITD_ROOM1",
            "lat": 28.5450,
            "lng": 77.1926
        })
        self.assertEqual(res_checkin.status_code, 403)

        # Priya attempts check-out on Aarav's booking
        res_checkout = self.client.post(f"/api/booking/{booking_id}/check-out", json={
            "exit_photo": "https://example.com/photo.jpg"
        })
        self.assertEqual(res_checkout.status_code, 403)

        # Priya attempts cancel on Aarav's booking
        res_cancel = self.client.post(f"/api/booking/{booking_id}/cancel")
        self.assertEqual(res_cancel.status_code, 403)

        # Priya attempts to access active session page of Aarav's booking
        res_session = self.client.get(f"/booking/{booking_id}/session")
        # Should redirect to access denied (302)
        self.assertEqual(res_session.status_code, 302)
        self.assertIn("/auth/access-denied", res_session.headers.get("Location", ""))

    def test_renter_and_host_session_access_allowed(self):
        """Both the verified renter and the hosting space owner can view the session page."""
        with self.app.app_context():
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()
            booking_id = aarav_booking.id
            host_id = aarav_booking.space.owner_id
            host = User.query.get(host_id)

        # 1. Renter Aarav accesses session page
        self.client.post("/api/v1/auth/login", json={
            "email": "aarav@iitd.ac.in",
            "password": "password123"
        })
        res_aarav = self.client.get(f"/booking/{booking_id}/session")
        self.assertEqual(res_aarav.status_code, 200)

        # 2. Host accesses session page
        self.client.post("/api/v1/auth/login", json={
            "email": host.email,
            "password": "password123"
        })
        res_host = self.client.get(f"/booking/{booking_id}/session")
        self.assertEqual(res_host.status_code, 200)


if __name__ == "__main__":
    unittest.main()
