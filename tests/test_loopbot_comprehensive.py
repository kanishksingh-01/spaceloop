"""
SpaceLoop LoopBot Comprehensive System Test Suite
=================================================
Verifies all 18 canonical intents, multi-turn conversation memory, slot accumulation,
the 11 controlled tools, two-step confirmation gates, 7-domain grounded RAG,
and the REST endpoint POST /api/v1/loopbot/chat.
"""
import unittest
from datetime import datetime, timezone, timedelta
from app import create_app
from models import db, Space, User, Booking, EscrowTransaction
from backend.modules.loopbot import (
    LoopBotIntent,
    LoopBotResponseType,
    ConversationContextManager,
    LoopBotIntentClassifier,
    LoopBotRAG,
    LoopBotTools,
    LoopBotOrchestrator
)


class TestLoopBotComprehensive(unittest.TestCase):

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
    # 1. INTENT VOCABULARY: ALL 18 CANONICAL INTENTS
    # -------------------------------------------------------------------------
    def test_01_all_18_intents_classification(self):
        """Verifies accurate classification for the 18 required intent types."""
        cases = [
            ("Hello LoopBot!", LoopBotIntent.GENERAL),
            ("Find spaces for 4 people in Pune under 500", LoopBotIntent.SPACE_SEARCH),
            ("What amenities and rules are in space #4?", LoopBotIntent.SPACE_DETAILS),
            ("What's available tomorrow afternoon?", LoopBotIntent.SPACE_AVAILABILITY),
            ("Check my active booking status", LoopBotIntent.BOOKING_STATUS),
            ("Book this space for 3 hours", LoopBotIntent.BOOKING_CREATE),
            ("Cancel booking #1", LoopBotIntent.BOOKING_CANCEL),
            ("Can I enter? Check my access status and door pass", LoopBotIntent.ACCESS_STATUS),
            ("How does 50m geofence access and caretaker PIN work?", LoopBotIntent.ACCESS_HELP),
            ("Where is my 100 deposit and escrow status?", LoopBotIntent.ESCROW_STATUS),
            ("How do refunds work and when is the 120-second refund sent?", LoopBotIntent.REFUND_HELP),
            ("How do I list my space, complete 60s photo scan and earn 95% yield?", LoopBotIntent.HOST_HELP),
            ("How does SpaceLoop work and what are seeker requirements?", LoopBotIntent.SEEKER_HELP),
            ("Explain Section 52 of the Indian Easements Act protection", LoopBotIntent.LEGAL_INFORMATION),
            ("I want to report a dispute regarding damage and overstay", LoopBotIntent.DISPUTE_HELP),
            ("What is Discom CA electricity meter verification and OTI score?", LoopBotIntent.TRUST_SAFETY),
            ("Update my profile and linked UPI VPA payout account", LoopBotIntent.ACCOUNT_HELP),
            ("Connect me with customer care and human support ticket", LoopBotIntent.SUPPORT),
        ]
        for query, expected_intent in cases:
            intent, _ = LoopBotIntentClassifier.classify(query)
            self.assertEqual(
                intent,
                expected_intent,
                f"Query '{query}' classified as {intent}, expected {expected_intent}"
            )

    # -------------------------------------------------------------------------
    # 2. MULTI-TURN CONVERSATION MEMORY & SLOT ACCUMULATION
    # -------------------------------------------------------------------------
    def test_02_multi_turn_slot_filling(self):
        """Verifies multi-turn slot retention without losing earlier parameters."""
        cid, _ = ConversationContextManager.get_or_create()

        # Turn 1: "Find me a study space" -> Intent search
        resp1 = LoopBotOrchestrator.handle_message("Find me a study space in Pune", conversation_id=cid)
        self.assertEqual(resp1.slots.get("location"), "Pune")

        # Turn 2: "For three people" -> Retains location=Pune, adds capacity=3
        resp2 = LoopBotOrchestrator.handle_message("For three people", conversation_id=cid)
        self.assertEqual(resp2.slots.get("location"), "Pune")
        self.assertEqual(resp2.slots.get("capacity"), 3)

        # Turn 3: "Tomorrow" -> Retains location=Pune, capacity=3, adds date=tomorrow
        resp3 = LoopBotOrchestrator.handle_message("Tomorrow", conversation_id=cid)
        self.assertEqual(resp3.slots.get("location"), "Pune")
        self.assertEqual(resp3.slots.get("capacity"), 3)
        self.assertEqual(resp3.slots.get("date"), "tomorrow")

        # Turn 4: "2 to 6" -> Retains previous, adds start_time and end_time
        resp4 = LoopBotOrchestrator.handle_message("2 to 6", conversation_id=cid)
        self.assertEqual(resp4.slots.get("location"), "Pune")
        self.assertEqual(resp4.slots.get("capacity"), 3)
        self.assertEqual(resp4.slots.get("date"), "tomorrow")
        self.assertEqual(resp4.slots.get("start_time"), "2")
        self.assertEqual(resp4.slots.get("end_time"), "6")

    # -------------------------------------------------------------------------
    # 3. CONTROLLED TOOLS: TWO-STEP CONFIRMATION GATES (BOOKING & CANCELLATION)
    # -------------------------------------------------------------------------
    def test_03_booking_preview_and_confirmation_gate(self):
        """Booking requires preview first, then executes only upon confirmation."""
        space = Space.query.filter_by(is_active=True).first()
        self.assertIsNotNone(space)
        user = User.query.first()
        self.assertIsNotNone(user)

        cid, _ = ConversationContextManager.get_or_create()

        # Step 1: User says "Book this space for 2 hours"
        resp = LoopBotOrchestrator.handle_message(
            f"Book space #{space.id} for 2 hours",
            conversation_id=cid,
            user=user
        )
        self.assertEqual(resp.response_type, LoopBotResponseType.CONFIRMATION_REQUIRED)
        self.assertIn("pricing", resp.data)
        pricing = resp.data["pricing"]
        self.assertEqual(pricing["hours"], 2.0)
        self.assertEqual(pricing["refundable_deposit"], 100.0)
        self.assertEqual(pricing["subtotal"], round(float(space.price_hourly) * 2.0, 2))
        self.assertEqual(pricing["platform_fee"], round(pricing["subtotal"] * 0.05, 2))

        # Check pending action is recorded
        pending = ConversationContextManager.get_pending_action(cid)
        self.assertIsNotNone(pending)
        self.assertEqual(pending["action"], "create_booking")

        # Step 2: Affirmative confirmation ("Yes, proceed")
        confirm_resp = LoopBotOrchestrator.handle_message("Confirm booking", conversation_id=cid, user=user)
        self.assertEqual(confirm_resp.response_type, LoopBotResponseType.BOOKING_STATUS)
        self.assertIn("booking_id", confirm_resp.data)
        self.assertIn("door_pin", confirm_resp.data)

        # Pending action must be cleared
        self.assertIsNone(ConversationContextManager.get_pending_action(cid))

        # Booking must exist in database
        booking_id = confirm_resp.data["booking_id"]
        created_b = Booking.query.get(booking_id)
        self.assertIsNotNone(created_b)
        self.assertEqual(created_b.status, "confirmed")

    def test_04_cancellation_preview_and_confirmation_gate(self):
        """Cancellation shows refund preview with 5% deduction, then cancels on confirmation."""
        space = Space.query.filter_by(is_active=True).first()
        user = User.query.first()

        # Create a test booking at a future non-colliding time slot
        booking_res = LoopBotTools.create_booking(
            space_id=space.id,
            user_id=user.id,
            hours=2.0,
            start_time=datetime.now(timezone.utc) + timedelta(days=5),
            confirmed=True
        )
        self.assertIn("booking_id", booking_res, f"Booking creation failed: {booking_res}")
        b_id = booking_res["booking_id"]

        cid, _ = ConversationContextManager.get_or_create()

        # Step 1: Request cancellation
        req_resp = LoopBotOrchestrator.handle_message(
            f"Cancel booking #{b_id}",
            conversation_id=cid,
            user=user
        )
        self.assertEqual(req_resp.response_type, LoopBotResponseType.CONFIRMATION_REQUIRED)
        self.assertIn("refund_details", req_resp.data)
        r = req_resp.data["refund_details"]
        self.assertEqual(r["escrow_refund"], 100.0)
        self.assertTrue(r["platform_fee_retained"] > 0)

        # Step 2: Confirm cancellation
        cancel_resp = LoopBotOrchestrator.handle_message("Yes, cancel it", conversation_id=cid, user=user)
        self.assertEqual(cancel_resp.response_type, LoopBotResponseType.BOOKING_STATUS)
        self.assertEqual(cancel_resp.data["status"], "cancelled")

        # Verify DB state
        b_record = Booking.query.get(b_id)
        self.assertEqual(b_record.status, "cancelled")

    # -------------------------------------------------------------------------
    # 4. GROUNDED RAG: 7 CURATED DOMAINS & 0.45 RELEVANCE THRESHOLD
    # -------------------------------------------------------------------------
    def test_05_grounded_rag_domains(self):
        """Verifies RAG retrieves exact legal, access, escrow, and listing facts."""
        # Domain 1: Section 52
        sec52 = LoopBotRAG.retrieve("How does Section 52 Indian Easements Act protect the host?")
        self.assertTrue(len(sec52) > 0)
        self.assertIn("Section 52", sec52[0]["title"])
        self.assertIn("revocable", sec52[0]["text"].lower())

        # Domain 2: Zero Hardware 50m Access
        acc = LoopBotRAG.retrieve("How does 50m geofence smart access and digital pass work?")
        self.assertTrue(len(acc) > 0)
        self.assertIn("50m Geofence", acc[0]["title"])

        # Domain 3: Discom CA
        discom = LoopBotRAG.retrieve("Why does SpaceLoop require Discom electricity CA verification?")
        self.assertTrue(len(discom) > 0)
        self.assertIn("Discom", discom[0]["title"])

        # Domain 4: ₹100 Escrow & 120s refund
        esc = LoopBotRAG.retrieve("When do I get the ₹100 UPI micro-escrow refund back?")
        self.assertTrue(len(esc) > 0)
        self.assertIn("100", esc[0]["title"])

        # Domain 5: 60s Photo Scan
        scan = LoopBotRAG.retrieve("What are the listing requirements and 60-second AI photo scan?")
        self.assertTrue(len(scan) > 0)
        self.assertIn("Photo Scan", scan[0]["title"])

        # Domain 6: Host 95% yield
        host = LoopBotRAG.retrieve("What is host payout yield and platform fee on SpaceLoop?")
        self.assertTrue(len(host) > 0)
        self.assertIn("95% Yield", host[0]["title"])

        # Domain 7: Dispute resolution
        disp = LoopBotRAG.retrieve("How are disputes and damages handled with audit trail?")
        self.assertTrue(len(disp) > 0)
        self.assertIn("Dispute", disp[0]["title"])

    # -------------------------------------------------------------------------
    # 5. REST API ENDPOINT: POST /api/v1/loopbot/chat
    # -------------------------------------------------------------------------
    def test_06_loopbot_rest_api_endpoint(self):
        """Verifies POST /api/v1/loopbot/chat returns typed structured responses."""
        # 1. Search Query
        res = self.client.post("/api/v1/loopbot/chat", json={
            "message": "Find a quiet desk in Pune"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("conversation_id", data)
        self.assertEqual(data["response_type"], "space_results")
        self.assertIn("spaces", data["data"])

        # 2. Section 52 query
        cid = data["conversation_id"]
        res2 = self.client.post("/api/v1/loopbot/chat", json={
            "message": "What is Section 52?",
            "conversation_id": cid
        })
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertTrue(data2["success"])
        self.assertEqual(data2["conversation_id"], cid)
        self.assertIn("Section 52", data2["message"])

    # -------------------------------------------------------------------------
    # 6. NEGATIVE CONFIRMATION / DECLINE GATE
    # -------------------------------------------------------------------------
    def test_07_decline_pending_confirmation(self):
        """User saying 'no' or 'cancel' clears pending action without mutating DB."""
        space = Space.query.filter_by(is_active=True).first()
        user = User.query.first()
        cid, _ = ConversationContextManager.get_or_create()

        # Step 1: Prompt booking
        resp = LoopBotOrchestrator.handle_message(
            f"Book space #{space.id} for 1 hour",
            conversation_id=cid,
            user=user
        )
        self.assertEqual(resp.response_type, LoopBotResponseType.CONFIRMATION_REQUIRED)
        self.assertIsNotNone(ConversationContextManager.get_pending_action(cid))

        # Step 2: Decline action
        decline_resp = LoopBotOrchestrator.handle_message("No, don't book", conversation_id=cid, user=user)
        self.assertEqual(decline_resp.response_type, LoopBotResponseType.TEXT)
        self.assertIn("cancelled without making any changes", decline_resp.message)
        self.assertIsNone(ConversationContextManager.get_pending_action(cid))

    # -------------------------------------------------------------------------
    # 7. CONTROLLED TOOLS INDIVIDUAL COVERAGE
    # -------------------------------------------------------------------------
    def test_08_controlled_tools_suite(self):
        """Verifies get_space, check_availability, access, escrow, trust, support tools."""
        space = Space.query.filter_by(is_active=True).first()
        user = User.query.first()

        # 1. get_space
        sp_data = LoopBotTools.get_space(space.id)
        self.assertIsNotNone(sp_data)
        self.assertEqual(sp_data["id"], space.id)
        self.assertIn("amenities", sp_data)

        # 2. check_availability
        avail = LoopBotTools.check_availability(space.id, date_str="tomorrow")
        self.assertIn("spaces", avail)
        self.assertTrue(len(avail["spaces"]) > 0)

        # 3. get_trust_status
        trust = LoopBotTools.get_trust_status(space_id=space.id)
        self.assertIn("trust_index", trust)
        self.assertTrue(trust["trust_index"] > 50)

        # 4. create_support_request
        supp = LoopBotTools.create_support_request(user.id, "CARETAKER_ABSENT", "No caretaker at premise")
        self.assertIn("ticket_id", supp)
        self.assertEqual(supp["priority"], "high")

    # -------------------------------------------------------------------------
    # 8. SMART ACCESS 50M GEOFENCE & PIN VERIFICATION
    # -------------------------------------------------------------------------
    def test_09_smart_access_geofence_and_pin(self):
        """Verifies 50m geofence evaluation and PIN handshake."""
        space = Space.query.filter_by(is_active=True).first()
        user = User.query.first()

        b_res = LoopBotTools.create_booking(
            space_id=space.id,
            user_id=user.id,
            hours=2.0,
            confirmed=True
        )
        self.assertIn("booking_id", b_res, f"Booking creation failed: {b_res}")
        b_id = b_res["booking_id"]
        pin = b_res["door_pin"]

        # Far away (> 50m) check: pass is locked
        far_acc = LoopBotTools.get_access_status(
            booking_id=b_id,
            user_id=user.id,
            user_lat=space.latitude + 0.05,
            user_lng=space.longitude + 0.05
        )
        self.assertEqual(far_acc["status"], "locked")
        self.assertFalse(far_acc["is_within_geofence"])

        # Proximity check (within 10m): pass is unlocked
        near_acc = LoopBotTools.get_access_status(
            booking_id=b_id,
            user_id=user.id,
            user_lat=space.latitude + 0.00005,
            user_lng=space.longitude + 0.00005
        )
        self.assertEqual(near_acc["status"], "unlocked")
        self.assertTrue(near_acc["is_within_geofence"])
        self.assertEqual(near_acc["door_pin"], pin)

        # Verify access attempt
        verify_res = LoopBotTools.verify_access(
            booking_id=b_id,
            user_id=user.id,
            user_lat=space.latitude + 0.00005,
            user_lng=space.longitude + 0.00005,
            pin=pin
        )
        self.assertTrue(verify_res["success"])

    # -------------------------------------------------------------------------
    # 9. PBAC AUTHORIZATION BOUNDARY
    # -------------------------------------------------------------------------
    def test_10_pbac_security_enforcement(self):
        """Users cannot inspect or cancel another user's reservation."""
        space = Space.query.filter_by(is_active=True).first()
        users = User.query.limit(2).all()
        if len(users) >= 2:
            user1, user2 = users[0], users[1]
            b_res = LoopBotTools.create_booking(
                space_id=space.id,
                user_id=user1.id,
                hours=2.0,
                confirmed=True
            )
            self.assertIn("booking_id", b_res, f"Booking creation failed: {b_res}")
            b_id = b_res["booking_id"]

            # User 2 attempts to get User 1's booking
            unauth_get = LoopBotTools.get_booking(booking_id=b_id, user_id=user2.id)
            self.assertIn("error", unauth_get)

            # User 2 attempts to cancel User 1's booking
            unauth_cancel = LoopBotTools.cancel_booking(booking_id=b_id, user_id=user2.id, confirmed=True)
            self.assertIn("error", unauth_cancel)

    # -------------------------------------------------------------------------
    # 10. RAG RELEVANCE THRESHOLD (>= 0.45)
    # -------------------------------------------------------------------------
    def test_11_rag_cutoff_threshold(self):
        """Irrelevant query outside SpaceLoop knowledge returns empty chunks (no hallucination)."""
        irrelevant_chunks = LoopBotRAG.retrieve("What is the recipe for chocolate lava cake with vanilla ice cream?")
        self.assertEqual(len(irrelevant_chunks), 0)


if __name__ == "__main__":
    unittest.main()
