import unittest
import json
from app import create_app
from models import db, User
from backend.modules.auth.email_service import DevelopmentEmailAdapter
from config import Config


class TestAuditSecurityFixes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_finding1_password_overwrite_and_master_passwords_blocked(self):
        """Finding 1: Prevent arbitrary password overwrite on login & block master bypass passwords."""
        test_email = "secure_victim_user@example.com"
        with self.app.app_context():
            user = User.query.filter_by(email=test_email).first()
            if not user:
                user = User(
                    name="Victim User",
                    first_name="Victim",
                    last_name="User",
                    email=test_email,
                    role="seeker",
                    is_active=True
                )
                db.session.add(user)
            user.set_password("RealLegitPassword123!")
            db.session.commit()

            orig_hash = user.password_hash

        # 1. Attacker attempts login with 4+ char arbitrary password
        res = self.client.post("/api/v1/auth/login", json={
            "email": test_email,
            "password": "AttackerHackedPassword!"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid", data["error"])

        # Verify password hash was NOT overwritten in database
        with self.app.app_context():
            user = User.query.filter_by(email=test_email).first()
            self.assertEqual(user.password_hash, orig_hash)
            self.assertTrue(user.check_password("RealLegitPassword123!"))
            self.assertFalse(user.check_password("AttackerHackedPassword!"))

        # 2. Attacker attempts master bypass passwords
        master_passwords = ["password123", "Host@1234", "Student@1234", "Admin@1234", "demo1234", "SpaceLoop@123"]
        for bypass_pwd in master_passwords:
            res = self.client.post("/api/v1/auth/login", json={
                "email": test_email,
                "password": bypass_pwd
            })
            self.assertEqual(res.status_code, 401, f"Bypass password {bypass_pwd} should be rejected")

    def test_finding2_switch_user_route_eliminated(self):
        """Finding 2: /switch-user/<id> endpoint must return 404 (completely eliminated)."""
        res_get = self.client.get("/switch-user/1")
        self.assertEqual(res_get.status_code, 404)

        res_post = self.client.post("/switch-user/1")
        self.assertEqual(res_post.status_code, 404)

    def test_finding3_demo_switch_routes_eliminated(self):
        """Finding 3: All demo-switch endpoints must return 404 (completely eliminated)."""
        endpoints = [
            "/auth/demo-switch/admin",
            "/auth/demo-switch/host",
            "/auth/demo-switch/seeker",
            "/api/v1/auth/demo-switch/admin",
            "/api/v1/auth/demo-switch/host",
            "/api/v1/auth/demo-switch/seeker"
        ]
        for ep in endpoints:
            res_get = self.client.get(ep)
            self.assertEqual(res_get.status_code, 404, f"{ep} GET should be 404")
            res_post = self.client.post(ep)
            self.assertEqual(res_post.status_code, 404, f"{ep} POST should be 404")

    def test_finding4_config_secret_key_security(self):
        """Finding 4: Config.SECRET_KEY must be defined and secure."""
        self.assertTrue(bool(Config.SECRET_KEY))
        self.assertGreaterEqual(len(Config.SECRET_KEY), 16)

    def test_finding5_digilocker_and_sso_random_passwords(self):
        """Finding 5: DigiLocker & SSO users must not have static backdoor passwords."""
        # Test DigiLocker registration
        dl_payload = {
            "name": "Audit Aadhaar Test",
            "aadhaar_number": "123456789012",
            "otp": "654321",
            "role": "seeker"
        }
        res = self.client.post("/api/v1/auth/digilocker", json=dl_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        dl_email = data["user"]["email"]

        # Verify account CANNOT be logged into with the old static password "DigiLockerAuth2026!"
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": dl_email,
            "password": "DigiLockerAuth2026!"
        })
        self.assertEqual(login_res.status_code, 401)

        # Test Student SSO registration
        sso_email = "student_audit_test@iitd.ac.in"
        sso_payload = {
            "college_email": sso_email,
            "name": "Audit Student",
            "college_name": "IIT Delhi",
            "student_id": "2023CSB999"
        }
        res_sso = self.client.post("/api/v1/auth/student-sso", json=sso_payload)
        self.assertEqual(res_sso.status_code, 200)

        # Verify account CANNOT be logged into with the old static password "StudentSSO2026!"
        login_res2 = self.client.post("/api/v1/auth/login", json={
            "email": sso_email,
            "password": "StudentSSO2026!"
        })
        self.assertEqual(login_res2.status_code, 401)

    def test_finding6_anti_csrf_custom_header_protection(self):
        """Finding 6: State-changing API calls with active session require custom anti-CSRF header."""
        # Create non-testing app instance to test middleware enforcement
        prod_app = create_app()
        prod_app.config["TESTING"] = False
        client = prod_app.test_client()

        # Log in as test host
        with prod_app.app_context():
            host = User.query.filter_by(email="sunita@spaceloop.in").first()
            if not host:
                host = User(name="Sunita", email="sunita@spaceloop.in", role="host", is_host_verified=True, is_active=True)
                host.set_password("password123")
                db.session.add(host)
                db.session.commit()

        login_res = client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        }, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(login_res.status_code, 200)

        # Now send state-changing API request WITHOUT custom header -> should return 403 Forbidden
        post_without_header = client.post("/api/spaces", json={"title": "Unauthorized CSRF Space"})
        self.assertEqual(post_without_header.status_code, 403)
        self.assertIn("CSRF", post_without_header.get_json()["error"])

        # Send WITH custom header -> passes anti-CSRF check
        post_with_header = client.post("/api/spaces", json={"title": "Legit Space"}, headers={
            "X-Requested-With": "XMLHttpRequest"
        })
        # Note: may return 400 due to space validation fields, but must NOT return 403 CSRF error
        self.assertNotEqual(post_with_header.status_code, 403)

    def test_finding7_cors_origin_protection(self):
        """Finding 7: Insecure arbitrary origin reflection is blocked."""
        # 1. Malicious untrusted origin
        evil_origin = "https://malicious-attacker.com"
        res = self.client.options("/api/v1/auth/me", headers={"Origin": evil_origin})
        # Access-Control-Allow-Origin must NOT reflect evil origin
        self.assertNotEqual(res.headers.get("Access-Control-Allow-Origin"), evil_origin)

        # 2. Whitelisted origin
        trusted_origin = "http://localhost:3000"
        res_trusted = self.client.options("/api/v1/auth/me", headers={"Origin": trusted_origin})
        self.assertEqual(res_trusted.headers.get("Access-Control-Allow-Origin"), trusted_origin)
        self.assertEqual(res_trusted.headers.get("Access-Control-Allow-Credentials"), "true")

    def test_finding10_password_reset_flow_and_email_delivery(self):
        """Finding 10: Password reset endpoints exist and dispatch via EmailService."""
        reset_email = "reset_user_test@example.com"
        with self.app.app_context():
            u = User.query.filter_by(email=reset_email).first()
            if not u:
                u = User(name="Reset User", email=reset_email, role="seeker", is_active=True)
                u.set_password("OldPassword123!")
                db.session.add(u)
            else:
                u.set_password("OldPassword123!")
            db.session.commit()

        # 1. Request password reset
        DevelopmentEmailAdapter.last_sent = None
        req_res = self.client.post("/api/v1/auth/forgot-password", json={"email": reset_email})
        self.assertEqual(req_res.status_code, 200)
        self.assertTrue(req_res.get_json()["success"])

        # Verify email was dispatched by adapter
        self.assertIsNotNone(DevelopmentEmailAdapter.last_sent)
        self.assertEqual(DevelopmentEmailAdapter.last_sent["to"], reset_email)
        body = DevelopmentEmailAdapter.last_sent["body"]
        token = body.split("/auth/reset-password/")[1].split()[0]
        self.assertTrue(len(token) > 20)

        # 2. Reset password using token
        reset_res = self.client.post("/api/v1/auth/reset-password", json={
            "token": token,
            "password": "NewSecurePassword456!",
            "confirm_password": "NewSecurePassword456!"
        })
        self.assertEqual(reset_res.status_code, 200)
        self.assertTrue(reset_res.get_json()["success"])

        # 3. Verify user can log in with new password
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": reset_email,
            "password": "NewSecurePassword456!"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
