"""
Unit and Integration Test Suite for SpaceLoop Transactional Email System (Resend API)
Verifies:
1. All 12 transactional email events (welcome, verification, security alerts, booking requests,
   approvals, rejections, confirmations, reminders, cancellations, escrow holds, escrow refunds,
   payment failures).
2. Strict idempotency / duplicate prevention.
3. Fault-isolation (booking transaction remains intact even if email fails).
4. Accurate booking times and role targeting (host vs seeker).
5. Resend adapter header formatting and retry logic.
6. Secret leakage prevention (RESEND_API_KEY never exposed).
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Space, Booking, EmailLog
from backend.modules.email import (
    EmailService,
    DevelopmentEmailAdapter,
    ResendEmailAdapter,
    BaseEmailAdapter
)


class TestSpaceLoopEmailSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Reset development adapter in-memory records
        DevelopmentEmailAdapter.reset()
        EmailService.set_adapter(DevelopmentEmailAdapter())

        # Create verified test host
        self.host = User(
            name="Vikram Malhotra",
            first_name="Vikram",
            last_name="Malhotra",
            email="host_vikram@example.com",
            role="host",
            is_active=True,
            is_email_verified=True,
            is_host_verified=True
        )
        self.host.set_password("HostPass123!")

        # Create verified test seeker
        self.seeker = User(
            name="Ananya Sharma",
            first_name="Ananya",
            last_name="Sharma",
            email="seeker_ananya@example.com",
            role="seeker",
            is_active=True,
            is_email_verified=True
        )
        self.seeker.set_password("SeekerPass123!")

        db.session.add_all([self.host, self.seeker])
        db.session.commit()

        # Create test space
        self.space = Space(
            owner_id=self.host.id,
            title="Kharadi Design Studio & Quiet Focus Pod",
            description="Quiet creative space for teams and focused work.",
            category="Studio",
            address="Plot 14, EON Free Zone, Kharadi",
            city="Pune",
            state="Maharashtra",
            price_hourly=40.0,
            price_daily=200.0,
            max_capacity=6,
            is_active=True
        )
        db.session.add(self.space)
        db.session.commit()

        # Create confirmed test booking with fixed scheduled window
        self.booking_start = datetime(2026, 10, 15, 14, 0, 0)
        self.booking_end = datetime(2026, 10, 15, 17, 0, 0)
        self.booking = Booking(
            space_id=self.space.id,
            renter_id=self.seeker.id,
            start_time=self.booking_start,
            end_time=self.booking_end,
            hours_booked=3.0,
            attendees_count=4,
            total_price=126.0,
            status="confirmed",
            intended_purpose="Design Review Workshop",
            session_state="confirmed",
            arrival_pin="9241",
            escrow_deposit_amount=100.0,
            escrow_status="held"
        )
        db.session.add(self.booking)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # ==========================================================================
    # 1. Authentication & Security Email Tests
    # ==========================================================================

    def test_welcome_email_dispatch(self):
        """1. Welcome email dispatched upon user account creation."""
        res = EmailService.notify_welcome(self.seeker)
        self.assertTrue(res)

        self.assertIsNotNone(DevelopmentEmailAdapter.last_sent)
        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], "seeker_ananya@example.com")
        self.assertIn("Welcome to SpaceLoop", sent["subject"])
        self.assertIn("Ananya Sharma", sent["html"])
        self.assertIn("Zero-Hardware Physical Space Network", sent["html"])

        # Verify EmailLog database entry
        log_entry = EmailLog.query.filter_by(event_type="user_welcome", recipient_email="seeker_ananya@example.com").first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.status, "sent")
        self.assertEqual(log_entry.user_id, self.seeker.id)

    def test_email_verification_dispatch(self):
        """2. Email verification link email dispatch."""
        raw_token = "secure_test_token_abcdef123456"
        res = EmailService.notify_email_verification(
            to_email=self.seeker.email,
            raw_token=raw_token,
            user_id=self.seeker.id
        )
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("Verify Your SpaceLoop Email Address", sent["subject"])
        self.assertIn(raw_token, sent["html"])

    def test_security_alert_dispatch(self):
        """3. Account security notification dispatch (MFA/Password)."""
        res = EmailService.notify_security_event(
            user=self.host,
            alert_title="Two-Factor Authentication Enabled",
            alert_message="TOTP protection was successfully configured on your account."
        )
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.host.email)
        self.assertIn("Security Alert", sent["subject"])
        self.assertIn("Vikram Malhotra", sent["html"])
        self.assertIn("TOTP protection", sent["html"])

    # ==========================================================================
    # 2. Booking Lifecycle Email Tests
    # ==========================================================================

    def test_booking_request_to_host(self):
        """4. New reservation request notifies Host."""
        pending_booking = Booking(
            space_id=self.space.id,
            renter_id=self.seeker.id,
            start_time=self.booking_start,
            end_time=self.booking_end,
            hours_booked=3.0,
            attendees_count=5,
            total_price=126.0,
            status="pending",
            intended_purpose="Team Planning",
            session_state="pending",
            arrival_pin="7721",
            escrow_deposit_amount=100.0,
            escrow_status="held"
        )
        db.session.add(pending_booking)
        db.session.commit()

        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_booking_created(pending_booking)
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertIsNotNone(sent)
        self.assertEqual(sent["to"], self.host.email)  # Host must receive it!
        self.assertIn("New Reservation Request", sent["subject"])
        self.assertIn("Kharadi Design Studio", sent["html"])
        self.assertIn(self.space.title, sent["text"])
        self.assertIn("Oct 15, 2026", sent["html"])
        self.assertIn("Team Planning", sent["html"])

    def test_booking_confirmed_notifies_both_roles(self):
        """5. Confirmed booking sends pass to seeker and notice to host."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_booking_created(self.booking)
        self.assertTrue(res)

        # Both host and seeker should receive emails
        self.assertEqual(len(DevelopmentEmailAdapter.sent_emails), 2)
        recipients = [e["to"] for e in DevelopmentEmailAdapter.sent_emails]
        self.assertIn(self.host.email, recipients)
        self.assertIn(self.seeker.email, recipients)

        # Seeker email must include Arrival PIN
        seeker_email = next(e for e in DevelopmentEmailAdapter.sent_emails if e["to"] == self.seeker.email)
        self.assertIn("9241", seeker_email["html"])
        self.assertIn("Oct 15, 2026", seeker_email["html"])

    def test_host_approval_notification(self):
        """6. Host approves booking -> Seeker receives confirmation pass."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_host_approved(self.booking)
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("Booking Approved!", sent["subject"])
        self.assertIn("9241", sent["html"])
        self.assertIn("Plot 14, EON Free Zone", sent["html"])

    def test_host_rejection_notification(self):
        """7. Host rejects booking -> Seeker receives decline and refund notice."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_host_rejected(self.booking)
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("Reservation Declined", sent["subject"])
        self.assertIn("refunded", sent["html"])

    def test_upcoming_booking_reminder(self):
        """8. Upcoming booking reminder sent with correct scheduled time."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_upcoming_reminder(self.booking)
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("Reminder: Your upcoming session", sent["subject"])
        self.assertIn("Oct 15, 2026", sent["html"])
        self.assertIn("9241", sent["html"])

    def test_booking_cancelled_notifies_both(self):
        """9. Booking cancellation notifies host and seeker."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_booking_cancelled(self.booking)
        self.assertTrue(res)

        self.assertEqual(len(DevelopmentEmailAdapter.sent_emails), 2)
        recipients = [e["to"] for e in DevelopmentEmailAdapter.sent_emails]
        self.assertIn(self.host.email, recipients)
        self.assertIn(self.seeker.email, recipients)

    # ==========================================================================
    # 3. Escrow & Payment Email Tests
    # ==========================================================================

    def test_escrow_deposit_held_receipt(self):
        """10. Escrow receipt sent when deposit is held."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_escrow_held(self.booking)
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("Escrow Deposit Receipt: ₹100", sent["subject"])
        self.assertIn("UPI Micro-Escrow", sent["html"])

    def test_escrow_refund_notification(self):
        """11. Escrow released / refunded notification."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_escrow_refunded(self.booking, reason="Check-out Inspection Cleared")
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("₹100 UPI Escrow Released", sent["subject"])
        self.assertIn("Check-out Inspection Cleared", sent["html"])

    def test_payment_failure_notification(self):
        """12. Payment failure notification contains specific reason."""
        DevelopmentEmailAdapter.reset()
        res = EmailService.notify_payment_failed(
            user=self.seeker,
            space_title=self.space.title,
            amount=226.0,
            reason="UPI Authorization Declined by issuing bank"
        )
        self.assertTrue(res)

        sent = DevelopmentEmailAdapter.last_sent
        self.assertEqual(sent["to"], self.seeker.email)
        self.assertIn("Payment Failed", sent["subject"])
        self.assertIn("226.00", sent["html"])
        self.assertIn("UPI Authorization Declined", sent["html"])

    # ==========================================================================
    # 4. Idempotency & Duplicate Prevention Tests
    # ==========================================================================

    def test_idempotency_prevents_duplicate_emails(self):
        """Verifies duplicate email dispatches with identical keys are skipped."""
        DevelopmentEmailAdapter.reset()
        key = "booking-approved-unique-test-key-999"

        # First dispatch
        res1 = EmailService.send_email(
            to_email="test_recipient@example.com",
            subject="First Notification",
            html_body="<p>Test</p>",
            idempotency_key=key
        )
        self.assertTrue(res1)
        self.assertEqual(len(DevelopmentEmailAdapter.sent_emails), 1)

        # Second dispatch with identical key
        res2 = EmailService.send_email(
            to_email="test_recipient@example.com",
            subject="First Notification (Duplicate)",
            html_body="<p>Test Duplicate</p>",
            idempotency_key=key
        )
        self.assertTrue(res2)
        # In-memory sent count MUST still be 1 (no duplicate network dispatch)
        self.assertEqual(len(DevelopmentEmailAdapter.sent_emails), 1)

    # ==========================================================================
    # 5. Fault Isolation: Booking Logic Does NOT Depend on Email Success
    # ==========================================================================

    class FailingMockAdapter(BaseEmailAdapter):
        def send_email(self, to_email, subject, html_body, text_body="", idempotency_key=None):
            raise ConnectionError("Simulated Resend API Network Timeout")

    def test_booking_succeeds_even_when_email_fails(self):
        """Verifies that an email provider outage never aborts or reverts a booking."""
        EmailService.set_adapter(self.FailingMockAdapter())

        # Authenticate seeker
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(self.seeker.id)

        # Request new booking
        future_start = (datetime.utcnow() + timedelta(days=10)).isoformat()
        future_end = (datetime.utcnow() + timedelta(days=10, hours=2)).isoformat()

        res = self.client.post("/api/bookings", json={
            "space_id": self.space.id,
            "hours": 2.0,
            "start_time": future_start,
            "end_time": future_end,
            "attendees_count": 2,
            "purpose": "Fault Isolation Verification"
        })

        # Booking MUST succeed with HTTP 201
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        booking_id = data["booking_id"]

        # Booking MUST be persisted in DB
        persisted = Booking.query.get(booking_id)
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.intended_purpose, "Fault Isolation Verification")
        self.assertEqual(persisted.escrow_status, "held")

        # Email failure MUST be logged in EmailLog without crashing
        failed_log = EmailLog.query.filter_by(booking_id=booking_id, status="failed").first()
        self.assertIsNotNone(failed_log)
        self.assertIn("Simulated Resend API Network Timeout", failed_log.error_message)

    # ==========================================================================
    # 6. Resend Adapter Unit & Retry Tests
    # ==========================================================================

    @patch("requests.post")
    def test_resend_adapter_bearer_auth_and_idempotency_headers(self, mock_post):
        """Verifies ResendEmailAdapter sets correct Bearer token, Idempotency-Key, and payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "re_live_test_12345"}'
        mock_response.json.return_value = {"id": "re_live_test_12345"}
        mock_post.return_value = mock_response

        adapter = ResendEmailAdapter(
            api_key="re_secret_test_key_123",
            from_email="SpaceLoop <notifications@spaceloop.in>"
        )

        success, resend_id, error = adapter.send_email(
            to_email="customer@example.com",
            subject="Test Subject",
            html_body="<h1>Hello SpaceLoop</h1>",
            idempotency_key="idemp_key_456"
        )

        self.assertTrue(success)
        self.assertEqual(resend_id, "re_live_test_12345")
        self.assertIsNone(error)

        # Inspect request arguments
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        headers = call_kwargs["headers"]
        json_body = call_kwargs["json"]

        self.assertEqual(headers["Authorization"], "Bearer re_secret_test_key_123")
        self.assertEqual(headers["Idempotency-Key"], "idemp_key_456")
        self.assertEqual(json_body["from"], "SpaceLoop <notifications@spaceloop.in>")
        self.assertEqual(json_body["to"], ["customer@example.com"])
        self.assertEqual(json_body["subject"], "Test Subject")

    @patch("requests.post")
    def test_resend_adapter_retries_on_500_error(self, mock_post):
        """Verifies ResendEmailAdapter retries on 500 server error and succeeds on attempt 2."""
        mock_500 = MagicMock()
        mock_500.status_code = 500
        mock_500.text = "Internal Server Error"
        mock_500.json.side_effect = ValueError("No JSON")

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = '{"id": "re_retry_success"}'
        mock_200.json.return_value = {"id": "re_retry_success"}

        mock_post.side_effect = [mock_500, mock_200]

        adapter = ResendEmailAdapter(api_key="re_test_key", max_retries=1)
        success, resend_id, error = adapter.send_email(
            to_email="retry_user@example.com",
            subject="Retry Test",
            html_body="<p>Testing Retries</p>"
        )

        self.assertTrue(success)
        self.assertEqual(resend_id, "re_retry_success")
        self.assertEqual(mock_post.call_count, 2)

    # ==========================================================================
    # 7. Secret Leakage Prevention Tests
    # ==========================================================================

    def test_no_secret_leakage_in_api_or_logs(self):
        """Verifies RESEND_API_KEY is never exposed in user profiles or email logs."""
        EmailService.notify_welcome(self.seeker)

        # Query email log
        log = EmailLog.query.filter_by(recipient_email=self.seeker.email).first()
        self.assertIsNotNone(log)
        log_dict = log.to_dict()

        # Ensure no api_key or secret tokens in log serialization
        self.assertNotIn("api_key", log_dict)
        self.assertNotIn("secret", log_dict)
        self.assertNotIn("password", log_dict)

        # Query safe user profile via endpoint
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(self.seeker.id)

        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 200)
        user_data = me_res.get_json()["user"]

        self.assertNotIn("resend", str(user_data).lower())
        self.assertNotIn("api_key", str(user_data).lower())


if __name__ == "__main__":
    unittest.main()
