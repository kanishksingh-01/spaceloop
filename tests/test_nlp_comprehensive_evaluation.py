"""
SpaceLoop Comprehensive NLP Evaluation Suite
Exhaustive verification of end-to-end NLP capabilities across:
- Natural phrasing & colloquial language
- Synonyms, shorthand, & marketplace abbreviations
- Multi-script & Indic dialect understanding (EN, HI, MR, Garhwali, Kumaoni, Jaunsari, Hinglish)
- Qualitative & quantitative budgets
- Compound times and dates
- Multi-turn conversational state tracking
- RAG grounding and legal escrow safeguards
- Listing extraction & draft generation
- Low-confidence out-of-scope guardrails
"""
import unittest
from app import create_app
from backend.modules.nlp.pipeline import NLPPipeline
from backend.modules.nlp.schemas import IntentType, LanguageCode
from backend.modules.nlp.text_normalization import TextNormalizationService
from backend.modules.nlp.language_detection import LanguageDetectionService
from backend.modules.nlp.intent_service import IntentService
from backend.modules.nlp.entity_extraction import EntityExtractionService
from backend.modules.nlp.context import ConversationalContextManager
from backend.modules.search.query_understanding import understand_search_query
from backend.modules.search.hybrid_search import hybrid_search_spaces
from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query


class TestNLPComprehensiveEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    # -------------------------------------------------------------------------
    # 1. Conversational Phrasing & Natural Expressions
    # -------------------------------------------------------------------------
    def test_messy_natural_conversational_search(self):
        """Tests parsing of messy, unstructured user requests with multiple constraints."""
        query = "Hey, I'm looking for a quiet, sunlit room for 4 people to shoot a podcast in Pune under 2k"
        result = NLPPipeline.process(query)

        self.assertEqual(result.intent, IntentType.SEARCH_SPACE.value)
        self.assertGreaterEqual(result.confidence, 0.75)
        
        entities = result.entities
        self.assertEqual(str(entities.get("location")).lower(), "pune")
        self.assertEqual(entities.get("guest_count"), 4)
        self.assertEqual(entities.get("budget_max"), 2000.0)
        self.assertIn("podcast", result.query_understanding.semantic_query.lower())

    def test_shorthand_and_abbreviations(self):
        """Tests marketplace abbreviations canonicalization (conf rm w/ wifi & ac under 500/hr)."""
        query = "conf rm w/ wifi & ac under 500/hr"
        norm = TextNormalizationService.normalize(query)
        
        self.assertTrue("meeting room" in norm or "conference room" in norm)
        self.assertIn("with", norm)
        self.assertIn("500", norm)

        result = NLPPipeline.process(query)
        self.assertEqual(result.intent, IntentType.SEARCH_SPACE.value)
        self.assertIn("Wi-Fi", result.entities.get("amenities", []))
        self.assertIn("Air Conditioning", result.entities.get("amenities", []))
        self.assertEqual(result.entities.get("budget_max"), 500.0)

    # -------------------------------------------------------------------------
    # 2. Compound Times & Dates
    # -------------------------------------------------------------------------
    def test_compound_time_window_extraction(self):
        """Verifies extraction of complex time window expressions."""
        query = "Need a desk tomorrow from 5pm to 8pm"
        entities = EntityExtractionService.extract_entities(query)
        
        self.assertIsNotNone(entities.time_window)
        self.assertEqual(entities.time_window.start_hour, 17)
        self.assertEqual(entities.time_window.end_hour, 20)
        self.assertEqual(entities.time_window.duration_hours, 3.0)
        self.assertIn("tomorrow", entities.time_window.raw_text.lower())

    # -------------------------------------------------------------------------
    # 3. Qualitative & Quantitative Pricing
    # -------------------------------------------------------------------------
    def test_qualitative_pricing_recognition(self):
        """Verifies recognition of soft/qualitative price signals like 'affordable' and 'cheap'."""
        query = "Find an affordable workspace near metro"
        result = NLPPipeline.process(query)
        
        self.assertTrue(result.entities.get("qualitative_price") in ["affordable", "budget", "cheap"])

    def test_k_notation_and_spoken_thousands(self):
        """Verifies conversion of '3.5k' and 'two thousand' to exact ₹ figures."""
        norm1 = TextNormalizationService.normalize("budget under 3.5k")
        self.assertIn("₹3500", norm1)

        norm2 = TextNormalizationService.normalize("max two thousand rupees")
        self.assertIn("₹2000", norm2)

    # -------------------------------------------------------------------------
    # 4. Multilingual & Indic Dialects
    # -------------------------------------------------------------------------
    def test_multilingual_language_detection(self):
        """Verifies language detection across standard languages and Himalayan dialects."""
        # Marathi Devanagari
        lang_mr, _, _, _ = LanguageDetectionService.detect_language("पुण्यात अभ्यासासाठी शांत खोली पाहिजे")
        self.assertEqual(lang_mr, LanguageCode.MARATHI.value)

        # Hindi Hinglish
        lang_hi, _, is_cm, _ = LanguageDetectionService.detect_language("Mujhe 4 logo ke liye Pune me meeting room chahiye")
        self.assertIn(lang_hi, [LanguageCode.HINDI.value, LanguageCode.HINGLISH.value])
        self.assertTrue(is_cm)

        # Garhwali (Central Pahari)
        lang_gbm, _, _, _ = LanguageDetectionService.detect_language("भला छौ! कख शांत कमरो मिलल?")
        self.assertEqual(lang_gbm, LanguageCode.GARHWALI.value)

        # Kumaoni (Central Pahari)
        lang_kfy, _, _, _ = LanguageDetectionService.detect_language("दाज्यु कसिक छौ? कमरा भोल खाली छन?")
        self.assertEqual(lang_kfy, LanguageCode.KUMAONI.value)

    def test_multilingual_loopbot_conversation(self):
        """Verifies LoopBot converses naturally in Hindi, Marathi, and Pahari."""
        with self.app.app_context():
            # Hindi
            hi_res = orchestrate_loopbot_query("नमस्ते! मुझे एक शांत कमरा चाहिए", return_dict=True)
            self.assertEqual(hi_res["response_language"], LanguageCode.HINDI.value)
            self.assertTrue("परिणाम" in hi_res["reply"] or "कमरा" in hi_res["reply"] or "नमस्ते" in hi_res["reply"] or "उपलब्ध" in hi_res["reply"])

            # Marathi
            mr_res = orchestrate_loopbot_query("नमस्कार! मला पुण्यात खोली पाहिजे", return_dict=True)
            self.assertEqual(mr_res["response_language"], LanguageCode.MARATHI.value)
            self.assertTrue("निकाल" in mr_res["reply"] or "खोली" in mr_res["reply"] or "नमस्कार" in mr_res["reply"] or "उपलब्ध" in mr_res["reply"])

            # Pahari Greeting
            pahari_res = orchestrate_loopbot_query("भला छौ भैजी! स्पेस लूप क्या च?", return_dict=True)
            self.assertGreater(len(pahari_res["reply"]), 20)
            self.assertTrue(
                "भैजी" in pahari_res["reply"] or 
                "भला" in pahari_res["reply"] or 
                "नमस्ते" in pahari_res["reply"] or 
                "SpaceLoop" in pahari_res["reply"] or 
                "धारा 52" in pahari_res["reply"] or 
                "Section 52" in pahari_res["reply"]
            )

    # -------------------------------------------------------------------------
    # 5. Multi-Turn Conversational State Tracking
    # -------------------------------------------------------------------------
    def test_multi_turn_state_refinement(self):
        """Tests incremental constraint refinement across multi-turn user conversation."""
        # Turn 1
        turn1_result = NLPPipeline.process("I need a quiet workspace")
        context_history = [
            {"role": "user", "content": "I need a quiet workspace"},
            {"role": "assistant", "content": "Sure! Which city or area are you looking in?"}
        ]

        # Turn 2: Adds location and amenity
        turn2_result = NLPPipeline.process(
            "Make it in Pune with fast wifi",
            context_data={"history": context_history}
        )
        self.assertEqual(str(turn2_result.entities.get("location")).lower(), "pune")
        self.assertIn("Wi-Fi", turn2_result.entities.get("amenities", []))

        # Turn 3: Adds price constraint
        context_history.extend([
            {"role": "user", "content": "Make it in Pune with fast wifi"},
            {"role": "assistant", "content": "Got it. What is your hourly budget?"}
        ])
        turn3_result = NLPPipeline.process(
            "Under ₹400 per hour",
            context_data={"history": context_history}
        )
        self.assertEqual(str(turn3_result.entities.get("location")).lower(), "pune")
        self.assertIn("Wi-Fi", turn3_result.entities.get("amenities", []))
        self.assertEqual(turn3_result.entities.get("budget_max"), 400.0)

    # -------------------------------------------------------------------------
    # 6. Hybrid Search Integration with QueryUnderstanding
    # -------------------------------------------------------------------------
    def test_hybrid_search_end_to_end(self):
        """Verifies semantic search matches accurately based on IR extracted from natural text."""
        with self.app.app_context():
            search_res = hybrid_search_spaces(
                raw_query="quiet air conditioned study space in pune under 500",
                limit=5
            )
            self.assertIn("results", search_res)
            self.assertGreater(len(search_res["results"]), 0)
            
            top_match = search_res["results"][0]
            self.assertIn("space", top_match)
            self.assertIn("title", top_match["space"])
            self.assertIn("match_score", top_match)
            self.assertGreater(top_match["match_score"], 0)

    # -------------------------------------------------------------------------
    # 7. Listing Assistance & Draft Extraction
    # -------------------------------------------------------------------------
    def test_listing_assistance_end_to_end(self):
        """Verifies extracting listing attributes from unstructured host descriptions."""
        description = (
            "I have a 3 BHK duplex apartment with an open terrace in Baner, Pune. "
            "Fits 12 people comfortably. High-speed optical fiber wifi, 2 split ACs, "
            "and dedicated whiteboards for workshops. Asking ₹450 per hour."
        )
        with self.app.app_context():
            res = orchestrate_loopbot_query(
                f"I want to list my space: {description}",
                return_dict=True
            )
            self.assertEqual(res["intent"], IntentType.CREATE_LISTING.value)
            self.assertIn("listing_draft", res)
            
            draft_payload = res["listing_draft"]
            draft = draft_payload.get("listing_draft") or draft_payload.get("extracted_fields") or draft_payload
            self.assertTrue("Baner" in str(draft.get("location", "")) or "Pune" in str(draft.get("location", "")))
            self.assertTrue(any("wi-fi" in a.lower() or "wifi" in a.lower() for a in draft.get("amenities", [])))
            self.assertTrue(any("ac" in a.lower() or "air conditioning" in a.lower() for a in draft.get("amenities", [])))

    # -------------------------------------------------------------------------
    # 8. RAG Policy & Legal/Escrow Guardrails
    # -------------------------------------------------------------------------
    def test_rag_legal_and_security_grounding(self):
        """Verifies LoopBot answers legal (Section 52) and deposit escrow questions accurately."""
        with self.app.app_context():
            res = orchestrate_loopbot_query(
                "Is this a lease or a license? What about Section 52?",
                return_dict=True
            )
            self.assertEqual(res["intent"], IntentType.LEGAL_SAFETY.value)
            reply = res["reply"]
            self.assertIn("Section 52", reply)
            self.assertIn("Indian Easements Act", reply)
            self.assertIn("license", reply.lower())

    # -------------------------------------------------------------------------
    # 9. Out-of-Scope Guardrails & Non-Hallucination
    # -------------------------------------------------------------------------
    def test_out_of_scope_guardrails(self):
        """Verifies out-of-scope non-marketplace queries trigger clarification without hallucinating."""
        with self.app.app_context():
            # Crypto query
            res_crypto = orchestrate_loopbot_query("Will Ethereum hit 5000 dollars this year?", return_dict=True)
            self.assertEqual(res_crypto["intent"], IntentType.CLARIFICATION_NEEDED.value)
            self.assertTrue(
                "Information Unavailable" in res_crypto["reply"] or "unavailable on SpaceLoop" in res_crypto["reply"]
            )

            # Weather query
            res_weather = orchestrate_loopbot_query("What is the forecast in Mumbai tomorrow?", return_dict=True)
            self.assertEqual(res_weather["intent"], IntentType.CLARIFICATION_NEEDED.value)
            self.assertTrue(
                "Information Unavailable" in res_weather["reply"] or "unavailable on SpaceLoop" in res_weather["reply"]
            )


if __name__ == "__main__":
    unittest.main()
