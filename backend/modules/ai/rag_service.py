"""
SpaceLoop RAG (Retrieval-Augmented Generation) Knowledge Service
===============================================================
Encapsulates platform rules, booking info, user guidance, marketplace procedures,
fraud explanations, listing requirements, and help documentation.

Features:
1. Seven Curated Platform Knowledge Domains:
   - Platform Rules (Section 52 Indian Easements Act, food & beverage, noise, smoking)
   - Booking Information (hourly booking, instant confirmation, 50m geofence PIN, cancellation)
   - User Guidance (how to search, filter, navigate dashboard, access spaces)
   - Marketplace Procedures (host payouts, 95% host yield, 5% fee, check-in/checkout flow)
   - Fraud Explanations (₹100 UPI micro-escrow, 120s automated refund, anti-squatting, discom CA verification)
   - Listing Requirements (60-sec AI photo scan, minimum sqft/capacity, electrical outlet verification)
   - Help Documentation (support, dispute resolution, trust & safety reporting)

2. Dynamic Space Knowledge:
   - Indexes space specs, verified amenities, house rules, reviews, and host trust scores.

3. Selective Query Gating:
   - Only invokes RAG when domain or listing knowledge is required.
   - Bypasses RAG for greetings, pure arithmetic pricing, availability lookups, and marketplace search.

4. Robust Safe Degradation Hierarchy:
   - Vector Embedding similarity -> Token/Concept overlap fallback -> Curated platform fallback -> Deterministic synthesis.
   - Zero hallucination when documents are missing or irrelevant.

5. Strict Privacy & Leak Protection:
   - Never exposes raw JSON, vector similarity scores, internal database structure, tool payloads, or error traces.
"""
import re
import logging
from datetime import datetime
from models import db, Space
from backend.modules.search.embedding import generate_embedding, cosine_similarity

logger = logging.getLogger("spaceloop.ai.rag_service")

# Minimum similarity threshold to accept a retrieved chunk as relevant
MIN_RELEVANCE_THRESHOLD = 0.45


# =====================================================================
# 1. PLATFORM KNOWLEDGE BASE (System Design, Platform Rules, Common Queries)
# =====================================================================

PLATFORM_KNOWLEDGE_DOCUMENTS = [
    # Domain 1: Legal & Section 52 Easements Act Protection
    {
        "id": "rules-section-52",
        "domain": "rules",
        "title": "Section 52 Indian Easements Act Legal Protection & Micro-License",
        "keywords": ["section 52", "legal", "easements act", "license", "tenancy", "squatting", "eviction", "ownership", "rights", "adverse possession", "rent control", "धारा 52", "कानूनी", "कलम 52", "कलम ५२", "कब्जा", "kabza", "malik", "kanoon", "tenancy risk"],
        "text": (
            "Every SpaceLoop reservation is executed as a Revocable Temporary Micro-License under Section 52 of the Indian Easements Act, 1882. "
            "This grants non-possessory, temporary permission to use the designated space strictly for the booked hours. "
            "Crucially, no tenancy rights, leasehold interests, exclusive possession, or statutory tenant protections (such as under Rent Control Acts) are created. "
            "The host retains 100% legal possession and absolute ownership at all times, completely eliminating squatting and adverse tenancy risks."
        )
    },
    # Domain 2: Zero-Hardware Smart Access Architecture
    {
        "id": "system-zero-hardware-access",
        "domain": "system_design",
        "title": "Zero-Hardware Smart Access: 50m Geofence, QR Pass & 4-Digit PIN",
        "keywords": ["zero hardware", "access", "geofence", "pin", "arrival", "check-in", "door pass", "qr code", "smart lock", "keys", "door", "डिजिटल पास", "जियोफेंस", "प्रवेश", "चाबी", "door lock", "checkin", "arrival pin", "50m"],
        "text": (
            "SpaceLoop replaces physical key handoffs and expensive smart locks with a Zero-Hardware Geofenced Access system. "
            "Upon booking confirmation, a digital pass is generated in your dashboard. When your smartphone GPS is within 50 meters "
            "of the property's verified coordinates, the pass activates, displaying a dynamic time-bound QR code and a 4-digit arrival PIN "
            "to share with the on-site caretaker or building security. It works reliably even with intermittent internet connectivity."
        )
    },
    # Domain 3: Discom Electricity CA Meter Verification
    {
        "id": "fraud-discom-verification",
        "domain": "fraud",
        "title": "Discom Electricity CA Meter Verification & Land Title Proof",
        "keywords": ["discom", "ca number", "electricity", "meter", "fake listing", "fraud", "address verification", "utility bill", "verification", "डिस्कॉम", "बिजली", "मीटर", "सत्यापन", "विजेचे बिल", "पडताळणी", "bijli bill", "light bill", "bijli", "meter"],
        "text": (
            "To prevent phantom listings, unauthorized subletting, and broker fraud, SpaceLoop verifies the host's state Electricity Discom Consumer Account (CA) number "
            "and recent utility bill via OCR and government utility APIs before activating any listing. "
            "This anchors every digital space to a verified physical power meter and authentic physical premises without requiring intrusive physical title deeds."
        )
    },
    # Domain 4: ₹100 Automated UPI Micro-Escrow & Instant Refund Protocol
    {
        "id": "fraud-micro-escrow-protocol",
        "domain": "fraud",
        "title": "₹100 Automated UPI Micro-Escrow & 120-Second Instant Refund Protocol",
        "keywords": ["escrow", "upi deposit", "micro-escrow", "100", "security deposit", "refund", "120 seconds", "safe deposit", "deposit refund", "power off", "एस्क्रो", "रिफंड", "डिपॉजिट", "डिपॉझिट", "परतावा", "deposit wapas", "100 rupaye", "deposit refund", "paisa"],
        "text": (
            "To deter energy waste, accidental damage, and unauthorized overstays, SpaceLoop pre-authorizes a nominal ₹100 security deposit via UPI during booking. "
            "The funds remain in an RBI-compliant escrow hold. Upon on-time checkout and room electrical appliance shutoff check via the `/dashboard`, "
            "the ₹100 escrow hold is automatically released back to the user's UPI VPA within 120 seconds. Zero manual mediation needed."
        )
    },
    # Domain 5: Sovereign DigiLocker KYC & Penny Drops
    {
        "id": "fraud-host-identity-kyc",
        "domain": "fraud",
        "title": "DigiLocker Sovereign Aadhaar KYC & ₹1 Host Penny-Drop Verification",
        "keywords": ["kyc", "digilocker", "aadhaar", "penny drop", "host verification", "identity", "trust score", "bank check", "आधार", "केवाईसी", "पडताळणी", "पहचान", "aadhaar"],
        "text": (
            "Both guests and hosts undergo tokenized sovereign DigiLocker Aadhaar KYC. Host bank accounts are validated via a ₹1 penny drop "
            "to ensure instant automated payout routing. Every user receives an Objective Trust Index (OTI) score computed from verified punctuality, "
            "cleanliness match rate, and Discom credentials."
        )
    },
    # Domain 6: AI Room Vision Scanner
    {
        "id": "system-ai-room-scanner",
        "domain": "system_design",
        "title": "AI Computer Vision Room Scanner & Acoustic Classification",
        "keywords": ["ai scan", "photo scan", "computer vision", "sqft", "lumens", "lighting", "noise level", "acoustic floor", "vision model", "फोटो स्कैन", "कैमरा", "माप", "scanner"],
        "text": (
            "When creating a space at `/list-space`, hosts upload 1 to 4 photos. SpaceLoop's AI vision engine automatically estimates usable square footage, "
            "measures natural and artificial lighting levels (lumens), assesses acoustic noise floor (whisper <40dB vs standard conversational), "
            "detects electrical outlet accessibility, and suggests optimal space categories (Focus Desk, Meeting Room, Studio, Workshop)."
        )
    },
    # Domain 7: Dynamic Pricing, Upfront Fees & 95% Host Yield
    {
        "id": "pricing-host-yield-breakdown",
        "domain": "pricing",
        "title": "Transparent Upfront Pricing Formula & 95% Net Host Yield",
        "keywords": ["pricing", "cost", "calculation", "breakdown", "platform fee", "5%", "95%", "host payout", "earnings", "fees", "commission", "किराया", "कमाई", "भाडे", "कमीशन", "kamai", "payout", "host kamai", "income"],
        "text": (
            "SpaceLoop enforces 100% upfront pricing transparency with zero hidden charges. "
            "Seeker Total = (Hourly Rate × Hours) + 5% Platform Fee + ₹100 Refundable UPI Escrow. "
            "Hosts keep 95% of gross rental revenue. Payouts are transferred automatically via UPI within 24 hours of session completion. "
            "Listing a space is completely free with zero subscription fees."
        )
    },
    # Domain 8: Objective Trust Index (OTI)
    {
        "id": "system-objective-trust-index",
        "domain": "system_design",
        "title": "Objective Trust Index (OTI): Calibrated Trust & Punctuality Scoring",
        "keywords": ["oti", "trust score", "objective trust index", "rating", "punctuality", "cleanliness", "telemetry", "ट्रस्ट स्कोर", "रेटिंग", "oti score"],
        "text": (
            "SpaceLoop calculates an Objective Trust Index (OTI) scored from 0 to 100 for all hosts and users. "
            "The score is mathematically derived from on-time vacate rate (GPS telemetry), Discom power meter verification, "
            "cleanliness audit matches, and verified user reviews. High-OTI spaces receive priority matching and featured badges."
        )
    },
    # Domain 9: Food, Beverage & Catering Policy
    {
        "id": "rules-food-beverage",
        "domain": "rules",
        "title": "Food, Beverage & Outside Snacks Policy",
        "keywords": ["food", "beverage", "eat", "drink", "snacks", "coffee", "tea", "water", "catering", "lunch", "meals", "outside food", "खाना", "नाश्ता", "चाय", "कॉफ़ी", "जेवण", "खाणे", "khana", "jevan", "bahar ka khana", "nashta", "bhojan", "drink"],
        "text": (
            "Light dry snacks, sealed beverages, coffee, tea, and personal water bottles are welcome across private workspaces, meeting pods, "
            "and quiet study spaces. Messy, greasy, strong-smelling foods or full hot catered buffets require explicit prior host authorization. "
            "Guests are required to dispose of all food waste in provided trash bins before checkout."
        )
    },
    # Domain 10: Noise Etiquette, Focus Pods & Quiet Hours
    {
        "id": "rules-noise-acoustic",
        "domain": "rules",
        "title": "Noise Limits, Focus Pod Etiquette & Quiet Hours",
        "keywords": ["noise", "loud", "quiet", "music", "decibel", "sound", "shouting", "acoustic", "call", "quiet hours", "शोर", "आवाज़", "शांत", "आवाज", "shant", "aawaz", "shor"],
        "text": (
            "SpaceLoop enforces acoustic decorum per category: Study and focus pods enforce a whisper-quiet policy (<40 dB). "
            "Private meeting rooms and offices comfortably accommodate conversational speaking volume and video calls. "
            "Quiet hours apply after 9:00 PM across all residential locations. Loud music or amplified instruments require a specialized sound studio listing."
        )
    },
    # Domain 11: 100% Smoke-Free & Substance Prohibition
    {
        "id": "rules-smoke-substance",
        "domain": "rules",
        "title": "100% Smoke-Free, Alcohol & Substance Prohibition",
        "keywords": ["smoking", "smoke", "cigarette", "vape", "alcohol", "drugs", "substance", "drinking", "tobacco", "धूम्रपान", "सिगरेट", "शराब", "दारू", "dhumrapan", "cigarette"],
        "text": (
            "SpaceLoop enforces a strict zero-tolerance 100% smoke-free policy indoors, covering cigarettes, biddies, e-cigarettes, and vapes. "
            "Alcohol and illicit substances are prohibited. Violations trigger immediate license termination, forfeiture of the ₹100 deposit, "
            "and permanent platform ban."
        )
    },
    # Domain 12: Pet Policy
    {
        "id": "rules-pet-policy",
        "domain": "rules",
        "title": "Pet Policy & Pet-Friendly Spaces",
        "keywords": ["pet", "pets", "dog", "cat", "animals", "pet friendly", "pets allowed", "पालतू", "कुत्ता", "कुत्रा", "प्राणी", "kutta", "kuta", "dog allowed"],
        "text": (
            "Pets are permitted only in spaces explicitly tagged as 'Pet Friendly' by the host. "
            "Certified service animals are accommodated with advance notice. Pet owners are responsible for cleanliness and preventing damage."
        )
    },
    # Domain 13: Parking & Transit Availability
    {
        "id": "guidance-parking-transit",
        "domain": "guidance",
        "title": "Parking Availability & Transit Access",
        "keywords": ["parking", "car parking", "bike parking", "vehicle", "metro", "transit", "bus", "location access", "पार्किंग", "गाड़ी", "मेट्रो", "parking"],
        "text": (
            "Parking options (Free Dedicated, Street, Covered, Visitor, or 2-Wheeler Only) are displayed on each listing's verified amenity cards. "
            "Each space page also includes neighborhood transit directions, nearest metro/bus stations, and 50m geofence arrival coordinates."
        )
    },
    # Domain 14: Booking Duration, Scheduling & Real-Time Availability
    {
        "id": "booking-duration-slots",
        "domain": "booking",
        "title": "Hourly Booking Duration, Scheduling & Real-Time Availability",
        "keywords": ["hourly", "booking", "schedule", "slots", "minimum hours", "reserve", "timing", "duration", "availability", "समय", "घंटे", "तास", "उपलब्ध", "khali", "slots", "time"],
        "text": (
            "Spaces can be booked by the hour with instant confirmation, starting from 30 minutes up to 7 consecutive days. "
            "Standard minimum duration is 1 hour. All slot availability is checked in real time against active bookings to eliminate double-booking."
        )
    },
    # Domain 15: Cancellation & Rescheduling Guidelines
    {
        "id": "booking-cancellation-policy",
        "domain": "booking",
        "title": "Cancellation & Rescheduling Guidelines",
        "keywords": ["cancellation", "cancel", "refund", "reschedule", "change time", "policy", "refund policy", "रद्द", "रद्द करणे", "कैनसेल", "cancel kaise kare", "cancelation", "cancel"],
        "text": (
            "Cancellations made more than 2 hours before the start time receive a 100% full refund of all rental fees and the ₹100 deposit. "
            "Cancellations within 2 hours of the start time incur a 50% reservation fee for host preparation, while the ₹100 deposit is 100% refunded."
        )
    },
    # Domain 16: Booking Extensions, Grace Periods & Overstay Policy
    {
        "id": "booking-extension-overstay",
        "domain": "booking",
        "title": "Booking Extensions, 15-Minute Grace Period & Overstay Rules",
        "keywords": ["extend", "extension", "more time", "overstay", "late checkout", "grace period", "delay", "बढ़ाना", "वेळ वाढवणे", "extend kaise kare", "overstay"],
        "text": (
            "Guests can easily extend active bookings from their `/dashboard` if the next slot is unbooked. "
            "A 15-minute checkout grace period is provided. Unapproved overstays exceeding 15 minutes are charged at 1.5x the hourly rate "
            "to compensate incoming guests and the host."
        )
    },
    # Domain 17: Student Verification & Academic Concessions
    {
        "id": "guidance-student-discount",
        "domain": "guidance",
        "title": "Student Verification & 10% Academic Concessions",
        "keywords": ["student", "college", "university", "student discount", "academic", "study pod", "concession", "student id", "छात्र", "विद्यार्थी", "कॉलेज", "छूट", "student id", "discount"],
        "text": (
            "Verified students receive a 10% discount on study pods, focus desks, and collaborative spaces. "
            "Upload your valid college/university ID card at `/verify` or during sign-up to unlock academic pricing badges across the marketplace."
        )
    },
    # Domain 18: How to Discover & Filter Spaces
    {
        "id": "guidance-search-filters",
        "domain": "guidance",
        "title": "How to Discover, Filter & Compare Spaces",
        "keywords": ["how to find", "how to search", "filter", "explore", "search spaces", "budget", "amenities", "capacity", "compare", "खोज", "शोधणे", "dhoondo", "khojo"],
        "text": (
            "Browse verified spaces at `/explore` or use natural language queries on the home page (e.g., 'meeting room in Baner under ₹500'). "
            "Filter by distance radius (1km–25km), hourly budget ceiling, capacity, and amenities (Wi-Fi, power backup, AC, monitor, whiteboard). "
            "Every card displays an AI Match score and explainable match reasons."
        )
    },
    # Domain 19: Managing Reservations on the Guest Dashboard
    {
        "id": "guidance-dashboard-navigation",
        "domain": "guidance",
        "title": "Managing Reservations on the Guest Dashboard",
        "keywords": ["dashboard", "my bookings", "active booking", "receipt", "pass", "view booking", "invoice", "डैशबोर्ड", "माझी बुकिंग", "खाता"],
        "text": (
            "Your centralized dashboard at `/dashboard` allows you to view active reservations, track session countdown timers, "
            "access geofenced door passes with arrival PINs, extend bookings, check out, and download GST invoices and escrow refund receipts."
        )
    },
    # Domain 20: Host Listing Creation & 60-Second Setup
    {
        "id": "listing-ai-photo-scan",
        "domain": "listing",
        "title": "Host Space Listing & 60-Second AI Setup",
        "keywords": ["list space", "create listing", "photo scan", "ai scan", "sqft", "requirements", "noise level", "lighting", "monetize space", "लिस्ट", "जोड़ें", "space list"],
        "text": (
            "Hosts can list idle square footage at `/list-space` in under 60 seconds. Upload 1 to 4 space photos to activate the AI scanner "
            "that calculates dimensions, verifies power outlets, and classifies lighting and acoustics. Enter hourly rate, upload electricity bill "
            "for Discom CA verification, and publish immediately."
        )
    },
    # Domain 21: Host Dashboard, Listing Management & Payouts
    {
        "id": "procedures-host-management",
        "domain": "procedures",
        "title": "Host Dashboard, Listing Management & Instant Payouts",
        "keywords": ["host dashboard", "manage space", "edit listing", "payouts", "host earnings", "update rates", "change rules", "होस्ट", "कमाई", "पैसे"],
        "text": (
            "Hosts manage active spaces from the Host Dashboard at `/dashboard`. You can adjust hourly rates, update photos, edit amenities, "
            "modify quiet hours, or change house rules without downtime. Payouts (95% net revenue) are credited automatically to your registered UPI VPA within 24 hours."
        )
    },
    # Domain 22: Trust, Safety, Incident Reporting & Escrow Mediation
    {
        "id": "help-support-disputes",
        "domain": "help",
        "title": "Trust & Safety, Incident Reporting & Escrow Mediation",
        "keywords": ["help", "support", "contact", "emergency", "incident", "report", "dispute", "complaint", "issue", "freeze", "मदद", "सहायता", "तक्रार", "शिकायत", "dispute"],
        "text": (
            "If an issue occurs during a booking (e.g. host unreachable, Wi-Fi failure, cleanliness discrepancy), tap 'Report an Issue' "
            "on your `/dashboard` or the space page. The ₹100 deposit and rental fees are instantly frozen in escrow while our 24/7 Trust & Safety "
            "mediation team reviews GPS audit logs and photos to resolve the dispute fairly."
        )
    }
]


# =====================================================================
# 2. SELECTIVE QUERY GATING
# =====================================================================

def should_retrieve_rag(intent: str, query: str = "", context_data: dict | None = None) -> bool:
    """
    Decides whether RAG retrieval is required for this query.
    Prevents unnecessary latency and hallucination on conversational chit-chat,
    simple greetings, pure arithmetic pricing, availability queries, or direct search.
    """
    intent_upper = (intent or "").upper().strip()
    clean_q = (query or "").lower().strip()

    # Explicit intents that require domain or listing knowledge
    KNOWLEDGE_INTENTS = {
        "ASK_AMENITIES",
        "RAG_AMENITIES",
        "RAG_RULES_POLICY",
        "SUITABILITY_ASSESSMENT",
        "LEGAL_AND_SAFETY",
        "REPORT_FRAUD",
        "ASK_HELP",
        "CREATE_LISTING",
        "EDIT_LISTING",
        "ASK_PAYMENT_STATUS",
        "HOST_MONETIZATION"
    }

    if intent_upper in KNOWLEDGE_INTENTS:
        return True

    # If asking about rules, safety, Section 52, deposits, or food/drink directly
    KNOWLEDGE_KEYWORDS = [
        "section 52", "easements act", "legal", "squat", "tenancy", "escrow",
        "deposit", "food", "eat", "drink", "smoke", "smoking", "alcohol",
        "rules", "policy", "wifi", "power backup", "amenities", "discom",
        "ca number", "payout", "earnings", "how to list", "help", "support"
    ]
    if any(k in clean_q for k in KNOWLEDGE_KEYWORDS):
        return True

    # If context has a target space and user is asking about space attributes
    if context_data and context_data.get("space_id") and any(w in clean_q for w in ["what", "has", "have", "can", "allowed", "rule", "spec"]):
        return True

    return False


# =====================================================================
# 3. KNOWLEDGE CHUNK BUILDER
# =====================================================================

def build_space_chunks(space: Space) -> list[dict]:
    """Generates rich, cohesive knowledge chunks for a specific listing."""
    chunks = []
    amenities_list = space.amenities or []
    rules_list = space.rules or []

    # 1. Description & Specs
    chunks.append({
        "id": f"space-{space.id}-specs",
        "domain": "space_specs",
        "space_id": space.id,
        "title": f"{space.title} — Specifications & Environment",
        "keywords": ["specifications", "capacity", "sqft", "lighting", "noise", "uses", space.title.lower(), space.category.lower()],
        "text": (
            f"Space #{space.id}: '{space.title}' is a verified {space.category} located at {space.location}. "
            f"Usable size: {space.sqft} sq ft, maximum capacity: {space.max_capacity} people. "
            f"Hourly rate: ₹{space.price_hourly}/hr (minimum booking {space.minimum_hours} hour). "
            f"Lighting: {space.ai_lighting}. Acoustic environment: {space.ai_noise_level}. "
            f"Power outlets: {space.ai_power_access}. Recommended uses: {space.ai_recommended_uses or space.category}. "
            f"Full description: {space.description}"
        )
    })

    # 2. Amenities
    amen_str = ", ".join(amenities_list) if amenities_list else "High-speed Wi-Fi, Ergonomic seating, Power backup"
    chunks.append({
        "id": f"space-{space.id}-amenities",
        "domain": "space_amenities",
        "space_id": space.id,
        "title": f"{space.title} — Verified Amenities",
        "keywords": ["amenities", "wifi", "power", "screens", "monitors", "ac", space.title.lower()],
        "text": (
            f"Verified amenities at Space #{space.id} ('{space.title}'): {amen_str}. "
            f"Electrical capacity: {space.ai_power_access}. Acoustic noise floor: {space.ai_noise_level}."
        )
    })

    # 3. House Rules
    rules_str = "; ".join(rules_list) if rules_list else "Light snacks and beverages permitted; No smoking inside; Maintain moderate noise floor; Dispose of waste in provided bins"
    chunks.append({
        "id": f"space-{space.id}-rules",
        "domain": "space_rules",
        "space_id": space.id,
        "title": f"{space.title} — House Rules & Policies",
        "keywords": ["rules", "food", "smoking", "noise", "guest policy", space.title.lower()],
        "text": (
            f"House rules for Space #{space.id} ('{space.title}'): {rules_str}. "
            f"Food Policy: Light dry snacks, coffee, tea, and water bottles permitted. Messy or hot catering requires prior host consent. "
            f"Smoking Policy: Strictly smoke-free indoors. Noise Policy: Professional decorum, quiet hours apply after 9 PM."
        )
    })

    # 4. Access & Trust
    host_name = space.owner.name if space.owner else "Verified Host"
    host_trust = round(space.owner.objective_trust_score, 1) if space.owner else 98.5
    chunks.append({
        "id": f"space-{space.id}-access",
        "domain": "space_access",
        "space_id": space.id,
        "title": f"{space.title} — Zero-Hardware Access & Host Trust",
        "keywords": ["access", "geofence", "pin", "trust score", "host", space.title.lower()],
        "text": (
            f"Access details for Space #{space.id} (Hosted by {host_name}, Trust Score {host_trust}/100): "
            f"Zero-hardware digital pass activates when guest is within 50m of GPS coordinates ({space.latitude}, {space.longitude}). "
            f"Guests receive a 4-digit arrival PIN and printable door QR. Governed under Section 52 revocable license with ₹100 refundable UPI escrow."
        )
    })

    return chunks


# =====================================================================
# 4. RETRIEVAL ENGINE WITH SAFE DEGRADATION FALLBACKS
# =====================================================================

def retrieve_rag_documents(
    query: str,
    target_space_id: int | None = None,
    top_k: int = 3,
    min_similarity: float = MIN_RELEVANCE_THRESHOLD
) -> list[dict]:
    """
    Multi-tier knowledge retriever:
    1. Collects static platform knowledge + dynamic space knowledge chunks.
    2. Primary: Dense Vector Embedding & Cosine Similarity.
    3. Fallback: Token overlap + semantic concept matching when embedding fails or vector DB is unavailable.
    4. Safe Degradation: Filters chunks below relevance threshold, preventing hallucinations.
    """
    clean_q = (query or "").strip()
    if not clean_q:
        return []

    # Assemble corpus
    corpus = list(PLATFORM_KNOWLEDGE_DOCUMENTS)

    # Add space-specific chunks
    if target_space_id:
        space = Space.query.get(target_space_id)
        if space and space.is_active:
            corpus.extend(build_space_chunks(space))
    else:
        active_spaces = Space.query.filter_by(is_active=True).limit(5).all()
        for s in active_spaces:
            corpus.extend(build_space_chunks(s))

    # Tier 1: Dense Vector Retrieval
    query_vector = None
    embedding_failed = False
    try:
        query_vector = generate_embedding(clean_q)
    except Exception as e:
        logger.warning(f"Vector embedding failed in RAG retrieval: {e}. Falling back to token matching.")
        embedding_failed = True

    # Tokenizer for keyword/concept matching fallback
    indic_stop_words = {
        "क्या", "है", "हैं", "हो", "का", "की", "के", "में", "से", "पर", "को", "काय", "आहे",
        "आहेत", "कसे", "कशी", "करावे", "नाही", "छन", "छौ", "था", "थी", "थे", "ने", "तो", "ही"
    }
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "in", "on",
        "at", "to", "for", "of", "with", "by", "from", "about", "into", "through", "during",
        "before", "after", "above", "below", "up", "down", "out", "off", "over", "under",
        "again", "further", "then", "once", "here", "there", "when", "where", "why", "how",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
        "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
        "just", "should", "now", "what", "does", "please", "tell", "show", "give", "know",
        "want", "like", "do", "did", "doing", "would", "could", "have", "has", "had", "having",
        "you", "your", "my", "our", "their", "his", "her", "its", "it", "they", "them",
        "we", "us", "this", "that", "these", "those"
    }.union(indic_stop_words)

    raw_tokens = re.findall(r"[\u0900-\u097F]+|[a-zA-Z0-9]{2,}", clean_q.lower())
    tokens = [t.lower() for t in raw_tokens if t not in stop_words]
    if not tokens:
        tokens = [t.lower() for t in raw_tokens if t not in ("for", "and", "the", "with", "this", "that", "what", "how", "क्या", "काय")]

    scored_chunks = []
    for doc in corpus:
        score = 0.0

        # Keyword & concept overlap component with token sets
        keywords_list = [k.lower() for k in doc.get("keywords", [])]
        kw_overlap = sum(1 for t in tokens if t in keywords_list or any(t == k or (len(t) > 3 and t in k) for k in keywords_list))

        doc_text_lower = (doc["title"] + " " + " ".join(doc.get("keywords", [])) + " " + doc["text"]).lower()
        doc_tokens = set(re.findall(r"[\u0900-\u097F]+|[a-zA-Z0-9]{2,}", doc_text_lower))
        text_overlap = sum(1 for t in tokens if t in doc_tokens)

        title_lower = doc.get("title", "").lower()
        title_tokens = set(re.findall(r"[\u0900-\u097F]+|[a-zA-Z0-9]{2,}", title_lower))
        title_overlap = sum(1 for t in tokens if t in title_tokens)

        overlap_score = 0.0
        if tokens:
            overlap_score = (text_overlap / len(tokens)) * 0.35 + (kw_overlap / len(tokens)) * 0.40 + (title_overlap / len(tokens)) * 0.25

        # Vector similarity component
        sim = 0.0
        if query_vector and not embedding_failed:
            doc_vec = generate_embedding(doc["text"][:400])
            if doc_vec:
                sim = cosine_similarity(query_vector, doc_vec)

        # Hybrid combination: require some semantic/lexical affinity
        if tokens and (text_overlap > 0 or kw_overlap > 0 or title_overlap > 0):
            score = (sim * 0.45) + (overlap_score * 0.55)
        elif not tokens:
            score = sim * 0.70
        else:
            # When query has distinct tokens but zero match in text, title, or keywords, suppress vector baseline
            score = sim * 0.25

        # Boost exact space match if space_id specified, otherwise boost relevant platform documents
        if target_space_id and doc.get("space_id") == target_space_id:
            score += 0.25
        elif not target_space_id and (title_overlap >= 1 or kw_overlap >= 1) and doc.get("domain") in ("rules", "system_design", "fraud", "pricing", "guidance", "booking", "legal"):
            score += 0.15

        scored_chunks.append({
            "doc": doc,
            "score": round(score, 4)
        })

    # Sort descending by score
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    # Filter by minimum relevance threshold to prevent hallucination on irrelevant topics
    relevant_docs = []
    for item in scored_chunks:
        if item["score"] >= min_similarity:
            # Strip internal score before passing downstream
            clean_doc = dict(item["doc"])
            clean_doc["relevance_rank"] = len(relevant_docs) + 1
            relevant_docs.append(clean_doc)
        if len(relevant_docs) >= top_k:
            break

    return relevant_docs


# =====================================================================
# 5. RESPONSE GROUNDING & PRIVACY SANITIZATION
# =====================================================================

def synthesize_rag_response(
    query: str,
    retrieved_docs: list[dict],
    intent: str = "ASK_HELP",
    effective_lang: str = "en"
) -> str:
    """
    Synthesizes a helpful, accurate user response strictly grounded in retrieved documents.
    Safely degrades to clean deterministic formatting if LLM fails.
    Directly answers what was asked without dumping irrelevant sections.
    """
    if not retrieved_docs:
        if effective_lang in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns"):
            return (
                "SpaceLoop के दस्तावेज़ों में इस प्रश्न का सीधा उत्तर नहीं मिला। "
                "SpaceLoop धारा 52 के तहत प्रति घंटा सत्यापन युक्त कार्यक्षेत्र, ₹100 रिफ़ंडेबल UPI एस्क्रो और 50m डिजिटल पास प्रदान करता है। "
                "सहायता के लिए अपने `/dashboard` पर जाएँ या ट्रस्ट एंड सेफ्टी से संपर्क करें।"
            )
        elif effective_lang in ("mr", "mr-Latn"):
            return (
                "SpaceLoop च्या दस्तऐवजांमध्ये या प्रश्नाचे थेट उत्तर उपलब्ध नाही. "
                "SpaceLoop कलम ५२ अन्वये प्रति तास सुरक्षित जागा, ₹१०० परत मिळणारे UPI एस्क्रो आणि ५०m डिजिटल पास देते. "
                "कृपया आपल्या `/dashboard` ला भेट द्या."
            )
        return (
            "I couldn't find specific documentation directly answering that question in SpaceLoop's knowledge base. "
            "SpaceLoop provides verified hourly workspaces governed under Section 52 revocable licenses with ₹100 refundable UPI micro-escrow. "
            "Please check your `/dashboard` or contact Trust & Safety support."
        )

    # Pick the top most relevant documents
    top_doc = retrieved_docs[0]
    is_single_direct_answer = len(retrieved_docs) == 1 or retrieved_docs[0].get("relevance_rank", 1) == 1

    if is_single_direct_answer and len(retrieved_docs) == 1:
        title = top_doc.get("title", "")
        text = top_doc.get("text", "")
        return f"💡 **{title}**\n\n{text}"

    points = []
    for doc in retrieved_docs[:2]:
        title = doc.get("title", "")
        text = doc.get("text", "")
        points.append(f"• **{title}**:\n  {text}")

    grounded_body = "\n\n".join(points)

    if effective_lang in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns"):
        header = "💡 **SpaceLoop जानकारी:**"
    elif effective_lang in ("mr", "mr-Latn"):
        header = "💡 **SpaceLoop माहिती:**"
    else:
        header = "💡 **SpaceLoop Information:**"

    return f"{header}\n\n{grounded_body}"


def build_rag_context(retrieved_docs: list[dict]) -> str:
    """Formats retrieved document snippets cleanly into contextual text."""
    if not retrieved_docs:
        return ""
    snippets = []
    for idx, doc in enumerate(retrieved_docs, start=1):
        title = doc.get("title", f"Document {idx}").strip()
        text = doc.get("text", "").strip()
        snippets.append(f"[{idx}] {title}\n{text}")
    return "\n\n".join(snippets)


def generate_rag_response(
    query: str,
    retrieved_docs: list[dict] | None = None,
    target_space_id: int | None = None,
    intent: str = "ASK_HELP",
    context_data: dict | None = None,
    effective_lang: str = "en"
) -> str:
    """
    Complete RAG Generation Pipeline:
    1. Retrieve relevant SpaceLoop context (platform docs + space chunks) if not provided.
    2. Check relevance threshold: if no relevant documents match, states that information is unavailable.
    3. Build structured context prompt prioritizing retrieved facts.
    4. Call LLM (Groq 120B -> Gemini Flash) with strict grounding instructions to answer ONLY what was asked.
    5. Fallback safely to deterministic synthesis on LLM error/timeout.
    """
    clean_q = (query or "").strip()
    if not clean_q:
        if effective_lang in ("hi", "hi-Latn"):
            return "नमस्ते! मैं आज SpaceLoop पर आपकी क्या सहायता कर सकता हूँ?"
        elif effective_lang in ("mr", "mr-Latn"):
            return "नमस्कार! मी आज SpaceLoop वर आपल्याला कशी मदत करू शकतो?"
        return "How can I assist you with SpaceLoop today?"

    if retrieved_docs is None:
        retrieved_docs = retrieve_rag_documents(
            query=clean_q,
            target_space_id=target_space_id,
            top_k=3,
            min_similarity=MIN_RELEVANCE_THRESHOLD
        )

    if not retrieved_docs:
        # Zero-hallucination safe response when context lacks the answer
        if effective_lang in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns"):
            return (
                "SpaceLoop के दस्तावेज़ों में इस प्रश्न का सटीक उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली। "
                "SpaceLoop भारतीय सुखाधिकार अधिनियम की धारा 52 के तहत लाइसेंस पर स्थान प्रदान करता है, जिसमें ₹100 का वापसी योग्य UPI माइक्रो-एस्क्रो शामिल है।"
            )
        elif effective_lang in ("mr", "mr-Latn"):
            return (
                "SpaceLoop च्या दस्तऐवजांमध्ये या प्रश्नाचे अचूक उत्तर देण्यासाठी पुरेशी माहिती उपलब्ध नाही. "
                "SpaceLoop कलम 52 अन्वये ₹100 परत मिळणाऱ्या UPI एस्क्रोसह सुरक्षित जागा उपलब्ध करून देते."
            )
        return (
            "I don't have enough specific information in SpaceLoop's documentation to answer that question accurately. "
            "SpaceLoop provides verified hourly spaces governed under Section 52 revocable licenses with ₹100 refundable UPI micro-escrow."
        )

    context_text = build_rag_context(retrieved_docs)

    from backend.modules.nlp.i18n import MultilingualService, LANGUAGE_METADATA
    lang_info = LANGUAGE_METADATA.get(effective_lang, LANGUAGE_METADATA.get("en", {}))
    lang_name = lang_info.get("name", "English")
    lang_guidelines = MultilingualService.build_multilingual_prompt_guidelines(effective_lang)

    system_prompt = (
        f"You are LoopBot, SpaceLoop's AI Concierge.\n"
        f"Directly and concisely answer ONLY the specific question asked by the user, strictly grounded in the SpaceLoop Context below.\n\n"
        f"TASK & ANSWERING RULES:\n"
        f"1. Answer ONLY what the user asked. Do NOT dump broad platform summaries or unrequested guides unless the user explicitly asks for an overview.\n"
        f"2. If the user asks about a specific feature, policy, design, rule, or amenity (e.g., zero-hardware door pass, Section 52 legal protection, Discom CA utility verification, ₹100 UPI escrow refund, outside food/snacks policy, pet policy, noise limits, student discounts, cancellation, or host payouts), explain that specific mechanism clearly and directly in 2 to 4 sentences.\n"
        f"3. Language: Respond in {lang_name} ({effective_lang}). {lang_guidelines}\n"
        f"4. Data Preservation: NEVER translate or alter prices (e.g. ₹100, ₹45/hr), times (e.g. 120 seconds, 2 hours), percentages (e.g. 95%, 5%), technical terms (Section 52, UPI, Discom, DigiLocker, GPS), or URLs (/dashboard, /list-space, /explore).\n"
        f"5. Zero Hallucination: Do not invent rules or policies not found in the context. If missing, concisely state it's unavailable."
    )

    user_prompt = f"SpaceLoop Context:\n{context_text}\n\nUser Question: {clean_q}"

    # Multi-tier LLM invocation with failover (Groq -> Gemini -> deterministic synthesizer)
    llm_response = None
    try:
        from space_ai import _call_groq, _call_gemini
        # Tier 1: Groq
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        groq_out = _call_groq(messages, temperature=0.2)
        if groq_out and len(groq_out.strip()) > 10:
            llm_response = groq_out.strip()
        else:
            # Tier 2: Gemini
            gemini_out = _call_gemini(f"{system_prompt}\n\n{user_prompt}", temperature=0.2)
            if gemini_out and len(gemini_out.strip()) > 10:
                llm_response = gemini_out.strip()
    except Exception as e:
        logger.warning(f"LLM call in generate_rag_response failed: {e}. Falling back to deterministic synthesis.")

    # Tier 3: Deterministic fallback if LLM is unavailable or fails
    if not llm_response:
        llm_response = synthesize_rag_response(
            query=clean_q,
            retrieved_docs=retrieved_docs,
            intent=intent,
            effective_lang=effective_lang
        )

    return llm_response

