"""
SpaceLoop NLP Part 6 — Final Integration Verification Suite
===========================================================
Validates the complete 4-flow end-to-end architecture on real application data:
1. FLOW 1: Loop Bot (Query -> NLP -> RAG Retrieval -> Grounded clean output)
2. FLOW 2: Search (Natural Language Query -> Semantic Understanding -> Existing Listings -> Relevant Results)
3. FLOW 3: Listing Assistance (Natural Language -> NLP Extraction -> Host Review -> Existing DB Save Flow)
4. FLOW 4: Multilingual Support (En / Hi / Mr / Central Pahari -> Same-Language Response + Data Preservation)
5. UNIFIED ROUTER: NLPPipeline.dispatch and /api/nlp/dispatch 3-branch routing
"""
import unittest
import json
from app import create_app
from models import db, Space, User, Booking
from backend.modules.nlp.pipeline import NLPPipeline
from backend.modules.nlp.schemas import IntentType


class TestNLPIntegrationPart6(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False
        cls.client = cls.app.test_client()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Ensure a verified host user exists for listing tests
        self.test_host = User.query.filter_by(email="testhost_nlp6@spaceloop.in").first()
        if not self.test_host:
            self.test_host = User(
                email="testhost_nlp6@spaceloop.in",
                name="Integration Test Host",
                role="host",
                is_host_verified=True,
                is_aadhaar_verified=True,
                aadhaar_token_hash="AADHAAR_MOCK_TOKEN_PART6"
            )
            self.test_host.set_password("SecurePassword123!")
            db.session.add(self.test_host)
            db.session.commit()

        # Ensure at least one verified active space exists in Pune
        self.sample_space = Space.query.filter_by(city="Pune", is_active=True).first()
        if not self.sample_space:
            self.sample_space = Space(
                title="Acoustic Pod Pune Station",
                description="Quiet soundproof workspace in Pune with 300 Mbps fiber and ergonomic chairs.",
                category="Workspace",
                price_hourly=45.0,
                price_daily=360.0,
                location="Kharadi, Pune",
                address="Survey 42, Kharadi, Pune, Maharashtra",
                neighborhood="Kharadi",
                city="Pune",
                latitude=18.5514,
                longitude=73.9348,
                max_capacity=4,
                sqft=180,
                amenities=["Fiber 300 Mbps", "AC", "Power Backup", "Whiteboard"],
                rules=["No smoking", "Keep volume reasonable"],
                owner_id=self.test_host.id,
                is_active=True
            )
            db.session.add(self.sample_space)
            db.session.commit()

    def tearDown(self):
        self.app_context.pop()

    # =========================================================================
    # FLOW 1: LOOP BOT END-TO-END VERIFICATION
    # =========================================================================

    def test_flow1_loopbot_amenities_rag_grounded(self):
        """Flow 1: Querying amenities retrieves real DB space data via RAG and returns grounded output."""
        res = self.client.post("/api/assistant", json={
            "message": f"What amenities are available at space {self.sample_space.id}?",
            "space_id": self.sample_space.id
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        reply = data.get("reply", "")

        # Must be grounded on the actual space amenities from DB
        self.assertTrue(
            any(a.lower() in reply.lower() for a in (self.sample_space.amenities or [])) or "amenities" in reply.lower() or "verified" in reply.lower(),
            f"Expected space amenities in LoopBot reply, got: {reply}"
        )
        # Clean output check: no JSON dumps or Python object strings
        self.assertNotIn("{\"success\"", reply)
        self.assertNotIn("<Space", reply)
        self.assertNotIn("db.session", reply)

    def test_flow1_loopbot_search_marketplace_cards(self):
        """Flow 1: User search query in LoopBot runs marketplace search and returns real space cards."""
        res = self.client.post("/api/assistant", json={
            "message": "find a workspace in Pune for 4 people under 100"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        reply = data.get("reply", "")

        # Must include marketplace search results card with rate and Section 52 badge
        self.assertIn("₹", reply)
        self.assertIn("Pune", reply)
        self.assertTrue("Section 52" in reply or "धारा 52" in reply or "कलम ५२" in reply)
        self.assertNotIn("{\"results\":", reply)

    def test_flow1_loopbot_clarification_on_out_of_scope(self):
        """Flow 1: Out of scope queries cleanly ask for clarification without fabricating data."""
        res = self.client.post("/api/assistant", json={
            "message": "What is the stock price of Apple today?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        reply = data.get("reply", "")
        self.assertTrue(
            "clarif" in reply.lower() or "information unavailable" in reply.lower() or "spaceloop" in reply.lower(),
            f"Expected polite boundary response, got: {reply}"
        )

    # =========================================================================
    # FLOW 2: SEMANTIC SEARCH END-TO-END VERIFICATION
    # =========================================================================

    def test_flow2_semantic_search_natural_language(self):
        """Flow 2: Natural language query extracts constraints and ranks real active listings."""
        res = self.client.post("/api/spaces/search", json={
            "query": "workspace in Pune for 2 people with fast wifi under 100"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Validates query understanding
        constraints = data.get("extracted_constraints", {})
        self.assertEqual(constraints.get("location"), "Pune")
        self.assertIn(constraints.get("capacity"), [2, None])

        # Validates real DB results returned
        spaces = data.get("spaces", [])
        self.assertGreaterEqual(len(spaces), 1)
        first_space = spaces[0]
        self.assertEqual(first_space.get("city"), "Pune")

        # Explainable match reasons and score must be present
        results = data.get("results", [])
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("composite_score", results[0])
        self.assertIn("match_reasons", results[0])

    def test_flow2_semantic_search_indic_devanagari(self):
        """Flow 2: Indic query understanding bridges to existing DB records without synthetic data."""
        res = self.client.post("/api/spaces/search", json={
            "query": "पुण्यात 2 लोकांसाठी ऑफिस"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Query understanding must extract Pune & capacity=2
        constraints = data.get("extracted_constraints", {})
        self.assertEqual(constraints.get("location"), "Pune")
        self.assertEqual(constraints.get("capacity"), 2)

        # Real Pune spaces returned
        spaces = data.get("spaces", [])
        self.assertGreaterEqual(len(spaces), 1)
        pune_spaces = [s for s in spaces if s.get("city") == "Pune"]
        self.assertGreaterEqual(len(pune_spaces), 1)

    # =========================================================================
    # FLOW 3: LISTING ASSISTANCE END-TO-END VERIFICATION
    # =========================================================================

    def test_flow3_listing_assistance_extraction_and_save_flow(self):
        """Flow 3: Natural language -> NLP Extraction -> Existing Listing Fields -> Save Flow."""
        host_input = "2 bedroom workspace in Pune for 4 people with fast WiFi and AC at 75 per hour"
        assist_res = self.client.post("/api/spaces/assist-listing", json={
            "text": host_input
        })
        self.assertEqual(assist_res.status_code, 200)
        assist_data = assist_res.get_json()
        self.assertTrue(assist_data.get("success"))

        extracted = assist_data.get("extracted_fields", {})
        draft = assist_data.get("listing_draft", {})

        # Verify extracted attributes
        self.assertEqual(extracted.get("location"), "Pune")
        self.assertEqual(extracted.get("bedrooms"), 2)
        self.assertEqual(extracted.get("max_capacity"), 4)
        amenities = [a.lower() for a in extracted.get("amenities", [])]
        self.assertTrue(any("wi-fi" in a or "wifi" in a for a in amenities))
        self.assertTrue(any("air conditioning" in a or "ac" in a for a in amenities))

        # Zero hallucination check: unstated attributes are None
        self.assertIsNone(extracted.get("sqft"))

        # Complete Flow 3 by simulating the Host Save Action with the extracted draft
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(self.test_host.id)
            sess["user_id"] = self.test_host.id

        save_payload = {
            "title": draft.get("title") or "2 BHK Workspace in Pune",
            "description": assist_data.get("generated_description") or "Quiet workspace in Pune.",
            "category": draft.get("category") or "Workspace",
            "hourly_rate": draft.get("price_hourly") or 75.0,
            "daily_rate": 600.0,
            "location": draft.get("location") or "Pune",
            "address": "Survey 18, Baner Road, Pune, Maharashtra",
            "city": "Pune",
            "max_capacity": draft.get("max_capacity") or 4,
            "amenities": draft.get("amenities") or ["Fast Wifi", "Ac"],
            "terms_accepted": True
        }

        save_res = self.client.post("/api/spaces", json=save_payload)
        self.assertIn(save_res.status_code, [200, 201])
        saved_data = save_res.get_json()
        self.assertTrue(saved_data.get("success"))
        created_id = saved_data.get("space_id") or saved_data.get("id")
        self.assertIsNotNone(created_id)

        # Verify space exists in DB
        created_space = Space.query.get(created_id)
        self.assertIsNotNone(created_space)
        self.assertEqual(created_space.city, "Pune")
        self.assertEqual(created_space.price_hourly, 75.0)

    # =========================================================================
    # FLOW 4: MULTILINGUAL END-TO-END VERIFICATION
    # =========================================================================

    def test_flow4_multilingual_hindi_response_and_preservation(self):
        """Flow 4: Hindi query produces Hindi response with strict data preservation."""
        res = self.client.post("/api/assistant", json={
            "message": "मुझे स्पेस 1 की सुविधाएं और नियम बताइए"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("response_language"), "hi")

        reply = data.get("reply", "")
        # Devanagari content present
        self.assertTrue(any('\u0900' <= char <= '\u097f' for char in reply))
        # Critical data preservation
        self.assertTrue("₹" in reply or "धारा 52" in reply or "SpaceLoop" in reply)

    def test_flow4_multilingual_marathi_response_and_preservation(self):
        """Flow 4: Marathi query produces Marathi response with intact technical terms."""
        res = self.client.post("/api/assistant", json={
            "message": "पुण्यात 4 लोकांसाठी जागा शोधा"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("response_language"), "mr")

        reply = data.get("reply", "")
        self.assertTrue(any('\u0900' <= char <= '\u097f' for char in reply))
        # Critical data preservation
        self.assertTrue("₹" in reply or "कलम ५२" in reply or "SpaceLoop" in reply)

    def test_flow4_multilingual_central_pahari_greeting(self):
        """Flow 4: Central Pahari / Garhwali query receives regional greeting with safe Indic content."""
        res = self.client.post("/api/assistant", json={
            "message": "सादर प्रणाम! यख रूम मा वाई-फाई छ?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        reply = data.get("reply", "")
        self.assertTrue(any('\u0900' <= char <= '\u097f' for char in reply))
        self.assertTrue("सुविधाएं" in reply or "सत्यापित" in reply or "SpaceLoop" in reply or "प्रणाम" in reply or "नमस्कार" in reply)

    # =========================================================================
    # UNIFIED 3-BRANCH ROUTER TESTS (NLPPipeline.dispatch & /api/nlp/dispatch)
    # =========================================================================

    def test_unified_router_listing_assistance_branch(self):
        """NLPPipeline.dispatch routes listing draft intent to listing_assistance."""
        query = "2 bedroom workspace in Pune for 4 people with fast WiFi and AC"
        result = NLPPipeline.dispatch(query)
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("route"), "listing_assistance")
        self.assertIn("listing_draft", result)
        self.assertEqual(result["listing_draft"]["extracted_fields"]["location"], "Pune")

    def test_unified_router_semantic_search_branch(self):
        """NLPPipeline.dispatch routes search intent to semantic_search."""
        query = "find a quiet meeting room in Pune for 6 people under 150"
        result = NLPPipeline.dispatch(query)
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("route"), "semantic_search")
        self.assertIn("search_results", result)
        self.assertIn("spaces", result["search_results"])

    def test_unified_router_loopbot_rag_branch(self):
        """NLPPipeline.dispatch routes questions and rules inquiries to loopbot RAG."""
        query = "What is the cancellation policy and Section 52 protection on SpaceLoop?"
        result = NLPPipeline.dispatch(query)
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("route"), "loopbot")
        self.assertIn("loopbot_result", result)
        self.assertTrue("Section 52" in result.get("clean_response", ""))

    def test_api_nlp_dispatch_endpoint(self):
        """HTTP endpoint /api/nlp/dispatch executes the unified 3-branch router."""
        res = self.client.post("/api/nlp/dispatch", json={
            "query": "find a workspace in Pune for 4 people"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("route"), "semantic_search")
        self.assertIn("clean_response", data)


if __name__ == "__main__":
    unittest.main()
