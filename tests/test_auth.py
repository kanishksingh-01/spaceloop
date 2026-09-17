import unittest
from datetime import datetime, timedelta
from flask_wtf.csrf import generate_csrf
from app import create_app
from models import db, User, PasswordResetToken
from backend.modules.auth.service import AuthService
from backend.modules.auth.password import hash_password, verify_password


class TestAuthenticationSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    # ==========================================
    # TEST 1: Successful Registration
    # ==========================================
    def test_01_successful_registration(self):
        """User registration creates account, assigns role, and hashes password securely."""
        unique_email = "test_register_user_01@example.com"
        with self.app.app_context():
            existing = User.query.filter_by(email=unique_email).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

        payload = {
            "first_name": "New",
            "last_name": "Student",
            "email": unique_email,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
            "role": "seeker"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["email"], unique_email)
        self.assertEqual(data["user"]["role"], "seeker")

        with self.app.app_context():
            user = User.query.filter_by(email=unique_email).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "seeker")
            self.assertFalse(user.is_admin)
            # Password must NOT be stored in plaintext
            self.assertNotEqual(user.password_hash, "ValidPassword123!")
            self.assertTrue(user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:"))
            self.assertTrue(user.check_password("ValidPassword123!"))
            # Public ID must be generated
            self.assertTrue(bool(user.public_id))

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    # ==========================================
    # TEST 2: Duplicate Registration Rejected
    # ==========================================
    def test_02_duplicate_registration_rejected(self):
        """Duplicate email registration is rejected safely without 500 error or duplicate record."""
        payload = {
            "first_name": "Sunita",
            "last_name": "Sharma",
            "email": "sunita@spaceloop.in",
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
            "role": "seeker"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("already exists", data["error"].lower())

        with self.app.app_context():
            count = User.query.filter_by(email="sunita@spaceloop.in").count()
            self.assertEqual(count, 1)

    # ==========================================
    # TEST 3: Successful Login & Session Cookie
    # ==========================================
    def test_03_successful_login(self):
        """Valid credentials establish an authenticated session and issue a session cookie."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["email"], "sunita@spaceloop.in")

        # Verify session cookie was set
        set_cookie = res.headers.get("Set-Cookie", "")
        self.assertIn("session=", set_cookie)

    # ==========================================
    # TEST 4: Invalid Password -> Generic 401
    # ==========================================
    def test_04_invalid_password_generic_error(self):
        """Incorrect password returns generic 401 error without revealing field specifics."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "wrongpassword123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid email or password.")

    # ==========================================
    # TEST 5: Nonexistent Account -> Identical 401
    # ==========================================
    def test_05_nonexistent_account_generic_error(self):
        """Nonexistent email returns identical generic 401 error to prevent username enumeration."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "doesnotexist_987654@spaceloop.in",
            "password": "wrongpassword123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid email or password.")

    # ==========================================
    # TEST 6: Session Creation and Resolution
    # ==========================================
    def test_06_session_creation_and_current_user_resolution(self):
        """Session correctly resolves current_user and safe profile on protected endpoints."""
        self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["email"], "sunita@spaceloop.in")
        self.assertEqual(data["user"]["role"], "owner")
        # Ensure password hash is never exposed in profile
        self.assertNotIn("password_hash", data["user"])

    # ==========================================
    # TEST 7: Logout Session Invalidation
    # ==========================================
    def test_07_logout_session_invalidation(self):
        """Logout invalidates active session; subsequent protected requests are rejected."""
        self.client.post("/api/v1/auth/login", json={
            "email": "aarav@iitd.ac.in",
            "password": "password123"
        })
        res1 = self.client.get("/api/v1/auth/me")
        self.assertEqual(res1.status_code, 200)

        # Logout
        res_logout = self.client.post("/api/v1/auth/logout")
        self.assertEqual(res_logout.status_code, 200)

        # Subsequent call must fail with 401
        res2 = self.client.get("/api/v1/auth/me")
        self.assertEqual(res2.status_code, 401)

    # ==========================================
    # TEST 8: Session Fixation Protection
    # ==========================================
    def test_08_session_fixation_protection(self):
        """Pre-existing unauthenticated session state is purged upon login."""
        # Set pre-login session marker
        with self.client.session_transaction() as sess:
            sess["pre_login_untrusted_data"] = "attacker_marker"

        # Perform login
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)

        # Verify pre-existing session marker was erased
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("pre_login_untrusted_data"))
            self.assertIsNotNone(sess.get("_user_id"))

    # ==========================================
    # TEST 9: CSRF Protection on Web Login
    # ==========================================
    def test_09_csrf_protection_on_web_login(self):
        """Web login form requires valid CSRF token; missing or invalid tokens return 400."""
        self.app.config["WTF_CSRF_ENABLED"] = True
        client = self.app.test_client()

        # 1. Missing CSRF token -> Rejected 400
        res_missing = client.post("/auth/login", data={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res_missing.status_code, 400)
        self.assertIn(b"CSRF", res_missing.data)

        # 2. Valid CSRF token -> Accepted (redirect 302)
        with client:
            client.get("/auth/login")
            with self.app.test_request_context():
                token = generate_csrf()
            res_valid = client.post("/auth/login", data={
                "csrf_token": token,
                "email": "sunita@spaceloop.in",
                "password": "password123"
            })
            self.assertEqual(res_valid.status_code, 302)
            self.assertIn("/dashboard", res_valid.headers.get("Location", ""))

    # ==========================================
    # TEST 10: Rate Limiting (HTTP 429)
    # ==========================================
    def test_10_rate_limiting_triggers_429(self):
        """Repeated rapid login attempts trigger rate limiting (429 Too Many Requests)."""
        app = create_app()
        app.config["TESTING"] = True
        app.config["RATELIMIT_ENABLED"] = True
        client = app.test_client()

        statuses = []
        for _ in range(7):
            res = client.post("/api/v1/auth/login", json={
                "email": "ratelimit_test@example.com",
                "password": "wrongpassword"
            })
            statuses.append(res.status_code)

        # First 5 should be 401 (limit is 5 per minute), 6th and 7th should be 429
        self.assertEqual(statuses[:5], [401, 401, 401, 401, 401])
        self.assertEqual(statuses[5], 429)

    # ==========================================
    # TEST 11: Password Storage Format Verification
    # ==========================================
    def test_11_password_storage_format(self):
        """Stored passwords use scrypt or pbkdf2 and match verify operations."""
        with self.app.app_context():
            user = User.query.filter_by(email="sunita@spaceloop.in").first()
            self.assertIsNotNone(user)
            self.assertTrue(user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:"))
            self.assertTrue(user.check_password("password123"))
            self.assertFalse(user.check_password("altered_password123"))

    # ==========================================
    # TEST 12: Password Reset Lifecycle
    # ==========================================
    def test_12_password_reset_lifecycle(self):
        """Full lifecycle of password reset token: creation, reset, reuse prevention, expiry, tampering."""
        with self.app.app_context():
            # 1. Request reset token
            success, msg, token = AuthService.request_password_reset("priya@coep.ac.in")
            self.assertTrue(success)
            self.assertTrue(bool(token))

            # 2. Tampered token fails
            tampered_token = token + "tampered"
            tampered_ok, tampered_msg = AuthService.reset_password(tampered_token, "NewPass123!", "NewPass123!")
            self.assertFalse(tampered_ok)
            self.assertIn("invalid or has expired", tampered_msg)

            # 3. Successful reset with valid token
            reset_ok, reset_msg = AuthService.reset_password(token, "NewPriyaPass123!", "NewPriyaPass123!")
            self.assertTrue(reset_ok)

            # 4. Old password no longer authenticates
            old_user, old_err = AuthService.authenticate_user("priya@coep.ac.in", "password123")
            self.assertIsNone(old_user)
            self.assertEqual(old_err, "Invalid email or password.")

            # 5. New password authenticates successfully
            new_user, new_err = AuthService.authenticate_user("priya@coep.ac.in", "NewPriyaPass123!")
            self.assertIsNotNone(new_user)
            self.assertEqual(new_err, "")

            # 6. Re-use of consumed token fails
            reuse_ok, reuse_msg = AuthService.reset_password(token, "AnotherPass123!", "AnotherPass123!")
            self.assertFalse(reuse_ok)
            self.assertIn("invalid or has expired", reuse_msg)

            # 7. Expired token fails
            _, _, exp_token = AuthService.request_password_reset("priya@coep.ac.in")
            from backend.modules.auth.tokens import hash_token
            exp_entry = PasswordResetToken.query.filter_by(token_hash=hash_token(exp_token)).first()
            exp_entry.expires_at = datetime.utcnow() - timedelta(minutes=10)
            db.session.commit()

            exp_ok, exp_msg = AuthService.reset_password(exp_token, "ExpiredPass123!", "ExpiredPass123!")
            self.assertFalse(exp_ok)
            self.assertIn("invalid or has expired", exp_msg)

            # Restore original password
            priya = User.query.filter_by(email="priya@coep.ac.in").first()
            priya.set_password("password123")
            db.session.commit()

    # ==========================================
    # TEST 13: Protected Authentication State
    # ==========================================
    def test_13_protected_authentication_state(self):
        """Unauthenticated requests to protected endpoints fail with 401 or redirect to login."""
        # Unauthenticated API request -> 401
        res_api = self.client.get("/api/v1/auth/me")
        self.assertEqual(res_api.status_code, 401)

        # Unauthenticated Web request -> 302 redirect
        res_web = self.client.get("/dashboard")
        self.assertEqual(res_web.status_code, 302)
        self.assertIn("/auth/login", res_web.headers.get("Location", ""))

        # Authenticated Web request -> 200 OK
        self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        res_auth_web = self.client.get("/dashboard")
        self.assertEqual(res_auth_web.status_code, 200)

    # ==========================================
    # NEGATIVE EDGE CASES
    # ==========================================
    def test_edge_case_excessive_lengths(self):
        """Excessive password (>128 chars) and email (>254 chars) lengths are rejected to prevent DoS."""
        # Password > 128 characters
        res_pw = self.client.post("/api/v1/auth/register", json={
            "first_name": "Long",
            "last_name": "Pass",
            "email": "longpass@example.com",
            "password": "A" * 129 + "1!a",
            "confirm_password": "A" * 129 + "1!a",
            "role": "seeker"
        })
        self.assertEqual(res_pw.status_code, 400)
        self.assertIn("128 characters", res_pw.get_json()["error"])

        # Email > 254 characters
        long_email = "a" * 250 + "@example.com"
        res_em = self.client.post("/api/v1/auth/register", json={
            "first_name": "Long",
            "last_name": "Email",
            "email": long_email,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
            "role": "seeker"
        })
        self.assertEqual(res_em.status_code, 400)
        self.assertIn("254 characters", res_em.get_json()["error"])

    def test_edge_case_open_redirect_prevention(self):
        """Open redirect attacks via protocol-relative or external URLs fall back to safe default."""
        malicious_targets = [
            "//attacker.com",
            "/\\attacker.com",
            "https://attacker.com",
            "\\\\attacker.com"
        ]
        for target in malicious_targets:
            client = self.app.test_client()
            res = client.post(f"/auth/login?next={target}", data={
                "email": "sunita@spaceloop.in",
                "password": "password123"
            })
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res.headers.get("Location"), "/dashboard")

        # Safe redirect is honored
        client = self.app.test_client()
        res_safe = client.post("/auth/login?next=/explore", data={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res_safe.status_code, 302)
        self.assertEqual(res_safe.headers.get("Location"), "/explore")

    def test_edge_case_admin_escalation_blocked(self):
        """Public registration cannot escalate privileges to admin."""
        unique_email = "admin_hacker@example.com"
        res = self.client.post("/api/v1/auth/register", json={
            "first_name": "Hacker",
            "last_name": "Admin",
            "email": unique_email,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
            "role": "admin",
            "is_admin": True
        })
        self.assertEqual(res.status_code, 201)
        with self.app.app_context():
            user = User.query.filter_by(email=unique_email).first()
            self.assertFalse(user.is_admin)
            self.assertNotEqual(user.role, "admin")
            db.session.delete(user)
            db.session.commit()

    def test_edge_case_inactive_user_blocked(self):
        """Inactive accounts are denied authentication with generic error."""
        with self.app.app_context():
            user = User.query.filter_by(email="kabir@du.ac.in").first()
            user.is_active = False
            db.session.commit()

        res = self.client.post("/api/v1/auth/login", json={
            "email": "kabir@du.ac.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["error"], "Invalid email or password.")

        with self.app.app_context():
            user = User.query.filter_by(email="kabir@du.ac.in").first()
            user.is_active = True
            db.session.commit()

    def test_email_verification_flow(self):
        """Email verification token validates the account; single-use enforced."""
        import uuid
        unique_email = f"verif_test_{uuid.uuid4().hex[:8]}@example.com"
        with self.app.app_context():
            user, token, err = AuthService.register_user(
                first_name="Verif",
                last_name="Test",
                email=unique_email,
                password="ValidPassword123!",
                confirm_password="ValidPassword123!"
            )
            self.assertIsNotNone(user, f"Registration failed: {err}")
            self.assertFalse(user.is_email_verified)

            # Verify token
            success, msg = AuthService.verify_email(token)
            self.assertTrue(success)

            updated = User.query.filter_by(email=unique_email).first()
            self.assertTrue(updated.is_email_verified)

            # Reusing token fails
            success_reuse, _ = AuthService.verify_email(token)
            self.assertFalse(success_reuse)

            # Cleanup
            db.session.delete(updated)
            db.session.commit()


if __name__ == "__main__":
    unittest.main()
