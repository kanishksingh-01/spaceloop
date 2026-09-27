"""
Unit and Integration Test Suite for SpaceLoop NLP Part 4: Listing Assistance
=============================================================================
Tests:
1. Accurate extraction of example 1:
   "2 bedroom workspace in Pune for 4 people with fast WiFi and AC"
2. Strict zero-hallucination verification on example 2:
   "Workspace for 4 people with WiFi"
   (Ensures no AC, parking, price, address, or availability are invented)
3. Multi-tier LLM fallback routing:
   Groq -> Gemini -> Deterministic Rule Engine
4. Grounding validation:
   Ensures amenities not in user text are strictly rejected even if LLM invents them
5. API endpoint POST /api/spaces/assist-listing with listing_draft structure
"""
import unittest
from unittest.mock import patch
import json
from app import create_app
from backend.modules.nlp.listing_assistance import ListingAssistanceService


class TestNLPListingAssistancePart4(unittest.TestCase):

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

    def test_01_user_example_full_extraction(self):
        """
        Verify: "2 bedroom workspace in Pune for 4 people with fast WiFi and AC"
        Extracts only provided fields without hallucinating price, parking, or availability.
        """
        text = "2 bedroom workspace in Pune for 4 people with fast WiFi and AC"
        res = ListingAssistanceService.assist_listing(text, target_language="en")

        self.assertTrue(res["success"])
        fields = res["extracted_fields"]
        draft = res["listing_draft"]

        # Extracted fields check
        self.assertEqual(fields.get("bedrooms"), 2)
        self.assertEqual(fields.get("city"), "Pune")
        self.assertEqual(fields.get("max_capacity"), 4)
        self.assertIn("High-speed Wi-Fi", fields.get("amenities", []))
        self.assertIn("Air Conditioning", fields.get("amenities", []))

        # Strict zero-hallucination checks
        self.assertNotIn("Parking Available", fields.get("amenities", []))
        self.assertIsNone(fields.get("rent"))
        self.assertIsNone(fields.get("price_hourly"))
        self.assertIsNone(draft.get("price_hourly"))
        self.assertIsNone(draft.get("price_monthly"))

        # Draft schema check
        self.assertEqual(draft["max_capacity"], 4)
        self.assertEqual(draft["bedrooms"], 2)
        self.assertEqual(draft["city"], "Pune")
        self.assertIn("High-speed Wi-Fi", draft["amenities"])
        self.assertIn("Air Conditioning", draft["amenities"])
        self.assertIn("rent", res["missing_fields"])

    def test_02_zero_hallucination_sparse_input(self):
        """
        Verify: "Workspace for 4 people with WiFi"
        MUST NOT invent AC, parking, price, address, or availability.
        """
        text = "Workspace for 4 people with WiFi"
        res = ListingAssistanceService.assist_listing(text)

        self.assertTrue(res["success"])
        fields = res["extracted_fields"]
        draft = res["listing_draft"]

        # Provided
        self.assertEqual(fields.get("max_capacity"), 4)
        self.assertIn("High-speed Wi-Fi", fields.get("amenities", []))
        self.assertEqual(draft.get("max_capacity"), 4)

        # UNMENTIONED fields must be None / Empty (Zero Hallucination)
        self.assertNotIn("Air Conditioning", fields.get("amenities", []))
        self.assertNotIn("Parking Available", fields.get("amenities", []))
        self.assertNotIn("Air Conditioning", draft.get("amenities", []))
        self.assertNotIn("Parking Available", draft.get("amenities", []))
        self.assertIsNone(fields.get("rent"))
        self.assertIsNone(fields.get("price_hourly"))
        self.assertIsNone(fields.get("location"))
        self.assertIsNone(fields.get("city"))
        self.assertIsNone(draft.get("price_hourly"))
        self.assertIsNone(draft.get("price_monthly"))
        self.assertEqual(draft.get("location"), "")
        self.assertEqual(draft.get("city"), "")

        # Missing fields should include rent and location
        self.assertIn("rent", res["missing_fields"])
        self.assertIn("location", res["missing_fields"])

    def test_03_multi_tier_fallback_groq_primary(self):
        """Verify Groq is called first when available."""
        mock_groq_response = json.dumps({
            "title": "Modern Studio in Pune",
            "category": "Studio",
            "location": "Pune",
            "city": "Pune",
            "max_capacity": 6,
            "amenities": ["High-speed Wi-Fi", "Air Conditioning"],
            "price_hourly": None,
            "rent": None
        })

        with patch("space_ai._call_groq", return_value=mock_groq_response) as mock_groq:
            with patch("space_ai._call_gemini") as mock_gemini:
                text = "Studio in Pune for 6 people with wifi and ac"
                res = ListingAssistanceService.assist_listing(text)

                self.assertTrue(res["success"])
                self.assertEqual(res["ai_provider"], "groq")
                mock_groq.assert_called_once()
                mock_gemini.assert_not_called()
                self.assertEqual(res["listing_draft"]["category"], "Studio")
                self.assertEqual(res["listing_draft"]["max_capacity"], 6)

    def test_04_multi_tier_fallback_gemini_secondary(self):
        """Verify Gemini is called when Groq fails."""
        mock_gemini_response = json.dumps({
            "title": "Co-working Meeting Space",
            "category": "Meeting",
            "location": "Baner",
            "city": "Pune",
            "max_capacity": 8,
            "amenities": ["High-speed Wi-Fi"],
            "price_hourly": 400.0,
            "rent": None
        })

        with patch("space_ai._call_groq", side_effect=Exception("Groq rate limit")):
            with patch("space_ai._call_gemini", return_value=mock_gemini_response) as mock_gemini:
                text = "Meeting room in Baner for 8 people with wifi at 400/hr"
                res = ListingAssistanceService.assist_listing(text)

                self.assertTrue(res["success"])
                self.assertEqual(res["ai_provider"], "gemini")
                mock_gemini.assert_called_once()
                self.assertEqual(res["listing_draft"]["category"], "Meeting")
                self.assertEqual(res["listing_draft"]["price_hourly"], 400.0)

    def test_05_multi_tier_fallback_deterministic_tertiary(self):
        """Verify deterministic rules kick in when both Groq and Gemini fail."""
        with patch("space_ai._call_groq", side_effect=Exception("Groq offline")):
            with patch("space_ai._call_gemini", side_effect=Exception("Gemini offline")):
                text = "2 bedroom workspace in Pune for 4 people with fast WiFi and AC"
                res = ListingAssistanceService.assist_listing(text)

                self.assertTrue(res["success"])
                self.assertEqual(res["ai_provider"], "deterministic_rule_engine")
                self.assertEqual(res["extracted_fields"]["bedrooms"], 2)
                self.assertEqual(res["extracted_fields"]["city"], "Pune")
                self.assertEqual(res["extracted_fields"]["max_capacity"], 4)
                self.assertIn("High-speed Wi-Fi", res["extracted_fields"]["amenities"])
                self.assertIn("Air Conditioning", res["extracted_fields"]["amenities"])

    def test_06_grounding_rejects_hallucinated_amenities(self):
        """Even if an LLM hallucinates an amenity, grounding verification filters it out."""
        # LLM returns "Parking Available" and "Air Conditioning", but user only wrote "wifi"
        hallucinated_llm_json = json.dumps({
            "category": "Workspace",
            "amenities": ["High-speed Wi-Fi", "Air Conditioning", "Parking Available"],
            "max_capacity": 4
        })

        with patch("space_ai._call_groq", return_value=hallucinated_llm_json):
            text = "Workspace for 4 people with fast WiFi"
            res = ListingAssistanceService.assist_listing(text)

            self.assertTrue(res["success"])
            amenities = res["listing_draft"]["amenities"]
            self.assertIn("High-speed Wi-Fi", amenities)
            # AC and Parking MUST be eliminated because neither was in text
            self.assertNotIn("Air Conditioning", amenities)
            self.assertNotIn("Parking Available", amenities)

    def test_07_api_endpoint_returns_listing_draft(self):
        """POST /api/spaces/assist-listing returns HTTP 200 with listing_draft object."""
        payload = {
            "text": "2 bedroom workspace in Pune for 4 people with fast WiFi and AC",
            "language": "en"
        }
        res = self.client.post("/api/spaces/assist-listing", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertIn("listing_draft", data)
        draft = data["listing_draft"]
        self.assertEqual(draft["bedrooms"], 2)
        self.assertEqual(draft["city"], "Pune")
        self.assertEqual(draft["max_capacity"], 4)
        self.assertIsNone(draft["price_hourly"])


if __name__ == "__main__":
    unittest.main()
