"""
Unit and Integration Test Suite for SpaceLoop Part 6: NLP Listing Assistance
=============================================================================
Tests:
1. Field extraction (English, Hindi, Marathi, Hinglish).
2. Strict factual integrity (user-controlled numbers like ₹25,000 rent remain unedited).
3. Missing field identification & clarification question formulation.
4. Logical inconsistency detection (overcrowding, invalid rent, contradictory terms).
5. Multilingual translation of listings (English, Hindi, Marathi).
6. API endpoints (POST /api/spaces/assist-listing, POST /api/spaces/translate-listing).
7. LoopBot Orchestrator integration for CREATE_LISTING with natural language space details.
"""
import unittest
import json
from app import create_app
from backend.modules.nlp.listing_assistance import ListingAssistanceService
from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query


class TestListingAssistance(unittest.TestCase):

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

    def test_01_extract_listing_fields_english(self):
        """Extract structured fields from standard English prompt."""
        text = "2 bedroom flat in Pune, fully furnished, near IT park, 25k rent"
        res = ListingAssistanceService.assist_listing(text, target_language="en")
        
        self.assertTrue(res["success"])
        fields = res["extracted_fields"]
        self.assertEqual(fields["propertyType"], "flat")
        self.assertEqual(fields["bedrooms"], 2)
        self.assertEqual(fields["location"], "Pune")
        self.assertEqual(fields["city"], "Pune")
        self.assertTrue(fields["furnished"])
        self.assertEqual(fields["near"], "IT park")
        self.assertEqual(fields["rent"], 25000.0)
        self.assertEqual(fields["price_monthly"], 25000.0)
        self.assertGreater(fields["price_hourly"], 0)

    def test_02_extract_listing_fields_devanagari_hindi(self):
        """Extract structured fields from Devanagari Hindi prompt."""
        text = "पुणे में 2 कमरा फ्लैट, पूरी तरह सुसज्जित, आईटी पार्क के पास, 25000 किराया"
        res = ListingAssistanceService.assist_listing(text, target_language="hi")
        
        self.assertTrue(res["success"])
        fields = res["extracted_fields"]
        self.assertEqual(fields["propertyType"], "flat")
        self.assertEqual(fields["bedrooms"], 2)
        self.assertEqual(fields["location"], "Pune")
        self.assertTrue(fields["furnished"])
        self.assertEqual(fields["rent"], 25000.0)

    def test_03_extract_listing_fields_marathi(self):
        """Extract structured fields from Marathi prompt."""
        text = "पुण्यात २ बीएचके फ्लॅट, २५००० भाडं, आयटी पार्क जवळ, सुसज्ज"
        res = ListingAssistanceService.assist_listing(text, target_language="mr")
        
        self.assertTrue(res["success"])
        fields = res["extracted_fields"]
        self.assertEqual(fields["propertyType"], "flat")
        self.assertEqual(fields["bedrooms"], 2)
        self.assertEqual(fields["rent"], 25000.0)
        self.assertEqual(fields["location"], "Pune")
        self.assertTrue(fields["furnished"])

    def test_04_extract_listing_fields_hinglish(self):
        """Extract structured fields from code-mixed Hinglish prompt."""
        text = "Pune me 2 bhk flat near IT park, fully furnished, 25k rent"
        res = ListingAssistanceService.assist_listing(text)
        
        fields = res["extracted_fields"]
        self.assertEqual(fields["propertyType"], "flat")
        self.assertEqual(fields["bedrooms"], 2)
        self.assertEqual(fields["location"], "Pune")
        self.assertEqual(fields["near"], "IT park")
        self.assertEqual(fields["rent"], 25000.0)

    def test_05_strict_factual_integrity_guardrail(self):
        """Factual numbers specified by user (₹25,000 rent) must NEVER be altered."""
        text = "2 bedroom flat in Pune, fully furnished, near IT park, 25k rent"
        res = ListingAssistanceService.assist_listing(text)
        
        # User specified 25,000 rent. Check extracted fields, description, and improved wording.
        self.assertEqual(res["extracted_fields"]["rent"], 25000.0)
        self.assertIn("25,000", res["generated_description"])
        # Ensure hallucinated/drifted numbers do NOT exist in the output
        self.assertNotIn("20,000", res["generated_description"])
        self.assertNotIn("30,000", res["generated_description"])

    def test_06_missing_fields_and_clarification_generation(self):
        """Identify missing critical listing attributes and generate polite clarifications."""
        text = "2 bedroom flat, fully furnished"
        res = ListingAssistanceService.assist_listing(text)
        
        self.assertIn("location", res["missing_fields"])
        self.assertIn("rent", res["missing_fields"])
        self.assertGreater(len(res["clarifications"]), 0)
        
        # Clarification questions should address the missing location/rent
        has_location_prompt = any("location" in q.lower() or "city" in q.lower() for q in res["clarifications"])
        has_rent_prompt = any("rent" in q.lower() or "rate" in q.lower() or "price" in q.lower() for q in res["clarifications"])
        self.assertTrue(has_location_prompt)
        self.assertTrue(has_rent_prompt)

    def test_07_detect_logical_inconsistencies(self):
        """Detect absurd or physically impossible listing configurations."""
        # 1. Overcrowding: 50 people in 50 sq ft
        text_crowded = "Tiny 50 sq ft room for 50 people in Pune, 5k rent"
        res_crowded = ListingAssistanceService.assist_listing(text_crowded)
        self.assertGreater(len(res_crowded["inconsistencies"]), 0)
        self.assertTrue(any("sq ft" in inc["message"].lower() or "crowd" in inc["message"].lower() for inc in res_crowded["inconsistencies"]))

        # 2. Contradictory furnishing
        text_conflict = "Fully furnished unfurnished 1 bhk in Pune, 10k rent"
        res_conflict = ListingAssistanceService.assist_listing(text_conflict)
        self.assertTrue(any("furnish" in inc["message"].lower() for inc in res_conflict["inconsistencies"]))

    def test_08_multilingual_translation(self):
        """Test translating listing title, description, and amenities into Hindi and Marathi."""
        title = "Furnished 2 BHK Flat in Pune near IT park"
        desc = "Modern flat offering 900 sq ft. High-speed WiFi and air conditioning included."
        amenities = ["Fully Furnished", "High-Speed Wi-Fi", "Air Conditioning"]

        # Translate to Hindi
        res_hi = ListingAssistanceService.translate_listing_content(title, desc, amenities, target_language="hi")
        self.assertEqual(res_hi["target_language"], "hi")
        self.assertIn("पुणे", res_hi["title"])
        self.assertTrue(any("वाई-फाई" in a or "सुसज्जित" in a or "वातानुकूलन" in a for a in res_hi["amenities"]))

        # Translate to Marathi
        res_mr = ListingAssistanceService.translate_listing_content(title, desc, amenities, target_language="mr")
        self.assertEqual(res_mr["target_language"], "mr")
        self.assertIn("पुणे", res_mr["title"])

    def test_09_api_assist_listing_endpoint(self):
        """Test POST /api/spaces/assist-listing endpoint."""
        payload = {
            "text": "2 bedroom flat in Pune, fully furnished, near IT park, 25k rent",
            "language": "en"
        }
        res = self.client.post("/api/spaces/assist-listing", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["extracted_fields"]["propertyType"], "flat")
        self.assertEqual(data["extracted_fields"]["rent"], 25000.0)

    def test_10_api_translate_listing_endpoint(self):
        """Test POST /api/spaces/translate-listing endpoint."""
        payload = {
            "title": "2 BHK Flat in Pune",
            "description": "Spacious flat with high speed wifi",
            "amenities": ["Wi-Fi", "Parking"],
            "target_language": "hi"
        }
        res = self.client.post("/api/spaces/translate-listing", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["target_language"], "hi")
        self.assertIn("पुणे", data["title"])

    def test_11_loopbot_orchestrator_listing_assistance(self):
        """LoopBot orchestrator creates a drafted listing when space details are provided."""
        query = "I want to list a 2 bedroom flat in Pune, fully furnished, near IT park, 25k rent"
        res = orchestrate_loopbot_query(query, return_dict=True)
        
        self.assertEqual(res["intent"], "CREATE_LISTING")
        self.assertTrue(res.get("listing_draft"))
        draft = res["listing_draft"]
        self.assertEqual(draft["extracted_fields"]["rent"], 25000.0)
        self.assertIn("25,000", res["reply"])
        self.assertIn("Pune", res["reply"])
        self.assertIn("/list-space", res["reply"])

    def test_12_loopbot_orchestrator_general_monetize_fallback(self):
        """LoopBot orchestrator returns general guidance when no specific space attributes are given."""
        query = "How can I list my garage to earn passive income?"
        res = orchestrate_loopbot_query(query, return_dict=True)
        
        self.assertEqual(res["intent"], "CREATE_LISTING")
        self.assertNotIn("listing_draft", res)
        self.assertIn("95% Yield", res["reply"])
        self.assertIn("/list-space", res["reply"])


if __name__ == "__main__":
    unittest.main()
