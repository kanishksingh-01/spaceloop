"""
SpaceLoop Intent Extraction Service
Identifies conversational and transactional marketplace intents across 6 Indian languages,
regional Pahari dialects, and Romanized code-mixing.
Enforces a low-confidence guardrail returning CLARIFICATION_NEEDED rather than hallucinating intents.
"""
import re
from typing import Tuple, Dict, Any, Optional
from backend.modules.nlp.schemas import IntentType


# -----------------------------------------------------------------------------
# MULTILINGUAL INTENT PATTERNS (English, Hindi, Marathi, Garhwali, Kumaoni, Jaunsari)
# -----------------------------------------------------------------------------

GREETING_PATTERNS = [
    # English
    r"\b(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening))\b",
    # Hindi / Hinglish
    r"\b(?:नमस्ते|नमस्कार|प्रणाम|राम\s*राम|namaste|pranam|ram\s*ram|kaise\s+ho|kese\s+ho)\b",
    # Marathi
    r"\b(?:नमस्कार|कसे\s+आहात|कसा\s+आहेस|namaskar|kasa\s+aahat|kashi\s+aahat)\b",
    # Garhwali / Kumaoni / Jaunsari
    r"\b(?:भला\s+छौ|कन\s+छौ|कसिक\s+छौ|भैजी|दाज्यु|दगड्या|bhal\s+chho|kasa\s+chho|dagadya)\b"
]

BOOKING_PATTERNS = [
    # English
    r"\b(?:book\s+(?:this|a)?\s*(?:space|room|desk)|reserve\s+(?:now|this)|how\s+to\s+book|make\s+a\s+reservation|checkout\s+link|direct\s+booking)\b",
    # Hindi / Hinglish
    r"\b(?:book\s+karna\s+hai|reserve\s+karna\s+hai|booking\s+kaise\s+kare(?:in)?|booking\s+karo|booking\s+link\s+chahiye|ye\s+space\s+book\s+karo)\b",
    # Marathi
    r"\b(?:book\s+karaycha\s+aahe|aarakshan\s+kara|booking\s+kashi\s+karaychi|aarakshit\s+kara)\b",
    # Pahari
    r"\b(?:book\s+karno\s+chho|kamro\s+book\s+kara|basa\s+book\s+karno)\b"
]

COMPARE_PATTERNS = [
    # English
    r"\b(?:compare\s+(?:these|spaces?|#|\w+)|compare\b|difference\s+between|which\s+(?:one\s+is\s+)?better|side\s+by\s+side\s+comparison)\b",
    # Hindi / Hinglish
    r"\b(?:dono\s+me\s+kya\s+(?:farak|antar)\s+hai|compare\s+karo|kaunsa\s+(?:behtar|achha)\s+hai)\b",
    # Marathi
    r"\b(?:doghanmadhe\s+kay\s+pharak\s+aahe|tulna\s+kara|konti\s+jaga\s+chhan\s+aahe)\b"
]

PRICING_PATTERNS = [
    # English
    r"\b(?:how\s+much\s+(?:for|does\s+it\s+cost|will\s+it\s+cost)|calculate\s+cost|what\s+is\s+the\s+price|pricing\s+for|hourly\s+rate|fee\s+for)\b",
    # Hindi / Hinglish
    r"\b(?:kitna\s+(?:lagega|kharcha|hoga|padega)|price\s+kitni\s+hai|kitne\s+rupaye\s+lagenge|kiraya\s+kitna\s+hai|rates\s+kya\s+hain|rate\s+batao)\b",
    r"\bkitna\s+(?:lagega|hoga|hai)\b",
    # Marathi
    r"\b(?:kiti\s+kharch\s+yeil|bhada\s+kiti\s+aahe|kiti\s+rupaye\s+lagtil|dar\s+kay\s+aahet)\b",
    # Pahari
    r"\b(?:kituk\s+rupya\s+lagnu|kiti\s+laglo|kiraya\s+katuk\s+chha|bhadu\s+kiti\s+chho)\b"
]

AVAILABILITY_PATTERNS = [
    # English
    r"\b(?:available\s+(?:tomorrow|today|this\s+weekend)|what(?:'s|\s+is)\s+available|open\s+slots|free\s+slots|is\s+it\s+free\s+at)\b",
    r"\b(?:is\s+it|are\s+there\s+spaces?)\s+available\b",
    # Hindi / Hinglish
    r"\b(?:kal|aaj)\s+(?:\w+\s+)?(?:available|khali|free)\s*(?:hai|milega|hoga|kya)?\b",
    r"\b(?:open|free)\s+slots\s+hain\b",
    r"\bkab\s+(?:free|khali)\s+(?:hai|milega)\b",
    # Marathi
    r"\b(?:udya|aaj)\s+(?:\w+\s+)?(?:uplabdha|rikami|rikama|rikame)\b",
    r"\bslots\s+rikame\s+aahet\b",
    # Pahari
    r"\b(?:bhol|aaj)\s+(?:\w+\s+)?(?:milal|khali)\b",
    r"\bkakh\s+khali\s+chho\b"
]

AMENITIES_PATTERNS = [
    # English
    r"\b(?:what\s+amenities|amenities\s+does\s+this|is\s+there\s+wifi|has\s+air\s+conditioning|have\s+ac|power\s+backup|presentation\s+screen|whiteboard|parking\s+available)\b",
    # Hindi / Hinglish
    r"\b(?:wifi\s+(?:milega|hai)|ac\s+hai\s+kya|power\s+backup\s+hai|screen\s+milegi|kya\s+suvidhayein\s+hain|amenities\s+kya\s+hain)\b",
    # Marathi
    r"\b(?:wifi\s+aahe\s+ka|ac\s+uplabdha\s+aahe\s+ka|kay\s+suvidha\s+aahet|parking\s+aahe\s+ka)\b",
    # Pahari
    r"\b(?:suvidha\s+kya\s+chhan|wifi\s+chho\s+ki\s+na|bijli\s+chhan\s+ki\s+na)\b"
]

RULES_PATTERNS = [
    # English
    r"\b(?:bring\s+food|food\s+allowed|can\s+i\s+eat|smoking\s+policy|house\s+rules|pets\s+allowed|cancellation\s+policy|guest\s+policy)\b",
    # Hindi / Hinglish
    r"\b(?:khana\s+la\s+sakte\s+hain|food\s+allowed\s+hai|smoking\s+kar\s+sakte\s+hain|house\s+rules\s+kya\s+hain|cancellation\s+rules)\b",
    # Marathi
    r"\b(?:jevan\s+aanta\s+yeil\s+ka|niyam\s+kay\s+aahet|dhumrapan\s+chalel\s+ka|shashan\s+kay\s+aahe)\b",
    # Pahari
    r"\b(?:khano\s+la\s+sakan\s+ki\s+na|niyam\s+kya\s+chhan)\b"
]

HOST_MONETIZE_PATTERNS = [
    # English
    r"\b(?:how\s+to\s+(?:host|monetize|rent\s+out)|monetiz\w*|list\s+my\s+(?:space|room|garage|office|property)|earn\s+money|earnings\s+calculator|host\s+calculator)\b",
    # Hindi / Hinglish
    r"\b(?:apni\s+jagah\s+rent\s+pe\s+kaise\s+du|garage\s+se\s+kamai|space\s+list\s+karna\s+hai|host\s+kaise\s+banein|kitna\s+kama\s+sakte\s+hain|kamai\s+kaise\s+kare)\b",
    # Marathi
    r"\b(?:maza\s+garage\s+bhadyane\s+kasa\s+deu|paisa\s+kasa\s+kamvaycha|space\s+list\s+karaychi\s+aahe|host\s+kasa\s+honar)\b",
    # Pahari
    r"\b(?:ghaur\s+kiraye\s+ma\s+kankari\s+diyun|kamro\s+kiraya\s+ma\s+deno\s+chho)\b"
]

LEGAL_SAFETY_PATTERNS = [
    # English
    r"\b(?:section\s+52|easements\s+act|tenancy\s+protection|squatting|upi\s+escrow|refundable\s+deposit|geofence\s+pass|digital\s+pass)\b",
    # Hindi / Hinglish
    r"\b(?:section\s+52\s+kya\s+hai|tenancy\s+ka\s+(?:lafda|risk)|deposit\s+kaise\s+wapas\s+hoga|kabza\s+to\s+nahi\s+karega)\b",
    # Marathi
    r"\b(?:section\s+52\s+kay\s+aahe|kabja\s+tar\s+honar\s+nahi\s+na|deposit\s+parat\s+kase\s+milnar)\b"
]

SEARCH_SPACE_PATTERNS = [
    # English
    r"\b(?:find|search|looking\s+for|need)\s+(?:a\s+|an\s+)?(?:\w+\s+)?(?:space|spaces|room|rooms|desk|desks|studio|studios|workspace|workspaces|office|offices|hall|halls)\b",
    r"\b(?:spaces?|rooms?|desks?|studios?)\s+for\b",
    # Hindi / Hinglish
    r"\b(?:kamra|kamre|desk|meeting\s+room|office|jagah|studio|hall)\s+(?:chahiye|khojo|dhoondo|dedo|milega|dikhao|dakhva)\b",
    r"\b(?:kamra|kamre|jagah|desk)\s+(?:dhoond|khoj)\b",
    # Marathi
    r"\b(?:kholi|kholya|desk|jaga|office)\s+(?:pahije|shodha|dakhva|havay|havi|hava)\b",
    # Pahari
    r"\b(?:kamro|basa|jaga)\s+(?:chyan|chho|chha)\b",
    r"\b(?:kakh|ketha)\s+(?:jaga|kamro|basa)\s+milal\b",
    r"\bpadhai\s+khatir\s+jaga\s+chyan\b"
]


class IntentService:
    """
    Deterministic multilingual intent classifier with strict confidence scoring.
    """

    INTENT_MAP = [
        (IntentType.BOOK_SPACE.value, BOOKING_PATTERNS, 0.96),
        (IntentType.COMPARE_SPACES.value, COMPARE_PATTERNS, 0.94),
        (IntentType.GET_PRICING.value, PRICING_PATTERNS, 0.95),
        (IntentType.CHECK_AVAILABILITY.value, AVAILABILITY_PATTERNS, 0.94),
        (IntentType.INQUIRE_AMENITIES.value, AMENITIES_PATTERNS, 0.93),
        (IntentType.INQUIRE_RULES.value, RULES_PATTERNS, 0.93),
        (IntentType.HOST_MONETIZE.value, HOST_MONETIZE_PATTERNS, 0.95),
        (IntentType.LEGAL_SAFETY.value, LEGAL_SAFETY_PATTERNS, 0.92),
        (IntentType.SEARCH_SPACE.value, SEARCH_SPACE_PATTERNS, 0.94),
        (IntentType.GENERAL_GREETING.value, GREETING_PATTERNS, 0.92),
    ]

    @classmethod
    def extract_intent(cls, normalized_text: str, context_data: Optional[Dict[str, Any]] = None) -> Tuple[str, float]:
        """
        Extracts intent and confidence from normalized text.
        Guarantees: If query does not match known patterns or confidence is below 0.60,
        returns (CLARIFICATION_NEEDED, 0.50).
        """
        if not normalized_text or len(normalized_text.strip()) < 2:
            return IntentType.CLARIFICATION_NEEDED.value, 0.10

        clean = normalized_text.lower().strip()

        # 1. Match against deterministic multilingual pattern groups
        for intent_name, patterns, base_conf in cls.INTENT_MAP:
            for pattern in patterns:
                if re.search(pattern, clean, flags=re.IGNORECASE):
                    return intent_name, base_conf

        # 2. Check standalone single greetings
        if clean in ("hi", "hello", "hey", "hola", "namaste", "pranam", "namaskar", "ram ram"):
            return IntentType.GENERAL_GREETING.value, 0.95

        # 3. Keyword co-occurrence heuristic for search (e.g. mentions of location + capacity or price)
        has_search_indicators = any(k in clean for k in ["for", "near", "under", "₹", "seats", "pax", "people", "hours", "hr"])
        has_space_types = any(k in clean for k in ["desk", "office", "studio", "meeting", "workshop", "retail", "hall", "study"])
        if has_search_indicators and has_space_types:
            return IntentType.SEARCH_SPACE.value, 0.82

        # 4. Low-confidence fallback guardrail: Do NOT invent an intent
        return IntentType.CLARIFICATION_NEEDED.value, 0.50
