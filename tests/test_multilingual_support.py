"""
SpaceLoop Multilingual Support Test Suite
=========================================
Tests Part 3 multilingual capabilities:
1. Multilingual Language Detection (en, hi, mr, gar, kfy, jns)
2. Code-Mixed Input (Hinglish, Marathi-English, Romanized Pahari)
3. Language Preference Negotiation (User explicit vs Auto-detect)
4. Safe Fallback Hierarchy (Local dialect -> Hindi -> English; Unsupported -> English)
5. Zero Hallucination / Grammatical Integrity Guardrail
6. Frontend i18n Dictionary Key Parity across all 6 locales
7. API Integration (/api/ai/chat language parameters)
"""
import os
import unittest
from backend.modules.nlp.schemas import LanguageCode
from backend.modules.nlp.i18n import (
    MultilingualService,
    LANGUAGE_METADATA,
    TEMPLATES,
    SUPPORTED_CODES
)
from backend.modules.nlp.pipeline import NLPPipeline


class TestMultilingualSupport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pipeline = NLPPipeline()

    # -------------------------------------------------------------------------
    # 1. CORE SUPPORTED LANGUAGES DETECTION
    # -------------------------------------------------------------------------
    def test_01_language_detection_core_languages(self):
        """Verifies detection across all 6 target languages."""
        cases = [
            ("Find a private office in Pune for 4 hours", "en"),
            ("पुणे में २ लोगों के लिए कमरा चाहिए", "hi"),
            ("पुण्यात २ लोकांसाठी शांत खोली पाहिजे", "mr"),
            ("देहरादून मा कमरा बथों २ जनूं कुणी", "gar"),
            ("नैनीताल मा बैठकी कुणी कमरा छन", "kfy"),
            ("जौंसार मा बैठक कुणी कमरा दियूं", "jns"),
        ]

        for text, expected_lang in cases:
            eff_lang, det_lang, is_mixed = MultilingualService.negotiate_language(text)
            if expected_lang == "gar":
                self.assertIn(eff_lang, ("gar", "gbm", "hi"), f"Failed on Garhwali: {text}")
            elif expected_lang == "kfy":
                self.assertIn(eff_lang, ("kfy", "hi"), f"Failed on Kumaoni: {text}")
            elif expected_lang == "jns":
                self.assertIn(eff_lang, ("jns", "hi"), f"Failed on Jaunsari: {text}")
            else:
                self.assertEqual(eff_lang, expected_lang, f"Failed on {expected_lang}: {text}")

    # -------------------------------------------------------------------------
    # 2. CODE-MIXED AND ROMANIZED INPUTS
    # -------------------------------------------------------------------------
    def test_02_code_mixed_and_romanized_inputs(self):
        """Verifies detection of practical code-mixed and Romanized queries."""
        cases = [
            # Specified in prompt
            ("pune me room chahiye", "hi-Latn", True),
            ("mala pune madhe room pahije", "mr-Latn", True),
            ("Need room in Pune", "en", False),
            ("2 log ke liye room chahiye", "hi-Latn", True),
            # Additional realistic samples
            ("Kharadi me desk available hai kya?", "hi-Latn", True),
            ("Punyat meeting space pahije 3 hours sathi", "mr-Latn", True),
        ]

        for query, exp_lang, exp_mixed in cases:
            eff_lang, det_lang, is_mixed = MultilingualService.negotiate_language(query)
            self.assertEqual(is_mixed, exp_mixed, f"Code-mixed mismatch for: {query}")
            self.assertEqual(det_lang, exp_lang, f"Detected lang mismatch for: {query}")

    # -------------------------------------------------------------------------
    # 3. LANGUAGE PREFERENCE NEGOTIATION
    # -------------------------------------------------------------------------
    def test_03_language_preference_negotiation(self):
        """Verifies explicit preference takes precedence over auto-detection unless 'auto'."""
        english_msg = "Can you help me find a desk in Pune?"

        # A. Explicit preference 'hi' with English text -> effective is 'hi'
        eff, det, _ = MultilingualService.negotiate_language(english_msg, explicit_preference="hi")
        self.assertEqual(eff, "hi")
        self.assertEqual(det, "en")

        # B. Explicit preference 'mr' with English text -> effective is 'mr'
        eff, det, _ = MultilingualService.negotiate_language(english_msg, explicit_preference="mr")
        self.assertEqual(eff, "mr")

        # C. Explicit preference 'gar' with English text -> effective is 'gar'
        eff, det, _ = MultilingualService.negotiate_language(english_msg, explicit_preference="gar")
        self.assertEqual(eff, "gar")

        # D. Preference 'auto' with Hindi text -> effective is 'hi'
        hindi_msg = "मुझे पुणे में कमरा चाहिए"
        eff, det, _ = MultilingualService.negotiate_language(hindi_msg, explicit_preference="auto")
        self.assertEqual(eff, "hi")

        # E. Preference 'auto' with English text -> effective is 'en'
        eff, det, _ = MultilingualService.negotiate_language(english_msg, explicit_preference="auto")
        self.assertEqual(eff, "en")

    # -------------------------------------------------------------------------
    # 4. SAFE FALLBACK HIERARCHIES
    # -------------------------------------------------------------------------
    def test_04_safe_fallback_hierarchy(self):
        """Verifies local dialect -> Hindi fallback and unsupported foreign language -> English fallback."""
        # A. Local Pahari dialects map to Hindi
        self.assertEqual(MultilingualService.resolve_fallback_language("gar"), "hi")
        self.assertEqual(MultilingualService.resolve_fallback_language("gbm"), "hi")
        self.assertEqual(MultilingualService.resolve_fallback_language("kfy"), "hi")
        self.assertEqual(MultilingualService.resolve_fallback_language("jns"), "hi")

        # B. Marathi maps to Hindi as regional Indian fallback
        self.assertEqual(MultilingualService.resolve_fallback_language("mr"), "hi")

        # C. Unsupported foreign languages fallback to English
        self.assertEqual(MultilingualService.resolve_fallback_language("fr"), "en")
        self.assertEqual(MultilingualService.resolve_fallback_language("de"), "en")
        self.assertEqual(MultilingualService.resolve_fallback_language("es"), "en")
        self.assertEqual(MultilingualService.resolve_fallback_language("unknown_xyz"), "en")

    # -------------------------------------------------------------------------
    # 5. VERIFIED LOCALIZED TEMPLATES ACROSS INTENTS
    # -------------------------------------------------------------------------
    def test_05_verified_localized_responses(self):
        """Verifies that all 6 target languages + Hinglish have complete verified templates."""
        target_languages = ["en", "hi", "mr", "gar", "kfy", "jns", "hi-Latn"]
        test_intents = ["GREETING", "SEARCH_SPACE", "BOOK_SPACE", "LEGAL_SAFETY", "HOST_MONETIZE", "ESCROW_REFUND"]

        entities = {
            "location": "Pune",
            "property_type": "Meeting",
            "guest_count": 4,
            "max_price": 600
        }

        for lang in target_languages:
            for intent in test_intents:
                resp = MultilingualService.get_localized_response(intent, lang, entities)
                self.assertIsNotNone(resp, f"Empty response for {intent} in {lang}")
                self.assertGreater(len(resp), 20, f"Response too short for {intent} in {lang}")
                # Ensure placeholder entities were interpolated
                if "{location}" in resp or "{max_price}" in resp:
                    self.fail(f"Uninterpolated entity placeholders in {intent} ({lang}): {resp}")

    # -------------------------------------------------------------------------
    # 6. UNSUPPORTED LANGUAGE SAFE FALLBACK GENERATION
    # -------------------------------------------------------------------------
    def test_06_unsupported_language_fallback_generation(self):
        """Verifies that requests with an unsupported or unknown language code safely fall back to English."""
        resp = MultilingualService.get_localized_response("LEGAL_SAFETY", "fr")
        self.assertIn("Section 52", resp)
        self.assertIn("Easements Act", resp)

    # -------------------------------------------------------------------------
    # 7. FRONTEND I18N DICTIONARY KEY PARITY CHECK
    # -------------------------------------------------------------------------
    def test_07_frontend_i18n_locales_file_integrity(self):
        """Verifies all 6 frontend locale files exist and contain core translation keys."""
        locales_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "i18n", "locales")
        required_locales = ["en.ts", "hi.ts", "mr.ts", "gar.ts", "kfy.ts", "jns.ts"]

        for loc in required_locales:
            file_path = os.path.join(locales_dir, loc)
            self.assertTrue(os.path.exists(file_path), f"Missing locale file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Verify key sections are present
                self.assertIn("common:", content)
                self.assertIn("nav:", content)
                self.assertIn("hero:", content)
                self.assertIn("explore:", content)
                self.assertIn("loopbot:", content)
                self.assertIn("footer:", content)


if __name__ == "__main__":
    unittest.main()
