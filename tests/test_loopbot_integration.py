"""
SpaceLoop Loop Bot Integration Test Suite
==========================================
Tests Part 4 end-to-end integration:
1. Dual API endpoint access (/api/assistant and /api/ai/chat)
2. NLP Pipeline parsing (Language, Normalization, Intent, Entities)
3. Subsystem routing across all 13 canonical intents
4. Low-confidence clarification guardrail (zero hallucinations)
5. Clean output guarantees (no raw JSON, DB repr, tool tags, or debug info)
6. Multilingual localization and safe fallback integration
"""
import os
import re
import json
import unittest
from app import create_app
from models import db, Space, User, Booking
from backend.modules.nlp.schemas import IntentType, LanguageCode
from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query, _sanitize_loopbot_response


class TestLoopBotIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    # -------------------------------------------------------------------------
    # 1. DUAL API ENDPOINT ACCESS (/api/assistant & /api/ai/chat)
    # -------------------------------------------------------------------------
    def test_01_api_assistant_endpoint(self):
        """Verifies /api/assistant responds with 200 and structured payload."""
        payload = {
            "message": "Find a quiet desk in Pune under 500 rs",
            "language_preference": "en"
        }
        res = self.client.post("/api/assistant", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("reply", data)
        self.assertEqual(data.get("intent"), "SEARCH_PROPERTY")
        self.assertIn("Pune", str(data.get("entities", {})))
        self.assertFalse(data.get("requires_clarification"))

    def test_02_api_ai_chat_backward_compatibility(self):
        """Verifies existing /api/ai/chat endpoint works with identical schema."""
        payload = {
            "message": "How much for 4 hours at space #4?",
            "space_id": 4
        }
        res = self.client.post("/api/ai/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("reply", data)
        self.assertEqual(data.get("intent"), "ASK_PRICE")

    # -------------------------------------------------------------------------
    # 2. CANONICAL INTENT ROUTING ACROSS ALL 13 CAPABILITIES
    # -------------------------------------------------------------------------
    def test_03_intent_routing_search_property(self):
        """SEARCH_PROPERTY: Marketplace search and formatted cards."""
        res = orchestrate_loopbot_query("Search spaces for 6 people under 600", return_dict=True)
        self.assertEqual(res["intent"], "SEARCH_PROPERTY")
        self.assertIn("Marketplace Search Results", res["reply"])
        self.assertIn("Rate: ₹", res["reply"])

    def test_04_intent_routing_check_availability(self):
        """CHECK_AVAILABILITY: Real-time overlap check and available slots."""
        res = orchestrate_loopbot_query("What's available tomorrow for 4 people?", return_dict=True)
        self.assertEqual(res["intent"], "CHECK_AVAILABILITY")
        self.assertIn("Availability", res["reply"])

    def test_05_intent_routing_book_property(self):
        """BOOK_PROPERTY: Direct booking link and 4-step protocol."""
        res = orchestrate_loopbot_query("Book this space now for 2 hours", return_dict=True)
        self.assertEqual(res["intent"], "BOOK_PROPERTY")
        self.assertIn("/space/", res["reply"])
        self.assertIn("Instant Reservation Steps", res["reply"])

    def test_06_intent_routing_ask_price(self):
        """ASK_PRICE: Hourly rate calculation breakdown."""
        res = orchestrate_loopbot_query("How much does it cost for 3 hours?", return_dict=True)
        self.assertEqual(res["intent"], "ASK_PRICE")
        self.assertIn("Pricing Calculation Breakdown", res["reply"])
        self.assertIn("Base Hourly Rent", res["reply"])
        self.assertIn("Platform & Safety Fee", res["reply"])

    def test_07_intent_routing_ask_location(self):
        """ASK_LOCATION: Coordinates, neighborhood, and 50m geofence."""
        res = orchestrate_loopbot_query("What is the exact location of space #4?", return_dict=True)
        self.assertEqual(res["intent"], "ASK_LOCATION")
        self.assertIn("Location Details", res["reply"])
        self.assertIn("Zero-Hardware Arrival", res["reply"])

    def test_08_intent_routing_ask_amenities(self):
        """ASK_AMENITIES: Semantic RAG retrieval over verified amenities."""
        res = orchestrate_loopbot_query("Does this space have high speed wifi and ac?", return_dict=True)
        self.assertEqual(res["intent"], "ASK_AMENITIES")
        self.assertIn("Verified Amenities", res["reply"])

    def test_09_intent_routing_create_listing(self):
        """CREATE_LISTING: Host monetization guidance and AI camera scan."""
        res = orchestrate_loopbot_query("How can I list my garage to earn passive income?", return_dict=True)
        self.assertEqual(res["intent"], "CREATE_LISTING")
        self.assertIn("/list-space", res["reply"])
        self.assertIn("95% Yield", res["reply"])

    def test_10_intent_routing_edit_listing(self):
        """EDIT_LISTING: Instructions for updating pricing, photos, or rules."""
        res = orchestrate_loopbot_query("How do I edit my listing price or photos?", return_dict=True)
        self.assertEqual(res["intent"], "EDIT_LISTING")
        self.assertIn("/dashboard", res["reply"])
        self.assertIn("Host Spaces", res["reply"])

    def test_11_intent_routing_ask_booking_status(self):
        """ASK_BOOKING_STATUS: Status inquiry and digital door pass check."""
        res = orchestrate_loopbot_query("What is my booking status and arrival pin?", return_dict=True)
        self.assertEqual(res["intent"], "ASK_BOOKING_STATUS")
        self.assertIn("Booking Status", res["reply"])

    def test_12_intent_routing_ask_payment_status(self):
        """ASK_PAYMENT_STATUS: ₹100 UPI escrow status and 120s refund protocol."""
        res = orchestrate_loopbot_query("When will my 100 rs deposit refund get returned?", return_dict=True)
        self.assertEqual(res["intent"], "ASK_PAYMENT_STATUS")
        self.assertIn("120 seconds", res["reply"])
        self.assertIn("UPI", res["reply"])

    def test_13_intent_routing_report_fraud(self):
        """REPORT_FRAUD: Trust & Safety incident reporting procedure."""
        res = orchestrate_loopbot_query("I want to report fraud and a suspicious host listing", return_dict=True)
        self.assertEqual(res["intent"], "REPORT_FRAUD")
        self.assertIn("Trust & Safety", res["reply"])
        self.assertIn("Report an Issue", res["reply"])

    def test_14_intent_routing_ask_help(self):
        """ASK_HELP: Platform guidance and Section 52 micro-leasing."""
        res = orchestrate_loopbot_query("Help me understand Section 52 legal protection", return_dict=True)
        self.assertEqual(res["intent"], "ASK_HELP")
        self.assertIn("Section 52", res["reply"])
        self.assertIn("Easements Act", res["reply"])

    def test_15_intent_routing_general_conversation(self):
        """GENERAL_CONVERSATION: Friendly greeting and platform introduction."""
        res = orchestrate_loopbot_query("Hello LoopBot!", return_dict=True)
        self.assertEqual(res["intent"], "GENERAL_CONVERSATION")
        self.assertIn("LoopBot", res["reply"])

    # -------------------------------------------------------------------------
    # 3. LOW CONFIDENCE CLARIFICATION GUARDRAIL
    # -------------------------------------------------------------------------
    def test_16_low_confidence_clarification_guardrail(self):
        """Verifies low-confidence/ambiguous query asks clarification without hallucinations."""
        res = orchestrate_loopbot_query("asdfgh qwerty zxcvbnm", return_dict=True)
        self.assertEqual(res["intent"], "CLARIFICATION_NEEDED")
        self.assertTrue(res["requires_clarification"])
        self.assertIn("clarify", res["reply"].lower())

    # -------------------------------------------------------------------------
    # 4. CLEAN OUTPUT SANITIZATION GUARANTEES
    # -------------------------------------------------------------------------
    def test_17_sanitizer_cleans_raw_json_db_objects_and_debug(self):
        """Verifies _sanitize_loopbot_response strips JSON, DB repr, tool tags, and scores."""
        dirty_input = (
            "Here are the details:\n"
            "```json\n{\"space_id\": 4, \"status\": \"ok\"}\n```\n"
            "<Space 4: Acoustic Studio at 0x7fa890>\n"
            "[TOOL_OUTPUT: db_query_completed]\n"
            "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\nValueError: invalid\n"
            "• **Title**: Study Pod\n"
            "cosine_similarity: 0.9412\n"
            "<br><p>Ready to book!</p>"
        )
        cleaned = _sanitize_loopbot_response(dirty_input)

        # Assert zero raw JSON blocks
        self.assertNotIn("```json", cleaned)
        self.assertNotIn("space_id", cleaned)

        # Assert zero DB object strings
        self.assertNotIn("<Space", cleaned)
        self.assertNotIn("0x7fa890", cleaned)

        # Assert zero tool output or debug traces
        self.assertNotIn("[TOOL_OUTPUT", cleaned)
        self.assertNotIn("Traceback", cleaned)
        self.assertNotIn("ValueError", cleaned)

        # Assert zero vector similarity scores
        self.assertNotIn("cosine_similarity", cleaned)

        # Assert zero HTML tags
        self.assertNotIn("<br>", cleaned)
        self.assertNotIn("<p>", cleaned)

        # Assert valid markdown content preserved
        self.assertIn("Study Pod", cleaned)
        self.assertIn("Ready to book!", cleaned)

    # -------------------------------------------------------------------------
    # 5. MULTILINGUAL ORCHESTRATION & CODE-MIXED INPUTS
    # -------------------------------------------------------------------------
    def test_18_multilingual_orchestration_hinglish(self):
        """Verifies code-mixed query is parsed and returned with correct language flags."""
        res = orchestrate_loopbot_query("Pune me meeting room chahiye under 400", return_dict=True)
        self.assertEqual(res["detected_language"], "hi-Latn")
        self.assertEqual(res["intent"], "SEARCH_PROPERTY")
        self.assertIn("₹", res["reply"])

    def test_19_multilingual_orchestration_marathi(self):
        """Verifies Marathi query routes cleanly."""
        res = orchestrate_loopbot_query("पुण्यात २ लोकांसाठी शांत खोली पाहिजे", return_dict=True)
        self.assertEqual(res["detected_language"], "mr")
        self.assertEqual(res["intent"], "SEARCH_PROPERTY")


if __name__ == "__main__":
    unittest.main()
