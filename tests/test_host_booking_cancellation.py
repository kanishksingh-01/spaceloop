import unittest
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Space, Booking, EscrowTransaction, AuditLog


class TestHostBookingCancellation(unittest.TestCase):
    """
    End-to-End Test Suite for SpaceLoop Host Booking Cancellation.
    Covers:
    - Authentication and authorization boundaries (Host ownership, IDOR prevention).
    - Status validation (only cancellable states accepted).
    - Escrow and refund calculations (₹100 UPI micro-escrow & platform fee deductions).
    - Database state mutation and immutable audit records.
    - API response contract and error statuses (401, 403, 404, 400, 200).
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

    def _create_test_booking(self, owner_user, renter_user, status="confirmed", session_state="confirmed", total_price=500.0):
        """Creates an isolated test space and booking directly in db."""
        with self.app.app_context():
            space = Space(
                title=f"Test Premises {datetime.utcnow().timestamp()}",
                description="Quiet test studio",
                category="Workspace",
                max_capacity=2,
                sqft=120,
                price_hourly=100.0,
                address="12 Hauz Khas Village",
                city="New Delhi",
                state="Delhi",
                latitude=28.5494,
                longitude=77.2001,
                owner_id=owner_user.id,
                is_active=True,
                is_verified=True
            )
            db.session.add(space)
            db.session.flush()

            start_dt = datetime.utcnow() + timedelta(days=2)
            end_dt = start_dt + timedelta(hours=3)

            booking = Booking(
                space_id=space.id,
                renter_id=renter_user.id,
                start_time=start_dt,
                end_time=end_dt,
                hours_booked=3.0,
                total_price=total_price,
                status=status,
                intended_purpose="Research work",
                session_state=session_state,
                escrow_status="held",
                escrow_deposit_amount=100.0,
                platform_fee_amount=round((total_price - 100.0) - ((total_price - 100.0) / 1.05), 2)
            )
            db.session.add(booking)
            db.session.commit()
            return booking.id, space.id

    def test_unauthenticated_request_rejected(self):
        """Unauthenticated requests must receive HTTP 401."""
        res = self.client.post("/api/booking/1/cancel", json={"reason": "Test cancel"})
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])

    def test_host_can_cancel_own_confirmed_booking(self):
        """A space host can successfully cancel a confirmed booking for their space."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()
            self.assertIsNotNone(host)
            self.assertIsNotNone(seeker)

        booking_id, space_id = self._create_test_booking(host, seeker, status="confirmed")

        # Login as Host Sunita
        self._login(host.email)

        # Cancel the booking with custom reason
        res = self.client.post(f"/api/booking/{booking_id}/cancel", json={
            "reason": "Host emergency maintenance required"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("cancelled successfully", data["message"])
        self.assertIn("refund_amount", data)
        self.assertIn("platform_fee", data)
        self.assertIn("booking", data)
        self.assertEqual(data["booking"]["status"], "cancelled")

        # Verify database mutation
        with self.app.app_context():
            bk = Booking.query.get(booking_id)
            self.assertEqual(bk.status, "cancelled")
            self.assertEqual(bk.session_state, "cancelled")
            self.assertEqual(bk.escrow_status, "refunded")
            self.assertIsNotNone(bk.settled_at)

            # Verify immutable EscrowTransaction record
            tx = EscrowTransaction.query.filter_by(booking_id=booking_id, transaction_type="refund").first()
            self.assertIsNotNone(tx)
            self.assertEqual(tx.status, "completed")
            self.assertEqual(tx.user_id, seeker.id)
            self.assertAlmostEqual(tx.amount, data["refund_amount"], places=2)

            # Verify AuditLog record
            audit = AuditLog.query.filter_by(user_id=host.id, action="booking_cancelled").order_by(AuditLog.id.desc()).first()
            self.assertIsNotNone(audit)
            self.assertIn(f"Booking #{booking_id}", audit.details)
            self.assertIn("emergency maintenance", audit.details)

    def test_unrelated_host_cannot_cancel_booking(self):
        """Host B cannot cancel a booking belonging to Host A (IDOR defense)."""
        with self.app.app_context():
            host_a = User.query.filter_by(email="sunita@spaceloop.in").first()
            host_b = User.query.filter_by(email="vikram@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()

        booking_id, _ = self._create_test_booking(host_a, seeker, status="confirmed")

        # Login as Host B (Vikram)
        self._login(host_b.email)

        # Vikram attempts to cancel Sunita's booking
        res = self.client.post(f"/api/booking/{booking_id}/cancel", json={
            "reason": "Malicious attempt by unauthorized host"
        })
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("permission", data["error"].lower())

        # Verify booking status remained confirmed in database
        with self.app.app_context():
            bk = Booking.query.get(booking_id)
            self.assertEqual(bk.status, "confirmed")

    def test_unrelated_seeker_cannot_cancel_booking(self):
        """Seeker B cannot cancel Seeker A's booking."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker_a = User.query.filter_by(email="aarav@iitd.ac.in").first()
            seeker_b = User.query.filter_by(email="priya@coep.ac.in").first()

        booking_id, _ = self._create_test_booking(host, seeker_a, status="confirmed")

        # Login as Seeker B (Priya)
        self._login(seeker_b.email)

        res = self.client.post(f"/api/booking/{booking_id}/cancel")
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data["success"])

        with self.app.app_context():
            bk = Booking.query.get(booking_id)
            self.assertEqual(bk.status, "confirmed")

    def test_cancel_nonexistent_booking_returns_404(self):
        """Attempting to cancel an invalid/non-existent booking ID returns 404."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()

        self._login(host.email)
        res = self.client.post("/api/booking/999999/cancel")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("not found", data["error"].lower())

    def test_cannot_cancel_already_cancelled_booking(self):
        """Attempting to cancel a booking that is already cancelled returns 400."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()

        booking_id, _ = self._create_test_booking(host, seeker, status="cancelled")

        self._login(host.email)
        res = self.client.post(f"/api/booking/{booking_id}/cancel")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("already cancelled", data["error"].lower())

    def test_cannot_cancel_completed_booking(self):
        """Attempting to cancel an already completed reservation returns 400."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()

        booking_id, _ = self._create_test_booking(host, seeker, status="completed", session_state="checked_out")

        self._login(host.email)
        res = self.client.post(f"/api/booking/{booking_id}/cancel")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("completed", data["error"].lower())

    def test_cannot_cancel_active_checked_in_session(self):
        """An active session with seeker checked in cannot be cancelled directly (must check out)."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()

        booking_id, _ = self._create_test_booking(host, seeker, status="confirmed", session_state="checked_in")

        self._login(host.email)
        res = self.client.post(f"/api/booking/{booking_id}/cancel")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("active session", data["error"].lower())

    def test_plural_and_singular_cancel_routes_behave_identically(self):
        """Both /api/booking/<id>/cancel and /api/bookings/<id>/cancel route to the same handler."""
        with self.app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()

        b1_id, _ = self._create_test_booking(host, seeker, status="confirmed")
        b2_id, _ = self._create_test_booking(host, seeker, status="confirmed")

        self._login(host.email)

        res1 = self.client.post(f"/api/booking/{b1_id}/cancel")
        self.assertEqual(res1.status_code, 200)

        res2 = self.client.post(f"/api/bookings/{b2_id}/cancel")
        self.assertEqual(res2.status_code, 200)


if __name__ == "__main__":
    unittest.main()
