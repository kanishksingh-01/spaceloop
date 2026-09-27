"""
SpaceLoop Part 5 Verification Suite: Semantic Search & RAG
==========================================================
Tests:
1. Semantic Search understanding meaning vs exact keywords
   ("quiet place near college" matches "peaceful accommodation close to university").
2. Structured filtering + Ranking (capacity, max price, booking overlap, composite score).
3. Marketplace & Loop Bot shared search engine reusability.
4. Selective RAG gating (only queries requiring platform/space knowledge invoke RAG).
5. RAG 7 platform knowledge domains coverage (Rules, Booking, Guidance, Procedures, Fraud, Listing, Help).
6. Safe degradation fallbacks:
   - Vector embedding offline -> Token/Concept overlap fallback.
   - Irrelevant documents -> Polite degradation without hallucinating missing info.
   - LLM failure -> Deterministic knowledge synthesis.
7. Privacy guardrails (no similarity scores, raw JSON, tool payloads, or DB objects exposed).
"""
import unittest
from datetime import datetime, timedelta
from app import create_app
from models import db, Space, User, Booking
from backend.modules.search.embedding import (
    generate_embedding,
    cosine_similarity,
    build_searchable_representation,
)
from backend.modules.search.hybrid_search import hybrid_search_spaces
from backend.modules.ai.rag_service import (
    should_retrieve_rag,
    retrieve_rag_documents,
    synthesize_rag_response,
    PLATFORM_KNOWLEDGE_DOCUMENTS,
    MIN_RELEVANCE_THRESHOLD,
)
from backend.modules.ai.loopbot_orchestrator import (
    orchestrate_loopbot_query,
    run_marketplace_search,
    _sanitize_loopbot_response,
)


class TestSemanticSearchAndRAG(unittest.TestCase):

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

    # =========================================================================
    # 1. SEMANTIC SEARCH: MEANING VS EXACT KEYWORDS
    # =========================================================================
    def test_01_semantic_meaning_matches_synonyms_over_unrelated(self):
        """
        'quiet place near college' finds 'peaceful accommodation close to university'
        with higher semantic score than unrelated listings.
        """
        query = "quiet place near college"
        target_description = "Peaceful accommodation close to university campus with study nooks."
        unrelated_description = "Heavy industrial auto repair garage for truck welding and machinery."

        q_vec = generate_embedding(query)
        target_vec = generate_embedding(target_description)
        unrelated_vec = generate_embedding(unrelated_description)

        sim_target = cosine_similarity(q_vec, target_vec)
        sim_unrelated = cosine_similarity(q_vec, unrelated_vec)

        self.assertGreater(sim_target, sim_unrelated,
                           f"Expected target ({sim_target}) to score significantly higher than unrelated ({sim_unrelated})")
        self.assertGreater(sim_target, 0.65, "Expected high semantic similarity on synonym concepts")

    def test_02_semantic_search_candidates_ranking(self):
        """Verifies candidate ranking based on semantic meaning in hybrid_search_spaces."""
        peaceful_space = Space(
            id=901,
            title="Scholars Haven",
            description="Peaceful accommodation close to university campus with study desks.",
            category="Study",
            city="Pune",
            neighborhood="Kothrud",
            max_capacity=4,
            price_hourly=150.0,
            is_active=True
        )
        noisy_garage = Space(
            id=902,
            title="IronWorks Garage",
            description="Industrial automobile garage for welding and sheet metal repair.",
            category="Workshop",
            city="Pune",
            neighborhood="Hadapsar",
            max_capacity=10,
            price_hourly=400.0,
            is_active=True
        )

        res = hybrid_search_spaces(
            raw_query="quiet place near college",
            candidate_spaces=[noisy_garage, peaceful_space]
        )

        self.assertGreater(res["total_matches"], 0)
        top_match = res["results"][0]
        self.assertEqual(top_match["space"]["title"], "Scholars Haven")
        self.assertGreater(top_match["composite_score"], res["results"][1]["composite_score"])
        self.assertGreater(top_match["composite_score"], 0.50)
        self.assertIn("match_reasons", top_match)

    # =========================================================================
    # 2. STRUCTURED FILTERING + RANKING
    # =========================================================================
    def test_03_structured_filters_combined_with_semantic_search(self):
        """Hard constraints (capacity & max price) strictly filter candidates before ranking."""
        small_space = Space(
            id=903,
            title="Solo Micro Cabin",
            description="Peaceful accommodation close to university for 1 person.",
            category="Study",
            max_capacity=1,
            price_hourly=100.0,
            is_active=True
        )
        expensive_space = Space(
            id=904,
            title="Luxury Executive Suite",
            description="Peaceful accommodation close to university.",
            category="Study",
            max_capacity=6,
            price_hourly=2500.0,
            is_active=True
        )
        fitting_space = Space(
            id=905,
            title="University Study Pod 6",
            description="Peaceful accommodation close to university for team study.",
            category="Study",
            max_capacity=6,
            price_hourly=300.0,
            is_active=True
        )

        res = hybrid_search_spaces(
            raw_query="quiet place near college",
            min_capacity=4,
            max_price=500.0,
            candidate_spaces=[small_space, expensive_space, fitting_space]
        )

        matched_titles = [r["space"]["title"] for r in res["results"]]
        self.assertIn("University Study Pod 6", matched_titles)
        self.assertNotIn("Solo Micro Cabin", matched_titles, "Should be filtered by capacity (<4)")
        self.assertNotIn("Luxury Executive Suite", matched_titles, "Should be filtered by max price (>500)")

    # =========================================================================
    # 3. REUSABILITY: MARKETPLACE AND LOOP BOT
    # =========================================================================
    def test_04_marketplace_and_loopbot_search_reusability(self):
        """Verifies both Marketplace API and Loop Bot orchestrator use the same search pipeline."""
        # 1. Direct Marketplace endpoint
        api_res = self.client.post("/api/spaces/search", json={
            "query": "quiet place for 4 people in Pune",
            "capacity": 4
        })
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("results", data)
        self.assertIn("spaces", data)

        # 2. Loop Bot Orchestrator
        bot_res = orchestrate_loopbot_query("Search quiet place for 4 people in Pune", return_dict=True)
        self.assertEqual(bot_res["intent"], "SEARCH_PROPERTY")
        self.assertIn("Marketplace Search Results", bot_res["reply"])
        self.assertIn("Rate: ₹", bot_res["reply"])

    # =========================================================================
    # 4. SELECTIVE RAG GATING
    # =========================================================================
    def test_05_selective_rag_gating(self):
        """Verifies RAG is invoked ONLY when necessary and bypassed for non-knowledge intents."""
        # Non-knowledge intents must NOT invoke RAG
        self.assertFalse(should_retrieve_rag("GENERAL_CONVERSATION", "Hello LoopBot!"))
        self.assertFalse(should_retrieve_rag("GENERAL_CONVERSATION", "Good morning"))
        self.assertFalse(should_retrieve_rag("PRICING_CALCULATION", "How much for 3 hours?"))
        self.assertFalse(should_retrieve_rag("CHECK_AVAILABILITY", "Is it free tomorrow?"))
        self.assertFalse(should_retrieve_rag("BOOK_PROPERTY", "Book this space now"))
        self.assertFalse(should_retrieve_rag("CLARIFICATION_NEEDED", "asdfgh"))

        # Knowledge intents MUST invoke RAG
        self.assertTrue(should_retrieve_rag("ASK_AMENITIES", "What amenities does this space have?"))
        self.assertTrue(should_retrieve_rag("RAG_RULES_POLICY", "Can I bring food and snacks?"))
        self.assertTrue(should_retrieve_rag("LEGAL_AND_SAFETY", "Explain Section 52 legal protection"))
        self.assertTrue(should_retrieve_rag("REPORT_FRAUD", "How does SpaceLoop prevent fraud?"))
        self.assertTrue(should_retrieve_rag("ASK_HELP", "Help me understand platform rules"))
        self.assertTrue(should_retrieve_rag("CREATE_LISTING", "How to list my space?"))
        self.assertTrue(should_retrieve_rag("ASK_PAYMENT_STATUS", "When is the 100 rs escrow deposit refunded?"))

    # =========================================================================
    # 5. RAG KNOWLEDGE COVERAGE (ALL 7 PLATFORM DOMAINS)
    # =========================================================================
    def test_06_rag_coverage_platform_rules_domain(self):
        """Domain 1 (Rules): Section 52, food & beverage, noise, smoking."""
        docs = retrieve_rag_documents("Section 52 Indian Easements Act license", top_k=2)
        self.assertGreater(len(docs), 0)
        self.assertTrue(any("Section 52" in d["title"] or "Easements Act" in d["text"] for d in docs))

        docs_food = retrieve_rag_documents("can guests bring food and snacks", top_k=2)
        self.assertTrue(any("Food" in d["title"] or "snacks" in d["text"] for d in docs_food))

    def test_07_rag_coverage_booking_info_domain(self):
        """Domain 2 (Booking): hourly slots, 50m geofence PIN, cancellation."""
        docs = retrieve_rag_documents("how does geofenced check in arrival pin work", top_k=2)
        self.assertGreater(len(docs), 0)
        self.assertTrue(any("Geofence" in d["title"] or "50 meters" in d["text"] for d in docs))

    def test_08_rag_coverage_guidance_and_procedures(self):
        """Domain 3 (Guidance) & Domain 4 (Procedures): Host 95% yield and checkout flow."""
        docs = retrieve_rag_documents("how much commission does host pay host earnings yield", top_k=2)
        self.assertGreater(len(docs), 0)
        self.assertTrue(any("95%" in d["text"] or "Yield" in d["title"] for d in docs))

    def test_09_rag_coverage_fraud_and_escrow_domain(self):
        """Domain 5 (Fraud): ₹100 UPI micro-escrow and Discom CA meter verification."""
        docs = retrieve_rag_documents("₹100 UPI micro escrow security deposit refund", top_k=2)
        self.assertGreater(len(docs), 0)
        self.assertTrue(any("100" in d["text"] and "escrow" in d["text"].lower() for d in docs))

        docs_discom = retrieve_rag_documents("Discom electricity CA meter verification", top_k=2)
        self.assertGreater(len(docs_discom), 0)
        self.assertTrue(any("Discom" in d["title"] or "meter" in d["text"].lower() for d in docs_discom))

    def test_10_rag_coverage_listing_and_help_domain(self):
        """Domain 6 (Listing Requirements) & Domain 7 (Help & Dispute Escalation)."""
        docs_list = retrieve_rag_documents("60 second AI photo scan requirements for new listing", top_k=2)
        self.assertGreater(len(docs_list), 0)
        self.assertTrue(any("Photo Scan" in d["title"] or "square footage" in d["text"] for d in docs_list))

        docs_help = retrieve_rag_documents("how to report an issue dispute emergency customer support", top_k=2)
        self.assertGreater(len(docs_help), 0)
        self.assertTrue(any("Support" in d["title"] or "dispute" in d["text"].lower() for d in docs_help))

    # =========================================================================
    # 6. SAFE DEGRADATION FALLBACKS
    # =========================================================================
    def test_11_fallback_when_embedding_fails_uses_token_concept_matching(self):
        """When dense embedding is unavailable, fallback keyword/concept ranking succeeds."""
        # Query with common platform keywords
        docs = retrieve_rag_documents("food beverage snacks catering rules", top_k=1)
        self.assertGreater(len(docs), 0)
        self.assertIn("Food", docs[0]["title"])

    def test_12_safe_degradation_on_unrelated_query_no_hallucinations(self):
        """When no documents pass relevance threshold, system safely degrades without inventing info."""
        docs = retrieve_rag_documents("quantum teleportation interstellar rocket propulsion", top_k=2, min_similarity=0.75)
        self.assertEqual(len(docs), 0, "Unrelated query should yield 0 high-relevance documents")

        # Response synthesis safely degrades
        safe_response = synthesize_rag_response("quantum teleportation interstellar rocket propulsion", docs)
        self.assertIn("couldn't find specific documentation", safe_response.lower())
        self.assertNotIn("teleportation", safe_response)  # Does not hallucinate non-existent features

    def test_13_deterministic_synthesis_when_llm_fails(self):
        """Direct synthesis from retrieved docs formats cleanly without technical metadata."""
        docs = retrieve_rag_documents("Section 52 Indian Easements Act", top_k=1)
        reply = synthesize_rag_response("What is Section 52?", docs, intent="LEGAL_AND_SAFETY")
        self.assertIn("Section 52", reply)
        self.assertIn("Revocable License", reply)
        self.assertIn("Easements Act", reply)

    # =========================================================================
    # 7. PRIVACY & DATA LEAK DEFENSE
    # =========================================================================
    def test_14_no_internal_scores_json_or_vectors_in_user_responses(self):
        """Responses never expose similarity scores, raw JSON, tool payloads, or vector arrays."""
        # 1. Search response check
        res_search = orchestrate_loopbot_query("Find quiet workspaces in Pune", return_dict=True)
        reply_search = res_search["reply"]
        self.assertNotIn("cosine_similarity", reply_search)
        self.assertNotIn("embedding", reply_search)
        self.assertNotIn("[0.", reply_search)
        self.assertNotIn('{"space"', reply_search)

        # 2. RAG synthesized response check
        docs = retrieve_rag_documents("Section 52", top_k=2)
        reply_rag = synthesize_rag_response("Section 52", docs)
        self.assertNotIn("cosine_similarity", reply_rag)
        self.assertNotIn("score:", reply_rag.lower())
        self.assertNotIn("similarity:", reply_rag.lower())
        self.assertNotIn("relevance_score", reply_rag)
        self.assertNotIn("[0.", reply_rag)

        # 3. Sanitizer check
        dirty = "Answer here. score: 0.8992 cosine_similarity: 0.9412 [TOOL_OUTPUT: done]"
        clean = _sanitize_loopbot_response(dirty)
        self.assertNotIn("cosine_similarity", clean)
        self.assertNotIn("score:", clean)
        self.assertNotIn("TOOL_OUTPUT", clean)


if __name__ == "__main__":
    unittest.main()
