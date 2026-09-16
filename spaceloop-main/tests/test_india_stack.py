"""
Suite 1: India Stack & Operational Telemetry Unit Tests (9 Tests)
Target: test_india_stack.py
Validations: Aadhaar OTP tokenization, .ac.in parsing, Discom CA match, UPI penny drop, AI visual delta, OTI formula, GPS geofence.
"""

import unittest
from india_stack import (
    verify_digilocker_aadhaar, verify_academic_credentials,
    verify_discom_meter, execute_upi_penny_drop
)
from telemetry import (
    haversine_distance, verify_gps_geofence,
    calculate_oti, calculate_punctuality_score, execute_upi_escrow_refund
)
from space_ai import evaluate_condition_delta
from datetime import datetime, timedelta


class TestIndiaStackAndTelemetry(unittest.TestCase):

    def test_01_aadhaar_otp_tokenization(self):
        """Test 1: Aadhaar OTP tokenization generates valid masked display and token hash."""
        res = verify_digilocker_aadhaar("984512344821", otp="123456")
        self.assertTrue(res['success'])
        self.assertEqual(res['masked_aadhaar'], "XXXX-XXXX-4821")
        self.assertTrue(len(res['token_hash']) == 64)  # SHA-256 length

    def test_02_zero_raw_aadhaar_storage(self):
        """Test 2: Raw 12-digit Aadhaar number is never stored (DPDP Act Section 8)."""
        raw = "984512344821"
        res = verify_digilocker_aadhaar(raw, otp="123456")
        self.assertNotIn(raw, res['masked_aadhaar'])
        self.assertNotEqual(raw, res['token_hash'])

    def test_03_academic_domain_regex_success(self):
        """Test 3: Institutional .ac.in and .edu.in email domains pass validation."""
        emails = ["rohit@iitd.ac.in", "ananya@iitb.ac.in", "student@bits-pilani.ac.in", "research@du.ac.in"]
        for email in emails:
            res = verify_academic_credentials(email, student_id="STU-1044")
            self.assertTrue(res['success'], f"Failed for {email}")
            self.assertTrue(res['subsidized_rates_unlocked'])
            self.assertTrue(res['student_id_masked'].startswith("STU-***-"))

    def test_04_academic_domain_regex_rejection(self):
        """Test 4: Non-academic email domains (e.g. gmail, yahoo) are strictly rejected."""
        invalid_emails = ["user@gmail.com", "fake@yahoo.com", "test@company.org", "none@school.net"]
        for email in invalid_emails:
            res = verify_academic_credentials(email)
            self.assertFalse(res['success'])
            self.assertIn("Invalid academic email", res['error'])

    def test_05_discom_ca_verification(self):
        """Test 5: State Discom CA number lookup validates active meter status."""
        res_bescom = verify_discom_meter("BES883920194", provider="BESCOM")
        self.assertTrue(res_bescom['success'])
        self.assertEqual(res_bescom['meter_status'], 'ACTIVE')
        self.assertEqual(res_bescom['state'], 'Karnataka')

        res_bses = verify_discom_meter("10029384912", provider="BSES")
        self.assertTrue(res_bses['success'])
        self.assertEqual(res_bses['state'], 'Delhi')

    def test_06_upi_penny_drop_verification(self):
        """Test 6: NPCI UPI Rs. 1 Penny Drop matches beneficiary title against KYC name."""
        res = execute_upi_penny_drop("sunita@okaxis", claimed_name="Sunita Rao")
        self.assertTrue(res['success'])
        self.assertEqual(res['beneficiary_name'], "Sunita Rao")
        self.assertTrue(res['payout_ready'])
        self.assertEqual(res['penny_drop_status'], 'SUCCESS_RESOLVED')

    def test_07_ai_visual_delta_and_appliances(self):
        """Test 7: AI visual delta verifies cleanliness baseline and confirms appliances powered off."""
        res = evaluate_condition_delta("entry.jpg", "exit.jpg", "Workspace")
        self.assertTrue(res['appliances_off'])
        self.assertGreaterEqual(res['condition_match_score'], 90.0)
        self.assertTrue(res['escrow_refund_approved'])

    def test_08_oti_formula_calculation(self):
        """Test 8: Objective Telemetry Index (OTI) deterministic mathematical formulation."""
        # OTI = (0.35 * 100) + (0.35 * 95) + (0.20 * 100) + (0.10 * 100)
        # = 35 + 33.25 + 20 + 10 = 98.25 -> 98.2 or 98.3
        calc = calculate_oti(punctuality=100.0, condition_match=95.0, is_dual_verified=True, dispute_count=0)
        expected = round((0.35 * 100.0) + (0.35 * 95.0) + (0.20 * 100.0) + (0.10 * 100.0), 1)
        self.assertEqual(calc['oti_score'], expected)
        self.assertEqual(calc['tier'], 'Elite Trust')

    def test_09_haversine_gps_geofence(self):
        """Test 9: Haversine distance geofence accurately allows <50m and rejects >50m check-ins."""
        space_lat, space_lng = 28.5450, 77.1926

        # Very close coords (~14 meters away)
        nearby_lat, nearby_lng = 28.5451, 77.1925
        allowed_near, dist_near = verify_gps_geofence(nearby_lat, nearby_lng, space_lat, space_lng, radius_meters=50.0)
        self.assertTrue(allowed_near)
        self.assertLessEqual(dist_near, 50.0)

        # Far coords (~300 meters away)
        far_lat, far_lng = 28.5480, 77.1950
        allowed_far, dist_far = verify_gps_geofence(far_lat, far_lng, space_lat, space_lng, radius_meters=50.0)
        self.assertFalse(allowed_far)
        self.assertGreater(dist_far, 50.0)


if __name__ == '__main__':
    unittest.main()
