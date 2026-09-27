"""
SpaceLoop NLP Core Processing Layer Unit Tests
Verifies:
1. Multi-script language detection (English, Hindi, Marathi, Garhwali, Kumaoni, Jaunsari).
2. Code-mixing detection (Hinglish, Marathi-English) and secondary language tagging.
3. Multilingual text normalization (Devanagari digits, currency ₹, number words, colloquial spelling).
4. Deterministic intent extraction across all 10 intent classes.
5. Low-confidence fallback guardrail (CLARIFICATION_NEEDED) preventing intent hallucination.
6. Strict entity validation (locations, guest count bounds, duration limits, budget bounds, listing IDs).
7. End-to-end pipeline structured result output.
"""
import unittest
from backend.modules.nlp import (
    LanguageCode,
    IntentType,
    LanguageDetectionService,
    TextNormalizationService,
    IntentService,
    EntityExtractionService,
    NLPPipeline
)


class TestNLPCore(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. LANGUAGE DETECTION TESTS (Devanagari)
    # -------------------------------------------------------------------------
    def test_01_language_detection_devanagari(self):
        """Verifies script identification and lexical discrimination for Devanagari Indian languages."""
        # 1. Hindi Devanagari
        lang, sec, cm, conf = LanguageDetectionService.detect_language("मुझे पुणे में एक शांत कमरा चाहिए")
        self.assertEqual(lang, LanguageCode.HI.value)
        self.assertFalse(cm)
        self.assertGreaterEqual(conf, 0.75)

        # 2. Marathi Devanagari (Distinctive markers: पाहिजे, आहे, खोली)
        lang_mr, _, _, conf_mr = LanguageDetectionService.detect_language("मला पुण्यात एक खोली पाहिजे आहे")
        self.assertEqual(lang_mr, LanguageCode.MR.value)
        self.assertGreaterEqual(conf_mr, 0.75)

        # 3. Marathi with unique ळ character
        lang_mr2, _, _, _ = LanguageDetectionService.detect_language("बेंगळुरू येथे जागा मिळेल का")
        self.assertEqual(lang_mr2, LanguageCode.MR.value)

        # 4. Garhwali Devanagari (Central Pahari: कख, कमरो, भैजी, बथौ)
        lang_gbm, _, _, conf_gbm = LanguageDetectionService.detect_language("कख कमरो मिलल भैजी बथौ")
        self.assertEqual(lang_gbm, LanguageCode.GBM.value)
        self.assertGreaterEqual(conf_gbm, 0.70)

        # 5. Kumaoni Devanagari (Central Pahari: कसिक, भला, च्यांहूं)
        lang_kfy, _, _, conf_kfy = LanguageDetectionService.detect_language("कसिक छौ भला कमरा च्यांहूं")
        self.assertEqual(lang_kfy, LanguageCode.KFY.value)
        self.assertGreaterEqual(conf_kfy, 0.70)

        # 6. Jaunsari Devanagari (Western/Central Pahari: केथा, बासा, छा)
        lang_jns, _, _, conf_jns = LanguageDetectionService.detect_language("केथा बासा छा जोड़ा खातिर")
        self.assertEqual(lang_jns, LanguageCode.JNS.value)

    # -------------------------------------------------------------------------
    # 2. CODE-MIXING & ROMANIZED TRANSLITERATION TESTS
    # -------------------------------------------------------------------------
    def test_02_language_detection_code_mixing_and_romanized(self):
        """Verifies detection of Hinglish, Marathi-English, Romanized Pahari, and pure English."""
        # 1. Hinglish (Code-Mixed Hindi + English)
        lang, sec, cm, conf = LanguageDetectionService.detect_language("Mujhe Pune me meeting room chahiye 4 hours ke liye")
        self.assertEqual(lang, LanguageCode.HI_LATN.value)
        self.assertTrue(cm)
        self.assertIn("en", sec)
        self.assertGreaterEqual(conf, 0.80)

        # 2. Marathi-English (Code-Mixed Marathi + English)
        lang_mr, sec_mr, cm_mr, _ = LanguageDetectionService.detect_language("Mala Pune madhe office space pahije")
        self.assertEqual(lang_mr, LanguageCode.MR_LATN.value)
        self.assertTrue(cm_mr)
        self.assertIn("en", sec_mr)

        # 3. Romanized Garhwali
        lang_gbm, _, _, _ = LanguageDetectionService.detect_language("Kakh space milal bhaiji batho")
        self.assertEqual(lang_gbm, LanguageCode.GBM_LATN.value)

        # 4. Pure English
        lang_en, sec_en, cm_en, conf_en = LanguageDetectionService.detect_language("Find a quiet desk in Kharadi under ₹500 per hour")
        self.assertEqual(lang_en, LanguageCode.EN.value)
        self.assertFalse(cm_en)
        self.assertEqual(sec_en, [])
        self.assertGreaterEqual(conf_en, 0.85)

    # -------------------------------------------------------------------------
    # 3. TEXT NORMALIZATION TESTS
    # -------------------------------------------------------------------------
    def test_03_text_normalization(self):
        """Verifies Unicode cleaning, digit conversion, currency symbols, and colloquial variations."""
        # 1. Zero-width and control character stripping
        dirty = "meeting\u200b\u200c room\ufeff"
        self.assertEqual(TextNormalizationService.normalize(dirty), "meeting room")

        # 2. Devanagari numerals to ASCII digits
        self.assertEqual(TextNormalizationService.normalize("४ लोग ५ घंटे"), "4 लोग 5 घंटे")

        # 3. Currency standardization to ₹
        self.assertIn("₹500", TextNormalizationService.normalize("under rs 500"))
        self.assertIn("₹400", TextNormalizationService.normalize("below 400 inr"))
        self.assertIn("₹600", TextNormalizationService.normalize("budget 600 rupaye"))
        self.assertIn("₹350/hr", TextNormalizationService.normalize("₹350 per hour"))

        # 4. Multilingual number words normalization
        self.assertIn("2", TextNormalizationService.normalize("for two people"))
        self.assertIn("3", TextNormalizationService.normalize("teen ghante ke liye"))
        self.assertIn("2", TextNormalizationService.normalize("don taas sathi"))

        # 5. Colloquial spelling canonicalization
        self.assertIn("chahiye", TextNormalizationService.normalize("mujhe desk chahye"))
        self.assertIn("please", TextNormalizationService.normalize("plz book this space"))
        self.assertIn("pahije", TextNormalizationService.normalize("mala jaga pahijea"))
        self.assertIn("kahan", TextNormalizationService.normalize("kaha pe space milega"))

    # -------------------------------------------------------------------------
    # 4. MULTILINGUAL INTENT EXTRACTION TESTS
    # -------------------------------------------------------------------------
    def test_04_intent_extraction_multilingual(self):
        """Verifies intent extraction across English, Hindi, Marathi, and Pahari."""
        cases = [
            ("SEARCH_SPACE", "find a meeting room in Kharadi", IntentType.SEARCH_SPACE.value),
            ("SEARCH_SPACE (HI)", "pune me ek study desk chahiye", IntentType.SEARCH_SPACE.value),
            ("SEARCH_SPACE (MR)", "pune madhe meeting sathi jaga pahije", IntentType.SEARCH_SPACE.value),
            ("SEARCH_SPACE (Pahari)", "kamro chyan padhai khatir", IntentType.SEARCH_SPACE.value),
            ("CHECK_AVAILABILITY", "what's available tomorrow for 4 people", IntentType.CHECK_AVAILABILITY.value),
            ("CHECK_AVAILABILITY (HI)", "kal open slots hain kya", IntentType.CHECK_AVAILABILITY.value),
            ("CHECK_AVAILABILITY (MR)", "udya jaga uplabdha aahe ka", IntentType.CHECK_AVAILABILITY.value),
            ("GET_PRICING", "how much for 4 hours at space #4", IntentType.GET_PRICING.value),
            ("GET_PRICING (HI)", "4 ghante ke liye kitna lagega", IntentType.GET_PRICING.value),
            ("GET_PRICING (MR)", "4 taas sathi kiti kharch yeil", IntentType.GET_PRICING.value),
            ("INQUIRE_AMENITIES", "is there wifi and air conditioning", IntentType.INQUIRE_AMENITIES.value),
            ("INQUIRE_AMENITIES (HI)", "kya wifi aur power backup milega", IntentType.INQUIRE_AMENITIES.value),
            ("INQUIRE_RULES", "can i bring food and eat inside", IntentType.INQUIRE_RULES.value),
            ("INQUIRE_RULES (HI)", "kya khana la sakte hain", IntentType.INQUIRE_RULES.value),
            ("BOOK_SPACE", "book this space now", IntentType.BOOK_SPACE.value),
            ("BOOK_SPACE (HI)", "ye space book karna hai", IntentType.BOOK_SPACE.value),
            ("COMPARE_SPACES", "compare space #3 and space #4", IntentType.COMPARE_SPACES.value),
            ("HOST_MONETIZE", "how to monetize my empty garage on spaceloop", IntentType.HOST_MONETIZE.value),
            ("LEGAL_SAFETY", "how does section 52 protect me from squatters", IntentType.LEGAL_SAFETY.value),
            ("GENERAL_GREETING", "hello loopbot", IntentType.GENERAL_GREETING.value),
            ("GENERAL_GREETING (HI)", "namaste kaise ho", IntentType.GENERAL_GREETING.value),
            ("GENERAL_GREETING (MR)", "namaskar kashi aahat", IntentType.GENERAL_GREETING.value),
            ("GENERAL_GREETING (Pahari)", "pranam bhaiji bhal chho", IntentType.GENERAL_GREETING.value)
        ]

        for desc, text, expected_intent in cases:
            norm = TextNormalizationService.normalize(text)
            intent, conf = IntentService.extract_intent(norm)
            self.assertEqual(intent, expected_intent, f"Failed for case: {desc} ('{text}')")
            self.assertGreaterEqual(conf, 0.70)

    # -------------------------------------------------------------------------
    # 5. LOW-CONFIDENCE CLARIFICATION GUARDRAIL TESTS
    # -------------------------------------------------------------------------
    def test_05_low_confidence_clarification_guardrail(self):
        """Verifies that ambiguous, noisy, or unparseable queries trigger CLARIFICATION_NEEDED."""
        unclear_inputs = [
            "asdfghjkl qwerty 123",
            "??? !!! ...",
            "tell me something random",
            "just testing",
            "x"
        ]

        for inp in unclear_inputs:
            norm = TextNormalizationService.normalize(inp)
            intent, conf = IntentService.extract_intent(norm)
            self.assertEqual(
                intent,
                IntentType.CLARIFICATION_NEEDED.value,
                f"Expected clarification for input '{inp}', got {intent}"
            )
            self.assertLessEqual(conf, 0.60)

    # -------------------------------------------------------------------------
    # 6. STRICT ENTITY EXTRACTION & BOUNDARY VALIDATION TESTS
    # -------------------------------------------------------------------------
    def test_06_entity_extraction_and_strict_validation(self):
        """Verifies factual extraction and strict domain range validation."""
        # 1. Comprehensive valid query
        query = "Need a meeting room for 6 people in Kharadi under ₹800 for 4 hours tomorrow"
        norm = TextNormalizationService.normalize(query)
        entities = EntityExtractionService.extract_entities(norm)

        self.assertEqual(entities.location, "Kharadi, Pune")
        self.assertEqual(entities.property_type, "Meeting")
        self.assertEqual(entities.guest_count, 6)
        self.assertEqual(entities.max_price, 800.0)
        self.assertEqual(entities.duration_hours, 4.0)
        self.assertEqual(entities.date_str, "tomorrow")

        # 2. Strict Boundary Rejection
        # A. Absurd guest count (> 500) must be rejected
        absurd_guests = "Need room for 5000 people in Pune"
        ent_ag = EntityExtractionService.extract_entities(TextNormalizationService.normalize(absurd_guests))
        self.assertIsNone(ent_ag.guest_count, "Absurd capacity > 500 should be rejected!")

        # B. Absurd duration (> 168 hours / 7 days maximum) must be rejected
        absurd_dur = "Need space for 300 hours in Delhi"
        ent_ad = EntityExtractionService.extract_entities(TextNormalizationService.normalize(absurd_dur))
        self.assertIsNone(ent_ad.duration_hours, "Duration > 168h should be rejected!")

        # C. Price below ₹5 minimum must be rejected
        absurd_price = "Need desk under ₹2 in Hauz Khas"
        ent_ap = EntityExtractionService.extract_entities(TextNormalizationService.normalize(absurd_price))
        self.assertIsNone(ent_ap.max_price, "Price < ₹5 should be rejected!")

        # 3. Listing ID Extraction
        listing_query = "Calculate pricing for space #4 for 2 hours"
        ent_l = EntityExtractionService.extract_entities(TextNormalizationService.normalize(listing_query))
        self.assertEqual(ent_l.listing_id, 4)
        self.assertEqual(ent_l.duration_hours, 2.0)

        # 4. Amenities Extraction
        amen_query = "Looking for a studio with wifi, ac, and power backup in Bandra"
        ent_am = EntityExtractionService.extract_entities(TextNormalizationService.normalize(amen_query))
        self.assertIn("High-Speed Wi-Fi", ent_am.amenities)
        self.assertIn("Air Conditioning", ent_am.amenities)
        self.assertIn("Power Backup", ent_am.amenities)
        self.assertEqual(ent_am.location, "Bandra, Mumbai")

    # -------------------------------------------------------------------------
    # 7. END-TO-END PIPELINE & STRUCTURED RESULT TESTS
    # -------------------------------------------------------------------------
    def test_07_full_pipeline_structured_result(self):
        """Verifies NLPPipeline produces the exact required JSON structure and attributes."""
        raw_msg = "Mujhe Pune me 2 logon ke liye meeting room chahiye under ₹600"
        result = NLPPipeline.process(raw_msg)

        # Verify Typed StructuredNLPResult
        self.assertEqual(result.language, LanguageCode.HI_LATN.value)
        self.assertTrue(result.is_code_mixed)
        self.assertIn("en", result.secondary_languages)
        self.assertEqual(result.intent, IntentType.SEARCH_SPACE.value)
        self.assertGreaterEqual(result.confidence, 0.80)

        # Verify Validated Entities
        self.assertEqual(result.entities.get("location"), "Pune")
        self.assertEqual(result.entities.get("property_type"), "Meeting")
        self.assertEqual(result.entities.get("guest_count"), 2)
        self.assertEqual(result.entities.get("max_price"), 600.0)

        # Verify Serialization
        data = result.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["language"], LanguageCode.HI_LATN.value)
        self.assertTrue(data["isCodeMixed"])
        self.assertEqual(data["intent"], IntentType.SEARCH_SPACE.value)
        self.assertIn("Pune", data["entities"]["location"])


if __name__ == "__main__":
    unittest.main()
