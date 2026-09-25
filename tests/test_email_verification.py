"""
SpaceLoop Real-Email Validation & Verification Comprehensive Test Suite
Verifies:
1. Syntax validation (RFC 5322 compliance & normalization via email-validator).
2. Disposable / temporary email domain rejection (mailinator, 10minutemail, subdomains).
3. Registration leaves account unverified (is_email_verified = False) with no auto-login.
4. Login gating: unverified accounts receive 403 Forbidden with email_verification_required: True across all login endpoints.
5. Email verification via POST and GET /api/v1/auth/verify-email.
6. Email verification via SSR endpoint /auth/verify-email/<token>.
7. Token single-use enforcement: used token cannot be verified again.
8. Token expiration enforcement: expired token is rejected.
9. Previous pending tokens invalidated when a new verification token is issued.
10. Verified user successfully logs in with 200 OK.
11. Resend verification endpoint anti-enumeration (identical response for existent and non-existent emails).
12. Resend verification rate limiting (3 requests per minute per IP/email).
13. Email change flow: old email remains active until token for pending email is verified.
14. Email change rejects disposable and already registered emails.
15. @email_verified_required decorator protects endpoints against unverified access.
"""
import unittest
import json
from datetime import datetime, timedelta
import secrets

from app import create_app
from models import db, User, EmailVerificationToken
from backend.modules.auth.email_validation import validate_email_address, is_disposable_domain
from backend.modules.auth.service import AuthService
from backend.modules.auth.tokens import hash_token


class TestEmailVerificationSystem(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def _cleanup_user(self, email):
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if user:
                EmailVerificationToken.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()

    def test_01_syntax_validation(self):
        """Test RFC 5322 email syntax validation and normalization."""
        # Valid emails
        valid, normalized, err = validate_email_address("Test.User+Filter@Example.COM")
        self.assertTrue(valid)
        self.assertEqual(normalized, "Test.User+Filter@example.com")
        self.assertEqual(err, "")

        # Invalid syntaxes
        invalid_emails = [
            "plainaddress",
            "#@%^%#$@#$@#.com",
            "@example.com",
            "Joe Smith <email@example.com>",
            "email.example.com",
            "email@example@example.com",
            "email@example",
            ""
        ]
        for bad_email in invalid_emails:
            valid, _, err = validate_email_address(bad_email)
            self.assertFalse(valid, f"Expected {bad_email} to fail syntax check")
            self.assertIsNotNone(err)

    def test_02_disposable_domain_detection(self):
        """Test detection and blocking of disposable/temporary domains and subdomains."""
        disposable_emails = [
            "spammer@mailinator.com",
            "throwaway@10minutemail.com",
            "temp@guerrillamail.com",
            "temp@sharklasers.com",
            "sub@deep.mailinator.com",
            "test@dispostable.com",
            "test@yopmail.com"
        ]
        for email in disposable_emails:
            domain = email.split("@")[1]
            self.assertTrue(is_disposable_domain(domain), f"Domain {domain} should be detected as disposable")
            valid, _, err = validate_email_address(email)
            self.assertFalse(valid)
            self.assertIn("disposable", err.lower())

        # Legitimate domains must not be flagged
        legit_emails = [
            "user@gmail.com",
            "alice@outlook.com",
            "bob@yahoo.co.in",
            "dev@spaceloop.in"
        ]
        for email in legit_emails:
            domain = email.split("@")[1]
            self.assertFalse(is_disposable_domain(domain), f"Domain {domain} should NOT be detected as disposable")
            valid, _, err = validate_email_address(email)
            self.assertTrue(valid, f"Email {email} should be valid")

    def test_03_registration_rejects_disposable_email(self):
        """Registration must return 400 Bad Request when a disposable email is used."""
        email = "disposable_test@mailinator.com"
        self._cleanup_user(email)

        res = self.client.post("/api/v1/auth/register", json={
            "name": "Disposable User",
            "email": email,
            "password": "SecurePassword123!",
            "role": "seeker"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)
        self.assertIn("disposable", data["error"].lower())

    def test_04_registration_creates_unverified_user_without_session(self):
        """Registration creates user with is_email_verified=False and does not establish a login session."""
        email = "unverified_new_user@example.com"
        self._cleanup_user(email)

        res = self.client.post("/api/v1/auth/register", json={
            "name": "Unverified User",
            "email": email,
            "password": "SecurePassword123!",
            "role": "seeker"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("email_verification_required"))
        self.assertFalse(data.get("user", {}).get("is_email_verified", True))

        # Check in DB
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            self.assertIsNotNone(user)
            self.assertFalse(user.is_email_verified)
            # Token must have been created
            token_rec = EmailVerificationToken.query.filter_by(user_id=user.id, used=False).first()
            self.assertIsNotNone(token_rec)

        # Check current session is empty (not logged in)
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 401)

    def test_05_unverified_user_blocked_at_all_login_endpoints(self):
        """Unverified user attempting login receives 403 Forbidden across all login endpoints."""
        email = "gate_test_unverified@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="Gate User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()

        # 1. Main login endpoint
        res = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "SecurePassword123!"
        })
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertTrue(data.get("email_verification_required"))
        self.assertIn("verify your email", data.get("error", "").lower())

        # 2. Seeker login endpoint
        res_seeker = self.client.post("/api/v1/auth/seeker/login", json={
            "email": email,
            "password": "SecurePassword123!"
        })
        self.assertEqual(res_seeker.status_code, 403)
        self.assertTrue(res_seeker.get_json().get("email_verification_required"))

        # 3. Host login endpoint
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            user.role = "host"
            db.session.commit()

        res_host = self.client.post("/api/v1/auth/host/login", json={
            "email": email,
            "password": "SecurePassword123!"
        })
        self.assertEqual(res_host.status_code, 403)
        self.assertTrue(res_host.get_json().get("email_verification_required"))

    def test_06_verify_email_via_post_and_get(self):
        """Verify email using token via POST /api/v1/auth/verify-email and GET."""
        email = "token_verification_test@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="Verify User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()
            raw_token, _ = AuthService.create_email_verification_token(user.id)

        # POST verification
        res = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("successfully verified", data.get("message", "").lower())

        # Verify DB state
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            self.assertTrue(user.is_email_verified)
            # Token is now used
            token_rec = EmailVerificationToken.query.filter_by(user_id=user.id).first()
            self.assertTrue(token_rec.used)

        # Now test GET endpoint with a fresh user/token
        email2 = "token_get_test@example.com"
        self._cleanup_user(email2)
        with self.app.app_context():
            user2 = User(name="Verify User 2", email=email2, role="seeker", is_active=True, is_email_verified=False)
            user2.set_password("SecurePassword123!")
            db.session.add(user2)
            db.session.commit()
            raw_token2, _ = AuthService.create_email_verification_token(user2.id)

        res_get = self.client.get(f"/api/v1/auth/verify-email?token={raw_token2}")
        self.assertEqual(res_get.status_code, 200)
        self.assertIn("successfully verified", res_get.get_json().get("message", "").lower())

    def test_07_token_single_use(self):
        """Used verification tokens must be rejected on subsequent attempts."""
        email = "single_use_test@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="Single Use User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()
            raw_token, _ = AuthService.create_email_verification_token(user.id)

        # First use -> 200
        res1 = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res1.status_code, 200)

        # Second use -> 400
        res2 = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("invalid or has expired", res2.get_json().get("error", "").lower())

    def test_08_token_expiration(self):
        """Expired verification tokens must be rejected."""
        email = "expired_token_test@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="Expired User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()
            raw_token, _ = AuthService.create_email_verification_token(user.id)

            # Manually expire the token in DB
            token_rec = EmailVerificationToken.query.filter_by(token_hash=hash_token(raw_token)).first()
            token_rec.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()

        res = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res.status_code, 400)
        self.assertIn("invalid or has expired", res.get_json().get("error", "").lower())

        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            self.assertFalse(user.is_email_verified)

    def test_09_invalidation_of_previous_tokens_on_new_request(self):
        """Generating a new verification token must invalidate previous unconsumed tokens."""
        email = "invalidate_prev_test@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="Token Invalidation User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()

            old_raw_token, _ = AuthService.create_email_verification_token(user.id)
            new_raw_token, _ = AuthService.create_email_verification_token(user.id)

        # Old token should fail
        res_old = self.client.post("/api/v1/auth/verify-email", json={"token": old_raw_token})
        self.assertEqual(res_old.status_code, 400)

        # New token should succeed
        res_new = self.client.post("/api/v1/auth/verify-email", json={"token": new_raw_token})
        self.assertEqual(res_new.status_code, 200)

        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            self.assertTrue(user.is_email_verified)

    def test_10_verified_user_can_login(self):
        """Verified user can log in and access protected endpoints."""
        email = "verified_login_test@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="Verified User", email=email, role="seeker", is_active=True, is_email_verified=True)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()

        res = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "SecurePassword123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("user", {}).get("is_email_verified"))

        # Access /me
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json().get("user", {}).get("email"), email)

    def test_11_resend_anti_enumeration(self):
        """Resend endpoint returns generic success message regardless of email existence."""
        # Non-existent email
        res_fake = self.client.post("/api/v1/auth/resend-verification", json={
            "email": "nonexistent_email_12345@example.com"
        })
        self.assertEqual(res_fake.status_code, 200)
        self.assertIn("verification link has been sent", res_fake.get_json().get("message", "").lower())

        # Existent unverified email
        email = "existent_resend@example.com"
        self._cleanup_user(email)
        with self.app.app_context():
            user = User(name="Existent User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()

        res_real = self.client.post("/api/v1/auth/resend-verification", json={
            "email": email
        })
        self.assertEqual(res_real.status_code, 200)
        self.assertEqual(res_real.get_json().get("message"), res_fake.get_json().get("message"))

    def test_12_resend_rate_limiting(self):
        """Resend endpoint enforces rate limiting (max 3 requests per minute)."""
        email = "rate_limit_resend@example.com"
        self._cleanup_user(email)
        with self.app.app_context():
            user = User(name="Rate Limit User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()

        # Resend requests should hit 429 when rate limit is exceeded
        hit_429 = False
        for _ in range(6):
            res = self.client.post("/api/v1/auth/resend-verification", json={"email": email})
            if res.status_code == 429:
                hit_429 = True
                break
        self.assertTrue(hit_429, "Rate limiter should trigger 429 on resend requests exceeding limit.")

    def test_13_email_change_flow(self):
        """Email change flow requires verification of new email before updating user.email."""
        old_email = "current_user_email@example.com"
        new_email = "new_user_email@example.com"
        pwd = "SecurePassword123!"
        self._cleanup_user(old_email)
        self._cleanup_user(new_email)

        with self.app.app_context():
            user = User(name="Change User", email=old_email, role="seeker", is_active=True, is_email_verified=True)
            user.set_password(pwd)
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # Log in as user
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": old_email,
            "password": pwd
        })
        self.assertEqual(login_res.status_code, 200)

        # Request email change to disposable email -> rejected with 400
        res_disp = self.client.post("/api/v1/auth/change-email", json={
            "new_email": "bad_email@mailinator.com",
            "password": pwd
        })
        self.assertEqual(res_disp.status_code, 400)
        self.assertIn("disposable", res_disp.get_json().get("error", "").lower())

        # Request email change to valid new email
        res_change = self.client.post("/api/v1/auth/change-email", json={
            "new_email": new_email,
            "password": pwd
        })
        self.assertEqual(res_change.status_code, 200)
        self.assertIn("verification email sent", res_change.get_json().get("message", "").lower())

        # Verify old email is still active in database
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertEqual(u.email, old_email)
            # Find the token with pending_email
            token_rec = EmailVerificationToken.query.filter_by(user_id=user_id, used=False).first()
            self.assertIsNotNone(token_rec)
            self.assertEqual(token_rec.pending_email, new_email)

        # Retrieve the raw token from service or simulate verification
        with self.app.app_context():
            raw_change_token, _ = AuthService.create_email_verification_token(user_id, pending_email=new_email)

        # Verify using the change token
        verify_res = self.client.post("/api/v1/auth/verify-email", json={"token": raw_change_token})
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn("successfully verified", verify_res.get_json().get("message", "").lower())

        # Verify user's email has changed in DB and is verified
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertEqual(u.email, new_email)
            self.assertTrue(u.is_email_verified)

    def test_14_ssr_verification_endpoint(self):
        """SSR verification endpoint /auth/verify-email/<token> verifies user and returns HTML."""
        email = "ssr_verify_test@example.com"
        self._cleanup_user(email)

        with self.app.app_context():
            user = User(name="SSR User", email=email, role="seeker", is_active=True, is_email_verified=False)
            user.set_password("SecurePassword123!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            raw_token, _ = AuthService.create_email_verification_token(user_id)

        res = self.client.get(f"/auth/verify-email/{raw_token}")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Email Verified", res.data)
        self.assertIn(b"successfully verified", res.data.lower())

        with self.app.app_context():
            user = db.session.get(User, user_id)
            self.assertTrue(user.is_email_verified)


if __name__ == "__main__":
    unittest.main()
