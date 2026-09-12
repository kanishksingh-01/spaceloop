import os
import json
import unittest
from datetime import date, timedelta

from app import create_app
from models import db, User, CycleLog, DailyLog, CareAction, SymptomEntry, PCODAssessment, JournalEntry, Notification, ChatMessage
from cycle_logic import calculate_phase, get_hormone_curves, check_symptom, score_pcod_risk, analyze_mood
from chatbot import chat_reply, get_partner_tip, detect_mode


class TestCycleCare(unittest.TestCase):
    def setUp(self):
        class TestConfig:
            TESTING = True
            SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            SECRET_KEY = "test-secret"
            GROQ_API_KEY = ""

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_user_registration_and_login(self):
        # Register Maya (Self)
        res = self.client.post("/api/register", json={
            "name": "Maya Lin",
            "email": "maya.test@example.com",
            "password": "securepassword123",
            "role": "self"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["name"], "Maya Lin")
        self.assertEqual(data["role"], "self")
        self.assertTrue(data["connect_code"].startswith("CARE-"))

        # Duplicate email test
        res_dup = self.client.post("/api/register", json={
            "name": "Another Maya",
            "email": "maya.test@example.com",
            "password": "somepassword",
            "role": "self"
        })
        self.assertEqual(res_dup.status_code, 409)

        # Login test
        res_login = self.client.post("/api/login", json={
            "email": "maya.test@example.com",
            "password": "securepassword123"
        })
        self.assertEqual(res_login.status_code, 200)

        # Bad password test
        res_bad = self.client.post("/api/login", json={
            "email": "maya.test@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(res_bad.status_code, 401)

    def test_partner_linking(self):
        # Register Self
        self_res = self.client.post("/api/register", json={
            "name": "Sarah", "email": "sarah@test.com", "password": "pass", "role": "self"
        }).get_json()

        # Register Partner
        partner_res = self.client.post("/api/register", json={
            "name": "Sam", "email": "sam@test.com", "password": "pass", "role": "partner"
        }).get_json()

        # Link partner using connect code
        link_res = self.client.post("/api/partner/link", json={
            "partner_user_id": partner_res["id"],
            "connect_code": self_res["connect_code"]
        })
        self.assertEqual(link_res.status_code, 200)

        # Verify status
        status = self.client.get(f"/api/partner/status/{self_res['id']}").get_json()
        self.assertTrue(status["is_linked"])
        self.assertEqual(status["partner_name"], "Sam")

    def test_cycle_log_deduplication(self):
        # Register user
        user = self.client.post("/api/register", json={
            "name": "Elena", "email": "elena@test.com", "password": "pass", "role": "self"
        }).get_json()

        today_str = date.today().isoformat()

        # Log cycle 1st time
        res1 = self.client.post("/api/cycle/log", json={
            "user_id": user["id"],
            "period_start": today_str,
            "cycle_length": 28
        })
        self.assertEqual(res1.status_code, 200)

        # Log cycle 2nd time with same date (simulating cold-start double-click)
        res2 = self.client.post("/api/cycle/log", json={
            "user_id": user["id"],
            "period_start": today_str,
            "cycle_length": 30
        })
        self.assertEqual(res2.status_code, 200)

        # Verify only 1 record exists, updated to 30
        logs = CycleLog.query.filter_by(user_id=user["id"]).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].cycle_length, 30)

    def test_cycle_phases_and_hormones(self):
        start = date.today() - timedelta(days=2)
        phase_info = calculate_phase(start, cycle_length=28)
        self.assertEqual(phase_info["phase"], "Menstrual")
        self.assertEqual(phase_info["day_in_cycle"], 3)

        curves = get_hormone_curves(day_in_cycle=14, cycle_length=28)
        self.assertIn("estrogen_series", curves)
        self.assertIn("progesterone_series", curves)
        self.assertIn("today_levels", curves)
        self.assertTrue(curves["today_levels"]["lh"] > 50)  # LH surge at ovulation

    def test_symptom_triage_red_flags(self):
        # Urgent symptom
        urgent = check_symptom("I am soaking through a pad an hour with unbearable pelvic pain")
        self.assertFalse(urgent["flagged_normal"])
        self.assertEqual(urgent["severity"], "urgent")

        # Normal symptom
        normal = check_symptom("I have mild cramps and feel tired today")
        self.assertTrue(normal["flagged_normal"])
        self.assertEqual(normal["severity"], "normal")

    def test_pcod_rotterdam_scoring(self):
        # Low risk answers
        low = score_pcod_risk({"irregular_periods": False, "acne_or_oily_skin": False})
        self.assertEqual(low["risk_level"], "low")

        # Elevated risk answers
        high = score_pcod_risk({
            "irregular_periods": True,
            "excess_hair_growth": True,
            "weight_gain_unexplained": True,
            "difficulty_conceiving": True
        })
        self.assertEqual(high["risk_level"], "elevated")
        self.assertTrue(len(high["doctor_checklist"]) > 0)

    def test_partner_empathy_bridge_and_privacy(self):
        # Register & link Maya and Alex
        maya = self.client.post("/api/register", json={
            "name": "Maya", "email": "maya@empathy.com", "password": "pass", "role": "self"
        }).get_json()

        alex = self.client.post("/api/register", json={
            "name": "Alex", "email": "alex@empathy.com", "password": "pass", "role": "partner"
        }).get_json()

        self.client.post("/api/partner/link", json={
            "partner_user_id": alex["id"],
            "connect_code": maya["connect_code"]
        })

        # Maya logs cycle & daily check-in
        self.client.post("/api/cycle/log", json={
            "user_id": maya["id"],
            "period_start": (date.today() - timedelta(days=20)).isoformat(),
            "cycle_length": 28
        })
        self.client.post("/api/daily/log", json={
            "user_id": maya["id"],
            "mood": "sensitive",
            "energy_level": 2,
            "flow_intensity": "none"
        })

        # Alex views partner vibe
        vibe = self.client.get(f"/api/partner/view/{alex['id']}").get_json()
        self.assertEqual(vibe["phase"], "Luteal")
        self.assertEqual(vibe["recent_mood"], "sensitive")
        self.assertEqual(vibe["recent_energy"], 2)
        self.assertIn("progesterone", vibe["partner_tip"].lower())

        # Alex sends a Micro-Care Action (Virtual Heat Pack)
        care_res = self.client.post("/api/partner/care-action", json={
            "sender_id": alex["id"],
            "recipient_id": maya["id"],
            "action_type": "heat_pack",
            "custom_message": "Rest up, I love you!"
        })
        self.assertEqual(care_res.status_code, 200)

        # Maya checks care actions
        actions = self.client.get(f"/api/partner/care-actions/{maya['id']}").get_json()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "heat_pack")

        # Maya acknowledges care action
        ack_res = self.client.post(f"/api/partner/care-action/{actions[0]['id']}/ack", json={})
        self.assertEqual(ack_res.status_code, 200)

    def test_ai_companion_modes_and_partner_derived_tip(self):
        # Register user with partner
        user = self.client.post("/api/register", json={
            "name": "Nora", "email": "nora@test.com", "password": "pass", "role": "self"
        }).get_json()
        partner = self.client.post("/api/register", json={
            "name": "Leo", "email": "leo@test.com", "password": "pass", "role": "partner"
        }).get_json()
        self.client.post("/api/partner/link", json={
            "partner_user_id": partner["id"], "connect_code": user["connect_code"]
        })

        # Test Calm Mode in chat
        chat_res = self.client.post("/api/chat", json={
            "user_id": user["id"],
            "message": "I feel so anxious and overwhelmed right now",
            "mode": "calm"
        }).get_json()

        self.assertEqual(chat_res["mode"], "calm")
        self.assertTrue(chat_res.get("trigger_breathing", False))
        self.assertIn("4-7-8", chat_res["reply"])

        # Check Partner Notification: must be derived care tip, NOT the raw user text!
        notes = self.client.get(f"/api/notifications/{partner['id']}").get_json()
        self.assertTrue(len(notes) > 0)
        # Verify the notification contains caring advice and DOES NOT quote raw text
        self.assertTrue(any("overwhelm" in n["message"].lower() or "hug" in n["message"].lower() for n in notes))
        self.assertNotIn("I feel so anxious and overwhelmed right now", [n["message"] for n in notes])

        # Test Draft Mode
        draft_res = self.client.post("/api/chat", json={
            "user_id": user["id"],
            "message": "Can you draft an email to my manager asking for sick leave?",
            "mode": "draft",
            "companion_name": "Luna"
        }).get_json()
        self.assertEqual(draft_res["mode"], "draft")
        self.assertIn("under the weather", draft_res["reply"])

    def test_data_sovereignty_wipe(self):
        user = self.client.post("/api/register", json={
            "name": "Zoe", "email": "zoe@test.com", "password": "pass", "role": "self"
        }).get_json()

        # Add data
        self.client.post("/api/cycle/log", json={
            "user_id": user["id"], "period_start": date.today().isoformat()
        })
        self.client.post("/api/journal/add", json={
            "user_id": user["id"], "text": "Secret personal note"
        })

        self.assertEqual(CycleLog.query.filter_by(user_id=user["id"]).count(), 1)
        self.assertEqual(JournalEntry.query.filter_by(user_id=user["id"]).count(), 1)

        # Wipe data
        wipe_res = self.client.post("/api/user/wipe-data", json={"user_id": user["id"]})
        self.assertEqual(wipe_res.status_code, 200)

        # Verify completely erased
        self.assertEqual(CycleLog.query.filter_by(user_id=user["id"]).count(), 0)
        self.assertEqual(JournalEntry.query.filter_by(user_id=user["id"]).count(), 0)


if __name__ == "__main__":
    unittest.main()
