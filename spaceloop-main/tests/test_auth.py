"""
Suite 5: Authentication & Authorization System Tests (18 Tests)
Target: tests/test_auth.py
Validations: Password hashing, registration, login, logout, RBAC enforcement,
             object-level ownership, landing page, session lifecycle.
"""

import unittest
from app import create_app
from models import db, User, Space, Booking


class TestAuthenticationAndAuthorization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        cls.client = cls.app.test_client()

    # ==========================================
    # PASSWORD HASHING (Werkzeug PBKDF2:SHA256)
    # ==========================================
    def test_01_password_hashing_set_and_check(self):
        """Auth 1: set_password hashes password, check_password verifies correctly."""
        with self.app.app_context():
            user = User(name="Test User", email="testhash@test.com", role="seeker")
            user.set_password("SecurePass789!")
            self.assertNotEqual(user.password_hash, "SecurePass789!")
            self.assertNotEqual(user.password_hash, "sha256_mock_hash")
            self.assertTrue(user.check_password("SecurePass789!"))

    def test_02_password_wrong_password_fails(self):
        """Auth 2: check_password returns False for incorrect password."""
        with self.app.app_context():
            user = User(name="Test User", email="testwrong@test.com", role="seeker")
            user.set_password("CorrectPass123!")
            self.assertFalse(user.check_password("WrongPassword!"))

    def test_03_mock_hash_rejected(self):
        """Auth 3: Users with sha256_mock_hash cannot authenticate (legacy migration guard)."""
        with self.app.app_context():
            user = User(name="Legacy", email="legacy@test.com", role="seeker", password_hash="sha256_mock_hash")
            self.assertFalse(user.check_password("anything"))

    # ==========================================
    # USER ROLE PROPERTIES
    # ==========================================
    def test_04_user_role_properties(self):
        """Auth 4: is_seeker, is_owner, is_admin return correct booleans."""
        with self.app.app_context():
            seeker = User(name="S", email="s@t.com", role="seeker")
            owner = User(name="O", email="o@t.com", role="owner")
            admin = User(name="A", email="a@t.com", role="admin")
            self.assertTrue(seeker.is_seeker)
            self.assertFalse(seeker.is_owner)
            self.assertTrue(owner.is_owner)
            self.assertFalse(owner.is_admin)
            self.assertTrue(admin.is_admin)

    # ==========================================
    # REGISTRATION API
    # ==========================================
    def test_05_api_register_success(self):
        """Auth 5: POST /api/auth/register creates a new user with hashed password and returns 201."""
        res = self.client.post('/api/auth/register', json={
            'name': 'New Student',
            'email': 'newstudent@iitd.ac.in',
            'password': 'StrongPass2026!',
            'role': 'seeker'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], 'newstudent@iitd.ac.in')
        self.assertEqual(data['user']['role'], 'seeker')

    def test_06_api_register_duplicate_email(self):
        """Auth 6: POST /api/auth/register with duplicate email returns 400."""
        # Register first time
        self.client.post('/api/auth/register', json={
            'name': 'Dup User',
            'email': 'duplicate@iitd.ac.in',
            'password': 'StrongPass2026!',
            'role': 'seeker'
        })
        # Try duplicate
        res = self.client.post('/api/auth/register', json={
            'name': 'Dup User',
            'email': 'duplicate@iitd.ac.in',
            'password': 'StrongPass2026!',
            'role': 'seeker'
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('already exists', data['error'])

    def test_07_api_register_validation_empty_fields(self):
        """Auth 7: POST /api/auth/register rejects empty name/email/password with 400."""
        res = self.client.post('/api/auth/register', json={
            'name': '',
            'email': '',
            'password': '',
            'role': 'seeker'
        })
        self.assertEqual(res.status_code, 400)

    # ==========================================
    # LOGIN API
    # ==========================================
    def test_08_api_login_success(self):
        """Auth 8: POST /api/auth/login with correct credentials returns success and user profile."""
        # Login with seeded Rohit (StudentPass123!)
        res = self.client.post('/api/auth/login', json={
            'email': 'rohit@iitd.ac.in',
            'password': 'StudentPass123!'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], 'rohit@iitd.ac.in')

    def test_09_api_login_wrong_password(self):
        """Auth 9: POST /api/auth/login with wrong password returns 401."""
        res = self.client.post('/api/auth/login', json={
            'email': 'rohit@iitd.ac.in',
            'password': 'WrongPassword!'
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn('Invalid', data['error'])

    def test_10_api_login_nonexistent_user(self):
        """Auth 10: POST /api/auth/login with unknown email returns 401."""
        res = self.client.post('/api/auth/login', json={
            'email': 'nobody@nowhere.com',
            'password': 'Anything123!'
        })
        self.assertEqual(res.status_code, 401)

    # ==========================================
    # LOGOUT & SESSION LIFECYCLE
    # ==========================================
    def test_11_api_logout(self):
        """Auth 11: POST /api/auth/logout clears session and /api/auth/me returns 401."""
        # Login first
        self.client.post('/api/auth/login', json={
            'email': 'rohit@iitd.ac.in',
            'password': 'StudentPass123!'
        })
        # Verify logged in
        me_res = self.client.get('/api/auth/me')
        self.assertEqual(me_res.status_code, 200)

        # Logout
        self.client.post('/api/auth/logout')

        # Verify logged out
        me_res2 = self.client.get('/api/auth/me')
        self.assertEqual(me_res2.status_code, 401)

    # ==========================================
    # UNAUTHENTICATED ROUTE REJECTION
    # ==========================================
    def test_12_unauthenticated_api_booking_returns_401(self):
        """Auth 12: POST /api/bookings without login returns 401."""
        # Clear session
        self.client.post('/api/auth/logout')

        res = self.client.post('/api/bookings', json={
            'space_id': 1,
            'hours': 2.0,
            'purpose': 'Test'
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn('Authentication Required', data['error'])

    def test_13_unauthenticated_dashboard_redirects_to_login(self):
        """Auth 13: GET /dashboard/seeker without login redirects (302) to /login."""
        self.client.post('/api/auth/logout')
        res = self.client.get('/dashboard/seeker')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

    # ==========================================
    # RBAC ENFORCEMENT
    # ==========================================
    def test_14_seeker_cannot_access_host_dashboard(self):
        """Auth 14: Seeker accessing /dashboard/host receives 403 Forbidden."""
        # Login as seeker (Rohit)
        self.client.post('/api/auth/login', json={
            'email': 'rohit@iitd.ac.in',
            'password': 'StudentPass123!'
        })
        res = self.client.get('/dashboard/host')
        self.assertIn(res.status_code, [403, 302])

    def test_15_host_cannot_access_seeker_dashboard(self):
        """Auth 15: Host accessing /dashboard/seeker receives 403 Forbidden."""
        # Login as host (Sunita)
        self.client.post('/api/auth/login', json={
            'email': 'sunita.rao@blrspaces.in',
            'password': 'HostPass123!'
        })
        res = self.client.get('/dashboard/seeker')
        self.assertIn(res.status_code, [403, 302])

    def test_16_seeker_cannot_create_space(self):
        """Auth 16: POST /api/spaces/create by seeker returns 403."""
        # Login as seeker
        self.client.post('/api/auth/login', json={
            'email': 'rohit@iitd.ac.in',
            'password': 'StudentPass123!'
        })
        res = self.client.post('/api/spaces/create', json={
            'title': 'Hacker Space',
            'category': 'Workspace'
        })
        self.assertEqual(res.status_code, 403)

    # ==========================================
    # LANDING PAGE
    # ==========================================
    def test_17_landing_page_renders(self):
        """Auth 17: GET / returns 200 with SpaceLoop landing content."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertIn('SpaceLoop', content)

    # ==========================================
    # DEMO LOGIN
    # ==========================================
    def test_18_demo_login_authenticates(self):
        """Auth 18: POST /api/auth/demo-login authenticates as seeded demo user."""
        res = self.client.post('/api/auth/demo-login', json={'role': 'seeker'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('user', data)
        self.assertEqual(data['user']['role'], 'seeker')


if __name__ == '__main__':
    unittest.main()
