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
    r"\b(?:book\s+(?:this|a|listing)?\s*(?:space|room|desk|listing|\w+)|reserve\s+(?:now|this)|how\s+to\s+book|make\s+a\s+reservation|checkout\s+link|direct\s+booking)\b",
    # Hindi / Hinglish
    r"\b(?:book\s+karna\s+hai|reserve\s+karna\s+hai|booking\s+kaise\s+kare(?:in)?|booking\s+karo|booking\s+link\s+chahiye|ye\s+space\s+book\s+karo)\b",
    r"(?:बुक\s+करना\s+है|आरक्षण\s+करना)",
    # Marathi
    r"\b(?:book\s+karaycha\s+aahe|aarakshan\s+kara|booking\s+kashi\s+karaychi|aarakshit\s+kara)\b",
    r"बुक\s+करायचं\s+आहे",
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
    r"(?:कितना\s+(?:लगेगा|खर्चा|होगा|पड़ेगा)|किराया\s+कितना\s+है)",
    # Marathi
    r"\b(?:kiti\s+kharch\s+yeil|bhada\s+kiti\s+aahe|kiti\s+rupaye\s+lagtil|dar\s+kay\s+aahet)\b",
    r"(?:भाडं\s+किती\s+आहे|किती\s+खर्च\s+येईल)",
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
    r"(?:खाली|उपलब्ध)\s+(?:है|मिलेगा)",
    # Marathi
    r"\b(?:udya|aaj)\s+(?:\w+\s+)?(?:uplabdha|rikami|rikama|rikame)\b",
    r"\bslots\s+rikame\s+aahet\b",
    r"(?:उपलब्ध|रिकामी|रिकामे)\s+आहेत?",
    # Pahari
    r"\b(?:bhol|aaj)\s+(?:\w+\s+)?(?:milal|khali)\b",
    r"\bkakh\s+khali\s+chho\b"
]

AMENITIES_PATTERNS = [
    # English
    r"\b(?:what\s+amenities|amenities\s+(?:does\s+this|available)|is\s+there\s+wifi|has\s+air\s+conditioning|have\s+ac|power\s+backup|presentation\s+screen|whiteboard|parking\s+available)\b",
    r"\b(?:have|has|with|include[sd]?|is\s+there)\b.*?\b(?:wifi|wi-fi|ac|air\s+conditioning|power\s+backup|inverter|monitor|screen|whiteboard|parking)\b",
    r"\b(?:wifi|wi-fi|fiber\s+internet)\b.*?\b(?:available|speed|included)\b",
    # Hindi / Hinglish
    r"\b(?:wifi\s+(?:milega|hai)|ac\s+hai\s+kya|power\s+backup\s+hai|screen\s+milegi|kya\s+suvidhayein\s+hain|amenities\s+kya\s+hain)\b",
    r"सुविधाएं\s+क्या\s+हैं",
    # Marathi
    r"\b(?:wifi\s+aahe\s+ka|ac\s+uplabdha\s+aahe\s+ka|kay\s+suvidha\s+aahet|parking\s+aahe\s+ka)\b",
    r"काय\s+सुविधा\s+आहेत",
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
    r"\b(?:how\s+to\s+(?:host|monetize|rent\s+out)|monetiz\w*|list\s+(?:my\s+)?(?:\w+\s+)?(?:space|room|garage|office|property|terrace|hall|land|rooftop)|earn\s+(?:money|passive\s+income|income)|earnings\s+calculator|host\s+calculator)\b",
    r"\b(?:(?:i\s+)?(?:want\s+to\s+)?(?:list|create\s+listing|add\s+listing|draft\s+listing|put\s+on\s+rent|rent\s+out)(?:\s+(?:a|an|my))?.*?(?:space|room|flat|apartment|bhk|garage|office|property|terrace|hall|studio|desk))\b",
    # Hindi / Hinglish
    r"\b(?:apni\s+jagah\s+rent\s+pe\s+kaise\s+du|garage\s+se\s+kamai|space\s+list\s+karna\s+hai|host\s+kaise\s+banein|kitna\s+kama\s+sakte\s+hain|kamai\s+kaise\s+kare)\b",
    r"\b(?:\w+\s+)?(?:list\s+karna\s+hai|listing\s+banani\s+hai|rent\s+pe\s+dena\s+hai)\b",
    r"(?:जगह\s+लिस्ट\s+करना|किराये\s+पर\s+देना|लिस्टिंग\s+बना|कमरा\s+किराये)",
    # Marathi
    r"\b(?:maza\s+garage\s+bhadyane\s+kasa\s+deu|paisa\s+kasa\s+kamvaycha|space\s+list\s+karaychi\s+aahe|host\s+kasa\s+honar)\b",
    r"\b(?:\w+\s+)?(?:list\s+karaych[ei]\s+aahe|bhadyane\s+d[ey]aych[aei]\s+aahe)\b",
    r"(?:भाड्याने\s+द्यायची\s+आहे|जागा\s+लिस्ट\s+करायची)",
    # Pahari
    r"\b(?:ghaur\s+kiraye\s+ma\s+kankari\s+diyun|kamro\s+kiraya\s+ma\s+deno\s+chho)\b"
]

LEGAL_SAFETY_PATTERNS = [
    # English
    r"\b(?:section\s+52|easements\s+act|tenancy\s+protection|squatting|upi\s+escrow|refundable\s+deposit|geofence\s+pass|digital\s+pass|security\s+deposit|deposit\s+hold|get\s+refunded|when\s+will.*refund|dispute|raise\s+a\s+dispute|complaint|smart\s+lock|pin\s+code|qr\s*code|unlock.*gate|check[\s-]out|end\s+(?:my\s+)?session)\b",
    # Hindi / Hinglish
    r"\b(?:section\s+52\s+kya\s+hai|tenancy\s+ka\s+(?:lafda|risk)|deposit\s+kaise\s+wapas\s+hoga|kabza\s+to\s+nahi\s+karega)\b",
    r"(?:डिपॉजिट\s+वापस|रिफंड)",
    # Marathi
    r"\b(?:section\s+52\s+kay\s+aahe|kabja\s+tar\s+honar\s+nahi\s+na|deposit\s+parat\s+kase\s+milnar)\b",
    r"डिपॉझिट\s+परत"
]

SEARCH_SPACE_PATTERNS = [
    # English
    r"\b(?:find|search|looking\s+for|need)\s+(?:a\s+|an\s+)?(?:\w+\s+)?(?:space|spaces|room|rooms|desk|desks|studio|studios|workspace|workspaces|office|offices|hall|halls)\b",
    r"\b(?:spaces?|rooms?|desks?|studios?)\s+for\b",
    # Hindi / Hinglish (Latin & Devanagari)
    r"\b(?:kamra|kamre|desk|meeting\s+room|office|jagah|studio|hall)\s+(?:chahiye|khojo|dhoondo|dedo|milega|dikhao|dakhva)\b",
    r"(?:कमरा|कमरे|खोली|खोल्या|जागा|कक्ष|कक्षा|दफ्तर|कार्यालय).*?(?:चाहिए|पाहिजे|हवी|हवा|खोजो|ढूंढो|बथों|दिखाओ|दाखवा)",
    r"\b(?:kamra|kamre|jagah|desk)\s+(?:dhoond|khoj)\b",
    # Marathi
    r"\b(?:kholi|kholya|desk|jaga|office)\s+(?:pahije|shodha|dakhva|havay|havi|hava)\b",
    # Pahari
    r"\b(?:kamro|basa|jaga)\s+(?:chyan|chho|chha)\b",
    r"\b(?:kakh|ketha)\s+(?:jaga|kamro|basa)\s+milal\b",
    r"\bpadhai\s+khatir\s+jaga\s+chyan\b"
]

LOCATION_PATTERNS = [
    # English
    r"\b(?:where\s+is\s+(?:this|the)?\s*space|location\s+of|how\s+to\s+reach|what\s+is\s+the\s+address|neighborhood|exact\s+location|gps\s+coordinates|directions\s+to|where\s+located)\b",
    # Hindi / Hinglish
    r"\b(?:kahan\s+(?:pe\s+)?hai|address\s+kya\s+hai|kaise\s+pahunche|location\s+batao|kaha\s+hai|jagah\s+kahan\s+hai)\b",
    r"(?:कहाँ\s+है|पता\s+क्या\s+है|लोकेशन)",
    # Marathi
    r"\b(?:kuthe\s+aahe|patta\s+kay\s+aahe|kase\s+pohachayche)\b",
    r"कुठे\s+आहे",
    # Pahari
    r"\b(?:kakh\s+chho|ketha\s+chha)\b"
]

EDIT_LISTING_PATTERNS = [
    # English
    r"\b(?:edit\s+(?:my\s+)?listing|update\s+(?:my\s+)?space|change\s+(?:price|rate|photos|timing|amenities|rules)|modify\s+listing|update\s+listing)\b",
    # Hindi / Hinglish
    r"\b(?:listing\s+edit\s+karna|price\s+change\s+karna|photos\s+update\s+karna|listing\s+badalna\s+hai|details\s+update\s+karni)\b",
    # Marathi
    r"\b(?:listing\s+badlaychi\s+aahe|dar\s+badla|photos\s+badlayche)\b"
]

BOOKING_STATUS_PATTERNS = [
    # English
    r"\b(?:booking\s+status|check\s+(?:my\s+)?booking|my\s+reservation|is\s+my\s+booking\s+confirmed|door\s+pass\s+status|arrival\s+pin\s+code|check\s+status)\b",
    # Hindi / Hinglish
    r"\b(?:booking\s+(?:confirm\s+hui\s+kya|status\s+kya\s+hai|kaise\s+check\s+kare)|meri\s+booking|pass\s+mila\s+kya|pin\s+code\s+kya\s+hai)\b",
    # Marathi
    r"\b(?:booking\s+jhali\s+ka|majhi\s+booking|booking\s+status\s+dakhva)\b"
]

PAYMENT_STATUS_PATTERNS = [
    # English
    r"\b(?:payment\s+status|deposit\s+status|escrow\s+status|when\s+will.*(?:refund|deposit)|refund\s+status|100\s*(?:rs|rupees)?\s*deposit\s*refund|deposit\s+refund)\b",
    # Hindi / Hinglish
    r"\b(?:deposit\s+kab\s+aayega|refund\s+kab\s+milega|payment\s+status\s+kya\s+hai|paisa\s+wapas\s+aaya\s+kya|100\s*rupaye\s+kab\s+milenge)\b",
    # Marathi
    r"\b(?:refund\s+kadhi\s+yeil|paise\s+parat\s+ale\s+ka|payment\s+status\s+kay\s+aahe)\b"
]

REPORT_FRAUD_PATTERNS = [
    # English
    r"\b(?:report\s+fraud|report\s+(?:a\s+)?(?:scam|host|guest|violation)|suspicious\s+activity|safety\s+issue|fake\s+listing|fraud\s+report|fraudulent)\b",
    # Hindi / Hinglish
    r"\b(?:fraud\s+report\s+karna\s+hai|scam\s+hai|fraud\s+hai|dhokha\s+hua|report\s+karna\s+hai|fake\s+listing\s+hai)\b",
    # Marathi
    r"\b(?:fraud\s+aahe|takraar\s+karaychi\s+aahe|khota\s+listing)\b"
]

HELP_PATTERNS = [
    # English
    r"\b(?:help|how\s+does\s+spaceloop\s+work|what\s+is\s+spaceloop|support|contact\s+support|section\s+52\s+protection|terms\s+and\s+conditions|what\s+can\s+you\s+do)\b",
    # Hindi / Hinglish
    r"\b(?:help\s+chahiye|madad\s+chahiye|spaceloop\s+kaise\s+kam\s+karta\s+hai|support\s+se\s+baat\s+karni\s+hai|madad\s+karo)\b",
    # Marathi
    r"\b(?:madat\s+pahije|spaceloop\s+kasa\s+chalto|sahayyata)\b"
]

CANONICAL_INTENTS_MAP = {
    IntentType.SEARCH_SPACE.value: IntentType.SEARCH_PROPERTY.value,
    IntentType.SEARCH_PROPERTY.value: IntentType.SEARCH_PROPERTY.value,
    IntentType.CHECK_AVAILABILITY.value: IntentType.CHECK_AVAILABILITY.value,
    IntentType.BOOK_SPACE.value: IntentType.BOOK_PROPERTY.value,
    IntentType.BOOK_PROPERTY.value: IntentType.BOOK_PROPERTY.value,
    IntentType.GET_PRICING.value: IntentType.ASK_PRICE.value,
    IntentType.ASK_PRICE.value: IntentType.ASK_PRICE.value,
    IntentType.ASK_LOCATION.value: IntentType.ASK_LOCATION.value,
    IntentType.INQUIRE_AMENITIES.value: IntentType.ASK_AMENITIES.value,
    IntentType.ASK_AMENITIES.value: IntentType.ASK_AMENITIES.value,
    IntentType.HOST_MONETIZE.value: IntentType.CREATE_LISTING.value,
    IntentType.CREATE_LISTING.value: IntentType.CREATE_LISTING.value,
    IntentType.EDIT_LISTING.value: IntentType.EDIT_LISTING.value,
    IntentType.ASK_BOOKING_STATUS.value: IntentType.ASK_BOOKING_STATUS.value,
    IntentType.ASK_PAYMENT_STATUS.value: IntentType.ASK_PAYMENT_STATUS.value,
    IntentType.REPORT_FRAUD.value: IntentType.REPORT_FRAUD.value,
    IntentType.INQUIRE_RULES.value: IntentType.ASK_HELP.value,
    IntentType.LEGAL_SAFETY.value: IntentType.ASK_HELP.value,
    IntentType.ASK_HELP.value: IntentType.ASK_HELP.value,
    IntentType.COMPARE_SPACES.value: IntentType.SEARCH_PROPERTY.value,
    IntentType.GENERAL_GREETING.value: IntentType.GENERAL_CONVERSATION.value,
    IntentType.GENERAL_CONVERSATION.value: IntentType.GENERAL_CONVERSATION.value,
    IntentType.CLARIFICATION_NEEDED.value: IntentType.CLARIFICATION_NEEDED.value,
}


class IntentService:
    """
    Deterministic multilingual intent classifier with strict confidence scoring.
    """

    INTENT_MAP = [
        (IntentType.REPORT_FRAUD.value, REPORT_FRAUD_PATTERNS, 0.96),
        (IntentType.BOOK_SPACE.value, BOOKING_PATTERNS, 0.96),
        (IntentType.EDIT_LISTING.value, EDIT_LISTING_PATTERNS, 0.95),
        (IntentType.ASK_BOOKING_STATUS.value, BOOKING_STATUS_PATTERNS, 0.95),
        (IntentType.ASK_PAYMENT_STATUS.value, PAYMENT_STATUS_PATTERNS, 0.95),
        (IntentType.COMPARE_SPACES.value, COMPARE_PATTERNS, 0.94),
        (IntentType.GET_PRICING.value, PRICING_PATTERNS, 0.95),
        (IntentType.CHECK_AVAILABILITY.value, AVAILABILITY_PATTERNS, 0.94),
        (IntentType.ASK_LOCATION.value, LOCATION_PATTERNS, 0.94),
        (IntentType.INQUIRE_AMENITIES.value, AMENITIES_PATTERNS, 0.93),
        (IntentType.INQUIRE_RULES.value, RULES_PATTERNS, 0.93),
        (IntentType.HOST_MONETIZE.value, HOST_MONETIZE_PATTERNS, 0.95),
        (IntentType.LEGAL_SAFETY.value, LEGAL_SAFETY_PATTERNS, 0.92),
        (IntentType.ASK_HELP.value, HELP_PATTERNS, 0.92),
        (IntentType.SEARCH_SPACE.value, SEARCH_SPACE_PATTERNS, 0.94),
        (IntentType.GENERAL_GREETING.value, GREETING_PATTERNS, 0.92),
    ]

    @classmethod
    def canonicalize_intent(cls, intent_name: str) -> str:
        """
        Maps any intent variant or alias to the 13 canonical SpaceLoop intents.
        """
        return CANONICAL_INTENTS_MAP.get(intent_name, intent_name)

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
