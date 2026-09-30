"""
SpaceLoop NLP Part 5 — Multilingual Support Test Suite
======================================================
Verifies:
1. Multi-script language detection across English, Hindi, Marathi, Garhwali, Kumaoni, Hinglish, Marathi-English.
2. Loop Bot multilingual handling and safe Pahari fallback hierarchy.
3. Multilingual semantic search query parsing and zero-duplicate database search against existing listings.
4. Multilingual listing assistance factual extraction with strict zero-hallucination.
5. Strict preservation of critical data (prices, numbers, addresses, URLs, listing IDs, technical terms).
"""
import unittest
from app import create_app
from models import db, Space, User
from backend.modules.nlp.language_detection import LanguageDetectionService
from backend.modules.nlp.i18n import MultilingualService
from backend.modules.nlp.listing_assistance import ListingAssistanceService
from backend.modules.nlp.pipeline import NLPPipeline
from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query
from backend.modules.search import understand_search_query, hybrid_search_spaces


class TestNLPMultilingualPart5(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    # =========================================================================
    # 1. LANGUAGE DETECTION TESTS
    # =========================================================================

    def test_language_detection_english(self):
        """Pure English queries are accurately detected as 'en'."""
        text = "Find a quiet meeting room for 6 people in Pune with fast wifi and whiteboard"
        lang, _, is_cm, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "en")
        self.assertFalse(is_cm)
        self.assertGreaterEqual(conf, 0.75)

    def test_language_detection_hindi_devanagari(self):
        """Devanagari Hindi queries are accurately detected as 'hi'."""
        text = "मुझे पुणे में 4 लोगों के लिए शांत वर्कस्पेस चाहिए"
        lang, _, is_cm, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "hi")
        self.assertGreaterEqual(conf, 0.70)

    def test_language_detection_marathi_devanagari(self):
        """Devanagari Marathi queries with distinctive tokens or ळ are detected as 'mr'."""
        text = "मला पुण्यात 4 लोकांसाठी वायफाय असलेली शांत जागा पाहिजे"
        lang, _, is_cm, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "mr")
        self.assertGreaterEqual(conf, 0.70)

    def test_language_detection_garhwali_regional(self):
        """Central Pahari / Garhwali regional markers are accurately detected as 'gbm'."""
        text = "नमस्कार भैजी, कख कमरो मिलल? म्येरु घौर देहरादून मा च"
        lang, _, _, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "gbm")
        self.assertGreaterEqual(conf, 0.70)

    def test_language_detection_kumaoni_regional(self):
        """Central Pahari / Kumaoni regional markers are accurately detected as 'kfy'."""
        text = "पैलाग दाज्यु, नैनीताल मा कमरो खोजण छ, कसिक मिलल?"
        lang, _, _, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "kfy")
        self.assertGreaterEqual(conf, 0.70)

    def test_language_detection_hinglish_code_mixed(self):
        """Romanized Hinglish code-mixed queries are detected as 'hi-Latn' with English secondary."""
        text = "Mujhe Pune me 4 logon ke liye quiet workspace chahiye with good wifi"
        lang, secondaries, is_cm, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "hi-Latn")
        self.assertTrue(is_cm)
        self.assertIn("en", secondaries)

    def test_language_detection_marathi_romanized(self):
        """Romanized Marathi queries are detected as 'mr-Latn'."""
        text = "Mala Punyat 4 lokansathi quiet space pahije"
        lang, _, _, conf = LanguageDetectionService.detect_language(text)
        self.assertEqual(lang, "mr-Latn")

    # =========================================================================
    # 2. LOOP BOT MULTILINGUAL CONVERSATION & SAFE DIALECT BOUNDARIES
    # =========================================================================

    def test_loopbot_responds_in_hindi(self):
        """LoopBot understands Hindi query and responds naturally in Hindi."""
        query = "SpaceLoop क्या है?"
        res = orchestrate_loopbot_query(query, return_dict=True)
        self.assertEqual(res["detected_language"], "hi")
        self.assertEqual(res["response_language"], "hi")
        self.assertIn("SpaceLoop", res["reply"])
        self.assertIn("धारा 52", res["reply"])
        self.assertIn("₹100", res["reply"])

    def test_loopbot_responds_in_marathi(self):
        """LoopBot understands Marathi query and responds naturally in Marathi."""
        query = "SpaceLoop काय आहे?"
        res = orchestrate_loopbot_query(query, return_dict=True)
        self.assertEqual(res["detected_language"], "mr")
        self.assertEqual(res["response_language"], "mr")
        self.assertIn("SpaceLoop", res["reply"])
        self.assertIn("कलम ५२", res["reply"])
        self.assertIn("₹१००", res["reply"])

    def test_loopbot_responds_in_english(self):
        """LoopBot understands English query and responds in English."""
        query = "What is SpaceLoop?"
        res = orchestrate_loopbot_query(query, return_dict=True)
        self.assertEqual(res["detected_language"], "en")
        self.assertEqual(res["response_language"], "en")
        self.assertIn("SpaceLoop is India's premier", res["reply"])
        self.assertIn("Section 52", res["reply"])
        self.assertIn("₹100", res["reply"])

    def test_loopbot_garhwali_safe_dialect_boundary(self):
        """For Garhwali queries, LoopBot uses authentic localized greeting without broken hallucinations."""
        query = "नमस्कार भैजी, स्पेस लूप मा कमरो बथौ"
        res = orchestrate_loopbot_query(query, return_dict=True)
        self.assertIn(res["detected_language"], ["gbm", "gar"])
        self.assertTrue("भैजी" in res["reply"] or "नमस्ते" in res["reply"] or "SpaceLoop" in res["reply"])
        self.assertIn("धारा 52", res["reply"])

    # =========================================================================
    # 3. MULTILINGUAL SEMANTIC SEARCH QUERY HANDLING (ZERO DUPLICATE DB)
    # =========================================================================

    def test_semantic_search_hindi_query_understanding(self):
        """Hindi search query extracts canonical constraints and bridges semantic keywords."""
        query = "पुणे में 4 लोगों के लिए वाईफाई वाला ऑफिस"
        understood = understand_search_query(query)
        self.assertEqual(understood["location"], "Pune")
        self.assertEqual(understood["capacity"], 4)
        self.assertEqual(understood["space_type"], "Workspace")
        self.assertIn("Wi-Fi", understood["amenities"])
        self.assertIsNone(understood["max_price"])

    def test_semantic_search_marathi_query_understanding(self):
        """Marathi search query extracts canonical constraints and bridges semantic keywords."""
        query = "पुण्यात 4 लोकांसाठी वायफाय असलेली वर्कस्पेस"
        understood = understand_search_query(query)
        self.assertEqual(understood["location"], "Pune")
        self.assertEqual(understood["capacity"], 4)
        self.assertEqual(understood["space_type"], "Workspace")
        self.assertIn("Wi-Fi", understood["amenities"])

    def test_semantic_search_executes_against_existing_listings_without_duplicates(self):
        """Multilingual queries match directly against existing DB listings with no fake/duplicate rows."""
        initial_space_count = Space.query.count()

        # Execute search in Hindi via hybrid search engine
        search_res = hybrid_search_spaces(
            raw_query="पुणे में 4 लोगों के लिए वाईफाई वाला ऑफिस",
            limit=5
        )
        self.assertIsInstance(search_res, dict)
        self.assertIn("results", search_res)

        # Database space count must remain strictly unchanged (no fake/duplicate translated rows created)
        final_space_count = Space.query.count()
        self.assertEqual(initial_space_count, final_space_count)

    # =========================================================================
    # 4. LISTING ASSISTANCE MULTILINGUAL INPUT (ZERO HALLUCINATION)
    # =========================================================================

    def test_listing_assistance_hindi_description(self):
        """Listing assistance parses Hindi description, extracting only explicitly provided facts."""
        text = "पुणे में 4 लोगों के लिए 2 बेडरूम वर्कस्पेस, तेज वाईफाई और एसी के साथ"
        assist_result = ListingAssistanceService.assist_listing(text)
        self.assertTrue(assist_result["success"])
        draft = assist_result["listing_draft"]

        # Extracted fields
        self.assertEqual(draft["bedrooms"], 2)
        self.assertEqual(draft["max_capacity"], 4)
        self.assertEqual(draft["location"], "Pune")
        self.assertEqual(draft["category"], "Workspace")
        self.assertIn("High-speed Wi-Fi", draft["amenities"])
        self.assertIn("Air Conditioning", draft["amenities"])

        # Unstated fields MUST remain None (Zero-hallucination)
        self.assertIsNone(draft["price_hourly"])
        self.assertIsNone(draft["price_monthly"])
        self.assertIsNone(draft["sqft"])

    def test_listing_assistance_marathi_description(self):
        """Listing assistance parses Marathi description, extracting only explicitly provided facts."""
        text = "पुण्यात 4 लोकांसाठी 2 बेडरूम वर्कस्पेस, जलद वायफाय आणि एसी सह"
        assist_result = ListingAssistanceService.assist_listing(text)
        self.assertTrue(assist_result["success"])
        draft = assist_result["listing_draft"]

        # Extracted fields
        self.assertEqual(draft["bedrooms"], 2)
        self.assertEqual(draft["max_capacity"], 4)
        self.assertEqual(draft["location"], "Pune")
        self.assertEqual(draft["category"], "Workspace")
        self.assertIn("High-speed Wi-Fi", draft["amenities"])
        self.assertIn("Air Conditioning", draft["amenities"])

        # Zero-hallucination verification
        self.assertIsNone(draft["price_hourly"])
        self.assertIsNone(draft["price_monthly"])
        self.assertIsNone(draft["sqft"])

    # =========================================================================
    # 5. CRITICAL DATA PRESERVATION MANDATE
    # =========================================================================

    def test_critical_data_preservation_in_translation(self):
        """Prices, numbers, addresses, URLs, IDs, and legal identifiers are NEVER altered."""
        title = "Baner Executive Desk #104 in Pune"
        desc = (
            "Private desk at Baner, Pune for 4 people at ₹45/hr. "
            "Includes ₹100 refundable UPI micro-escrow governed under Section 52. "
            "Visit /dashboard to view your digital door pass."
        )
        amenities = ["High-speed Wi-Fi", "Air Conditioning"]

        # Translate to Hindi
        hi_trans = ListingAssistanceService.translate_listing_content(title, desc, amenities, target_language="hi")
        hi_desc = hi_trans["description"]

        # Strict data preservation checks
        self.assertIn("₹45/hr", hi_desc)
        self.assertIn("₹100", hi_desc)
        self.assertIn("4 people", hi_desc)
        self.assertIn("Baner, Pune", hi_desc)
        self.assertIn("Section 52", hi_desc)
        self.assertIn("/dashboard", hi_desc)
        self.assertIn("#104", hi_trans["title"])

        # Translate to Marathi
        mr_trans = ListingAssistanceService.translate_listing_content(title, desc, amenities, target_language="mr")
        mr_desc = mr_trans["description"]

        self.assertIn("₹45/hr", mr_desc)
        self.assertIn("₹100", mr_desc)
        self.assertIn("4 people", mr_desc)
        self.assertIn("Baner, Pune", mr_desc)
        self.assertIn("Section 52", mr_desc)
        self.assertIn("/dashboard", mr_desc)
        self.assertIn("#104", mr_trans["title"])


if __name__ == "__main__":
    unittest.main()
