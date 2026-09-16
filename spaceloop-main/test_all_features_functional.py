"""
Suite 4: 14-Point End-to-End Functional Audit (14 Tests)
Target: test_all_features_functional.py
Validations: Complete user journey: discovery -> verification -> booking -> check-in -> exit scan -> escrow refund -> all 10 templates HTTP 200.
"""

import unittest
from app import create_app
from models import db, Space, User, Booking


class Test14PointEndToEndAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        cls.client = cls.app.test_client()
        # Authenticate as seeker (Rohit Verma, id=1) by default
        with cls.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['persona'] = 'seeker'

    def test_01_marketplace_discovery_journey(self):
        """Audit 1: Seeker searches for quiet study pods near IIT Delhi."""
        res = self.client.get('/?q=Hauz+Khas')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Hauz Khas", res.data)

    def test_02_student_verification_journey(self):
        """Audit 2: Student completes dual-sided DigiLocker Aadhaar and academic email verification."""
        payload = {
            'name': 'Kanishk Singh',
            'aadhaar_number': '984512344821',
            'otp': '123456',
            'college_email': 'kanishk@iitd.ac.in',
            'college_name': 'IIT Delhi',
            'student_id': '2024CS9901'
        }
        res = self.client.post('/api/verify/student', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['masked_aadhaar'], 'XXXX-XXXX-4821')

    def test_03_host_verification_journey(self):
        """Audit 3: Host completes Discom active meter verification and UPI penny drop."""
        payload = {
            'ca_number': 'BES883920194',
            'provider': 'BESCOM',
            'address': 'Koramangala 4th Block, Bengaluru',
            'pan_name': 'Sunita Rao',
            'upi_vpa': 'sunita@okaxis'
        }
        res = self.client.post('/api/verify/host', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['discom']['meter_status'], 'ACTIVE')

    def test_04_instant_booking_and_lease_synthesis(self):
        """Audit 4: Instant booking validates rate, calculates Rs. 100 escrow, and synthesizes Section 52 lease."""
        payload = {
            'space_id': 1,
            'hours': 2.0,
            'purpose': 'AI Agent prototyping and benchmark run',
            'attendees_count': 1
        }
        res = self.client.post('/api/bookings', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['escrow_deposit'], 100.0)
        self.assertIn('arrival_pin', data)
        self.assertIn('lease_hash', data)
        Test14PointEndToEndAudit.created_booking_id = data['booking_id']

    def test_05_gps_checkin_geofence_violation(self):
        """Audit 5: Remote check-in attempt (>50m radar) is rejected with HTTP 400 Geofence Violation."""
        booking_id = getattr(Test14PointEndToEndAudit, 'created_booking_id', 1)
        with self.app.app_context():
            space = Booking.query.get(booking_id).space
            qr_token = space.room_qr_token

        # Far away coordinates (~2000m away)
        payload = {
            'qr_token': qr_token,
            'lat': 28.5900,
            'lng': 77.2500,
            'entry_photo': 'entry.jpg'
        }
        res = self.client.post(f'/api/booking/{booking_id}/check-in', json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data['error'], 'Geofence Violation')

    def test_06_gps_checkin_handshake_success(self):
        """Audit 6: In-range (<50m) check-in with door QR succeeds and returns dynamic PIN."""
        booking_id = getattr(Test14PointEndToEndAudit, 'created_booking_id', 1)
        with self.app.app_context():
            space = Booking.query.get(booking_id).space
            qr_token = space.room_qr_token
            # Coords ~12m from space
            lat = space.latitude + 0.0001
            lng = space.longitude + 0.0001

        payload = {
            'qr_token': qr_token,
            'lat': lat,
            'lng': lng,
            'entry_photo': 'entry.jpg'
        }
        res = self.client.post(f'/api/booking/{booking_id}/check-in', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['session_state'], 'checked_in')
        self.assertIn('arrival_pin', data)

    def test_07_exit_walkthrough_cv_diff_and_escrow_refund(self):
        """Audit 7: Exit walkthrough confirms fans/lights OFF and triggers instant Rs. 100 UPI refund."""
        booking_id = getattr(Test14PointEndToEndAudit, 'created_booking_id', 1)
        payload = {
            'exit_photo': 'exit.jpg'
        }
        res = self.client.post(f'/api/booking/{booking_id}/check-out', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['session_state'], 'checked_out')
        self.assertTrue(data['appliances_off'])
        self.assertTrue(data['escrow_refund']['success'])
        self.assertEqual(data['escrow_refund']['amount_inr'], 100.0)

    def test_08_template_index_http_200(self):
        """Audit 8: Template index.html loads HTTP 200."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

    def test_09_template_space_detail_http_200(self):
        """Audit 9: Template space_detail.html loads HTTP 200 with OTI card."""
        res = self.client.get('/space/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Objective Telemetry Index", res.data)

    def test_10_template_printable_qr_http_200(self):
        """Audit 10: Template printable_qr.html loads ready-to-print A4 Door Pass HTTP 200."""
        # printable-qr requires space owner; space 1 is owned by host_vikram (id=3)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['persona'] = 'owner'
        res = self.client.get('/space/1/printable-qr')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Zero-Hardware Physical Door Access", res.data)
        # Restore seeker session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['persona'] = 'seeker'
        self.assertIn(b"Cryptographic Door QR", res.data)

    def test_11_template_verify_student_http_200(self):
        """Audit 11: Template verify_student.html loads HTTP 200."""
        res = self.client.get('/verify/student')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"DPDP Act 2023", res.data)

    def test_12_template_verify_host_http_200(self):
        """Audit 12: Template verify_host.html loads HTTP 200."""
        res = self.client.get('/verify/host')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Discom Electricity Bill", res.data)

    def test_13_template_in_room_session_console_http_200(self):
        """Audit 13: Template in_room.html Live In-Room Session Console HUD loads HTTP 200."""
        res = self.client.get('/session/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Live In-Room Session Console", res.data)

    def test_14_template_dashboards_and_calculator_http_200(self):
        """Audit 14: Dashboards, Calculator, and Section 52 Micro-Lease view all load HTTP 200."""
        # Seeker dashboard (user_id=1, role=seeker)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['persona'] = 'seeker'
        res_seeker = self.client.get('/dashboard/seeker')
        self.assertEqual(res_seeker.status_code, 200)

        # Host dashboard (user_id=3, role=owner)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['persona'] = 'owner'
        res_host = self.client.get('/dashboard/host')
        self.assertEqual(res_host.status_code, 200)

        # Restore seeker for remaining assertions
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['persona'] = 'seeker'

        res_calc = self.client.get('/calculator')
        self.assertEqual(res_calc.status_code, 200)

        res_lease = self.client.get('/lease/1')
        self.assertEqual(res_lease.status_code, 200)
        self.assertIn(b"Indian Easements Act, 1882", res_lease.data)


if __name__ == '__main__':
    unittest.main()
