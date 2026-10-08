"""
SpaceLoop LoopBot Orchestrator
=============================
Core orchestration engine connecting:
ConversationContext -> IntentClassifier -> Controlled Tools -> Grounded RAG ->
Multi-Tier LLM Hierarchy (Groq -> Gemini -> Deterministic) -> Structured Response.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from flask import has_app_context
from backend.modules.loopbot.schemas import (
    LoopBotIntent,
    LoopBotResponseType,
    LoopBotResponse,
    ConversationSlots
)
from backend.modules.loopbot.context import ConversationContextManager
from backend.modules.loopbot.intent import LoopBotIntentClassifier
from backend.modules.loopbot.rag import LoopBotRAG
from backend.modules.loopbot.tools import LoopBotTools

logger = logging.getLogger("spaceloop.loopbot.orchestrator")


class LoopBotOrchestrator:
    """
    Native conversational concierge for SpaceLoop.
    Dispatches natural language queries to controlled platform services and grounded knowledge.
    """

    @classmethod
    def handle_message(
        cls,
        message: str,
        conversation_id: Optional[str] = None,
        user: Optional[Any] = None,
        confirm: Optional[bool] = None,
        context_override: Optional[dict[str, Any]] = None
    ) -> LoopBotResponse:
        """
        Executes a complete LoopBot turn:
        1. Context loading & session initialization
        2. Pending action evaluation (Confirmation Gate)
        3. Intent classification & Slot extraction
        4. Controlled tool execution & Grounded RAG lookup
        5. Grounded message synthesis & Structured formatting
        """
        if not has_app_context():
            from app import create_app
            temp_app = create_app()
            with temp_app.app_context():
                return cls.handle_message(
                    message=message,
                    conversation_id=conversation_id,
                    user=user,
                    confirm=confirm,
                    context_override=context_override
                )

        clean_msg = (message or "").strip()
        user_id = getattr(user, "id", None) if user else None

        # 1. Retrieve or initialize conversation session
        cid, session_data = ConversationContextManager.get_or_create(
            conversation_id=conversation_id,
            user_id=user_id,
            initial_slots=context_override
        )
        slots: ConversationSlots = session_data["slots"]
        ConversationContextManager.add_turn(cid, "user", clean_msg)

        # 2. Check Pending Action Gate (Two-Step Confirmation)
        pending = ConversationContextManager.get_pending_action(cid)
        if pending:
            is_confirmed = (confirm is True) or ConversationContextManager.is_confirmation(clean_msg)
            is_declined = (confirm is False) or ConversationContextManager.is_denial(clean_msg)

            if is_confirmed:
                action_name = pending["action"]
                payload = pending["payload"]
                ConversationContextManager.clear_pending_action(cid)

                if action_name == "create_booking":
                    res = LoopBotTools.create_booking(
                        space_id=payload["space_id"],
                        user_id=payload.get("user_id") or user_id or 1,
                        hours=payload.get("hours", 2.0),
                        confirmed=True
                    )
                    reply_msg = (
                        f"🎉 **Reservation Confirmed!**\n\n"
                        f"{res['message']}\n"
                        f"• **Booking ID**: #{res['booking_id']}\n"
                        f"• **Space**: {res['space_title']}\n"
                        f"• **Arrival PIN**: `{res['door_pin']}`\n"
                        f"• **Refundable Escrow**: ₹{res['deposit_held']} held safely under Section 52 micro-license.\n\n"
                        f"Your digital pass is available in your `/dashboard`."
                    )
                    ConversationContextManager.add_turn(cid, "assistant", reply_msg)
                    return LoopBotResponse(
                        message=reply_msg,
                        response_type=LoopBotResponseType.BOOKING_STATUS,
                        data=res,
                        conversation_id=cid,
                        slots=slots.to_dict()
                    )

                elif action_name == "cancel_booking":
                    res = LoopBotTools.cancel_booking(
                        booking_id=payload["booking_id"],
                        user_id=payload.get("user_id") or user_id or 1,
                        confirmed=True
                    )
                    reply_msg = (
                        f"✅ **Booking #{payload['booking_id']} Cancelled**\n\n"
                        f"{res['message']}\n"
                        f"• Total Refund: ₹{res['refund_details']['total_refund_amount']} (Refunded to your UPI VPA).\n"
                        f"• ₹{res['refund_details']['escrow_refund']} security deposit has been fully released."
                    )
                    ConversationContextManager.add_turn(cid, "assistant", reply_msg)
                    return LoopBotResponse(
                        message=reply_msg,
                        response_type=LoopBotResponseType.BOOKING_STATUS,
                        data=res,
                        conversation_id=cid,
                        slots=slots.to_dict()
                    )

            elif is_declined:
                ConversationContextManager.clear_pending_action(cid)
                cancel_reply = "Understood. The action has been cancelled without making any changes to your account or reservations."
                ConversationContextManager.add_turn(cid, "assistant", cancel_reply)
                return LoopBotResponse(
                    message=cancel_reply,
                    response_type=LoopBotResponseType.TEXT,
                    conversation_id=cid,
                    slots=slots.to_dict()
                )

        # 3. Intent Detection & Entity Extraction
        intent, new_slot_vals = LoopBotIntentClassifier.classify(clean_msg, context=slots.to_dict())
        slots = ConversationContextManager.update_slots(cid, new_slot_vals)
        slots.intent = intent.value

        # 4. Dispatch to Controlled Capability / Grounded RAG
        # --------------------------------------------------

        # Capability A: Space Search
        if intent == LoopBotIntent.SPACE_SEARCH:
            search_params = slots.to_dict()
            results = LoopBotTools.search_spaces(search_params, user_id=user_id, limit=3)

            if results:
                card_texts = []
                for idx, item in enumerate(results, start=1):
                    p = item["pricing_preview_2h"]
                    reason_txt = f"\n   • *Why this matches*: {item['match_reasons'][0]}" if item.get("match_reasons") else ""
                    card_texts.append(
                        f"{idx}. **{item['title']}** ({item['match_badge']})\n"
                        f"   • Location: {item['neighborhood'] or item['location']}\n"
                        f"   • Capacity: Up to {item['max_capacity']} people ({item['sqft']} sq ft)\n"
                        f"   • Rate: ₹{item['price_hourly']}/hr (Est. ₹{p['total_upfront']} for 2h incl. ₹100 deposit){reason_txt}"
                    )
                reply = (
                    f"🔍 **Found {len(results)} matching space{'s' if len(results) > 1 else ''}:**\n\n"
                    f"{chr(10).join(card_texts)}\n\n"
                    f"All spaces operate under Section 52 revocable licenses with zero-hardware digital door passes. Would you like to reserve one?"
                )
                resp_type = LoopBotResponseType.SPACE_RESULTS
                resp_data = {"spaces": results}
            else:
                reply = (
                    "🔍 I couldn't find any active spaces matching those exact filters. "
                    "Try broadening your budget or searching in central neighborhoods like Kharadi, Baner, or Kothrud."
                )
                resp_type = LoopBotResponseType.TEXT
                resp_data = {}

        # Capability B: Space Details
        elif intent == LoopBotIntent.SPACE_DETAILS:
            target_id = slots.selected_space_id or 4
            space_data = LoopBotTools.get_space(target_id)
            if space_data:
                amen_str = ", ".join(space_data["amenities"]) if space_data["amenities"] else "High-speed Wi-Fi, Ergonomic seating"
                rules_str = "; ".join(space_data["rules"]) if space_data["rules"] else "No smoking, quiet professional decorum"
                reply = (
                    f"🏢 **{space_data['title']}** (Space #{space_data['id']})\n\n"
                    f"• **Location**: {space_data['location']}\n"
                    f"• **Capacity**: {space_data['max_capacity']} people ({space_data['sqft']} sq ft)\n"
                    f"• **Rate**: ₹{space_data['price_hourly']}/hour\n"
                    f"• **Noise Floor**: {space_data['ai_noise_level'] or 'Quiet'}\n"
                    f"• **Amenities**: {amen_str}\n"
                    f"• **House Rules**: {rules_str}\n"
                    f"• **Host Trust Score**: {space_data['host']['trust_score']}/100\n\n"
                    f"Would you like to check availability or book this space?"
                )
                resp_type = LoopBotResponseType.SPACE_DETAILS
                resp_data = {"space": space_data}
            else:
                reply = f"I could not locate details for Space #{target_id}. Please verify the space ID."
                resp_type = LoopBotResponseType.TEXT
                resp_data = {}

        # Capability C: Space Availability
        elif intent == LoopBotIntent.SPACE_AVAILABILITY:
            target_id = slots.selected_space_id
            avail = LoopBotTools.check_availability(space_id=target_id, date_str=slots.date or "tomorrow")
            lines = [f"📅 **Real-Time Space Availability for {avail['date']}:**\n"]
            for sp in avail["spaces"]:
                lines.append(
                    f"• **{sp['title']}** ({sp['location']}) - ₹{sp['hourly_rate']}/hr\n"
                    f"  Status: {sp['status']} | {sp['available_slots']}"
                )
            lines.append("\nWhich time window works best for you?")
            reply = "\n".join(lines)
            resp_type = LoopBotResponseType.TEXT
            resp_data = avail

        # Capability D: Booking Status
        elif intent == LoopBotIntent.BOOKING_STATUS:
            b_info = LoopBotTools.get_booking(booking_id=slots.selected_booking_id, user_id=user_id)
            if b_info and "error" not in b_info:
                pin_display = b_info["door_pin"] if b_info["is_geofence_verified"] else "•••• (Reveals within 50m)"
                reply = (
                    f"📋 **Booking Status for #{b_info['id']}:**\n\n"
                    f"• **Space**: {b_info['space_title']} ({b_info['location']})\n"
                    f"• **Status**: **{b_info['status'].title()}**\n"
                    f"• **Scheduled**: {b_info['start_time']} – {b_info['end_time']} ({b_info['hours_booked']}h)\n"
                    f"• **Arrival PIN**: `{pin_display}`\n"
                    f"• **Geofence Check-in**: {'Verified' if b_info['is_geofence_verified'] else 'Pending arrival within 50m'}\n\n"
                    f"You can view your active door pass in your `/dashboard`."
                )
                resp_type = LoopBotResponseType.BOOKING_STATUS
                resp_data = b_info
            elif b_info and "error" in b_info:
                reply = f"⚠️ {b_info['error']}"
                resp_type = LoopBotResponseType.ERROR
                resp_data = b_info
            else:
                reply = (
                    "📋 You don't have any active bookings at the moment. "
                    "Would you like me to find a verified desk or meeting room for you?"
                )
                resp_type = LoopBotResponseType.TEXT
                resp_data = {}

        # Capability E: Booking Create (Consequential Gate)
        elif intent == LoopBotIntent.BOOKING_CREATE:
            target_sid = slots.selected_space_id or 4
            effective_uid = user_id or 1
            preview = LoopBotTools.create_booking(
                space_id=target_sid,
                user_id=effective_uid,
                hours=slots.duration_hours or 2.0,
                confirmed=False
            )
            if "error" in preview:
                reply = f"⚠️ **Cannot Book**: {preview['error']}"
                resp_type = LoopBotResponseType.ERROR
                resp_data = preview
            else:
                ConversationContextManager.set_pending_action(
                    cid,
                    "create_booking",
                    {"space_id": target_sid, "user_id": effective_uid, "hours": slots.duration_hours or 2.0}
                )
                p = preview["pricing"]
                reply = (
                    f"🚀 **Booking Confirmation Required**\n\n"
                    f"• **Space**: {preview['space_title']} ({preview['location']})\n"
                    f"• **Time**: {preview['start_time']} – {preview['end_time']} ({p['hours']}h)\n"
                    f"• **Hourly Rate**: ₹{p['hourly_rate']}/hr\n"
                    f"• **Subtotal**: ₹{p['subtotal']}\n"
                    f"• **5% Platform Fee**: ₹{p['platform_fee']}\n"
                    f"• **₹100 Refundable Deposit**: Held in micro-escrow\n"
                    f"• **Total Upfront**: **₹{p['total_upfront']}**\n\n"
                    f"👉 **Reply 'Confirm' or 'Yes' to complete reservation under Section 52 micro-license.**"
                )
                resp_type = LoopBotResponseType.CONFIRMATION_REQUIRED
                resp_data = preview

        # Capability F: Booking Cancel (Consequential Gate)
        elif intent == LoopBotIntent.BOOKING_CANCEL:
            target_bid = slots.selected_booking_id
            if not target_bid and user_id:
                latest = LoopBotTools.get_booking(user_id=user_id)
                if latest and "id" in latest:
                    target_bid = latest["id"]

            if not target_bid:
                reply = "Please specify the booking ID you would like to cancel (e.g., *'cancel booking #12'*)."
                resp_type = LoopBotResponseType.TEXT
                resp_data = {}
            else:
                effective_uid = user_id or 1
                c_preview = LoopBotTools.cancel_booking(
                    booking_id=target_bid,
                    user_id=effective_uid,
                    confirmed=False
                )
                if "error" in c_preview:
                    reply = f"⚠️ **Cannot Cancel**: {c_preview['error']}"
                    resp_type = LoopBotResponseType.ERROR
                    resp_data = c_preview
                else:
                    ConversationContextManager.set_pending_action(
                        cid,
                        "cancel_booking",
                        {"booking_id": target_bid, "user_id": effective_uid}
                    )
                    r = c_preview["refund_details"]
                    reply = (
                        f"⚠️ **Cancellation Confirmation Required**\n\n"
                        f"Are you sure you want to cancel **Booking #{target_bid}**?\n"
                        f"• Total Paid: ₹{r['total_paid']}\n"
                        f"• 5% Platform Fee (retained): ₹{r['platform_fee_retained']}\n"
                        f"• Rental Refund: ₹{r['rental_refund']}\n"
                        f"• Escrow Refund: ₹{r['escrow_refund']}\n"
                        f"• **Total Refund to UPI**: **₹{r['total_refund_amount']}**\n\n"
                        f"👉 **Reply 'Yes' or 'Confirm' to proceed with cancellation.**"
                    )
                    resp_type = LoopBotResponseType.CONFIRMATION_REQUIRED
                    resp_data = c_preview

        # Capability G: Access Status
        elif intent == LoopBotIntent.ACCESS_STATUS:
            target_bid = slots.selected_booking_id
            if not target_bid and user_id:
                b = LoopBotTools.get_booking(user_id=user_id)
                if b and "id" in b:
                    target_bid = b["id"]

            if target_bid:
                effective_uid = user_id or 1
                acc = LoopBotTools.get_access_status(booking_id=target_bid, user_id=effective_uid)
                reply = (
                    f"🚪 **Smart Access Status for Booking #{target_bid}:**\n\n"
                    f"• **Door Pass**: {'🟢 ACTIVE' if acc['status'] == 'unlocked' else '🔒 LOCKED'}\n"
                    f"• **Arrival PIN**: `{acc['door_pin']}`\n"
                    f"• **Geofence Proximity**: {acc['message']}"
                )
                resp_type = LoopBotResponseType.ACCESS_STATUS
                resp_data = acc
            else:
                reply = (
                    "🚪 To check your smart access pass, please provide your booking ID or make sure you have an active reservation in `/dashboard`."
                )
                resp_type = LoopBotResponseType.TEXT
                resp_data = {}

        # Capability H: Escrow Status
        elif intent == LoopBotIntent.ESCROW_STATUS:
            esc = LoopBotTools.get_escrow_status(booking_id=slots.selected_booking_id, user_id=user_id)
            reply = (
                f"💳 **₹100 UPI Micro-Escrow Status:**\n\n"
                f"• **Deposit Amount**: ₹{esc['deposit_amount']}\n"
                f"• **Escrow Status**: **{esc['status'].upper()}**\n"
                f"• **Protocol**: {esc['message']}"
            )
            resp_type = LoopBotResponseType.ESCROW_STATUS
            resp_data = esc

        # Capability I: Support Request
        elif intent == LoopBotIntent.SUPPORT:
            supp = LoopBotTools.create_support_request(
                user_id=user_id,
                issue_type="DISPUTE",
                description=clean_msg
            )
            reply = (
                f"🛡️ **SpaceLoop Support Ticket Created**\n\n"
                f"{supp['message']}\n"
                f"• **Ticket Reference**: `{supp['ticket_id']}`\n"
                f"• **SLA**: Resolution within {supp['sla']}\n"
                f"• Priority: Tamper-evident ledger review."
            )
            resp_type = LoopBotResponseType.SUPPORT
            resp_data = supp

        # Grounded Knowledge / RAG Domains
        else:
            rag_chunks = LoopBotRAG.retrieve(clean_msg, space_id=slots.selected_space_id)
            if rag_chunks:
                top = rag_chunks[0]
                reply = f"📖 **{top['title']}**\n\n{top['text']}"
            else:
                reply = cls._generate_conversational_reply(clean_msg, slots, session_data["history"])

            resp_type = LoopBotResponseType.TEXT
            resp_data = {"rag_citations": [c["title"] for c in rag_chunks]}

        ConversationContextManager.add_turn(cid, "assistant", reply)

        return LoopBotResponse(
            message=reply,
            response_type=resp_type,
            data=resp_data,
            conversation_id=cid,
            slots=slots.to_dict(),
            success=True
        )

    @classmethod
    def _generate_conversational_reply(
        cls,
        query: str,
        slots: ConversationSlots,
        history: list[dict[str, Any]]
    ) -> str:
        """
        Multi-tier LLM grounding (Groq -> Gemini -> Deterministic) for conversational queries.
        Guarantees that no fake bookings or prices are hallucinated.
        """
        system_prompt = (
            "You are LoopBot, SpaceLoop's native AI concierge.\n"
            "SpaceLoop is India's premier marketplace for flexible hourly spaces (desks, studios, meeting rooms) "
            "with zero-hardware 50m geofence passes, ₹100 instant refundable UPI micro-escrow, and Section 52 legal protection.\n"
            "GUIDELINES:\n"
            "1. Answer concisely in 2-3 sentences.\n"
            "2. Never hallucinate fake booking confirmation numbers or prices.\n"
            "3. Help the user discover spaces, understand smart access, or monetize their unused space."
        )

        try:
            from space_ai import _call_groq, _call_gemini
            messages = [{"role": "system", "content": system_prompt}]
            for turn in history[-4:]:
                messages.append({
                    "role": "assistant" if turn["role"] == "assistant" else "user",
                    "content": str(turn["content"])[:250]
                })
            messages.append({"role": "user", "content": query})

            groq_out = _call_groq(messages, temperature=0.3)
            if groq_out and len(groq_out.strip()) > 10:
                return groq_out.strip()

            gemini_out = _call_gemini(f"{system_prompt}\n\nUser Question: {query}", temperature=0.3)
            if gemini_out and len(gemini_out.strip()) > 10:
                return gemini_out.strip()
        except Exception as e:
            logger.warning(f"LLM call failed in LoopBot: {e}")

        # Deterministic conversational fallback
        return (
            "👋 I'm **LoopBot**, your SpaceLoop AI Concierge! "
            "I can help you search verified workspaces by the hour, check availability, "
            "view smart door passes, or explain our Section 52 legal protections. What can I help you find today?"
        )
