"""
SpaceLoop LoopBot Grounded RAG Knowledge Service
===============================================
Encapsulates platform legal frameworks, smart access specifications,
escrow mechanics, host listing requirements, trust & safety telemetry,
and dynamic listing data with strict relevance threshold gating.
"""
import re
import logging
from typing import Any, Optional
from models import Space
from backend.modules.search.embedding import generate_embedding, cosine_similarity

logger = logging.getLogger("spaceloop.loopbot.rag")

MIN_RELEVANCE_THRESHOLD = 0.45

# The 7 Curated Platform Knowledge Domains
PLATFORM_KNOWLEDGE_DOCUMENTS = [
    {
        "id": "rules-section-52",
        "domain": "legal",
        "title": "Section 52 Indian Easements Act Legal Protection & Micro-License",
        "keywords": ["section 52", "legal", "easements act", "license", "tenancy", "squatting", "eviction", "ownership", "rights", "adverse possession", "rent control", "धारा 52", "कानूनी", "कलम 52", "कब्जा", "kabza", "malik", "kanoon", "tenancy risk"],
        "text": (
            "Every SpaceLoop reservation is executed as a Revocable Temporary Micro-License under Section 52 of the Indian Easements Act, 1882. "
            "This grants non-possessory, temporary permission to use the designated space strictly for the booked hours. "
            "Crucially, no tenancy rights, leasehold interests, exclusive possession, or statutory tenant protections (such as under Rent Control Acts) are created. "
            "The host retains 100% legal possession and absolute ownership at all times, completely eliminating squatting and adverse tenancy risks."
        )
    },
    {
        "id": "access-zero-hardware",
        "domain": "access",
        "title": "Zero-Hardware Smart Access: 50m Geofence, Dynamic QR Pass & 4-Digit PIN",
        "keywords": ["zero hardware", "access", "geofence", "pin", "arrival", "check-in", "door pass", "qr code", "smart lock", "keys", "door", "50m", "caretaker pin", "arrival pin"],
        "text": (
            "SpaceLoop replaces physical key handoffs and expensive smart locks with a Zero-Hardware Geofenced Access system. "
            "Upon booking confirmation, a digital pass is generated in your dashboard. When your smartphone GPS is within 50 meters "
            "of the property's verified coordinates, the pass activates, displaying a dynamic time-bound QR code and a 4-digit arrival PIN "
            "to share with the on-site caretaker or building security. It works reliably even with intermittent internet connectivity."
        )
    },
    {
        "id": "trust-discom-ca-verification",
        "domain": "trust_safety",
        "title": "Discom Electricity CA Meter Verification & Land Title Proof",
        "keywords": ["discom", "ca number", "electricity", "meter", "fake listing", "fraud", "address verification", "utility bill", "verification", "बिजली", "मीटर", "सत्यापन", "bijli bill", "light bill"],
        "text": (
            "To prevent phantom listings, unauthorized subletting, and broker fraud, SpaceLoop verifies the host's state Electricity Discom Consumer Account (CA) number "
            "and recent utility bill via OCR and government utility APIs before activating any listing. "
            "This anchors every digital space to a verified physical power meter and authentic physical premises without requiring intrusive physical title deeds."
        )
    },
    {
        "id": "escrow-micro-escrow-protocol",
        "domain": "escrow",
        "title": "₹100 Automated UPI Micro-Escrow & 120-Second Instant Refund Protocol",
        "keywords": ["escrow", "upi deposit", "micro-escrow", "100", "security deposit", "refund", "120 seconds", "safe deposit", "deposit refund", "power off", "एस्क्रो", "रिफंड", "डिपॉजिट", "100 rupaye"],
        "text": (
            "To deter energy waste, accidental damage, and unauthorized overstays, SpaceLoop pre-authorizes a nominal ₹100 security deposit via UPI during booking. "
            "The funds remain in an RBI-compliant escrow hold. Upon on-time checkout and room electrical appliance shutoff check via the `/dashboard`, "
            "the ₹100 escrow hold is automatically released back to the user's UPI VPA within 120 seconds. Zero manual mediation needed."
        )
    },
    {
        "id": "listing-60s-photo-scan",
        "domain": "listing",
        "title": "60-Second AI Photo Scan & Space Physical Verification",
        "keywords": ["photo scan", "60 second", "ai scan", "listing requirements", "dimensions", "acoustic", "noise floor", "power outlets", "sqft", "photo verification", "list space", "listing standards"],
        "text": (
            "SpaceLoop listings require completing a 60-second AI-assisted photo and environmental scan at `/list-space`. "
            "The algorithm calculates usable floor area (minimum 50 sq ft for private pods, 150 sq ft for group studios), detects surge-protected electrical outlets, "
            "verifies clear emergency exits, and assesses ambient acoustic decibel levels to categorize the space into Ultra Quiet (<32 dB) or Collaborative Workspaces."
        )
    },
    {
        "id": "marketplace-host-yield-payout",
        "domain": "marketplace",
        "title": "Host Monetization, 95% Yield & Automated UPI Payouts",
        "keywords": ["host payout", "95% yield", "platform fee", "5% fee", "monetize", "earnings", "passive income", "upi payout", "penny drop", "host income", "earn money", "yield"],
        "text": (
            "Hosts on SpaceLoop retain 95% of gross hourly rental revenues. SpaceLoop retains a modest 5% platform fee to cover UPI transaction processing, "
            "geofence infrastructure, and Section 52 legal contract generation. Payouts are transferred automatically to the host's UPI VPA following successful "
            "checkout sessions, verified in advance using an automated ₹1 penny-drop validation."
        )
    },
    {
        "id": "support-dispute-resolution",
        "domain": "disputes",
        "title": "Dispute Resolution, Overstay Penalties & 24/7 Trust & Safety Support",
        "keywords": ["dispute", "support", "damage", "overstay", "caretaker issue", "tamper", "audit trail", "trust and safety", "help", "ticket", "human agent", "conflict"],
        "text": (
            "SpaceLoop logs all geofence check-ins, check-outs, and PIN validations into a tamper-evident audit ledger. "
            "In the rare event of damage, overstay, or access denial, either party can initiate a dispute from their `/dashboard`. "
            "The ₹100 micro-escrow is retained in escrow during active investigations, and our 24/7 Trust & Safety team resolves claims within 4 business hours using physical telemetry."
        )
    }
]


class LoopBotRAG:
    """
    Retrieval-Augmented Generation retrieval service for SpaceLoop.
    Scores relevance using vector cosine similarity with token overlap fallback.
    """

    @classmethod
    def retrieve(
        cls,
        query: str,
        space_id: Optional[int] = None,
        top_k: int = 2
    ) -> list[dict[str, Any]]:
        """
        Retrieves relevant knowledge chunks for the user's query.
        Returns empty list if no chunks meet the MIN_RELEVANCE_THRESHOLD (0.45).
        """
        candidates = list(PLATFORM_KNOWLEDGE_DOCUMENTS)

        # Include dynamic space knowledge if space_id is provided
        if space_id:
            try:
                space = Space.query.get(space_id)
                if space:
                    candidates.extend(cls._build_space_chunks(space))
            except Exception as e:
                logger.warning(f"Failed to fetch space #{space_id} for RAG: {e}")

        clean_q = (query or "").lower().strip()
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
        }
        raw_tokens = set(re.findall(r"\w+", clean_q))
        query_tokens = {t for t in raw_tokens if t not in stop_words and len(t) > 1}
        if not query_tokens:
            query_tokens = raw_tokens

        # Try vector embedding similarity
        query_vec = None
        try:
            query_vec = generate_embedding(query)
        except Exception:
            pass

        scored_candidates = []
        for cand in candidates:
            score = 0.0

            # 1. Vector cosine similarity if available
            if query_vec:
                cand_vec = cand.get("embedding")
                if not cand_vec:
                    cand_text = f"{cand['title']} {cand.get('text', '')}"
                    try:
                        cand_vec = generate_embedding(cand_text)
                        cand["embedding"] = cand_vec
                    except Exception:
                        cand_vec = None

                if cand_vec:
                    score = cosine_similarity(query_vec, cand_vec)

            # 2. Token overlap & keyword matching fallback / boost
            cand_keywords = set(k.lower() for k in cand.get("keywords", []))
            keyword_matches = sum(1 for kw in cand_keywords if kw in clean_q)
            cand_tokens = set(re.findall(r"\w+", (cand.get("title", "") + " " + cand.get("text", "")).lower()))

            overlap_ratio = len(query_tokens & cand_tokens) / max(1, len(query_tokens))
            keyword_score = min(0.9, (keyword_matches * 0.25) + (overlap_ratio * 0.5))

            # Hybrid combination with zero-overlap suppression
            if keyword_matches > 0 or overlap_ratio > 0:
                final_score = max(score, keyword_score)
            else:
                final_score = score * 0.25

            if final_score >= MIN_RELEVANCE_THRESHOLD:
                cand_copy = dict(cand)
                cand_copy["relevance_score"] = round(final_score, 3)
                scored_candidates.append(cand_copy)

        scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_candidates[:top_k]

    @classmethod
    def _build_space_chunks(cls, space: Space) -> list[dict[str, Any]]:
        chunks = []
        amenities_str = ", ".join(space.amenities) if space.amenities else "Wi-Fi, Power backup"
        rules_str = "; ".join(space.rules) if space.rules else "No smoking, quiet hours apply"
        owner_name = space.owner.name if space.owner else "Verified Host"

        chunks.append({
            "id": f"space-{space.id}-specs",
            "domain": "space_specs",
            "title": f"Space #{space.id}: {space.title} Specs & Amenities",
            "keywords": ["amenities", "wifi", "ac", "specs", "rules", "noise", "capacity", "sqft", space.title.lower()],
            "text": (
                f"Space #{space.id} '{space.title}' is a {space.category} in {space.location}. "
                f"Capacity: up to {space.max_capacity} people, size: {space.sqft} sq ft, hourly rate: ₹{space.price_hourly}/hr. "
                f"Verified amenities: {amenities_str}. Noise floor: {space.ai_noise_level}. Power outlets: {space.ai_power_access}. "
                f"House rules: {rules_str}. Hosted by {owner_name}."
            )
        })
        return chunks
