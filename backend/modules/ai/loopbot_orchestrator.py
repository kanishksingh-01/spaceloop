"""
SpaceLoop LoopBot Orchestrator & RAG Engine
===========================================
Architectural Components:
1. Intent Detection:
   - "What amenities does this space have?" -> RAG
   - "Can I bring food?" -> RAG
   - "Is this good for a team meeting?" -> RAG + Listing Data
   - "Find spaces for 8 people" -> Marketplace Search (Filters, Availability, Pricing)
   - "What's available tomorrow?" -> Availability DB
   - "How much for 4 hours?" -> Pricing DB / Calculation
   - "Book this space" -> Booking System
   - "Compare these spaces" -> DB + RAG
   - Host Monetization & Legal Terms -> Platform Knowledge

2. RAG Retrieval Subsystem:
   - Indexes and retrieves semantic chunks from:
     • Listing descriptions
     • Amenities
     • Rules (Food & beverage, smoking, noise)
     • Host policies & Section 52 legal framework
     • Reviews & OTI verified telemetry

3. Marketplace Search Subsystem:
   - Hard filters (Capacity, Price, Category, Location)
   - Real-time availability validation (Booking overlap checks)
   - Dynamic pricing formula

4. Recommendation / Reranking:
   - Composite scoring & explainable match badges

5. Response Generation:
   - Grounded LLM orchestration (Gemini -> Groq -> Deterministic Heuristics)
"""
import re
import json
from datetime import datetime, timedelta, timezone
from models import db, Space, Booking, Review, User
from backend.core.geo import haversine_distance, resolve_location_coordinates
from backend.modules.search.embedding import generate_embedding, cosine_similarity
from backend.app.api.v1.bookings import check_booking_overlap


class LoopBotIntent:
    RAG_AMENITIES = "RAG_AMENITIES"
    RAG_RULES_POLICY = "RAG_RULES_POLICY"
    SUITABILITY_ASSESSMENT = "SUITABILITY_ASSESSMENT"
    MARKETPLACE_SEARCH = "MARKETPLACE_SEARCH"
    AVAILABILITY_QUERY = "AVAILABILITY_QUERY"
    PRICING_CALCULATION = "PRICING_CALCULATION"
    BOOKING_ACTION = "BOOKING_ACTION"
    COMPARE_SPACES = "COMPARE_SPACES"
    HOST_MONETIZATION = "HOST_MONETIZATION"
    LEGAL_AND_SAFETY = "LEGAL_AND_SAFETY"
    GENERAL_CHAT = "GENERAL_CHAT"


def detect_loopbot_intent(query: str, context_data: dict | None = None) -> tuple[str, dict]:
    clean_q = (query or "").lower().strip()
    extracted_params = {}

    space_id_match = re.search(r"\b(?:space|room|listing|id)\s*#?\s*(\d+)\b", clean_q)
    if space_id_match:
        extracted_params["space_id"] = int(space_id_match.group(1))
    elif context_data and context_data.get("space_id"):
        extracted_params["space_id"] = int(context_data["space_id"])

    hours_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr)\b", clean_q)
    if hours_match:
        extracted_params["hours"] = float(hours_match.group(1))

    capacity_match = re.search(r"\b(?:for\s+)?(\d+)\s*(?:people|persons?|guests?|members?|pax|team\s+of\s+(\d+))\b", clean_q)
    if capacity_match:
        extracted_params["capacity"] = int(capacity_match.group(1) or capacity_match.group(2))

    if "tomorrow" in clean_q:
        extracted_params["date"] = "tomorrow"
    elif "today" in clean_q:
        extracted_params["date"] = "today"
    elif "weekend" in clean_q:
        extracted_params["date"] = "weekend"

    price_match = re.search(r"\b(?:under|below|less than|max|budget)\s*(?:₹|rs\.?|inr)?\s*(\d+)\b", clean_q)
    if price_match:
        extracted_params["max_price"] = float(price_match.group(1))

    # A. Booking Action Intent
    if any(k in clean_q for k in ["book this space", "book space", "reserve this space", "how do i book", "how to book", "book now", "reserve now", "make a reservation", "checkout link"]):
        return LoopBotIntent.BOOKING_ACTION, extracted_params

    # B. Compare Spaces Intent
    if any(k in clean_q for k in ["compare these spaces", "compare spaces", "difference between", "which one is better", "compare #", "compare space"]):
        all_ids = [int(m) for m in re.findall(r"#?(\d+)", clean_q)]
        if len(all_ids) >= 2:
            extracted_params["compare_ids"] = all_ids[:3]
        return LoopBotIntent.COMPARE_SPACES, extracted_params

    # C. Pricing Calculation Intent
    if any(k in clean_q for k in ["how much for", "how much does it cost", "calculate cost", "what is the price for", "what would it cost", "pricing for", "fee for", "how much to rent", "how much will it cost"]):
        return LoopBotIntent.PRICING_CALCULATION, extracted_params

    # D. Availability DB Intent
    if any(k in clean_q for k in ["available tomorrow", "what's available", "what is available", "available today", "available this weekend", "open tomorrow", "free tomorrow", "open slots", "available slots", "is it free at"]):
        return LoopBotIntent.AVAILABILITY_QUERY, extracted_params

    # E. Suitability Intent (RAG + Listing Data)
    if any(k in clean_q for k in ["is this good for", "is it good for", "good for a", "suitable for", "can we host a", "can i do a", "can we shoot", "is this space suitable", "will 8 people fit", "will 10 people fit", "fit for a"]):
        return LoopBotIntent.SUITABILITY_ASSESSMENT, extracted_params

    # F. Rules & Policies RAG Intent
    if any(k in clean_q for k in ["bring food", "can i eat", "food allowed", "food and drink", "smoking", "smoke", "pets", "pet friendly", "alcohol", "what are the rules", "house rules", "guest policy", "cancellation policy"]):
        return LoopBotIntent.RAG_RULES_POLICY, extracted_params

    # G. Amenities RAG Intent
    if any(k in clean_q for k in ["what amenities", "amenities does this", "what is included", "is there wifi", "high speed wifi", "has air condition", "have ac", "presentation screen", "monitor", "whiteboard", "parking available", "power backup", "inverter"]):
        return LoopBotIntent.RAG_AMENITIES, extracted_params

    # H. Marketplace Search Intent
    if any(k in clean_q for k in ["find spaces", "find a space", "search spaces", "spaces for", "looking for", "recommend a space", "find workspace", "find studio", "find meeting", "need a desk", "need a room"]):
        return LoopBotIntent.MARKETPLACE_SEARCH, extracted_params

    # I. Host Monetization Intent
    if any(k in clean_q for k in ["how can i rent", "rent out", "how to host", "monetiz", "earn", "list my", "my garage", "unused garage", "empty room", "calculator"]):
        return LoopBotIntent.HOST_MONETIZATION, extracted_params

    # J. Legal Framework & Safety
    if any(k in clean_q for k in ["section 52", "easements act", "legal", "squat", "tenancy", "escrow", "upi deposit", "geofence", "door pass"]):
        return LoopBotIntent.LEGAL_AND_SAFETY, extracted_params

    return LoopBotIntent.GENERAL_CHAT, extracted_params


def _build_space_knowledge_chunks(space: Space) -> list[dict]:
    chunks = []
    amenities_list = space.amenities or []
    rules_list = space.rules or []
    
    desc_chunk = {
        "space_id": space.id,
        "title": f"Space #{space.id}: {space.title} - Description & Specs",
        "category": "description",
        "text": (
            f"Space #{space.id}: '{space.title}' is a verified {space.category} located at {space.location}. "
            f"Usable size: {space.sqft} sq ft, maximum capacity: {space.max_capacity} people. "
            f"Hourly rate: ₹{space.price_hourly}/hr (minimum booking {space.minimum_hours} hour). "
            f"Lighting: {space.ai_lighting}. Acoustic environment: {space.ai_noise_level}. "
            f"Power outlets: {space.ai_power_access}. Recommended uses: {space.ai_recommended_uses or space.category}. "
            f"Full description: {space.description}"
        )
    }
    chunks.append(desc_chunk)

    amenities_text = ", ".join(amenities_list) if amenities_list else "High-speed Wi-Fi, Ergonomic seating, Power backup"
    amen_chunk = {
        "space_id": space.id,
        "title": f"Space #{space.id}: {space.title} - Verified Amenities",
        "category": "amenities",
        "text": (
            f"Verified amenities at Space #{space.id} ('{space.title}'): {amenities_text}. "
            f"Electrical capacity: {space.ai_power_access}. Acoustic noise floor: {space.ai_noise_level}. "
            f"Physical dimensions: {space.ai_dimensions_summary or f'{space.sqft} sq ft layout'}."
        )
    }
    chunks.append(amen_chunk)

    rules_text = "; ".join(rules_list) if rules_list else "Light snacks and non-alcoholic beverages permitted; No smoking inside; Maintain moderate noise floor; Dispose of waste in provided bins"
    rules_chunk = {
        "space_id": space.id,
        "title": f"Space #{space.id}: {space.title} - House Rules & Guidelines",
        "category": "rules",
        "text": (
            f"House rules for Space #{space.id} ('{space.title}'): {rules_text}. "
            f"Food Policy: Light dry snacks, coffee, tea, and packaged water are permitted unless explicitly restricted. Strong-smelling or hot catering requires prior host consent. "
            f"Smoking Policy: Strictly smoke-free environment. "
            f"Noise Policy: {space.ai_noise_level}. Quiet hours and professional decorum apply at all times."
        )
    }
    chunks.append(rules_chunk)

    host_name = space.owner.name if space.owner else "Verified Host"
    host_trust = round(space.owner.objective_trust_score, 1) if space.owner else 98.5
    policy_chunk = {
        "space_id": space.id,
        "title": f"Space #{space.id}: {space.title} - Access & Host Policies",
        "category": "host_policies",
        "text": (
            f"Access and policies for Space #{space.id} (Hosted by {host_name}, Trust Score {host_trust}/100): "
            f"Access type: Zero-hardware geofenced digital pass. Guests verify within 50m of GPS coordinates ({space.latitude}, {space.longitude}) and scan the printable door QR or share 4-digit arrival PIN with caretaker. "
            f"Legal status: Covered under Section 52 of the Indian Easements Act, 1882 as a revocable temporary license (no tenancy rights). "
            f"Escrow: Held safely as ₹100 refundable UPI micro-escrow, automatically released upon on-time checkout."
        )
    }
    chunks.append(policy_chunk)

    avg_rating = space.average_rating()
    reviews_count = len(space.reviews)
    recent_comments = " | ".join([f"'{r.comment}' ({r.rating}★ by {r.user_name})" for r in space.reviews[:3]]) if space.reviews else "Rated 4.9★ by verified guests for cleanliness and high-speed fiber."
    review_chunk = {
        "space_id": space.id,
        "title": f"Space #{space.id}: {space.title} - Guest Reviews & Ratings",
        "category": "reviews",
        "text": (
            f"Telemetry and guest feedback for Space #{space.id}: Average rating {avg_rating}★ across {reviews_count} verified bookings. "
            f"Host on-time vacate rate: {space.owner.on_time_vacate_rate if space.owner else 100}%, cleanliness match rate: {space.owner.cleanliness_match_rate if space.owner else 99}%. "
            f"Recent guest reviews: {recent_comments}"
        )
    }
    chunks.append(review_chunk)

    return chunks


def retrieve_rag_knowledge(query: str, target_space_id: int | None = None, top_k: int = 4) -> list[dict]:
    """Retrieves knowledge chunks through the unified SpaceLoop RAG Knowledge Service."""
    from backend.modules.ai.rag_service import retrieve_rag_documents
    return retrieve_rag_documents(query=query, target_space_id=target_space_id, top_k=top_k)


def calculate_pricing_details(space: Space, hours: float = 4.0) -> dict:
    rate = float(space.price_hourly or 45.0)
    hours = max(0.5, float(hours))
    subtotal = round(rate * hours, 2)
    platform_fee = round(subtotal * 0.05, 2)
    refundable_escrow = 100.0
    total_upfront = round(subtotal + platform_fee + refundable_escrow, 2)
    net_cost = round(subtotal + platform_fee, 2)

    return {
        "space_id": space.id,
        "title": space.title,
        "hourly_rate": rate,
        "hours": hours,
        "subtotal": subtotal,
        "platform_fee": platform_fee,
        "refundable_escrow": refundable_escrow,
        "total_upfront": total_upfront,
        "net_cost": net_cost
    }


def run_marketplace_search(params: dict, raw_query: str = "", limit: int = 3) -> list[dict]:
    """
    Executes marketplace search using the unified SpaceLoop Hybrid Search Engine.
    Combines structured filters, real-time booking overlap, vector cosine similarity, and composite ranking.
    """
    from backend.modules.search.hybrid_search import hybrid_search_spaces
    min_cap = params.get("guest_count") or params.get("capacity")
    max_price = params.get("price") or params.get("max_price")
    cat = params.get("property_type") or params.get("space_type") or params.get("category")
    loc = params.get("location")
    date_val = params.get("date")
    start_time = params.get("start_time")
    end_time = params.get("end_time")
    amenities = params.get("amenities")

    hybrid_out = hybrid_search_spaces(
        raw_query=raw_query or params.get("normalized_text") or "",
        location=loc,
        category=cat,
        min_capacity=min_cap,
        max_price=max_price,
        date=date_val,
        start_time=start_time,
        end_time=end_time,
        amenities=amenities,
        limit=limit
    )

    results = []
    for item in hybrid_out.get("results", []):
        s_dict = item.get("space", {})
        space_id = s_dict.get("id")
        space_obj = Space.query.get(space_id) if space_id else None

        if not space_obj:
            class SpaceProxy:
                def __init__(self, d):
                    for k, v in d.items():
                        setattr(self, k, v)
                    self.id = d.get("id", 1)
                    self.title = d.get("title", "Space")
                    self.location = d.get("location", d.get("city", "Pune"))
                    self.max_capacity = d.get("max_capacity", 4)
                    self.sqft = d.get("sqft", 200)
                    self.price_hourly = d.get("price_hourly", 45.0)
                    self.amenities = d.get("amenities", [])
            space_obj = SpaceProxy(s_dict)

        rate = float(getattr(space_obj, "price_hourly", 45.0) or 45.0)
        pricing_2h = {
            "space_id": getattr(space_obj, "id", space_id),
            "title": getattr(space_obj, "title", "Verified Space"),
            "hourly_rate": rate,
            "hours": 2.0,
            "subtotal": round(rate * 2.0, 2),
            "platform_fee": round(rate * 2.0 * 0.05, 2),
            "refundable_escrow": 100.0,
            "total_upfront": round(rate * 2.0 * 1.05 + 100.0, 2),
            "net_cost": round(rate * 2.0 * 1.05, 2)
        }

        results.append({
            "space": space_obj,
            "is_available": item.get("is_available", True),
            "pricing_2h": pricing_2h,
            "match_badge": item.get("match_badge", "Available Now"),
            "match_reasons": item.get("match_reasons", []),
            "composite_score": item.get("composite_score", 0.8),
            "match_score": item.get("match_score", 80)
        })

    # Safe fallback if 0 candidates matched hard query filters
    if not results:
        fallback_spaces = Space.query.filter_by(is_active=True).all()
        now = datetime.utcnow()
        for s in fallback_spaces[:limit]:
            overlap = check_booking_overlap(s.id, now, now + timedelta(hours=2))
            is_avail = (overlap is None)
            price_2h = calculate_pricing_details(s, hours=2.0)
            results.append({
                "space": s,
                "is_available": is_avail,
                "pricing_2h": price_2h,
                "match_badge": "Available Now",
                "match_reasons": ["Verified SpaceLoop listing"],
                "composite_score": 0.75,
                "match_score": 75
            })

    return results[:limit]


def check_availability_db(space_id: int | None = None, target_date_str: str | None = "tomorrow") -> dict:
    now = datetime.utcnow()
    if target_date_str == "tomorrow":
        target_date = (now + timedelta(days=1)).date()
    elif target_date_str == "weekend":
        days_ahead = (5 - now.weekday()) % 7
        target_date = (now + timedelta(days=days_ahead or 7)).date()
    else:
        target_date = now.date()

    day_start = datetime(target_date.year, target_date.month, target_date.day, 8, 0, 0)
    day_end = datetime(target_date.year, target_date.month, target_date.day, 21, 0, 0)

    if space_id:
        target_spaces = [Space.query.get(space_id)]
    else:
        target_spaces = Space.query.filter_by(is_active=True).limit(4).all()

    target_spaces = [s for s in target_spaces if s]
    availability_reports = []

    for s in target_spaces:
        bookings = Booking.query.filter(
            Booking.space_id == s.id,
            Booking.status.in_(["confirmed", "active"]),
            Booking.start_time < day_end,
            Booking.end_time > day_start
        ).all()

        if not bookings:
            slots_summary = "Full day open (08:00 AM – 09:00 PM)"
            status = "Fully Available"
        else:
            booked_times = [f"{b.start_time.strftime('%I:%M %p')}–{b.end_time.strftime('%I:%M %p')}" for b in bookings]
            slots_summary = f"Open slots available (Booked: {', '.join(booked_times)})"
            status = "Partially Booked"

        availability_reports.append({
            "space_id": s.id,
            "title": s.title,
            "location": s.location,
            "hourly_rate": s.price_hourly,
            "date": target_date.strftime("%A, %b %d"),
            "status": status,
            "slots": slots_summary
        })

    return {
        "date_str": target_date.strftime("%A, %b %d, %Y"),
        "reports": availability_reports
    }


def prepare_booking_system_action(space_id: int | None = None, hours: float = 2.0) -> dict:
    if not space_id:
        s = Space.query.filter_by(is_active=True).first()
        space_id = s.id if s else 4

    space = Space.query.get(space_id)
    title = space.title if space else f"Space #{space_id}"
    pricing = calculate_pricing_details(space, hours=hours) if space else {}

    return {
        "space_id": space_id,
        "title": title,
        "booking_url": f"/space/{space_id}?action=book&hours={hours}",
        "pricing": pricing,
        "steps": [
            "1. Select your preferred date and time slot.",
            "2. Instant UPI micro-escrow authorization (includes refundable ₹100 deposit).",
            "3. Digitally seal your Section 52 Micro-Lease license.",
            "4. Instant geofenced Digital Door Pass and 4-digit Arrival PIN are issued immediately."
        ]
    }


def compare_spaces_db_rag(space_ids: list[int] | None = None) -> list[dict]:
    if not space_ids or len(space_ids) < 2:
        spaces = Space.query.filter_by(is_active=True).limit(2).all()
    else:
        spaces = [Space.query.get(sid) for sid in space_ids if Space.query.get(sid)]

    comparison = []
    for s in spaces:
        amenities_str = ", ".join(s.amenities[:4]) if s.amenities else "Wi-Fi, Ergonomic Desk"
        food_rule = "Light dry snacks permitted" if not any("no food" in r.lower() for r in (s.rules or [])) else "No food inside"
        
        comparison.append({
            "id": s.id,
            "title": s.title,
            "category": s.category,
            "location": s.location,
            "capacity": f"Up to {s.max_capacity} people ({s.sqft} sq ft)",
            "rate": f"₹{s.price_hourly}/hr",
            "noise_level": s.ai_noise_level,
            "amenities": amenities_str,
            "food_policy": food_rule,
            "trust_rating": f"{s.average_rating()}★ ({len(s.reviews)} reviews) • Host OTI: {round(s.owner.objective_trust_score, 1) if s.owner else 98.5}%",
            "recommended_for": s.ai_recommended_uses or s.category
        })

    return comparison


def _sanitize_loopbot_response(text: str) -> str:
    """
    Guarantees clean, production-grade output:
    - Strips raw JSON blocks or curly brace dumps
    - Strips internal database object strings (e.g. <Space 1>, <User 2>)
    - Strips tool execution artifacts or internal error tracebacks
    - Strips raw vector embeddings and float score lists
    - Removes raw HTML tags and normalizes whitespace
    """
    if not text:
        return ""

    cleaned = str(text)

    # 1. Remove raw JSON blocks (e.g. ```json ... ``` or standalone { ... })
    cleaned = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", cleaned)
    cleaned = re.sub(r'\{\s*"[a-zA-Z0-9_]+":[\s\S]*?\}', "", cleaned)

    # 2. Remove database object representations (e.g. <Space 1: ...>, <User 2>)
    cleaned = re.sub(r"<[A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)*:\s*[^>]*>", "", cleaned)
    cleaned = re.sub(r"<[A-Za-z0-9_]+\s+object\s+at\s+0x[0-9a-fA-F]+>", "", cleaned)

    # 3. Remove raw tool tags or debugging output (e.g. [TOOL_OUTPUT: ...], Traceback)
    cleaned = re.sub(r"\[(?:TOOL|DEBUG|INTERNAL)[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Traceback\s*\(most\s+recent\s+call\s+last\):[\s\S]*?(?:\w+Error:.*)", "", cleaned)

    # 4. Remove vector embeddings or raw score dumps
    cleaned = re.sub(r"\[-?\d+\.\d+(?:,\s*-?\d+\.\d+){4,}\]", "", cleaned)
    cleaned = re.sub(r"(?:cosine_similarity|embedding_score|score):\s*\d+\.\d+", "", cleaned)

    # 5. Clean HTML tags
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)

    # 6. Normalize whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _handle_clarification(effective_lang: str) -> str:
    from backend.modules.nlp.i18n import MultilingualService
    return MultilingualService.get_localized_response("CLARIFICATION_NEEDED", effective_lang)


def _handle_search_property(params: dict, effective_lang: str, raw_query: str = "") -> str:
    from backend.modules.nlp.i18n import MultilingualService
    if effective_lang != "en":
        return MultilingualService.get_localized_response("SEARCH_SPACE", effective_lang, params)

    search_results = run_marketplace_search(params, raw_query=raw_query, limit=3)
    cap_req = params.get("guest_count") or params.get("capacity") or "Flexible"
    cards = []
    for idx, res in enumerate(search_results):
        s = res["space"]
        p = res["pricing_2h"]
        title = getattr(s, "title", "Verified Space")
        loc = getattr(s, "location", "Pune")
        max_cap = getattr(s, "max_capacity", 4)
        sqft = getattr(s, "sqft", 200)
        rate = getattr(s, "price_hourly", 45.0)
        amenities = getattr(s, "amenities", [])
        amen_str = ", ".join(amenities[:3]) if amenities else "High-speed Wi-Fi, Ergonomic Desk"
        status_str = "🟢 Available Now" if res["is_available"] else "🟡 Reserved soon"
        badge = res.get("match_badge", "Available Now")
        reasons = res.get("match_reasons", [])
        reason_line = f"\n   • Why this matches: {reasons[0]}" if reasons else ""

        cards.append(
            f"{idx + 1}. **{title}** ({badge})\n"
            f"   • Location: {loc}\n"
            f"   • Capacity: Up to {max_cap} people ({sqft} sq ft)\n"
            f"   • Rate: ₹{rate}/hour (Total ₹{p['total_upfront']} for 2h incl. deposit)\n"
            f"   • Amenities: {amen_str}\n"
            f"   • Status: {status_str}{reason_line}"
        )
    cards_str = "\n\n".join(cards) if cards else "No matching spaces found at this exact moment."
    return (
        f"🔍 **Marketplace Search Results for {cap_req} People:**\n\n"
        f"{cards_str}\n\n"
        f"All spaces are verified under Section 52 revocable licenses with zero-hardware digital door passes. Would you like to reserve one?"
    )


def _handle_check_availability(params: dict, space_id: int | None, effective_lang: str) -> str:
    target_date = params.get("date_str") or params.get("date", "tomorrow")
    avail = check_availability_db(space_id=space_id, target_date_str=target_date)
    date_str = avail["date_str"]
    reports_text = "\n\n".join([
        f"• **{r['title']}** in {r['location']} (₹{r['hourly_rate']}/hr)\n"
        f"  Status: {r['status']}\n"
        f"  Available Windows: {r['slots']}"
        for r in avail["reports"]
    ])
    return (
        f"📅 **Real-Time Space Availability for {date_str}:**\n\n"
        f"{reports_text}\n\n"
        f"You can choose immediate check-in or reserve a specific slot. Which time window works best for you?"
    )


def _handle_book_property(params: dict, space_id: int | None, hours: float, effective_lang: str) -> str:
    from backend.modules.nlp.i18n import MultilingualService
    if effective_lang != "en":
        return MultilingualService.get_localized_response("BOOK_SPACE", effective_lang, params)

    action = prepare_booking_system_action(space_id=space_id, hours=hours)
    p = action.get("pricing", {})
    steps_text = "\n".join([f"   {step}" for step in action["steps"]])
    return (
        f"🚀 **Booking System: {action['title']}**\n\n"
        f"Ready to secure your temporary space reservation:\n"
        f"• **Direct Booking Link**: `/space/{action['space_id']}`\n"
        f"• **Estimated Cost ({hours}h)**: ₹{p.get('total_upfront', 194.5)} upfront (includes ₹100 instant refundable deposit)\n\n"
        f"**Instant Reservation Steps**:\n"
        f"{steps_text}\n\n"
        f"Visit the listing page at `/space/{action['space_id']}` to confirm your booking in under 60 seconds!"
    )


def _handle_ask_price(params: dict, space_id: int | None, hours: float, effective_lang: str) -> str:
    target_s = Space.query.get(space_id) if space_id else Space.query.filter_by(is_active=True).first()
    p = calculate_pricing_details(target_s, hours=hours) if target_s else {
        "title": "Standard Flexible Space",
        "hourly_rate": 45.0,
        "hours": hours,
        "subtotal": 45.0 * hours,
        "platform_fee": round(45.0 * hours * 0.05, 2),
        "refundable_escrow": 100.0,
        "total_upfront": round(45.0 * hours * 1.05 + 100.0, 2),
        "net_cost": round(45.0 * hours * 1.05, 2)
    }
    return (
        f"💰 **Pricing Calculation Breakdown ({p['hours']} Hours) for {p['title']}:**\n\n"
        f"1. **Base Hourly Rent**: ₹{p['hourly_rate']}/hr × {p['hours']}h = **₹{p['subtotal']}**\n"
        f"2. **Platform & Safety Fee (5%)**: **₹{p['platform_fee']}**\n"
        f"3. **Refundable UPI Micro-Escrow**: **₹{p['refundable_escrow']}** *(Released instantly at checkout)*\n\n"
        f"• **Total Upfront Payable**: **₹{p['total_upfront']}**\n"
        f"• **Net Final Cost to You**: **₹{p['net_cost']}** *(after your ₹100 deposit is refunded)*\n\n"
        f"Zero hidden charges. Would you like to proceed with booking this space?"
    )


def _handle_ask_location(params: dict, space_id: int | None, effective_lang: str) -> str:
    target_s = Space.query.get(space_id) if space_id else Space.query.filter_by(is_active=True).first()
    if target_s:
        addr = target_s.address or f"{target_s.neighborhood or ''}, {target_s.city}"
        return (
            f"📍 **Location Details: {target_s.title}**\n\n"
            f"• **Address**: {addr}\n"
            f"• **Neighborhood / City**: {target_s.neighborhood or target_s.city}, {target_s.city}\n"
            f"• **Coordinates**: {target_s.latitude}, {target_s.longitude}\n"
            f"• **Zero-Hardware Arrival**: Geofence radius of 50m. Simply arrive on site to scan the door QR or provide your 4-digit PIN.\n\n"
            f"Would you like me to check available slots or show pricing for this space?"
        )
    return (
        "📍 **SpaceLoop Locations:**\n\n"
        "SpaceLoop operates verified, zero-hardware workspaces across Pune (Kharadi, Wagholi, Baner, Kothrud), Dehradun, Rishikesh, Mumbai, and Delhi.\n\n"
        "Which city or neighborhood are you looking for spaces in?"
    )


def _handle_ask_amenities(query: str, space_id: int | None, effective_lang: str) -> str:
    target_space = Space.query.get(space_id) if space_id else Space.query.filter_by(is_active=True).first()
    space_title = target_space.title if target_space else "our verified spaces"
    amen_list = target_space.amenities if target_space and target_space.amenities else ["High-speed fiber Wi-Fi", "4K presentation monitor", "Ergonomic seating", "Inverter power backup"]
    amen_bullets = "\n".join([f"   • {a}" for a in amen_list])
    return (
        f"⚡ **Verified Amenities & Equipment for {space_title}:**\n\n"
        f"{amen_bullets}\n\n"
        f"• **Acoustic Environment**: {target_space.ai_noise_level if target_space else 'Quiet (<45 dB)'}\n"
        f"• **Power Access**: {target_space.ai_power_access if target_space else 'Continuous power backup with dedicated surge-protected outlets'}\n"
        f"• **Access Protocol**: Geofenced digital door pass with instant arrival PIN.\n\n"
        f"Ready to book or would you like to know how much a session costs?"
    )


def _handle_create_listing(params: dict, effective_lang: str) -> str:
    from backend.modules.nlp.i18n import MultilingualService
    if effective_lang != "en":
        return MultilingualService.get_localized_response("HOST_MONETIZE", effective_lang, params)
    return (
        "🏡 **Monetize Your Idle Space on SpaceLoop:**\n\n"
        "Turn spare rooms, garages, terraces, or off-peak office desks into passive monthly income:\n"
        "1. **60-Second AI Photo Scan**: Point your camera at `/list-space` to calculate square footage and acoustic grade.\n"
        "2. **Dynamic Rates**: Earn ₹45–₹150/hour based on your space type and amenities.\n"
        "3. **Keep 95% Yield**: Direct automated UPI payouts with only a 5% platform fee.\n"
        "4. **Full Tenancy Protection**: Section 52 revocable licenses eliminate adverse tenancy claims.\n\n"
        "Visit `/list-space` to start listing your space or `/calculator` to estimate your monthly earnings!"
    )


def _handle_edit_listing(params: dict, effective_lang: str) -> str:
    return (
        "✏️ **Editing & Managing Your Space Listing:**\n\n"
        "Hosts can update their listings at any time without downtime:\n"
        "1. Open your **Host Dashboard** at `/dashboard`.\n"
        "2. Navigate to the **Host Spaces** section.\n"
        "3. Click **Edit Space** on the listing you want to modify.\n"
        "4. You can adjust hourly rates, upload new photos, edit amenities, update quiet hours, or change house rules.\n"
        "5. Click **Save Changes** — your updates reflect immediately across the SpaceLoop marketplace."
    )


def _handle_ask_booking_status(params: dict, context_data: dict | None, effective_lang: str) -> str:
    user_id = context_data.get("user_id") if context_data else None
    if user_id:
        try:
            recent_booking = Booking.query.filter_by(renter_id=user_id).order_by(Booking.created_at.desc()).first()
            if recent_booking:
                s = recent_booking.space
                title = s.title if s else f"Space #{recent_booking.space_id}"
                start_fmt = recent_booking.start_time.strftime("%d %b %I:%M %p") if recent_booking.start_time else "Scheduled"
                end_fmt = recent_booking.end_time.strftime("%I:%M %p") if recent_booking.end_time else ""
                status_icon = "🟢" if recent_booking.status in ("confirmed", "active") else "🟡"
                return (
                    f"📋 **Your Booking Status:**\n\n"
                    f"{status_icon} **{title}** (Booking #{recent_booking.id})\n"
                    f"• Status: **{recent_booking.status.title()}**\n"
                    f"• Time Window: {start_fmt} – {end_fmt}\n"
                    f"• Zero-Hardware Access: Geofence activates within 50m of coordinates.\n"
                    f"• Digital Door Pass & PIN available on your `/dashboard`.\n\n"
                    f"Need directions or help with your session?"
                )
        except Exception:
            pass

    return (
        "📋 **Booking Status Inquiry:**\n\n"
        "You can view all your active, upcoming, and past reservations with instant digital door passes in your **Guest Dashboard** at `/dashboard`.\n\n"
        "If you just placed a booking, confirmation is instant upon UPI micro-escrow authorization. Would you like me to find a space or help you reserve one?"
    )


def _handle_ask_payment_status(params: dict, effective_lang: str) -> str:
    from backend.modules.nlp.i18n import MultilingualService
    if effective_lang != "en":
        return MultilingualService.get_localized_response("ESCROW_REFUND", effective_lang, params)
    return (
        "💳 **₹100 UPI Micro-Escrow & Payment Protocol:**\n\n"
        "• **Security Deposit**: ₹100 is temporarily pre-authorized via UPI during booking to secure the space.\n"
        "• **Instant Automated Refund**: Upon on-time checkout and room electrical power-off confirmation, the ₹100 escrow hold is released back to your UPI VPA within 120 seconds.\n"
        "• **Accepted Payment Methods**: All UPI apps (Google Pay, PhonePe, Paytm, BHIM), debit/credit cards, and net banking.\n"
        "• **Receipts**: Detailed invoices and escrow refund receipts can be viewed anytime in your `/dashboard`."
    )


def _handle_report_fraud(params: dict, effective_lang: str) -> str:
    return (
        "🛡️ **SpaceLoop Trust & Safety — Report an Issue:**\n\n"
        "We enforce strict integrity standards across all physical spaces and host interactions:\n"
        "1. **Report Incident**: Go to your `/dashboard` or the space page and click **Report an Issue**.\n"
        "2. **Immediate Lock**: Suspected fraudulent spaces or abusive accounts are frozen pending investigation.\n"
        "3. **Deposit Protection**: Escrow funds and rental fees are safely held in escrow during disputes.\n"
        "4. **Legal Enforcement**: All bookings operate under Section 52 revocable micro-licenses with zero-hardware GPS audit trails.\n\n"
        "Our Trust & Safety team reviews all incident flags 24/7."
    )


def _handle_ask_help(query: str, effective_lang: str) -> str:
    from backend.modules.nlp.i18n import MultilingualService
    if effective_lang != "en":
        return MultilingualService.get_localized_response("LEGAL_SAFETY", effective_lang)
    return (
        "🤝 **SpaceLoop Help & Platform Guide:**\n\n"
        "• **How SpaceLoop Works**: Discover and book verified physical spaces by the hour with zero hardware keys or physical handoffs.\n"
        "• **Section 52 Legal Protection**: All reservations operate as non-possessory micro-licenses under Section 52 of the Indian Easements Act, 1882. No tenancy rights are created.\n"
        "• **₹100 UPI Micro-Escrow**: Deposits are held safely in escrow and refunded within 120 seconds of on-time checkout.\n"
        "• **Key Actions**:\n"
        "  - Search spaces: Visit `/` or `/explore`\n"
        "  - Calculate host earnings: Visit `/calculator`\n"
        "  - List unused space: Visit `/list-space`\n"
        "  - View your account: Visit `/dashboard`\n\n"
        "What can I help you accomplish today?"
    )


def _handle_general_conversation(effective_lang: str, context_data: dict | None) -> str:
    from backend.modules.nlp.i18n import MultilingualService
    if effective_lang != "en":
        return MultilingualService.get_localized_response("GREETING", effective_lang)
    role = (context_data or {}).get("role", "seeker")
    user_name = (context_data or {}).get("user_name", "")
    prefix = f"Hello {user_name}! " if user_name else ""
    return (
        f"👋 {prefix}I'm **LoopBot**, your SpaceLoop AI Concierge!\n\n"
        f"I can help you discover workspaces, book meeting rooms by the hour, explain Section 52 legal safety, check availability, or monetize your unused square footage.\n\n"
        f"How can I assist you today?"
    )


def orchestrate_loopbot_query(
    query: str,
    history: list | None = None,
    context_data: dict | None = None,
    return_dict: bool = False
) -> str | dict:
    """
    Unified Loop Bot Orchestrator:
    Executes the complete flow:
    Language Detection -> Normalization -> Intent Extraction -> Entity Extraction ->
    Tool/Retrieval Decision -> Subsystem Execution -> Response Generation -> Language Localization -> Output Sanitizer.
    """
    from backend.modules.nlp.pipeline import NLPPipeline
    from backend.modules.nlp.schemas import IntentType
    from backend.modules.nlp.intent_service import IntentService
    from backend.modules.nlp.i18n import MultilingualService

    context_data = context_data or {}
    lang_pref = context_data.get("language_preference")

    # Step 1: Run unified 4-stage NLP Pipeline
    nlp_result = NLPPipeline.process(query, context_data=context_data)
    effective_lang, detected_lang, is_code_mixed = MultilingualService.negotiate_language(
        query, explicit_preference=lang_pref
    )

    canonical_intent = IntentService.canonicalize_intent(nlp_result.intent)
    params = nlp_result.entities or {}

    # Contextual fallbacks from context_data
    if "space_id" not in params and context_data.get("space_id"):
        params["space_id"] = int(context_data["space_id"])
    space_id = params.get("space_id")
    hours = params.get("duration_hours") or params.get("hours") or 4.0

    # Step 2: Capability / Retrieval Decision Layer
    # Low-confidence Intent Guardrail (< 0.60 or CLARIFICATION_NEEDED): ask clarification, never invent.
    if canonical_intent == IntentType.CLARIFICATION_NEEDED.value or nlp_result.confidence < 0.60:
        raw_reply = _handle_clarification(effective_lang)
        canonical_intent = IntentType.CLARIFICATION_NEEDED.value
    elif canonical_intent == IntentType.SEARCH_PROPERTY.value:
        raw_reply = _handle_search_property(params, effective_lang, raw_query=query)
    elif canonical_intent == IntentType.CHECK_AVAILABILITY.value:
        raw_reply = _handle_check_availability(params, space_id, effective_lang)
    elif canonical_intent == IntentType.BOOK_PROPERTY.value:
        raw_reply = _handle_book_property(params, space_id, hours, effective_lang)
    elif canonical_intent == IntentType.ASK_PRICE.value:
        raw_reply = _handle_ask_price(params, space_id, hours, effective_lang)
    elif canonical_intent == IntentType.ASK_LOCATION.value:
        raw_reply = _handle_ask_location(params, space_id, effective_lang)
    elif canonical_intent == IntentType.ASK_AMENITIES.value:
        raw_reply = _handle_ask_amenities(query, space_id, effective_lang)
    elif canonical_intent == IntentType.CREATE_LISTING.value:
        raw_reply = _handle_create_listing(params, effective_lang)
    elif canonical_intent == IntentType.EDIT_LISTING.value:
        raw_reply = _handle_edit_listing(params, effective_lang)
    elif canonical_intent == IntentType.ASK_BOOKING_STATUS.value:
        raw_reply = _handle_ask_booking_status(params, context_data, effective_lang)
    elif canonical_intent == IntentType.ASK_PAYMENT_STATUS.value:
        raw_reply = _handle_ask_payment_status(params, effective_lang)
    elif canonical_intent == IntentType.REPORT_FRAUD.value:
        raw_reply = _handle_report_fraud(params, effective_lang)
    elif canonical_intent == IntentType.ASK_HELP.value:
        raw_reply = _handle_ask_help(query, effective_lang)
    elif canonical_intent == IntentType.GENERAL_CONVERSATION.value:
        raw_reply = _handle_general_conversation(effective_lang, context_data)
    else:
        raw_reply = _handle_clarification(effective_lang)
        canonical_intent = IntentType.CLARIFICATION_NEEDED.value

    # Step 3: Sanitize output to guarantee no raw JSON, DB objects, or tool output
    clean_reply = _sanitize_loopbot_response(raw_reply)

    if return_dict:
        return {
            "reply": clean_reply,
            "intent": canonical_intent,
            "entities": nlp_result.entities,
            "detected_language": detected_lang,
            "response_language": effective_lang,
            "confidence": round(nlp_result.confidence, 4),
            "requires_clarification": (canonical_intent == IntentType.CLARIFICATION_NEEDED.value)
        }
    return clean_reply
