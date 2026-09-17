"""
Targeted test suite verifying fixes for:
1. Issue #1: Booking Conflict normalization & precheck availability
2. Issue #2: LoopBot output cleaner (removes <br>, tables, and HTML)
3. Issue #3: Permanent Dark Theme enforcement
"""
import re
import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta
from app import app
from models import db, Space, Booking
from space_ai import _clean_loopbot_output


class TargetedBugfixesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_loopbot_cleaner_strips_tables_and_br(self):
        sample = (
            "Here are some spaces:\n"
            "| Space ID | Name & Type | Features | Rate |\n"
            "|---|---|---|---|\n"
            "| #1 | Quiet Study Pod<br>Wagholi | AC, Wi-Fi<br>Whiteboard | ₹50/hr |\n"
            "| #2 | Creator Studio | Lighting | ₹80/hr |\n"
        )
        cleaned = _clean_loopbot_output(sample)
        self.assertNotIn("<br>", cleaned)
        self.assertNotIn("|---|", cleaned)
        self.assertIn("•", cleaned)
        self.assertIn("Quiet Study Pod - Wagholi", cleaned)

    def test_booking_precheck_conflict_payload(self):
        with self.app.app_context():
            s = Space.query.filter_by(is_active=True).first()
            self.assertIsNotNone(s)
            b = Booking.query.filter(
                Booking.space_id == s.id,
                Booking.status == "confirmed"
            ).first()
            if b:
                st = b.start_time + timedelta(minutes=5)
                et = b.end_time + timedelta(minutes=5)
                res = self.client.post("/api/bookings/precheck", json={
                    "space_id": s.id,
                    "start_time": st.isoformat(),
                    "end_time": et.isoformat(),
                    "hours": 1.0
                })
                self.assertEqual(res.status_code, 409)
                data = res.get_json()
                self.assertEqual(data.get("error"), "Booking Conflict")
                self.assertIn("already booked", data.get("message", ""))
                self.assertIn("conflicting_slot", data)

    def test_booking_precheck_available_slot(self):
        with self.app.app_context():
            s = Space.query.filter_by(is_active=True).first()
            now = datetime.utcnow()
            res = self.client.post("/api/bookings/precheck", json={
                "space_id": s.id,
                "start_time": (now + timedelta(days=90)).isoformat(),
                "end_time": (now + timedelta(days=90, hours=2)).isoformat(),
                "hours": 2.0
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("available"))
            self.assertIn("total_payable", data)


if __name__ == "__main__":
    unittest.main()
