"""
SpaceLoop NLP Part 1: Loop Bot Foundation Unit Tests
Verifies:
1. Basic SpaceLoop Queries:
   - What is SpaceLoop?
   - How does SpaceLoop work?
   - How do I find a space?
   - How do I book a space?
   - What information is required?
2. Out-of-scope non-hallucination guardrails (weather, crypto, etc.)
3. Response formatting & clean string delivery (no raw JSON, tracebacks, or null values)
"""
import unittest
from app import create_app
from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query


class TestLoopBotPart1Foundation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_what_is_spaceloop(self):
        """Verifies clear, concise, accurate answer to 'What is SpaceLoop?'."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("What is SpaceLoop?", return_dict=True)
            self.assertEqual(res["intent"], "ASK_HELP")
            self.assertIn("SpaceLoop", res["reply"])
            self.assertIn("peer-to-peer marketplace", res["reply"])
            self.assertIn("Section 52", res["reply"])
            self.assertIn("₹100", res["reply"])

    def test_02_how_spaceloop_works(self):
        """Verifies clear 4-step explanation for 'How does SpaceLoop work?'."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("How does SpaceLoop work?", return_dict=True)
            self.assertEqual(res["intent"], "ASK_HELP")
            reply = res["reply"]
            self.assertIn("How SpaceLoop Works", reply)
            self.assertIn("Search & Match", reply)
            self.assertIn("Instant Booking", reply)
            self.assertIn("Zero-Hardware Arrival", reply)
            self.assertIn("Checkout & Instant Refund", reply)

    def test_03_how_to_find_space(self):
        """Verifies instructions for 'How do I find a space?'."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("How do I find a space?", return_dict=True)
            self.assertEqual(res["intent"], "ASK_HELP")
            reply = res["reply"]
            self.assertIn("How to Find a Space", reply)
            self.assertIn("/explore", reply)

    def test_04_how_to_book_space(self):
        """Verifies booking instructions for 'How do I book a space?'."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("How do I book a space?", return_dict=True)
            self.assertIn(res["intent"], ["BOOK_PROPERTY", "ASK_HELP"])
            reply = res["reply"]
            self.assertTrue("Book" in reply or "Reservation" in reply)
            self.assertIn("/space", reply)

    def test_05_information_required(self):
        """Verifies requirements breakdown for 'What information is required?'."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("What information is required?", return_dict=True)
            self.assertEqual(res["intent"], "ASK_HELP")
            reply = res["reply"]
            self.assertIn("Information Required", reply)
            self.assertIn("To Book a Space", reply)
            self.assertIn("To List a Space", reply)
            self.assertIn("Aadhaar", reply)

    def test_06_out_of_scope_guardrail_weather(self):
        """Verifies out-of-scope query for weather clearly states information is unavailable without hallucinating."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("What is the weather in Delhi today?", return_dict=True)
            self.assertEqual(res["intent"], "CLARIFICATION_NEEDED")
            reply = res["reply"]
            self.assertTrue(
                "Information Unavailable" in reply or "unavailable on SpaceLoop" in reply or "जानकारी उपलब्ध नहीं" in reply
            )

    def test_07_out_of_scope_guardrail_crypto(self):
        """Verifies out-of-scope query for cryptocurrency states information is unavailable."""
        with self.app.app_context():
            res = orchestrate_loopbot_query("Tell me about Bitcoin and crypto investment", return_dict=True)
            self.assertEqual(res["intent"], "CLARIFICATION_NEEDED")
            reply = res["reply"]
            self.assertTrue(
                "Information Unavailable" in reply or "unavailable on SpaceLoop" in reply or "जानकारी उपलब्ध नहीं" in reply
            )

    def test_08_api_endpoint_structure(self):
        """Verifies POST /api/assistant returns standard structure with non-empty reply."""
        response = self.client.post(
            "/api/assistant",
            json={"messages": [{"role": "user", "content": "What is SpaceLoop?"}]}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("reply"), str)
        self.assertGreater(len(data.get("reply")), 20)
        self.assertEqual(data.get("intent"), "ASK_HELP")


if __name__ == "__main__":
    unittest.main()
