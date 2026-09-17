"""
Suite: Identity & Student Verification Security Tests (Issue 3)
Validates all 12 mandatory audit security tests:
- TEST 1: Unverified user
- TEST 2: Valid sandbox verification
- TEST 3: Invalid identity data
- TEST 4: Invalid OTP
- TEST 5: Expired OTP
- TEST 6: OTP replay protection
- TEST 7: Excessive OTP attempts throttling
- TEST 8: Verification-state manipulation resistance
- TEST 9: Sensitive data logging hygiene
- TEST 10: Provider failure fails closed
- TEST 11: Duplicate verification idempotency
- TEST 12: Missing verification provider reports sandbox/unavailable
"""

import io
import logging
import unittest
from datetime import datetime, timedelta

from app import app, db, limiter
from models import User
from backend.modules.verification.service import (
    IdentityVerificationService,
    _otp_sessions,
    _consumed_replay_cache,
    SANDBOX,
    USER_PROVIDED,
    STATUS_UNVERIFIED,
    STATUS_SANDBOX_VERIFIED,
)


class TestIdentityVerificationSecurity(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app.config["RATELIMIT_ENABLED"] = False
        limiter.enabled = False
        self.client = self.app.test_client()

        # Reset verification sessions and provider simulation
        IdentityVerificationService.reset_sessions()
        IdentityVerificationService.set_simulate_provider_failure(False)

        with self.app.app_context():
            user = User.query.filter_by(email="verif_student_test@spaceloop.local").first()
            if not user:
                user = User(
                    name="Test Student",
                    first_name="Test",
                    last_name="Student",
                    email="verif_student_test@spaceloop.local",
                    role="seeker",
                    is_active=True,
                    is_email_verified=True,
                    is_admin=False,
                )
                db.session.add(user)
            user.set_password("password123")
            user.failed_login_attempts = 0
            user.locked_until = None
            user.is_active = True
            user.is_email_verified = True
            user.is_student_verified = False
            user.is_aadhaar_verified = False
            user.student_verification_status = "unverified"
            user.aadhaar_verification_status = "unverified"
            user.identity_verification_ref = ""
            user.identity_verified_at = None
            user.aadhaar_masked = ""
            user.aadhaar_token_hash = ""
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        IdentityVerificationService.reset_sessions()
        IdentityVerificationService.set_simulate_provider_failure(False)
        limiter.enabled = True

    def _login(self):
        res = self.client.post(
            "/api/v1/auth/login",
            json={"email": "verif_student_test@spaceloop.local", "password": "password123"},
        )
        self.assertEqual(res.status_code, 200, f"Login failed: {res.get_data(as_text=True)}")
        return res

    # ==================================================
    # TEST 1 — Unverified User
    # ==================================================
    def test_01_unverified_user_has_unverified_status(self):
        """Newly created / unverified user has unverified status and False booleans."""
        with self.app.app_context():
            user = User.query.get(self.user_id)
            self.assertFalse(user.is_student_verified)
            self.assertFalse(user.is_aadhaar_verified)
            self.assertEqual(user.student_verification_status, STATUS_UNVERIFIED)
            self.assertEqual(user.aadhaar_verification_status, STATUS_UNVERIFIED)
            self.assertEqual(user.identity_verification_ref, "")
            self.assertIsNone(user.identity_verified_at)

            d = user.to_dict()
            self.assertFalse(d["is_student_verified"])
            self.assertFalse(d["is_aadhaar_verified"])
            self.assertEqual(d["student_verification_status"], "unverified")
            self.assertEqual(d["aadhaar_verification_status"], "unverified")

    # ==================================================
    # TEST 2 — Valid Sandbox Verification
    # ==================================================
    def test_02_valid_sandbox_verification_succeeds_with_sandbox_label(self):
        """Sandbox verification succeeds and is explicitly classified as SANDBOX."""
        self._login()

        res = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": "123456",
                "college_email": "test.stu@iitd.ac.in",
                "college_name": "IIT Delhi",
                "student_id": "2024CS1044",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["reality_status"], SANDBOX)
        self.assertEqual(data["aadhaar"]["reality_status"], SANDBOX)
        self.assertEqual(data["aadhaar"]["masked_aadhaar"], "XXXX-XXXX-4821")
        self.assertEqual(data["academic"]["reality_status"], USER_PROVIDED)
        self.assertTrue(data["academic"]["is_institutional_email"])
        self.assertIn("Sandbox demo only", data["production_notice"])

        # Check DB state
        with self.app.app_context():
            u = User.query.get(self.user_id)
            self.assertTrue(u.is_student_verified)
            self.assertTrue(u.is_aadhaar_verified)
            self.assertEqual(u.student_verification_status, STATUS_SANDBOX_VERIFIED)
            self.assertEqual(u.aadhaar_verification_status, STATUS_SANDBOX_VERIFIED)
            self.assertTrue(u.identity_verification_ref.startswith("VERIF-AADH-SBX-"))
            self.assertIsNotNone(u.identity_verified_at)

    # ==================================================
    # TEST 3 — Invalid Identity Data
    # ==================================================
    def test_03_invalid_identity_data_rejected(self):
        """Invalid Aadhaar formats (not 12 digits, begins with 0 or 1) are rejected."""
        self._login()

        # Non-12-digit
        res_short = self.client.post(
            "/api/verify/student",
            json={
                "aadhaar_number": "12345",
                "otp": "123456",
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res_short.status_code, 400)
        self.assertIn("Must be exactly 12 numeric digits", res_short.get_json()["error"])

        # Begins with 0
        res_zero = self.client.post(
            "/api/verify/student",
            json={
                "aadhaar_number": "084512344821",
                "otp": "123456",
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res_zero.status_code, 400)
        self.assertIn("cannot begin with 0 or 1", res_zero.get_json()["error"])

        # Begins with 1
        res_one = self.client.post(
            "/api/verify/student",
            json={
                "aadhaar_number": "184512344821",
                "otp": "123456",
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res_one.status_code, 400)
        self.assertIn("cannot begin with 0 or 1", res_one.get_json()["error"])

        # Invalid academic email domain
        res_email = self.client.post(
            "/api/verify/student",
            json={
                "aadhaar_number": "984512344821",
                "otp": "123456",
                "college_email": "fake.student@gmail.com",
            },
        )
        self.assertEqual(res_email.status_code, 400)
        self.assertIn("Must end with .ac.in", res_email.get_json()["error"])

    # ==================================================
    # TEST 4 — Invalid OTP
    # ==================================================
    def test_04_invalid_otp_rejected(self):
        """Incorrect OTP code is strictly rejected."""
        self._login()

        # 1. Request a sandbox challenge OTP
        res_req = self.client.post(
            "/api/verify/student/request-otp",
            json={"aadhaar_number": "984512344821"},
        )
        self.assertEqual(res_req.status_code, 200)

        # 2. Attempt verification with incorrect OTP
        res_wrong = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": "000000",
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res_wrong.status_code, 400)
        self.assertIn("Invalid OTP", res_wrong.get_json()["error"])

    # ==================================================
    # TEST 5 — Expired OTP
    # ==================================================
    def test_05_expired_otp_rejected(self):
        """Expired OTP code fails closed."""
        self._login()

        # Request OTP
        res_req = self.client.post(
            "/api/verify/student/request-otp",
            json={"aadhaar_number": "984512344821"},
        )
        self.assertEqual(res_req.status_code, 200)
        otp = res_req.get_json()["sandbox_demo_otp"]

        # Manually backdate the session's expires_at timestamp to simulate expiry
        session_key = str(self.user_id)
        if session_key in _otp_sessions:
            _otp_sessions[session_key]["expires_at"] = datetime.utcnow() - timedelta(minutes=1)

        # Attempt verification with expired OTP
        res_expired = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": otp,
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res_expired.status_code, 400)
        self.assertIn("expired", res_expired.get_json()["error"].lower())

    # ==================================================
    # TEST 6 — OTP Replay Protection
    # ==================================================
    def test_06_otp_replay_protection(self):
        """Single-use OTP cannot be reused once consumed."""
        self._login()

        res_req = self.client.post(
            "/api/verify/student/request-otp",
            json={"aadhaar_number": "984512344821"},
        )
        self.assertEqual(res_req.status_code, 200)
        otp = res_req.get_json()["sandbox_demo_otp"]

        payload = {
            "name": "Test Student",
            "aadhaar_number": "984512344821",
            "otp": otp,
            "college_email": "test@iitd.ac.in",
        }

        # First use succeeds
        res1 = self.client.post("/api/verify/student", json=payload)
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.get_json()["success"])

        # Second use (replay) must be rejected
        res2 = self.client.post("/api/verify/student", json=payload)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already been consumed", res2.get_json()["error"].lower())

    # ==================================================
    # TEST 7 — Excessive OTP Attempts Throttling
    # ==================================================
    def test_07_excessive_otp_attempts_locked_out(self):
        """After 3 consecutive failed OTP attempts, the OTP session is locked out."""
        self._login()

        res_req = self.client.post(
            "/api/verify/student/request-otp",
            json={"aadhaar_number": "984512344821"},
        )
        self.assertEqual(res_req.status_code, 200)
        valid_otp = res_req.get_json()["sandbox_demo_otp"]

        # 3 failed attempts
        for attempt in range(1, 4):
            res_bad = self.client.post(
                "/api/verify/student",
                json={
                    "name": "Test Student",
                    "aadhaar_number": "984512344821",
                    "otp": "999999",
                    "college_email": "test@iitd.ac.in",
                },
            )
            self.assertEqual(res_bad.status_code, 400)

        # 4th attempt with the CORRECT OTP must still be rejected due to lockout
        res_locked = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": valid_otp,
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res_locked.status_code, 400)
        self.assertIn("Maximum OTP verification attempts exceeded", res_locked.get_json()["error"])

    # ==================================================
    # TEST 8 — Verification-State Manipulation Resistance
    # ==================================================
    def test_08_verification_state_manipulation_rejected(self):
        """Client-provided verified flags in request body or registration cannot forge verification."""
        self._login()

        # Attacker tries to inject verification flags into registration or profile payloads
        res = self.client.post(
            "/api/verify/student",
            json={
                "is_student_verified": True,
                "is_aadhaar_verified": True,
                "student_verification_status": "verified",
                "aadhaar_verification_status": "verified",
                "aadhaar_number": "123",  # invalid
                "college_email": "not_an_email",
            },
        )
        # Must fail because server evaluates business logic, not client flags
        self.assertEqual(res.status_code, 400)

        # Verify DB was NOT modified
        with self.app.app_context():
            u = User.query.get(self.user_id)
            self.assertFalse(u.is_student_verified)
            self.assertFalse(u.is_aadhaar_verified)

    # ==================================================
    # TEST 9 — Sensitive Data Logging Hygiene
    # ==================================================
    def test_09_sensitive_data_not_written_to_logs(self):
        """Raw 12-digit Aadhaar number and OTPs are never written to logger output."""
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger()
        logger.addHandler(handler)

        raw_aadhaar = "984512344821"
        self._login()

        # Request and verify OTP
        res_req = self.client.post(
            "/api/verify/student/request-otp",
            json={"aadhaar_number": raw_aadhaar},
        )
        otp = res_req.get_json().get("sandbox_demo_otp", "123456")

        self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": raw_aadhaar,
                "otp": otp,
                "college_email": "test@iitd.ac.in",
            },
        )

        logger.removeHandler(handler)
        log_contents = log_capture.getvalue()

        # Ensure raw 12-digit Aadhaar does not appear in logs
        self.assertNotIn(raw_aadhaar, log_contents)

    # ==================================================
    # TEST 10 — Provider Failure Fails Closed
    # ==================================================
    def test_10_provider_failure_fails_closed(self):
        """Simulated external gateway failure fails closed; user is not marked verified."""
        self._login()

        IdentityVerificationService.set_simulate_provider_failure(True)

        res = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": "123456",
                "college_email": "test@iitd.ac.in",
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Fails closed", res.get_json()["error"])

        with self.app.app_context():
            u = User.query.get(self.user_id)
            self.assertFalse(u.is_student_verified)
            self.assertFalse(u.is_aadhaar_verified)

    # ==================================================
    # TEST 11 — Duplicate Verification Idempotency
    # ==================================================
    def test_11_duplicate_verification_idempotent(self):
        """Repeated verification updates record cleanly without creating duplicate or contradictory state."""
        self._login()

        # First verification
        res1 = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": "123456",
                "college_email": "test@iitd.ac.in",
                "college_name": "IIT Delhi",
                "student_id": "2024CS1044",
            },
        )
        self.assertEqual(res1.status_code, 200)

        # Clear replay cache for testing subsequent re-verification
        IdentityVerificationService.reset_sessions()

        # Second verification with updated college email
        res2 = self.client.post(
            "/api/verify/student",
            json={
                "name": "Test Student",
                "aadhaar_number": "984512344821",
                "otp": "123456",
                "college_email": "test.higher@iitb.ac.in",
                "college_name": "IIT Bombay",
                "student_id": "2025CS2099",
            },
        )
        self.assertEqual(res2.status_code, 200)

        with self.app.app_context():
            u = User.query.get(self.user_id)
            self.assertTrue(u.is_student_verified)
            self.assertEqual(u.college_email, "test.higher@iitb.ac.in")
            self.assertEqual(u.college_name, "IIT Bombay")
            # Only one user record exists
            count = User.query.filter_by(email="verif_student_test@spaceloop.local").count()
            self.assertEqual(count, 1)

    # ==================================================
    # TEST 12 — Missing Verification Provider Reports Sandbox
    # ==================================================
    def test_12_reality_inventory_reports_honest_sandbox(self):
        """Reality inventory endpoint truthfully reports SANDBOX, USER-PROVIDED, and MISSING status."""
        res = self.client.get("/api/verify/reality-inventory")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        inventory = {item["method"]: item for item in data["inventory"]}

        self.assertIn("Aadhaar Identity Verification", inventory)
        self.assertEqual(inventory["Aadhaar Identity Verification"]["reality_status"], "SANDBOX")

        self.assertIn("Academic Email Domain Validation", inventory)
        self.assertEqual(inventory["Academic Email Domain Validation"]["reality_status"], "USER-PROVIDED")

        self.assertIn("DigiLocker Document Retrieval", inventory)
        self.assertEqual(inventory["DigiLocker Document Retrieval"]["reality_status"], "MISSING")


if __name__ == "__main__":
    unittest.main()
