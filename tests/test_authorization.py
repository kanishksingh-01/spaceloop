import unittest
from app import create_app
from models import db, User, Space, Booking
from backend.modules.auth.permissions import authorize, Permission, has_permission, ForbiddenError


class TestAuthorization(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_public_routes_accessible_anonymously(self):
        """Public pages must remain open to all unauthenticated visitors."""
        public_endpoints = [
            "/",
            "/explore",
            "/calculator",
            "/how-it-works",
            "/auth/login",
            "/auth/register",
            "/space/1"
        ]
        for ep in public_endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Failed public endpoint {ep}: {res.status_code}")

    def test_protected_web_routes_redirect_anonymous(self):
        """Web views requiring auth must redirect anonymous users to login."""
        protected_views = [
            "/dashboard",
            "/profile",
            "/list-space",
            "/inquiries",
            "/verify"
        ]
        for view in protected_views:
            res = self.client.get(view)
            self.assertEqual(res.status_code, 302, f"Failed redirect check for {view}: {res.status_code}")
            self.assertIn("/auth/login", res.headers.get("Location", ""))

    def test_protected_api_routes_return_401_anonymous(self):
        """Protected API endpoints must reject anonymous requests with HTTP 401."""
        api_endpoints = [
            ("/api/v1/auth/me", "GET", None),
            ("/api/bookings", "POST", {"space_id": 1}),
            ("/api/spaces", "POST", {"title": "New Space"}),
            ("/api/inquiries", "POST", {"question": "Is WiFi available?"}),
            ("/api/inquiries", "GET", None),
        ]
        for ep, method, payload in api_endpoints:
            if method == "GET":
                res = self.client.get(ep, headers={"Accept": "application/json"})
            else:
                res = self.client.post(ep, json=payload, headers={"Accept": "application/json"})
            self.assertEqual(res.status_code, 401, f"Expected 401 for anonymous {method} {ep}, got {res.status_code}")

    def test_seeker_authenticated_session(self):
        """Seekers can access dashboard, profile, and inquiries."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "dev-seeker@spaceloop.local",
            "password": "password123"
        })
        self.assertEqual(login_res.status_code, 200)

        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)

        res_prof = self.client.get("/profile")
        self.assertEqual(res_prof.status_code, 200)

        res_inq = self.client.get("/inquiries")
        self.assertEqual(res_inq.status_code, 200)

    def test_host_authenticated_session(self):
        """Hosts can access host dashboard and space creation."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "dev-host@spaceloop.local",
            "password": "password123"
        })
        self.assertEqual(login_res.status_code, 200)

        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)

        res_list = self.client.get("/list-space")
        self.assertEqual(res_list.status_code, 200)

    def test_context_switching_preserves_identity(self):
        """Switching role toggles UI context without mutating authenticated database identity."""
        self.client.post("/api/v1/auth/login", json={
            "email": "dev-host@spaceloop.local",
            "password": "password123"
        })

        # Check initial context via /switch-role
        switch_res = self.client.post("/switch-role", data={"target_role": "seeker"})
        self.assertEqual(switch_res.status_code, 302)

        # Ensure user identity is still dev-host
        me_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json()["user"]["email"], "dev-host@spaceloop.local")

    def test_admin_permissions_boundary(self):
        """Admin users possess ADMIN_ACCESS; regular users are denied."""
        with self.app.app_context():
            admin_user = User.query.filter_by(email="dev-admin@spaceloop.local").first()
            seeker_user = User.query.filter_by(email="dev-seeker@spaceloop.local").first()
            host_user = User.query.filter_by(email="dev-host@spaceloop.local").first()

            self.assertTrue(has_permission(admin_user, Permission.ADMIN_ACCESS))
            self.assertFalse(has_permission(seeker_user, Permission.ADMIN_ACCESS))
            self.assertFalse(has_permission(host_user, Permission.ADMIN_ACCESS))

            # Admin can perform any action
            self.assertTrue(has_permission(admin_user, Permission.SPACE_DELETE))
            self.assertTrue(has_permission(admin_user, Permission.BOOKING_CANCEL))


if __name__ == "__main__":
    unittest.main()
