import unittest
from flask_wtf.csrf import generate_csrf
from app import create_app
from models import db, User


class TestSecurityControls(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = True
        self.client = self.app.test_client()

    def test_csrf_rejection_missing_token_on_web_post(self):
        """Web POST requests without CSRF token must be rejected with 400."""
        # Attempt login form post without csrf_token
        res = self.client.post("/auth/login", data={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"CSRF", res.data)

    def test_csrf_validation_passes_with_valid_token(self):
        """Web POST requests with valid CSRF token proceed through validation."""
        with self.client:
            # First fetch the login page to initialize CSRF in session
            get_res = self.client.get("/auth/login")
            self.assertEqual(get_res.status_code, 200)

            # Generate token in this request context
            with self.app.test_request_context():
                token = generate_csrf()

            post_res = self.client.post("/auth/login", data={
                "csrf_token": token,
                "email": "sunita@spaceloop.in",
                "password": "password123"
            })
            # Successfully authenticated, redirects to dashboard (302)
            self.assertEqual(post_res.status_code, 302)
            self.assertIn("/dashboard", post_res.headers.get("Location", ""))

    def test_api_v1_exempt_from_web_csrf(self):
        """REST API v1 endpoints are exempt from CSRF tokens (stateless / JSON API)."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])

    def test_cookie_security_flags(self):
        """Session cookies must include HttpOnly and SameSite protection."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        cookies = res.headers.getlist("Set-Cookie")
        self.assertTrue(len(cookies) > 0, "Expected session cookie to be set")

        session_cookie = None
        for c in cookies:
            if "session=" in c:
                session_cookie = c
                break

        self.assertIsNotNone(session_cookie, "session cookie not found in response headers")
        self.assertIn("HttpOnly", session_cookie)
        self.assertIn("SameSite=Lax", session_cookie)

    def test_generic_auth_error_consistency(self):
        """User enumeration prevention: identical errors returned for missing user vs bad password."""
        res_bad_pw = self.client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "completely_wrong_password"
        })
        self.assertEqual(res_bad_pw.status_code, 401)
        err1 = res_bad_pw.get_json()["error"]

        res_nonexistent = self.client.post("/api/v1/auth/login", json={
            "email": "nonexistent_987654@spaceloop.in",
            "password": "completely_wrong_password"
        })
        self.assertEqual(res_nonexistent.status_code, 401)
        err2 = res_nonexistent.get_json()["error"]

        self.assertEqual(err1, err2)
        self.assertEqual(err1, "Invalid email or password.")


if __name__ == "__main__":
    unittest.main()
