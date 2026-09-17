import unittest
import json
from app import create_app
from models import db, User
from backend.modules.auth.service import AuthService
from backend.modules.auth.password import hash_password, verify_password


class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_password_hashing_security(self):
        """Plaintext passwords must never be stored; check_password must verify."""
        with self.app.app_context():
            user = User.query.filter_by(email="sunita@spaceloop.in").first()
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password_hash, "password123")
            self.assertTrue(user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:"))
            self.assertTrue(user.check_password("password123"))
            self.assertFalse(user.check_password("wrongpassword"))

    def test_registration_success(self):
        """User registration creates account, assigns role, and hashes password."""
        unique_email = "test_register_user@example.com"
        with self.app.app_context():
            # Clean up if existed
            existing = User.query.filter_by(email=unique_email).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

        payload = {
            "first_name": "Test",
            "last_name": "User",
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

        with self.app.app_context():
            user = User.query.filter_by(email=unique_email).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "seeker")
            self.assertFalse(user.is_admin)
            self.assertTrue(user.check_password("ValidPassword123!"))

    def test_registration_duplicate_email(self):
        """Duplicate email registration is rejected."""
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
        self.assertIn("already exists", data["error"])

    def test_registration_weak_password(self):
        """Password failing complexity rules is rejected."""
        payload = {
            "first_name": "Weak",
            "last_name": "Pass",
            "email": "weak_pass@example.com",
            "password": "123",
            "confirm_password": "123",
            "role": "seeker"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("at least 8 characters", data["error"])

    def test_registration_mismatched_password(self):
        """Mismatched password and confirm_password are rejected."""
        payload = {
            "first_name": "Mismatch",
            "last_name": "Test",
            "email": "mismatch@example.com",
            "password": "ValidPassword123!",
            "confirm_password": "DifferentPassword123!",
            "role": "seeker"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("do not match", data["error"])

    def test_registration_admin_escalation_blocked(self):
        """Public registration cannot escalate to admin."""
        unique_email = "admin_attempt@example.com"
        with self.app.app_context():
            existing = User.query.filter_by(email=unique_email).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

        payload = {
            "first_name": "Admin",
            "last_name": "Hacker",
            "email": unique_email,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
            "role": "admin",
            "is_admin": True
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        with self.app.app_context():
            user = User.query.filter_by(email=unique_email).first()
            self.assertFalse(user.is_admin)
            self.assertNotEqual(user.role, "admin")

    def test_login_success(self):
        """Valid credentials establish an authenticated session."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["email"], "sunita@spaceloop.in")

        # Calling /api/v1/auth/me should return current user
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        self.assertTrue(me_data["authenticated"])
        self.assertEqual(me_data["user"]["email"], "sunita@spaceloop.in")

    def test_login_invalid_password(self):
        """Invalid password returns generic 401 error."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "incorrect_password"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid email or password.")

    def test_login_nonexistent_user(self):
        """Nonexistent email returns identical generic 401 error."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "doesnotexist_9999@spaceloop.in",
            "password": "some_password_123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid email or password.")

    def test_login_inactive_user_blocked(self):
        """Inactive accounts are denied authentication."""
        with self.app.app_context():
            user = User.query.filter_by(email="kabir@du.ac.in").first()
            user.is_active = False
            db.session.commit()

        res = self.client.post("/api/v1/auth/login", json={
            "email": "kabir@du.ac.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data["error"], "Invalid email or password.")

        # Restore
        with self.app.app_context():
            user = User.query.filter_by(email="kabir@du.ac.in").first()
            user.is_active = True
            db.session.commit()

    def test_logout_session_invalidation(self):
        """Logout revokes the session; subsequent protected calls fail."""
        # Login
        self.client.post("/api/v1/auth/login", json={
            "email": "aarav@iitd.ac.in",
            "password": "password123"
        })
        # Check active
        res1 = self.client.get("/api/v1/auth/me")
        self.assertEqual(res1.status_code, 200)

        # Logout
        res_logout = self.client.post("/api/v1/auth/logout")
        self.assertEqual(res_logout.status_code, 200)

        # Check me again - should be unauthenticated
        res2 = self.client.get("/api/v1/auth/me")
        self.assertEqual(res2.status_code, 401)

    def test_password_reset_flow(self):
        """Password reset token generation and consumption flow."""
        with self.app.app_context():
            _, msg, token = AuthService.request_password_reset("priya@coep.ac.in")
            self.assertTrue(bool(token))

            # Reset password
            success, r_msg = AuthService.reset_password(token, "NewPriyaPass123!", "NewPriyaPass123!")
            self.assertTrue(success)

            # Re-verifying reset with same token fails (single use)
            success_reuse, _ = AuthService.reset_password(token, "AnotherPass123!", "AnotherPass123!")
            self.assertFalse(success_reuse)

            # Check user can authenticate with new password
            user, err = AuthService.authenticate_user("priya@coep.ac.in", "NewPriyaPass123!")
            self.assertIsNotNone(user)
            self.assertEqual(err, "")

            # Reset back to default
            user.set_password("password123")
            db.session.commit()

    def test_email_verification_flow(self):
        """Email verification token validates the account."""
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
