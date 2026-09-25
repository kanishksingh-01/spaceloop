"""
SpaceLoop Multi-Factor Authentication (MFA) Comprehensive Test Suite
Verifies:
1. Email verification gate blocks unverified users from MFA enrollment.
2. Setup generation (QR code, secret, setup token) for verified users.
3. Setup verification rejects invalid 6-digit TOTP code.
4. Setup verification succeeds with valid TOTP code (activates MFA & generates 10 recovery codes).
5. TOTP secret is encrypted at rest and never leaked in APIs.
6. Normal login succeeds directly for non-MFA users without challenge.
7. MFA user receives MFA challenge token without session establishment.
8. MFA challenge fails with invalid TOTP code.
9. MFA challenge succeeds with valid TOTP code.
10. MFA challenge succeeds with valid recovery code and marks it as used.
11. Used recovery code cannot be reused.
12. Rate limiting enforced on MFA challenge endpoint.
13. Disabling MFA fails with wrong password.
14. Disabling MFA succeeds with password + TOTP confirmation, purging secrets and recovery codes.
"""
import unittest
import json
import pyotp
from app import create_app
from models import db, User, MFARecoveryCode
from backend.modules.auth.mfa import (
    encrypt_totp_secret,
    decrypt_totp_secret,
    generate_totp_secret,
    hash_recovery_code
)


class TestMultiFactorAuthentication(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def _create_user(self, email, password="TestPassword123!", is_email_verified=True, mfa_enabled=False):
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    name="Test MFA User",
                    first_name="Test",
                    last_name="MFA",
                    email=email,
                    role="seeker",
                    is_active=True
                )
                db.session.add(user)
            user.set_password(password)
            user.is_email_verified = is_email_verified
            user.mfa_enabled = mfa_enabled
            if not mfa_enabled:
                user.totp_secret = None
                MFARecoveryCode.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            return user.id

    def test_01_email_verification_gate_blocks_enrollment(self):
        """Unverified user attempting to setup MFA is rejected with 403 and email_verification_required."""
        email = "unverified_mfa_user@example.com"
        pwd = "SafePassword123!"
        uid = self._create_user(email, password=pwd, is_email_verified=False, mfa_enabled=False)

        # 1. Unverified user attempting login must be blocked with 403
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        self.assertEqual(login_res.status_code, 403)
        self.assertTrue(login_res.get_json()["email_verification_required"])

        # 2. Even if an unverified user has an existing session, setup is blocked
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(uid)
            sess["_fresh"] = True

        # Attempt to initiate MFA setup
        setup_res = self.client.post("/api/v1/auth/mfa/setup")
        self.assertEqual(setup_res.status_code, 403)
        data = setup_res.get_json()
        self.assertFalse(data["success"])
        self.assertTrue(data.get("email_verification_required"))
        self.assertIn("Email verification is required", data.get("error", ""))

        # Verify no secret was saved in database
        with self.app.app_context():
            u = User.query.get(uid)
            self.assertFalse(u.mfa_enabled)
            self.assertIsNone(u.totp_secret)

    def test_02_setup_initiation_succeeds_for_verified_user(self):
        """Verified user receives secret, QR data URI, otpauth URI, and setup token."""
        email = "verified_mfa_user@example.com"
        pwd = "SafePassword123!"
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=False)

        # Log in
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        self.assertEqual(login_res.status_code, 200)

        # Request setup
        setup_res = self.client.post("/api/v1/auth/mfa/setup")
        self.assertEqual(setup_res.status_code, 200)
        data = setup_res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["secret"])
        self.assertTrue(data["qr_code"].startswith("data:image/png;base64,"))
        self.assertTrue(data["otpauth_uri"].startswith("otpauth://totp/"))
        self.assertTrue(data["setup_token"])

        # User MFA state in database is still NOT enabled until verification
        with self.app.app_context():
            u = User.query.get(uid)
            self.assertFalse(u.mfa_enabled)
            self.assertIsNone(u.totp_secret)

    def test_03_setup_verification_fails_with_invalid_totp(self):
        """MFA setup verification fails with incorrect 6-digit code."""
        email = "invalid_code_setup@example.com"
        pwd = "SafePassword123!"
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=False)

        self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        setup_res = self.client.post("/api/v1/auth/mfa/setup")
        setup_data = setup_res.get_json()

        verify_res = self.client.post("/api/v1/auth/mfa/verify-setup", json={
            "setup_token": setup_data["setup_token"],
            "code": "000000"
        })
        self.assertEqual(verify_res.status_code, 400)
        data = verify_res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid", data.get("error", ""))

        with self.app.app_context():
            u = User.query.get(uid)
            self.assertFalse(u.mfa_enabled)
            self.assertIsNone(u.totp_secret)

    def test_04_setup_verification_succeeds_with_valid_totp(self):
        """MFA setup verification succeeds with valid code, activates MFA, and yields 10 recovery codes."""
        email = "valid_setup_user@example.com"
        pwd = "SafePassword123!"
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=False)

        self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        setup_res = self.client.post("/api/v1/auth/mfa/setup")
        setup_data = setup_res.get_json()

        secret = setup_data["secret"]
        valid_code = pyotp.TOTP(secret).now()

        verify_res = self.client.post("/api/v1/auth/mfa/verify-setup", json={
            "setup_token": setup_data["setup_token"],
            "code": valid_code
        })
        self.assertEqual(verify_res.status_code, 200)
        data = verify_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data.get("recovery_codes", [])), 10)

        # Check database: mfa_enabled == True, totp_secret is encrypted, 10 recovery code hashes stored
        with self.app.app_context():
            u = User.query.get(uid)
            self.assertTrue(u.mfa_enabled)
            self.assertIsNotNone(u.totp_secret)
            self.assertNotEqual(u.totp_secret, secret)  # Must be encrypted!
            self.assertEqual(decrypt_totp_secret(u.totp_secret), secret)

            codes = MFARecoveryCode.query.filter_by(user_id=uid).all()
            self.assertEqual(len(codes), 10)
            for c in codes:
                self.assertFalse(c.used)
                self.assertIsNone(c.used_at)

    def test_05_secret_security_encrypted_at_rest_and_never_leaked(self):
        """Secrets are encrypted at rest and omitted from user profile endpoints."""
        email = "leaks_audit_user@example.com"
        pwd = "SafePassword123!"
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=False)

        self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        setup_data = self.client.post("/api/v1/auth/mfa/setup").get_json()
        code = pyotp.TOTP(setup_data["secret"]).now()
        self.client.post("/api/v1/auth/mfa/verify-setup", json={
            "setup_token": setup_data["setup_token"],
            "code": code
        })

        # Call profile endpoint
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        user_dict = me_data["user"]

        self.assertTrue(user_dict["mfa_enabled"])
        self.assertNotIn("totp_secret", user_dict)
        self.assertNotIn("secret", user_dict)
        self.assertNotIn("recovery_codes", user_dict)

    def test_06_normal_login_succeeds_for_non_mfa_user(self):
        """Existing non-MFA user logs in directly with single factor (no mfa_required)."""
        email = "single_factor_user@example.com"
        pwd = "SafePassword123!"
        self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=False)

        res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data.get("mfa_required", False))
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], email)

    def test_07_mfa_user_receives_challenge_token_without_session(self):
        """MFA-enabled user submitting correct password receives challenge token, not logged in yet."""
        email = "mfa_challenge_user@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)

        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            db.session.commit()

        # Step 1: Login with credentials using fresh client
        unauth_client = self.app.test_client()
        login_res = unauth_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        self.assertEqual(login_res.status_code, 200)
        data = login_res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data.get("mfa_required"))
        self.assertTrue(data.get("mfa_token"))
        self.assertNotIn("user", data)

        # Verify that unauth_client is NOT logged in yet
        me_res = unauth_client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 401)

    def test_08_mfa_challenge_fails_with_invalid_totp(self):
        """Submitting wrong 6-digit code for MFA challenge is rejected."""
        email = "mfa_wrong_code@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)
        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            db.session.commit()

        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        mfa_token = login_res.get_json()["mfa_token"]

        verify_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": "112233"
        })
        self.assertEqual(verify_res.status_code, 400)
        data = verify_res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid", data.get("error", ""))

    def test_09_mfa_challenge_succeeds_with_valid_totp(self):
        """Submitting valid 6-digit TOTP completes login and establishes authenticated session."""
        email = "mfa_login_success@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)
        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            db.session.commit()

        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        mfa_token = login_res.get_json()["mfa_token"]

        valid_code = pyotp.TOTP(raw_secret).now()
        verify_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": valid_code
        })
        self.assertEqual(verify_res.status_code, 200)
        data = verify_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["email"], email)

        # Verify session is now authenticated
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 200)

    def test_10_mfa_challenge_succeeds_with_recovery_code_and_burns_it(self):
        """Recovery code completes login and is marked as used."""
        email = "mfa_recovery_user@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)

        recovery_plain = "ABCD-1234"
        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            MFARecoveryCode.query.filter_by(user_id=uid).delete()
            db.session.add(MFARecoveryCode(
                user_id=uid,
                code_hash=hash_recovery_code(recovery_plain),
                used=False
            ))
            db.session.commit()

        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        mfa_token = login_res.get_json()["mfa_token"]

        verify_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "recovery_code": recovery_plain
        })
        self.assertEqual(verify_res.status_code, 200)
        data = verify_res.get_json()
        self.assertTrue(data["success"])

        # Assert recovery code in DB is marked used
        with self.app.app_context():
            rc = MFARecoveryCode.query.filter_by(user_id=uid).first()
            self.assertTrue(rc.used)
            self.assertIsNotNone(rc.used_at)

    def test_11_used_recovery_code_cannot_be_reused(self):
        """Reusing an already burned recovery code fails."""
        email = "mfa_reused_code@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)

        recovery_plain = "EFGH-5678"
        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            MFARecoveryCode.query.filter_by(user_id=uid).delete()
            db.session.add(MFARecoveryCode(
                user_id=uid,
                code_hash=hash_recovery_code(recovery_plain),
                used=True  # Already used!
            ))
            db.session.commit()

        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        mfa_token = login_res.get_json()["mfa_token"]

        verify_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "recovery_code": recovery_plain
        })
        self.assertEqual(verify_res.status_code, 400)
        data = verify_res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid or already used", data.get("error", ""))

    def test_12_mfa_challenge_rate_limiting(self):
        """MFA challenge endpoint enforces rate limits on brute force attacks."""
        email = "rate_limit_mfa@example.com"
        pwd = "SafePassword123!"
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)
        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(generate_totp_secret())
            db.session.commit()

        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        mfa_token = login_res.get_json()["mfa_token"]

        hit_429 = False
        for _ in range(8):
            res = self.client.post("/api/v1/auth/mfa/verify", json={
                "mfa_token": mfa_token,
                "code": "000000"
            })
            if res.status_code == 429:
                hit_429 = True
                break
        self.assertTrue(hit_429, "Rate limiter should trigger 429 after 5 requests per minute.")

    def test_13_disable_mfa_requires_correct_password(self):
        """Disabling MFA fails when submitting an incorrect password."""
        email = "disable_wrong_pwd@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)
        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            db.session.commit()

        # Log in session for disable call (simulate authenticated session)
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(uid)

        code = pyotp.TOTP(raw_secret).now()
        res = self.client.post("/api/v1/auth/mfa/disable", json={
            "password": "WrongPassword!",
            "code": code
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Incorrect", data.get("error", ""))

        with self.app.app_context():
            u = User.query.get(uid)
            self.assertTrue(u.mfa_enabled)

    def test_14_disable_mfa_purges_secret_and_recovery_codes(self):
        """Disabling MFA with valid password + code removes totp_secret and all recovery codes."""
        email = "disable_success@example.com"
        pwd = "SafePassword123!"
        raw_secret = generate_totp_secret()
        uid = self._create_user(email, password=pwd, is_email_verified=True, mfa_enabled=True)

        with self.app.app_context():
            u = User.query.get(uid)
            u.totp_secret = encrypt_totp_secret(raw_secret)
            db.session.add(MFARecoveryCode(user_id=uid, code_hash=hash_recovery_code("CODE-1111"), used=False))
            db.session.add(MFARecoveryCode(user_id=uid, code_hash=hash_recovery_code("CODE-2222"), used=False))
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(uid)

        code = pyotp.TOTP(raw_secret).now()
        res = self.client.post("/api/v1/auth/mfa/disable", json={
            "password": pwd,
            "code": code
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["user"]["mfa_enabled"])

        # Check database: mfa_enabled == False, totp_secret is None, recovery codes deleted
        with self.app.app_context():
            u = User.query.get(uid)
            self.assertFalse(u.mfa_enabled)
            self.assertIsNone(u.totp_secret)
            codes = MFARecoveryCode.query.filter_by(user_id=uid).all()
            self.assertEqual(len(codes), 0)


if __name__ == "__main__":
    unittest.main()
