"""
Suite 2: Core Marketplace Flow Verification (8 Tests)
Target: verify_spaceloop.py
Validations: Homepage listings, spaces REST API, multimodal AI scan, natural language match, booking creation, calculator, LoopBot.
"""

import unittest
from app import create_app
from models import db, Space, User, Booking


class TestSpaceLoopCoreMarketplace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        cls.client = cls.app.test_client()

    def test_01_homepage_listings_render(self):
        """Test 1: Homepage renders HTTP 200 with stats, search bar, and campus micro-spaces."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("SpaceLoop", content)
        self.assertIn("Zero-Hardware Micro-Spaces", content)
        self.assertIn("Quiet Campus Micro-Spaces", content)

    def test_02_spaces_rest_api(self):
        """Test 2: REST API GET /api/spaces returns active spaces with spatial telemetry."""
        response = self.client.get('/api/spaces')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertIn('geofence_radius_meters', data[0])
        self.assertNotIn('room_qr_token', data[0])  # P0-7: Secret token masked from public view
        self.assertIn('ai_suitability_score', data[0])
        self.assertIn('price_hourly', data[0])

    def test_03_multimodal_ai_scan(self):
        """Test 3: POST /api/spaces/ai-scan extracts spatial metrics, acoustics, and recommended rate."""
        payload = {
            'category': 'Workspace',
            'description': 'Quiet 2-car garage with white walls and lots of plugs near IIT Gate 1',
            'address': 'Hauz Khas, New Delhi'
        }
        response = self.client.post('/api/spaces/ai-scan', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('recommended_hourly_price', data)
        self.assertIn('suitability_score', data)
        self.assertIn('lighting', data)
        self.assertIn('noise', data)
        self.assertGreater(data['sqft'], 0)

    def test_04_natural_language_ai_match(self):
        """Test 4: POST /api/spaces/ai-match ranks spaces with compatibility score and badges."""
        payload = {
            'query': 'Need an acoustically quiet studio for a 3-person podcast recording this Saturday under Rs. 80/hr with good Wi-Fi'
        }
        response = self.client.post('/api/spaces/ai-match', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)
        top_result = data['results'][0]
        self.assertIn('match_score', top_result)
        self.assertIn('badge', top_result)
        self.assertIn('match_reasons', top_result)

    def test_05_booking_creation_with_escrow_and_micro_lease(self):
        """Test 5: POST /api/bookings recomputes rate server-side, holds Rs. 100 escrow, and synthesizes Section 52 lease."""
        # Authenticate as seeker
        self.client.post('/api/v1/auth/login', json={'email': 'aarav@iitd.ac.in', 'password': 'password123'})
        payload = {
            'space_id': 1,
            'hours': 2.0,
            'purpose': 'Hackathon prototype sprint and code deployment',
            'attendees_count': 1
        }
        response = self.client.post('/api/bookings', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['escrow_deposit'], 100.0)
        self.assertIn('arrival_pin', data)
        self.assertIn('lease_hash', data)
        self.assertTrue(data['session_url'].startswith('/session/'))

    def test_06_dynamic_yield_calculator(self):
        """Test 6: POST /api/calculate-yield computes non-linear rate, monthly yield, and student savings."""
        payload = {
            'category': 'Workspace',
            'sqft': 180,
            'occupancy_days': 12,
            'hours_per_day': 6.0
        }
        response = self.client.post('/api/calculate-yield', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('rate', data)
        self.assertIn('yield', data)
        self.assertIn('savings', data)
        self.assertGreater(data['yield']['net_monthly_income_inr'], 0)
        self.assertGreater(data['savings']['savings_percentage'], 50.0)

    def test_07_loopbot_concierge_chat(self):
        """Test 7: POST /api/concierge returns context-aware AI guidance."""
        payload = {
            'message': 'How does the Rs. 5 QR check-in work?',
            'space_id': 1
        }
        response = self.client.post('/api/concierge', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('reply', data)
        self.assertIn('Zero-Hardware', data['reply'])

    def test_08_direct_inquiry_dispatch(self):
        """Test 8: POST /api/space/<id>/inquire pre-answers routine questions using verified metadata."""
        payload = {
            'question': 'Is there high-speed fiber Wi-Fi in this space?'
        }
        response = self.client.post('/api/space/1/inquire', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('Wi-Fi', data['ai_answer'])


if __name__ == '__main__':
    unittest.main()
