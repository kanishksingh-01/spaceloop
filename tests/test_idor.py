import unittest
from app import create_app
from models import db, User, Space, Booking
from backend.modules.auth.permissions import authorize, Permission, has_permission, ForbiddenError


class TestIDORSecurity(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def tearDown(self):
        from space_ai import set_simulate_ai_failure
        set_simulate_ai_failure(False)

    # ==================================================
    # TEST 1 — Owner Can Access Own Resource
    # ==================================================
    def test_01_owner_can_access_own_resource(self):
        """Resource owners can access, view, and update their own spaces and bookings."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()

        # 1. Host Sunita accesses her own space printable QR pass
        self.client.post("/api/v1/auth/login", json={"email": "sunita@spaceloop.in", "password": "password123"})
        res_qr = self.client.get(f"/space/{sunita_space.id}/printable-qr")
        self.assertEqual(res_qr.status_code, 200)

        # 2. Host Sunita updates her own space via PUT
        res_put = self.client.put(f"/api/spaces/{sunita_space.id}", json={"title": "Updated Title By Sunita"})
        self.assertEqual(res_put.status_code, 200)
        self.assertTrue(res_put.get_json()["success"])

        # 3. Renter Aarav accesses his own booking via API and session view
        client_aarav = self.app.test_client()
        client_aarav.post("/api/v1/auth/login", json={"email": "aarav@iitd.ac.in", "password": "password123"})
        res_b = client_aarav.get(f"/api/booking/{aarav_booking.id}")
        self.assertEqual(res_b.status_code, 200)
        self.assertTrue(res_b.get_json()["success"])

        res_sess = client_aarav.get(f"/booking/{aarav_booking.id}/session")
        self.assertEqual(res_sess.status_code, 200)

    # ==================================================
    # TEST 2 — Different Authenticated User Cannot Access Private Resource
    # ==================================================
    def test_02_different_user_cannot_access_private_resource(self):
        """Authenticated User B cannot view private resources belonging to User A."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()

        # Login as Vikram (unrelated host)
        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})

        # Vikram cannot view Sunita's printable door pass
        res_qr = self.client.get(f"/space/{sunita_space.id}/printable-qr")
        self.assertEqual(res_qr.status_code, 302)
        self.assertIn("/auth/access-denied", res_qr.headers.get("Location", ""))

        # Login as Priya (unrelated seeker)
        client_priya = self.app.test_client()
        client_priya.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})

        # Priya cannot access Aarav's booking via API (403 Forbidden)
        res_b = client_priya.get(f"/api/booking/{aarav_booking.id}")
        self.assertEqual(res_b.status_code, 403)

        # Priya cannot access Aarav's session page (302 redirect)
        res_sess = client_priya.get(f"/booking/{aarav_booking.id}/session")
        self.assertEqual(res_sess.status_code, 302)
        self.assertIn("/auth/access-denied", res_sess.headers.get("Location", ""))

    # ==================================================
    # TEST 3 — Different User Cannot Modify Resource
    # ==================================================
    def test_03_different_user_cannot_modify_resource(self):
        """User B cannot modify User A's space or booking state."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()

        # Vikram attempts to edit Sunita's space via POST /edit and PUT
        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})

        res_post = self.client.post(f"/api/spaces/{sunita_space.id}/edit", json={"title": "Malicious Edit"})
        self.assertEqual(res_post.status_code, 403)

        res_put = self.client.put(f"/api/spaces/{sunita_space.id}", json={"title": "Malicious Edit"})
        self.assertEqual(res_put.status_code, 403)

        res_toggle = self.client.post(f"/api/spaces/{sunita_space.id}/toggle-status", json={})
        self.assertEqual(res_toggle.status_code, 403)

    # ==================================================
    # TEST 4 — Different User Cannot Delete Resource
    # ==================================================
    def test_04_different_user_cannot_delete_resource(self):
        """User B cannot delete User A's space listing."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()

        # Vikram attempts to delete Sunita's space
        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})
        res_del = self.client.delete(f"/api/spaces/{sunita_space.id}")
        self.assertEqual(res_del.status_code, 403)

        # Priya (seeker) attempts to delete Sunita's space
        client_priya = self.app.test_client()
        client_priya.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})
        res_del_priya = client_priya.delete(f"/api/spaces/{sunita_space.id}")
        self.assertEqual(res_del_priya.status_code, 403)

    # ==================================================
    # TEST 5 — Different User Cannot Cancel Another User's Booking
    # ==================================================
    def test_05_different_user_cannot_cancel_booking(self):
        """User B cannot cancel User A's booking."""
        with self.app.app_context():
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()

        # Priya attempts to cancel Aarav's booking via POST and DELETE
        self.client.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})

        res_cancel = self.client.post(f"/api/booking/{aarav_booking.id}/cancel")
        self.assertEqual(res_cancel.status_code, 403)

        res_del_b = self.client.delete(f"/api/booking/{aarav_booking.id}")
        self.assertEqual(res_del_b.status_code, 403)

    # ==================================================
    # TEST 6 — Host Cannot Access Another Host's Private Resources
    # ==================================================
    def test_06_host_cannot_access_another_host_private_resource(self):
        """Host B cannot access Host A's door pass or manage Host A's space."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})
        res = self.client.get(f"/space/{sunita_space.id}/printable-qr")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/auth/access-denied", res.headers.get("Location", ""))

    # ==================================================
    # TEST 7 — Student Cannot Perform Host-Only Operations
    # ==================================================
    def test_07_student_cannot_perform_host_only_operation(self):
        """A user without host capability cannot create spaces or edit another user's listing."""
        with self.app.app_context():
            student = User.query.filter_by(email="dev-seeker@spaceloop.local").first()
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()
            self.assertFalse(student.is_host)

        self.client.post("/api/v1/auth/login", json={"email": "dev-seeker@spaceloop.local", "password": "password123"})

        # Cannot POST to /api/spaces
        res_create = self.client.post("/api/spaces", json={
            "title": "Hacker Space",
            "category": "Studio",
            "address": "IIT Campus",
            "price_hourly": 50.0
        })
        self.assertEqual(res_create.status_code, 403)
        self.assertIn("Host capability", res_create.get_json()["error"])

        # Cannot edit another user's space on /list-space?edit=id
        res_edit = self.client.get(f"/list-space?edit={sunita_space.id}")
        self.assertEqual(res_edit.status_code, 302)
        self.assertIn("/dashboard", res_edit.headers.get("Location", ""))

    # ==================================================
    # TEST 8 — Non-Admin Cannot Access Admin Functionality
    # ==================================================
    def test_08_non_admin_cannot_access_admin_functionality(self):
        """Regular users are forbidden from calling administrative endpoints."""
        # Seeker attempt
        self.client.post("/api/v1/auth/login", json={"email": "aarav@iitd.ac.in", "password": "password123"})
        res_seeker = self.client.post("/api/dev/toggle-ai-simulation")
        self.assertEqual(res_seeker.status_code, 403)

        # Host attempt
        client_host = self.app.test_client()
        client_host.post("/api/v1/auth/login", json={"email": "sunita@spaceloop.in", "password": "password123"})
        res_host = client_host.post("/api/dev/toggle-ai-simulation")
        self.assertEqual(res_host.status_code, 403)

        # Admin access succeeds
        client_admin = self.app.test_client()
        client_admin.post("/api/v1/auth/login", json={"email": "dev-admin@spaceloop.local", "password": "password123"})
        res_admin = client_admin.post("/api/dev/toggle-ai-simulation", json={})
        self.assertEqual(res_admin.status_code, 200)
        # Toggle back to False
        client_admin.post("/api/dev/toggle-ai-simulation", json={})

    # ==================================================
    # TEST 9 — Client-Supplied owner_id Cannot Bypass Ownership
    # ==================================================
    def test_09_client_supplied_owner_id_cannot_bypass_ownership(self):
        """Client-supplied owner_id in request body is ignored; server enforces authenticated user."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            vikram = User.query.filter_by(email="vikram@spaceloop.in").first()

        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})

        # Vikram attempts to create a space attributing ownership to Sunita
        res = self.client.post("/api/spaces", json={
            "owner_id": sunita.id,
            "title": "Vikram Space Spoofing Sunita",
            "category": "Studio",
            "address": "Indiranagar, Bengaluru",
            "price_hourly": 60.0
        })
        self.assertEqual(res.status_code, 201)
        created_space = res.get_json()
        self.assertEqual(created_space["owner_id"], vikram.id)
        self.assertNotEqual(created_space["owner_id"], sunita.id)

        # Cleanup
        with self.app.app_context():
            sp = Space.query.get(created_space["id"])
            if sp:
                db.session.delete(sp)
                db.session.commit()

    # ==================================================
    # TEST 10 — Client-Supplied Role Cannot Elevate Privileges
    # ==================================================
    def test_10_client_supplied_role_cannot_elevate_privileges(self):
        """Client cannot elevate privileges by passing role=admin or is_admin=True."""
        self.client.post("/api/v1/auth/login", json={"email": "aarav@iitd.ac.in", "password": "password123"})
        res = self.client.post("/api/dev/toggle-ai-simulation", json={"role": "admin", "is_admin": True})
        self.assertEqual(res.status_code, 403)

    # ==================================================
    # TEST 11 — URL ID Manipulation Blocked
    # ==================================================
    def test_11_url_id_manipulation_blocked(self):
        """Changing resource IDs in URLs from A to B is blocked."""
        with self.app.app_context():
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})
        # Priya modifies URL to access Aarav's session page
        res = self.client.get(f"/booking/{aarav_booking.id}/session")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/auth/access-denied", res.headers.get("Location", ""))

    # ==================================================
    # TEST 12 — API ID Manipulation Blocked
    # ==================================================
    def test_12_api_id_manipulation_blocked(self):
        """Manipulating resource IDs in API request bodies is rejected."""
        with self.app.app_context():
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})
        # Priya tries to check in to Aarav's booking
        res = self.client.post(f"/api/booking/{aarav_booking.id}/check-in", json={
            "qr_token": "SOME_QR",
            "lat": 28.5450,
            "lng": 77.1926
        })
        self.assertEqual(res.status_code, 403)

    # ==================================================
    # TEST 13 — File ID / Printable QR Manipulation Blocked
    # ==================================================
    def test_13_file_id_manipulation_blocked(self):
        """Attempt to retrieve another user's protected door QR pass by ID is rejected."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})
        res = self.client.get(f"/space/{sunita_space.id}/printable-qr")
        # Priya has no booking on Sunita's space and is not owner -> 302 redirect
        self.assertEqual(res.status_code, 302)
        self.assertIn("/auth/access-denied", res.headers.get("Location", ""))

    # ==================================================
    # TEST 14 — Unauthenticated Access Blocked
    # ==================================================
    def test_14_unauthenticated_access_blocked(self):
        """Unauthenticated requests to sensitive API and web endpoints are rejected."""
        # Unauthenticated API calls return 401
        self.assertEqual(self.client.get("/api/booking/1").status_code, 401)
        self.assertEqual(self.client.delete("/api/spaces/1").status_code, 401)
        self.assertEqual(self.client.post("/api/booking/1/check-in").status_code, 401)
        self.assertEqual(self.client.post("/api/booking/1/check-out").status_code, 401)
        self.assertEqual(self.client.post("/api/booking/1/cancel").status_code, 401)

        # Unauthenticated web views return 302 redirect to login
        res_web = self.client.get("/dashboard")
        self.assertEqual(res_web.status_code, 302)
        self.assertIn("/auth/login", res_web.headers.get("Location", ""))

    # ==================================================
    # PHASE 17 MANUAL ATTACK SIMULATIONS
    # ==================================================
    def test_attack_a_edit_other_space_by_changing_id(self):
        """ATTACK A: User B attempts to edit Space A by changing space ID."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})
        res = self.client.post(f"/api/spaces/{sunita_space.id}/edit", json={"title": "Attacked Title"})
        self.assertEqual(res.status_code, 403)

    def test_attack_b_access_other_booking_by_changing_id(self):
        """ATTACK B: User B attempts to access User A's booking by changing booking ID."""
        with self.app.app_context():
            aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
            aarav_booking = Booking.query.filter_by(renter_id=aarav.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "priya@coep.ac.in", "password": "password123"})
        res = self.client.get(f"/api/booking/{aarav_booking.id}")
        self.assertEqual(res.status_code, 403)

    def test_attack_c_modify_owner_id_in_request_body(self):
        """ATTACK C: User B modifies owner_id in request body during space creation."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            vikram = User.query.filter_by(email="vikram@spaceloop.in").first()

        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})
        res = self.client.post("/api/spaces", json={
            "owner_id": sunita.id,
            "title": "Attack C Space",
            "category": "Studio",
            "address": "Koramangala",
            "price_hourly": 75.0
        })
        self.assertEqual(res.status_code, 201)
        created = res.get_json()
        self.assertEqual(created["owner_id"], vikram.id)
        with self.app.app_context():
            sp = Space.query.get(created["id"])
            if sp:
                db.session.delete(sp)
                db.session.commit()

    def test_attack_d_non_admin_attempts_admin_endpoint(self):
        """ATTACK D: Non-admin attempts an admin endpoint."""
        self.client.post("/api/v1/auth/login", json={"email": "aarav@iitd.ac.in", "password": "password123"})
        res = self.client.post("/api/dev/toggle-ai-simulation")
        self.assertEqual(res.status_code, 403)

    def test_attack_e_student_attempts_host_only_endpoint(self):
        """ATTACK E: Student attempts a host-only endpoint."""
        self.client.post("/api/v1/auth/login", json={"email": "dev-seeker@spaceloop.local", "password": "password123"})
        res = self.client.post("/api/spaces", json={
            "title": "Student Studio",
            "category": "Studio",
            "address": "Delhi",
            "price_hourly": 50.0
        })
        self.assertEqual(res.status_code, 403)

    def test_attack_f_user_requests_other_private_document(self):
        """ATTACK F: User B requests User A's private door QR pass."""
        with self.app.app_context():
            sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
            sunita_space = Space.query.filter_by(owner_id=sunita.id).first()

        self.client.post("/api/v1/auth/login", json={"email": "vikram@spaceloop.in", "password": "password123"})
        res = self.client.get(f"/space/{sunita_space.id}/printable-qr")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/auth/access-denied", res.headers.get("Location", ""))

    def test_attack_g_unauthenticated_user_attempts_protected_endpoint(self):
        """ATTACK G: Unauthenticated user attempts protected endpoint."""
        res = self.client.get("/api/booking/1")
        self.assertEqual(res.status_code, 401)
        res_del = self.client.delete("/api/spaces/1")
        self.assertEqual(res_del.status_code, 401)


if __name__ == "__main__":
    unittest.main()
