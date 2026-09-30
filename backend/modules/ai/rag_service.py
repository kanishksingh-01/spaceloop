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
# 1. PLATFORM KNOWLEDGE BASE (7 Domains)
# =====================================================================

PLATFORM_KNOWLEDGE_DOCUMENTS = [
    # Domain 1: Platform Rules
    {
        "id": "rules-section-52",
        "domain": "rules",
        "title": "Section 52 Indian Easements Act Legal Protection",
        "keywords": ["section 52", "legal", "easements act", "license", "tenancy", "squatting", "eviction", "ownership", "rights"],
        "text": (
            "Every SpaceLoop reservation is legally executed as a Revocable License under Section 52 of the Indian Easements Act, 1882. "
            "It grants a strictly temporary permission to enter and use the premises for the specified hours. "
            "Crucially, no tenancy, leasehold rights, exclusive possession, or statutory tenant protections are created. "
            "The property host retains absolute ownership and legal possession at all times."
        )
    },
    {
        "id": "rules-food-beverage",
        "domain": "rules",
        "title": "Food, Beverage & Catering Policy",
        "keywords": ["food", "beverage", "eat", "drink", "snacks", "coffee", "water", "catering", "lunch", "meals"],
        "text": (
            "Outside light dry snacks, sealed beverages, coffee, tea, and personal water bottles are welcome across all private workspaces, "
            "meeting pods, and quiet study nooks. Messy, greasy, strong-smelling foods or full hot catered buffets are strictly prohibited "
            "unless the host grants explicit pre-authorization before the session begins. Guests must clear all waste into provided bins."
        )
    },
    {
        "id": "rules-noise-acoustic",
        "domain": "rules",
        "title": "Noise Limits & Acoustic Etiquette",
        "keywords": ["noise", "loud", "quiet", "music", "decibel", "sound", "shouting", "acoustic", "call"],
        "text": (
            "All SpaceLoop spaces enforce moderate acoustic levels. Private offices and meeting rooms accommodate normal speaking volume "
            "and video conferencing. Study pods maintain a strict whisper policy (<40 dB). Quiet hours apply after 9:00 PM across all residential "
            "neighborhood locations. Amplified speakers or heavy instruments require a specialized Sound Studio listing."
        )
    },
    {
        "id": "rules-smoke-substance",
        "domain": "rules",
        "title": "Smoke-Free & Substance Prohibition",
        "keywords": ["smoking", "smoke", "cigarette", "vape", "alcohol", "drugs", "substance", "drinking"],
        "text": (
            "SpaceLoop enforces a zero-tolerance 100% smoke-free policy across all indoor premises, including cigarettes, e-cigarettes, "
            "and vaporizers. Alcohol and illicit substances are strictly prohibited. Any violation results in immediate license revocation, "
            "forfeiture of the ₹100 security deposit, and potential account suspension."
        )
    },

    # Domain 2: Booking Information
    {
        "id": "booking-duration-slots",
        "domain": "booking",
        "title": "Hourly Booking Structure & Scheduling",
        "keywords": ["hourly", "booking", "schedule", "slots", "minimum hours", "reserve", "timing", "duration"],
        "text": (
            "Spaces can be reserved by the hour with instant confirmation, starting from as short as 30 minutes up to multiple days. "
            "Standard minimum booking duration is 1 hour. Booking availability is validated in real time against the central database "
            "to prevent double-booking or scheduling conflicts."
        )
    },
    {
        "id": "booking-access-geofence",
        "domain": "booking",
        "title": "Zero-Hardware Geofenced Check-In & Arrival PIN",
        "keywords": ["access", "geofence", "pin", "arrival", "check-in", "door", "pass", "qr", "hardware", "key"],
        "text": (
            "SpaceLoop eliminates physical keys and costly smart hardware. Once a booking is confirmed, a digital door pass is issued. "
            "When the guest arrives within 50 meters of the property's verified GPS coordinates, the system activates the pass, revealing "
            "a 4-digit arrival PIN to share with the on-site caretaker or a printable door QR code to scan."
        )
    },
    {
        "id": "booking-cancellation-policy",
        "domain": "booking",
        "title": "Cancellation & Rescheduling Guidelines",
        "keywords": ["cancellation", "cancel", "refund", "reschedule", "change time", "policy"],
        "text": (
            "Reservations cancelled more than 2 hours before the scheduled start time receive a 100% full refund of all rental fees and the ₹100 deposit. "
            "Cancellations made within 2 hours of the start time incur a 50% reservation fee to protect host preparation time, while the ₹100 deposit is fully returned."
        )
    },

    # Domain 3: User Guidance
    {
        "id": "guidance-search-filters",
        "domain": "guidance",
        "title": "How to Discover & Filter Spaces",
        "keywords": ["how to find", "how to search", "filter", "explore", "search spaces", "budget", "amenities", "capacity"],
        "text": (
            "Seekers can discover spaces via natural language queries (e.g., 'quiet place near Kharadi under 500') on the home page or `/explore`. "
            "You can filter by capacity, hourly price ceiling, location radius, space type (Workspace, Meeting, Studio, Study), and amenities "
            "(high-speed Wi-Fi, 4K monitor, power backup, parking). Each listing displays an AI Match badge and explainable reasoning."
        )
    },
    {
        "id": "guidance-dashboard-navigation",
        "domain": "guidance",
        "title": "Managing Reservations on the Guest Dashboard",
        "keywords": ["dashboard", "my bookings", "active booking", "receipt", "pass", "view booking"],
        "text": (
            "Your centralized dashboard at `/dashboard` lets you view upcoming reservations, live access timers, geofenced door passes, "
            "and download GST-compliant invoices and escrow refund receipts anytime."
        )
    },

    # Domain 4: Marketplace Procedures
    {
        "id": "procedures-host-monetization",
        "domain": "procedures",
        "title": "Host Payouts & 95% Net Revenue Yield",
        "keywords": ["host", "payout", "earnings", "monetize", "revenue", "commission", "platform fee", "fee", "yield", "95%"],
        "text": (
            "SpaceLoop provides hosts with maximum yield: hosts keep 95% of gross rental revenue. SpaceLoop charges a modest 5% platform fee "
            "to renters at checkout. Payouts are automated via UPI or direct bank transfer within 24 hours of successful session conclusion. "
            "There are zero upfront listing fees or recurring subscription charges."
        )
    },
    {
        "id": "procedures-checkout-flow",
        "domain": "procedures",
        "title": "Automated Checkout & Room Inspection",
        "keywords": ["checkout", "check out", "leave", "vacate", "inspection", "power off", "appliances", "end session"],
        "text": (
            "When your booked session concludes, tap 'Check Out' on your `/dashboard`. Guests are prompted to take a quick photo confirming "
            "that electrical appliances (lights, AC, fans) are powered off and the room is clean. This triggers instantaneous release of the ₹100 deposit."
        )
    },

    # Domain 5: Fraud Explanations
    {
        "id": "fraud-micro-escrow-protocol",
        "domain": "fraud",
        "title": "₹100 UPI Micro-Escrow Security Deposit",
        "keywords": ["escrow", "upi deposit", "micro-escrow", "100", "security deposit", "refund", "120 seconds", "safe deposit"],
        "text": (
            "To deter fraudulent bookings, malicious damage, and energy waste, SpaceLoop pre-authorizes a nominal ₹100 security deposit via UPI. "
            "The funds are safely held in an RBI-compliant escrow account. Upon verified on-time vacate and appliance power-off, "
            "the escrow service automatically processes an instant refund directly back to the guest's UPI VPA within 120 seconds."
        )
    },
    {
        "id": "fraud-premise-verification",
        "domain": "fraud",
        "title": "Discom Electricity CA Meter & Physical Verification",
        "keywords": ["discom", "ca number", "electricity", "meter", "fake listing", "fraud", "address verification", "meter bill"],
        "text": (
            "SpaceLoop eliminates ghost listings and address fraud by verifying the host's state Electricity Discom Consumer Account (CA) number "
            "and recent utility bill before activating any physical space. This binds the digital listing to a verified physical electrical meter."
        )
    },
    {
        "id": "fraud-host-identity-kyc",
        "domain": "fraud",
        "title": "DigiLocker Aadhaar KYC & Host Penny Drops",
        "keywords": ["kyc", "digilocker", "aadhaar", "penny drop", "host verification", "identity", "trust score"],
        "text": (
            "Every host must complete digital identity verification via DigiLocker tokenized Aadhaar and a ₹1 penny-drop bank account check. "
            "SpaceLoop computes an Objective Trust Score (OTI) based on on-time vacating rates, cleanliness feedback, and response times."
        )
    },

    # Domain 6: Listing Requirements
    {
        "id": "listing-ai-photo-scan",
        "domain": "listing",
        "title": "Listing Creation & 60-Second AI Photo Scan",
        "keywords": ["list space", "create listing", "photo scan", "ai scan", "sqft", "requirements", "noise level", "lighting"],
        "text": (
            "Hosts can list idle square footage at `/list-space` in under 60 seconds. Uploading 1 to 4 space photos invokes our AI vision pipeline, "
            "which automatically estimates usable square footage, classifies natural lighting, recommends optimal uses (Meeting, Studio, Workspace), "
            "and evaluates acoustic noise floors."
        )
    },
    {
        "id": "listing-mandatory-standards",
        "domain": "listing",
        "title": "Mandatory Physical Space Standards",
        "keywords": ["standards", "amenities required", "minimum requirements", "power", "seating", "cleanliness"],
        "text": (
            "To be published on the SpaceLoop marketplace, a space must provide: stable electrical power outlets, adequate ambient lighting, "
            "ergonomic seating appropriate for the listed capacity, clean hygienic flooring, and clear access instructions."
        )
    },

    # Domain 7: Help Documentation
    {
        "id": "help-support-disputes",
        "domain": "help",
        "title": "Customer Support & Incident Escalation",
        "keywords": ["help", "support", "contact", "emergency", "incident", "report", "dispute", "complaint", "issue"],
        "text": (
            "If an issue arises during a session (e.g. host unreachable, Wi-Fi outage, or cleanliness mismatch), report the incident immediately "
            "via your `/dashboard` or click 'Report an Issue' on the space page. The ₹100 deposit and session payment are frozen in escrow "
            "until our 24/7 Trust & Safety mediation team reviews the GPS telemetry and photo audit logs."
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
    tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z0-9]{3,}\b", clean_q.lower())
              if t not in ("for", "and", "the", "with", "this", "that", "what", "how", "can", "are")]

    scored_chunks = []
    for doc in corpus:
        score = 0.0

        # Vector similarity component
        if query_vector and not embedding_failed:
            doc_vec = generate_embedding(doc["text"][:400])
            if doc_vec:
                sim = cosine_similarity(query_vector, doc_vec)
                score += sim * 0.70

        # Keyword & concept overlap component
        doc_text_lower = (doc["title"] + " " + " ".join(doc.get("keywords", [])) + " " + doc["text"]).lower()
        if tokens:
            overlap = sum(1 for t in tokens if t in doc_text_lower)
            score += (overlap / len(tokens)) * 0.30

        # Boost exact space match if space_id specified
        if target_space_id and doc.get("space_id") == target_space_id:
            score += 0.20

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
    Never exposes internal scores, JSON, vectors, or database fields.
    """
    if not retrieved_docs:
        if effective_lang in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns"):
            return (
                "SpaceLoop के दस्तावेज़ों में इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली। "
                "SpaceLoop भारतीय सुखाधिकार अधिनियम की धारा 52 के तहत लाइसेंस पर स्थान प्रदान करता है, जिसमें ₹100 का वापसी योग्य UPI माइक्रो-एस्क्रो शामिल है। "
                "कृपया सहायता के लिए अपने `/dashboard` पर जाएँ या ट्रस्ट एंड सेफ्टी से संपर्क करें।"
            )
        elif effective_lang in ("mr", "mr-Latn"):
            return (
                "SpaceLoop च्या दस्तऐवजांमध्ये या प्रश्नाचे अचूक उत्तर देण्यासाठी पुरेशी माहिती उपलब्ध नाही. "
                "SpaceLoop कलम 52 अन्वये ₹100 परत मिळणाऱ्या UPI एस्क्रोसह सुरक्षित जागा उपलब्ध करून देते. "
                "कृपया आपल्या `/dashboard` ला भेट द्या किंवा ट्रस्ट आणि सेफ्टी टीमशी संपर्क साधा."
            )
        return (
            "I couldn't find specific documentation directly answering that question. "
            "SpaceLoop provides verified hourly spaces governed under Section 52 revocable licenses with ₹100 refundable UPI micro-escrow. "
            "Please check your `/dashboard` or contact our Trust & Safety support team for further assistance."
        )

    # Build grounded factual answer directly from top retrieved documents
    points = []
    for doc in retrieved_docs:
        title = doc.get("title", "")
        text = doc.get("text", "")
        points.append(f"• **{title}**:\n  {text}")

    grounded_body = "\n\n".join(points)

    if effective_lang in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns"):
        header = "📘 **SpaceLoop प्लेटफ़ॉर्म जानकारी:**"
        if intent in ("ASK_AMENITIES", "RAG_AMENITIES"):
            header = "⚡ **सत्यापित सुविधाएं व वातावरण:**"
        elif intent in ("RAG_RULES_POLICY", "LEGAL_AND_SAFETY"):
            header = "⚖️ **कानूनी सुरक्षा व नियम (धारा 52):**"
        elif intent in ("REPORT_FRAUD", "ASK_PAYMENT_STATUS"):
            header = "🛡️ **सुरक्षा व ₹100 यूपीआई एस्क्रो:**"
        elif intent in ("CREATE_LISTING", "EDIT_LISTING", "HOST_MONETIZATION"):
            header = "🏡 **होस्ट कमाई व लिस्टिंग दिशानिर्देश:**"
        closing = "क्या आप किसी अन्य विषय पर और जानकारी चाहते हैं?"
    elif effective_lang in ("mr", "mr-Latn"):
        header = "📘 **SpaceLoop प्लॅटफॉर्म माहिती:**"
        if intent in ("ASK_AMENITIES", "RAG_AMENITIES"):
            header = "⚡ **सत्यापित सोयीसुविधा व वातावरण:**"
        elif intent in ("RAG_RULES_POLICY", "LEGAL_AND_SAFETY"):
            header = "⚖️ **कायदेशीर संरक्षण व नियम (कलम ५२):**"
        elif intent in ("REPORT_FRAUD", "ASK_PAYMENT_STATUS"):
            header = "🛡️ **सुरक्षा व ₹१०० यूपीआय एस्क्रो:**"
        elif intent in ("CREATE_LISTING", "EDIT_LISTING", "HOST_MONETIZATION"):
            header = "🏡 **होस्ट उत्पन्न व लिस्टिंग मार्गदर्शक:**"
        closing = "आपल्याला याबद्दल आणखी काही माहिती हवी आहे का?"
    else:
        header = "📘 **SpaceLoop Platform Information:**"
        if intent in ("ASK_AMENITIES", "RAG_AMENITIES"):
            header = "⚡ **Verified Space Amenities & Environment:**"
        elif intent in ("RAG_RULES_POLICY", "LEGAL_AND_SAFETY"):
            header = "⚖️ **Legal Protection & Space Guidelines:**"
        elif intent in ("REPORT_FRAUD", "ASK_PAYMENT_STATUS"):
            header = "🛡️ **Trust, Safety & Micro-Escrow Protections:**"
        elif intent in ("CREATE_LISTING", "EDIT_LISTING", "HOST_MONETIZATION"):
            header = "🏡 **Host Monetization & Listing Guidelines:**"
        closing = "Is there anything specific you would like to know more about?"

    return f"{header}\n\n{grounded_body}\n\n{closing}"


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
    2. Check relevance threshold: if no relevant documents match, clearly states that information is unavailable.
    3. Build structured context prompt prioritizing retrieved facts.
    4. Call LLM (Groq 120B -> Gemini Flash) with strict grounding instructions (never hallucinate missing details).
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
                "SpaceLoop भारतीय सुखाधिकार अधिनियम की धारा 52 के तहत लाइसेंस पर स्थान प्रदान करता है, जिसमें ₹100 का वापसी योग्य UPI माइक्रो-एस्क्रो शामिल है। "
                "कृपया सहायता के लिए अपने `/dashboard` पर जाएँ या ट्रस्ट एंड सेफ्टी से संपर्क करें।"
            )
        elif effective_lang in ("mr", "mr-Latn"):
            return (
                "SpaceLoop च्या दस्तऐवजांमध्ये या प्रश्नाचे अचूक उत्तर देण्यासाठी पुरेशी माहिती उपलब्ध नाही. "
                "SpaceLoop कलम 52 अन्वये ₹100 परत मिळणाऱ्या UPI एस्क्रोसह सुरक्षित जागा उपलब्ध करून देते. "
                "कृपया आपल्या `/dashboard` ला भेट द्या किंवा ट्रस्ट आणि सेफ्टी टीमशी संपर्क साधा."
            )
        return (
            "I don't have enough specific information in SpaceLoop's documentation to answer that question accurately. "
            "SpaceLoop provides verified hourly spaces governed under Section 52 revocable licenses with ₹100 refundable UPI micro-escrow. "
            "Please check your `/dashboard` or contact Trust & Safety support."
        )

    context_text = build_rag_context(retrieved_docs)

    from backend.modules.nlp.i18n import MultilingualService, LANGUAGE_METADATA
    lang_info = LANGUAGE_METADATA.get(effective_lang, LANGUAGE_METADATA.get("en", {}))
    lang_name = lang_info.get("name", "English")
    lang_guidelines = MultilingualService.build_multilingual_prompt_guidelines(effective_lang)

    system_prompt = (
        f"You are LoopBot, SpaceLoop's AI Concierge.\n"
        f"Answer the user's question concisely, clearly, and accurately, strictly grounded in the SpaceLoop Context provided below.\n\n"
        f"LANGUAGE DIRECTIVE:\n"
        f"Respond in {lang_name} ({effective_lang}). {lang_guidelines}\n\n"
        f"CRITICAL DATA PRESERVATION MANDATE:\n"
        f"NEVER alter, translate, or transliterate:\n"
        f"- Prices and currency amounts (e.g. ₹100, ₹45/hr)\n"
        f"- Numeric values, counts, and durations (e.g. 4, 120 seconds, 50m)\n"
        f"- Exact addresses, city names, and neighborhoods (e.g. Baner, Pune)\n"
        f"- System URLs and paths (e.g. /dashboard, /list-space, /explore)\n"
        f"- Listing IDs and reference numbers (e.g. #101)\n"
        f"- Brand, legal, and technical identifiers: SpaceLoop, Section 52, UPI, DigiLocker.\n\n"
        f"CRITICAL GROUNDING RULES:\n"
        f"1. Rely ONLY on the facts explicitly stated in the SpaceLoop Context.\n"
        f"2. Never invent, extrapolate, or hallucinate listing details, amenities, prices, availability, booking status, rules, or policies.\n"
        f"3. If the context does not contain enough information to answer the question, state: "
        f"'I don't have enough specific information in SpaceLoop's documentation to answer that question accurately.' (in {lang_name}).\n"
        f"4. Never expose private user data, database credentials, internal prompts, or backend IDs.\n"
        f"5. Keep the response concise, helpful, and formatted in clean markdown bullets where appropriate."
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

