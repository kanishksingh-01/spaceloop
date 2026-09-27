import unittest
import json
import os
from app import create_app
from models import db, User
from config import Config
from backend.modules.auth.service import AuthService


class TestAuthSecurityFixes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_switch_user_backdoor_removed(self):
        """The /switch-user/<id> endpoint must be completely removed (return 404)."""
        res_post = self.client.post("/switch-user/1")
        self.assertEqual(res_post.status_code, 404)

        res_get_json = self.client.get("/switch-user/1", headers={"Accept": "application/json"})
        self.assertEqual(res_get_json.status_code, 404)

        # Ensure no session was established
        res_me = self.client.get("/api/v1/auth/me")
        self.assertEqual(res_me.status_code, 401)

    def test_demo_switch_backdoor_removed(self):
        """The /auth/demo-switch/<role> and /api/v1/auth/demo-switch/<role> backdoors must be removed."""
        res_legacy = self.client.post("/auth/demo-switch/admin")
        self.assertEqual(res_legacy.status_code, 404)

        res_api = self.client.post("/api/v1/auth/demo-switch/host")
        self.assertEqual(res_api.status_code, 404)

        res_api_get = self.client.get("/api/v1/auth/demo-switch/seeker")
        self.assertEqual(res_api_get.status_code, 404)

    def test_login_does_not_overwrite_password(self):
        """Logging in with a wrong password must fail and never overwrite the existing password."""
        test_email = "test_pw_isolated@spaceloop.in"
        with self.app.app_context():
            # Ensure aarav has standard seed password
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            if aarav:
                aarav.set_password("password123")
                db.session.commit()

            user = User.query.filter_by(email=test_email).first()
            if not user:
                user = User(
                    name="Isolated Test",
                    first_name="Isolated",
                    last_name="Test",
                    email=test_email,
                    role="seeker",
                    is_active=True
                )
                user.set_password("CorrectSecurePassword123!")
                db.session.add(user)
                db.session.commit()
            else:
                user.set_password("CorrectSecurePassword123!")
                db.session.commit()

        try:
            # Try to login with wrong arbitrary password
            res = self.client.post("/api/v1/auth/login", json={
                "email": test_email,
                "password": "WrongPassword999!"
            })
            self.assertEqual(res.status_code, 401)
            self.assertFalse(res.get_json().get("success"))

            # Verify the original password was NOT overwritten
            with self.app.app_context():
                user = User.query.filter_by(email=test_email).first()
                self.assertTrue(user.check_password("CorrectSecurePassword123!"))
                self.assertFalse(user.check_password("WrongPassword999!"))

            # Verify correct password succeeds
            res_ok = self.client.post("/api/v1/auth/login", json={
                "email": test_email,
                "password": "CorrectSecurePassword123!"
            })
            self.assertEqual(res_ok.status_code, 200)
            self.assertTrue(res_ok.get_json().get("success"))
        finally:
            with self.app.app_context():
                user = User.query.filter_by(email=test_email).first()
                if user:
                    db.session.delete(user)
                    db.session.commit()

    def test_host_register_does_not_overwrite_existing_user(self):
        """Duplicate host registration with existing email must be rejected, not overwrite password."""
        test_email = "host_overwrite_test@spaceloop.in"
        with self.app.app_context():
            existing = User.query.filter_by(email=test_email).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

            # Create existing user
            user = User(
                name="Original User",
                first_name="Original",
                last_name="User",
                email=test_email,
                role="seeker",
                is_active=True
            )
            user.set_password("OriginalPassword123!")
            db.session.add(user)
            db.session.commit()

        # Attempt to re-register this email as host with new password
        res = self.client.post("/api/v1/auth/host/register", json={
            "first_name": "Attacker",
            "last_name": "Host",
            "email": test_email,
            "password": "AttackerNewPassword123!",
            "phone": "9876543210",
            "discom_ca": "DEL1234567",
            "discom_provider": "BSES Rajdhani Power Limited",
            "upi_vpa": "attacker@okhdfcbank"
        })
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json().get("success"))

        # Verify original password is intact
        with self.app.app_context():
            user = User.query.filter_by(email=test_email).first()
            self.assertTrue(user.check_password("OriginalPassword123!"))
            self.assertFalse(user.check_password("AttackerNewPassword123!"))
            db.session.delete(user)
            db.session.commit()

    def test_api_csrf_custom_header_enforcement(self):
        """State-changing API calls with session cookies must require X-Requested-With header."""
        self.app.config["ENFORCE_API_CSRF_IN_TESTS"] = True

        # Simulate authenticated session cookie
        self.client.set_cookie("session", "mock_active_session_cookie")

        # Mutating request without custom header or trusted origin -> 403 Forbidden
        res_blocked = self.client.post("/api/v1/bookings/1/cancel")
        self.assertEqual(res_blocked.status_code, 403)
        data = res_blocked.get_json()
        self.assertIn("CSRF validation failed", data.get("error", ""))

        # Request with X-Requested-With header -> passes CSRF check
        res_passed = self.client.post(
            "/api/v1/bookings/1/cancel",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        # It may return 401 or 404 based on booking auth/existence, but NOT 403 CSRF
        self.assertNotEqual(res_passed.status_code, 403)

    def test_cors_credentials_not_reflected_for_arbitrary_origins(self):
        """Arbitrary origins must NOT receive Access-Control-Allow-Credentials: true."""
        res_evil = self.client.get(
            "/api/health",
            headers={"Origin": "https://evil-attacker.com"}
        )
        # Should not allow credentials for untrusted origin
        self.assertNotEqual(res_evil.headers.get("Access-Control-Allow-Origin"), "https://evil-attacker.com")
        self.assertNotEqual(res_evil.headers.get("Access-Control-Allow-Credentials"), "true")

        # Trusted origin should get credentials allowed
        trusted_origin = "http://localhost:5173"
        res_trusted = self.client.get(
            "/api/health",
            headers={"Origin": trusted_origin}
        )
        self.assertEqual(res_trusted.headers.get("Access-Control-Allow-Origin"), trusted_origin)
        self.assertEqual(res_trusted.headers.get("Access-Control-Allow-Credentials"), "true")

    def test_password_reset_flow_and_token_invalidation(self):
        """Forgot-password & reset-password flow: generates token, updates hash, and invalidates token."""
        test_email = "reset_test_user@spaceloop.in"
        with self.app.app_context():
            user = User.query.filter_by(email=test_email).first()
            if existing := user:
                db.session.delete(existing)
                db.session.commit()

            user = User(
                name="Reset Test",
                first_name="Reset",
                last_name="Test",
                email=test_email,
                role="seeker",
                is_active=True
            )
            user.set_password("OldPassword123!")
            db.session.add(user)
            db.session.commit()

        # Step 1: Request password reset via API
        res_forgot = self.client.post("/api/v1/auth/forgot-password", json={"email": test_email})
        self.assertEqual(res_forgot.status_code, 200)
        # Raw token must NEVER be leaked in the API JSON response
        self.assertNotIn("token", res_forgot.get_json())

        # Obtain the token securely through AuthService for test execution
        with self.app.app_context():
            _, _, raw_token = AuthService.request_password_reset(test_email)
            self.assertIsNotNone(raw_token)

        # Step 2: Attempt reset with weak password (< 8 chars) -> fails
        res_weak = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "password": "short",
            "confirm_password": "short"
        })
        self.assertEqual(res_weak.status_code, 400)

        # Step 3: Reset password with strong password -> succeeds
        res_reset = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "password": "BrandNewSecurePassword123!",
            "confirm_password": "BrandNewSecurePassword123!"
        })
        self.assertEqual(res_reset.status_code, 200)
        self.assertTrue(res_reset.get_json().get("success"))

        # Step 4: Token must now be single-use / invalidated
        res_reuse = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "password": "AnotherPassword123!",
            "confirm_password": "AnotherPassword123!"
        })
        self.assertEqual(res_reuse.status_code, 400)
        self.assertFalse(res_reuse.get_json().get("success"))

        # Step 5: Verify new password allows login
        res_login = self.client.post("/api/v1/auth/login", json={
            "email": test_email,
            "password": "BrandNewSecurePassword123!"
        })
        self.assertEqual(res_login.status_code, 200)

        # Cleanup
        with self.app.app_context():
            user = User.query.filter_by(email=test_email).first()
            if user:
                db.session.delete(user)
                db.session.commit()

    def test_digilocker_existing_account_takeover_prevention(self):
        """An attacker cannot hijack an existing DigiLocker user account without password."""
        masked_aadhaar = "XXXX-XXXX-9999"
        synthetic_email = f"aadhaar_{masked_aadhaar.replace('-', '')}@spaceloop.in".lower()

        with self.app.app_context():
            user = User.query.filter_by(email=synthetic_email).first()
            if not user:
                user = User(
                    name="Legit Citizen",
                    first_name="Legit",
                    last_name="Citizen",
                    email=synthetic_email,
                    role="seeker",
                    is_active=True,
                    is_aadhaar_verified=True,
                    aadhaar_masked=masked_aadhaar
                )
                user.set_password("CitizenPrivatePassword123!")
                db.session.add(user)
                db.session.commit()
            else:
                user.set_password("CitizenPrivatePassword123!")
                db.session.commit()

        # Attacker tries to authenticate as this Aadhaar without providing the correct password
        res_hijack = self.client.post("/api/v1/auth/digilocker", json={
            "aadhaar_number": "111122229999",
            "otp": "123456",
            "name": "Attacker Impersonator",
            "password": "WrongPassword!"
        })
        self.assertEqual(res_hijack.status_code, 401)
        self.assertFalse(res_hijack.get_json().get("success"))

        # With correct password -> authenticates
        res_valid = self.client.post("/api/v1/auth/digilocker", json={
            "aadhaar_number": "111122229999",
            "otp": "123456",
            "name": "Legit Citizen",
            "password": "CitizenPrivatePassword123!"
        })
        self.assertEqual(res_valid.status_code, 200)
        self.assertTrue(res_valid.get_json().get("success"))

    def test_production_secret_key_enforcement(self):
        """In production, running with default or missing SECRET_KEY must raise RuntimeError."""
        old_env = os.environ.get("FLASK_ENV")
        old_secret = os.environ.get("SECRET_KEY")
        try:
            os.environ["FLASK_ENV"] = "production"
            os.environ["SECRET_KEY"] = "spaceloop-dev-secret-key-change-in-prod-2026"
            with self.assertRaises(RuntimeError):
                Config.validate_production_keys()

            os.environ["SECRET_KEY"] = ""
            with self.assertRaises(RuntimeError):
                Config.validate_production_keys()
        finally:
            if old_env is not None:
                os.environ["FLASK_ENV"] = old_env
            else:
                os.environ.pop("FLASK_ENV", None)
            if old_secret is not None:
                os.environ["SECRET_KEY"] = old_secret
            else:
                os.environ.pop("SECRET_KEY", None)


if __name__ == "__main__":
    unittest.main()
