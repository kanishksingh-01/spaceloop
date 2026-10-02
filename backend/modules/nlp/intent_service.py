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
    r"^(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening)|howdy)\b",
    r"\b(?:hi\s+there|hello\s+spaceloop|hey\s+bot|hey\s+loopbot)\b",
    # Hindi / Hinglish
    r"\b(?:नमस्ते|नमस्कार|प्रणाम|राम\s*राम|namaste|pranam|ram\s*ram|kaise\s+ho|kese\s+ho|kya\s+haal\s+hai)\b",
    # Marathi
    r"\b(?:नमस्कार|कसे\s+आहात|कसा\s+आहेस|namaskar|kasa\s+aahat|kashi\s+aahat)\b",
    # Garhwali / Kumaoni / Jaunsari
    r"\b(?:भला\s+छौ|कन\s+छौ|कसिक\s+छौ|भैजी|दाज्यु|दगड्या|bhal\s+chho|kasa\s+chho|dagadya)\b"
]

BOOKING_PATTERNS = [
    # English
    r"\b(?:book\s+(?:this|a|the|listing)?\s*(?:space|room|desk|studio|slot|\w+)?|reserve\s+(?:now|this|a\s+space)|how\s+to\s+book|make\s+a\s+reservation|checkout\s+link|direct\s+booking|proceed\s+to\s+book)\b",
    # Hindi / Hinglish
    r"\b(?:book\s+karna\s+hai|reserve\s+karna\s+hai|booking\s+kaise\s+kare(?:in)?|booking\s+karo|booking\s+link\s+chahiye|ye\s+space\s+book\s+karo)\b",
    r"(?:बुक\s+करना\s+है|आरक्षण\s+करना|बुकिंग\s+करो)",
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
    r"\b(?:how\s+much\s+(?:for|does\s+it\s+cost|will\s+it\s+cost)|calculate\s+cost|what\s+is\s+the\s+price|pricing\s+for|hourly\s+rate|fee\s+for|cost\s+breakdown)\b",
    # Hindi / Hinglish
    r"\b(?:kitna\s+(?:lagega|kharcha|hoga|padega)|price\s+kitni\s+hai|kitne\s+rupaye\s+lagenge|kiraya\s+kitna\s+hai|rates\s+kya\s+hain|rate\s+batao)\b",
    r"\bkitna\s+(?:lagega|hoga|hai)\b",
    r"(?:कितना\s+(?:लगेगा|खर्चा|होगा|पड़ेगा)|किराया\s+कितना\s+है|दर\s+क्या\s+है)",
    # Marathi
    r"\b(?:kiti\s+kharch\s+yeil|bhada\s+kiti\s+aahe|kiti\s+rupaye\s+lagtil|dar\s+kay\s+aahet)\b",
    r"(?:भाडं\s+किती\s+आहे|किती\s+खर्च\s+येईल)",
    # Pahari
    r"\b(?:kituk\s+rupya\s+lagnu|kiti\s+laglo|kiraya\s+katuk\s+chha|bhadu\s+kiti\s+chho)\b"
]

AVAILABILITY_PATTERNS = [
    # English
    r"\b(?:available\s+(?:tomorrow|today|this\s+weekend|after\s+\d+|at\s+\d+)|what(?:'s|\s+is)\s+available|open\s+slots|free\s+slots|is\s+it\s+free\s+at|show\s+places\s+available\s+after)\b",
    r"\b(?:is\s+it|are\s+there\s+spaces?)\s+available\b",
    r"\bavailable\s+after\s+\d+\b",
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

# Comprehensive rules and house policies
RULES_PATTERNS = [
    # English
    r"\b(?:bring\s+food|food\s+allowed|can\s+i\s+eat|outside\s+food|snacks\s+allowed|coffee\s+allowed|tea\s+allowed|smoking\s+policy|house\s+rules|pets?\s+allowed|pet\s+friendly|bring\s+my\s+dog|bring\s+my\s+pet|cancellation\s+policy|cancellation|cancel(?:ling)?|refund\s+policy|guest\s+policy|rules\s+for|what\s+are\s+the\s+rules|quiet\s+hours|noise\s+policy|overstay\s+policy|grace\s+period|extend\s+booking|booking\s+extension)\b",
    # Hindi / Hinglish
    r"\b(?:khana\s+la\s+sakte\s+hain|food\s+allowed\s+hai|bahar\s+ka\s+khana|smoking\s+kar\s+sakte\s+hain|house\s+rules\s+kya\s+hain|pet\s+la\s+sakte\s+hain|cancellation\s+rules|cancel\s+kaise\s+kare|extend\s+kaise\s+kare|late\s+ho\s+gaye\s+to|quiet\s+hours)\b",
    r"(?:खाना\s+ला\s+सकते|पालतू\s+जानवर|धूम्रपान|रद्द\s+करना|नियम\s+क्या\s+हैं)",
    # Marathi
    r"\b(?:jevan\s+aanta\s+yeil\s+ka|niyam\s+kay\s+aahet|dhumrapan\s+chalel\s+ka|shashan\s+kay\s+aahe|cancel\s+kasa\s+karaycha|kholit\s+jevan\s+chalel\s+ka)\b",
    r"(?:जेवण\s+आणता\s+येईल|नियम\s+काय\s+आहेत|धूम्रपान\s+चालेल)",
    # Pahari
    r"\b(?:khano\s+la\s+sakan\s+ki\s+na|niyam\s+kya\s+chhan)\b"
]

# System Design & Architecture Patterns
SYSTEM_DESIGN_PATTERNS = [
    # English
    r"\b(?:zero[\s-]hardware|geofence|50m\s+geofence|door\s+pass|arrival\s+pin|digital\s+pass|how\s+does\s+check[\s-]in\s+work|how\s+to\s+check[\s-]out|discom\s+verification|ca\s+number|power\s+meter|ai\s+photo\s+scan|ai\s+scanner|sqft\s+scan|objective\s+trust\s+index|oti\s+score|trust\s+score|student\s+discount|student\s+id|academic\s+discount|95%\s+yield|5%\s+fee|platform\s+fee|instant\s+refund|120\s+seconds|escrow\s+refund)\b",
    r"\b(?:how\s+does\s+(?:the\s+)?(?:access|pass|geofence|discom|escrow|verification|scanner|scoring)\s+work)\b",
    r"\b(?:why\s+(?:use\s+)?section\s+52|why\s+50m|why\s+discom|why\s+escrow)\b",
    # Hindi / Hinglish
    r"\b(?:zero\s+hardware\s+kya\s+hai|geofence\s+pass\s+kaise\s+kaam\s+karta\s+hai|discom\s+verification\s+kya\s+hai|electricity\s+bill\s+kyun|oti\s+score\s+kya\s+hai|student\s+discount\s+kaise\s+milega|checkout\s+kaise\s+kare|escrow\s+refund\s+kab\s+aayega|bijli\s+(?:bill|meter))\b",
    r"(?:जियोफेंस|डिजिटल\s+पास|डिस्कॉम|बिजली\s+मीटर|बिजली\s+का\s+बिल|सत्यापन|एस्क्रो\s+रिफंड|चेकआउट|विद्यार्थी\s+छूट)",
    # Marathi
    r"\b(?:geofence\s+pass\s+kasa\s+chaltoy|discom\s+padtalni\s+kashi\s+hote|checkout\s+kasa\s+karaycha|student\s+discount\s+kasa\s+milnar|vijeche\s+bill|bijli\s+bill)\b",
    r"(?:डिजिटल\s+पास|डिस्कॉम\s+पडताळणी|विजेचे\s+बिल|पडताळणी|चेकआउट)"
]

HOST_MONETIZE_PATTERNS = [
    # English
    r"\b(?:how\s+to\s+(?:host|monetize|rent\s+out)|monetiz\w*|list\s+(?:my\s+)?(?:\w+\s+)?(?:space|room|garage|office|property|terrace|hall|land|rooftop)|earn\s+(?:money|passive\s+income|income)|earnings\s+calculator|host\s+calculator|host\s+payouts?|how\s+much\s+can\s+i\s+earn)\b",
    r"\b(?:i\s+)?(?:want\s+to\s+)?(?:list|host|monetize)\s+(?:my|a|an|the|this)?\s*(?:space|property|room|flat|apartment|garage|terrace|hall|studio|desk|workspace)?\b",
    r"\b(?:\d+\s*(?:bhk|bedroom|bed\s+room))\b",
    r"\b(?:put\s+on\s+rent|rent\s+out|create\s+listing|add\s+listing|draft\s+listing)\b",
    # Hindi / Hinglish
    r"\b(?:apni\s+jagah\s+rent\s+pe\s+kaise\s+du|garage\s+se\s+kamai|space\s+list\s+karna\s+hai|host\s+kaise\s+banein|kitna\s+kama\s+sakte\s+hain|kamai\s+kaise\s+kare|payout\s+kab\s+milta\s+hai)\b",
    r"\b(?:\w+\s+)?(?:list\s+karna\s+hai|listing\s+banani\s+hai|rent\s+pe\s+dena\s+hai)\b",
    r"(?:जगह\s+लिस्ट\s+करना|किराये\s+पर\s+देना|लिस्टिंग\s+बना|कमरा\s+किराये|कमाई\s+कैसे)",
    # Marathi
    r"\b(?:maza\s+garage\s+bhadyane\s+kasa\s+deu|paisa\s+kasa\s+kamvaycha|space\s+list\s+karaychi\s+aahe|host\s+kasa\s+honar)\b",
    r"\b(?:\w+\s+)?(?:list\s+karaych[ei]\s+aahe|bhadyane\s+d[ey]aych[aei]\s+aahe)\b",
    r"(?:भाड्याने\s+द्यायची\s+आहे|जागा\s+लिस्ट\s+करायची)",
    # Pahari
    r"\b(?:ghaur\s+kiraye\s+ma\s+kankari\s+diyun|kamro\s+kiraya\s+ma\s+deno\s+chho)\b"
]

LEGAL_SAFETY_PATTERNS = [
    # English
    r"\b(?:section\s+52|easements\s+act|tenancy\s+protection|squatting|upi\s+escrow|refundable\s+deposit|security\s+deposit|deposit\s+hold|get\s+refunded|when\s+will.*refund|dispute|raise\s+a\s+dispute|complaint|legal\s+protection|adverse\s+possession|tenancy\s+rights|rent\s+control\s+act)\b",
    # Hindi / Hinglish
    r"\b(?:section\s+52\s+kya\s+hai|tenancy\s+ka\s+(?:lafda|risk)|deposit\s+kaise\s+wapas\s+hoga|kabza\s+to\s+nahi\s+karega|kanooni\s+suraksha)\b",
    r"(?:धारा\s+52|डिपॉजिट\s+वापस|रिफंड|सुरक्षा|कानूनी)",
    # Marathi
    r"\b(?:section\s+52\s+kay\s+aahe|kabja\s+tar\s+honar\s+nahi\s+na|deposit\s+parat\s+kase\s+milnar|kaydeshir\s+suraksha)\b",
    r"(?:कलम\s+५२|डिपॉझिट\s+परत|सुरक्षा)"
]

HELP_PATTERNS = [
    # English Help & Guides
    r"\b(?:what\s+is\s+spaceloop|about\s+spaceloop|tell\s+me\s+about\s+spaceloop|spaceloop\s+overview)\b",
    r"\b(?:how\s+(?:does\s+)?spaceloop\s+work|how\s+it\s+works|workflow)\b",
    r"\b(?:how\s+(?:do\s+i|to|can\s+i)\s+find(?:\s+(?:a\s+)?space)?|where\s+to\s+find(?:\s+(?:a\s+)?space)?|where\s+can\s+i\s+search)\b",
    r"\b(?:how\s+(?:do\s+i|to|can\s+i)\s+book(?:\s+(?:a\s+)?space)?|steps\s+to\s+book|booking\s+steps)\b",
    r"\b(?:what\s+information\s+is\s+required|what\s+documents|requirements)\b",
    r"^(?:help|platform\s+guide|support|what\s+can\s+you\s+do)$",
    # Multilingual / Code-mixed / Indic
    r"(?:spaceloop|स्पेस\s*लूप)\s*(?:क्या\s+है|काय\s+आहे|kya\s+hai|kay\s+aahe)",
    r"\b(?:spaceloop\s+kya\s+hai|kaise\s+kaam\s+karta\s+hai|spaceloop\s+kay\s+aahe|kasa\s+chaltoy|jaga\s+kashi\s+shodhaychi|book\s+kasa\s+karaycha)\b",
    r"(?:स्पेस\s*लूप\s+काय\s+आहे|स्पेस\s*लूप\s+क्या\s+है|कसा\s+वापरायचा|कसा\s+चालतो|स्पेस\s+कशी\s+शोधायची)"
]

# Comprehensive marketplace search queries
SEARCH_SPACE_PATTERNS = [
    # English natural phrasing
    r"\b(?:i\s+need|need|looking\s+for|look\s+for|find|search|search\s+for|any|can\s+i\s+find|show\s+me|get\s+me|want)\s+(?:a\s+|an\s+|some\s+)?.*?(?:place|space|room|desk|studio|workspace|office|hall|curb|booth|cafe|terrace|spot|somewhere)\b",
    r"\b(?:somewhere\s+to|place\s+to|space\s+to)\s+(?:work|study|record|shoot|host|meet|celebrate|park|gather|work\s+out|practice)\b",
    r"\b(?:place|space|room|desk|studio|workspace|office|hall)\s+(?:for|near|in|around|under|with)\b",
    r"\b(?:any\s+)?(?:affordable|cheap|quiet|budget|silent|sunlit)\s+(?:workspace|place|space|room|desk|studio)\b",
    r"\b(?:shoot\s+a\s+(?:short\s+)?film|birthday\s+party|podcast\s+recording|team\s+meeting|study\s+session|hackathon|collab)\b",
    r"\b(?:near\s+the\s+metro|around\s+me|near\s+[a-zA-Z]+)\b",
    # Hindi / Hinglish (Latin & Devanagari)
    r"\b(?:kamra|kamre|desk|meeting\s+room|office|jagah|studio|hall|workspace)\s+(?:chahiye|khojo|dhoondo|dedo|milega|dikhao|dakhva)\b",
    r"(?:कमरा|कमरे|खोली|खोल्या|जागा|कक्ष|कक्षा|दफ्तर|कार्यालय|वर्कस्पेस|स्टूडियो).*?(?:चाहिए|पाहिजे|हवी|हवा|खोजो|ढूंढो|बथों|दिखाओ|दाखवा|मिलेगा)",
    r"\b(?:kamra|kamre|jagah|desk|workspace)\s+(?:dhoond|khoj|chahiye)\b",
    r"\b(?:mujhe|humein|mere\s+ko)\s+.*?(?:chahiye|milega)\b",
    # Marathi
    r"\b(?:kholi|kholya|desk|jaga|office|workspace)\s+(?:pahije|shodha|dakhva|havay|havi|hava)\b",
    r"\b(?:mala|amhala)\s+.*?(?:pahije|hava|havi)\b",
    # Pahari
    r"\b(?:kamro|basa|jaga)\s+(?:chyan|chho|chha)\b",
    r"\b(?:kakh|ketha)\s+(?:jaga|kamro|basa)\s+milal\b",
    r"\bpadhai\s+khatir\s+jaga\s+chyan\b"
]


class IntentService:
    """
    Multilingual Intent Extraction Service with confidence grading and low-confidence guardrail.
    """

    @classmethod
    def extract_intent(cls, text: str, context_data: Optional[Dict[str, Any]] = None) -> Tuple[str, float]:
        """
        Determines the primary user intent and returns (intent_name, confidence).
        Returns CLARIFICATION_NEEDED when confidence is below threshold.
        """
        if not text or not text.strip():
            return IntentType.CLARIFICATION_NEEDED.value, 0.0

        clean = text.lower().strip()

        # Check for explicit out-of-scope queries (strictly non-SpaceLoop topics)
        out_of_scope = any(re.search(rf"\b{w}\b", clean) for w in [
            "weather", "forecast", "rain", "climate",
            "bitcoin", "crypto", "cryptocurrency", "ethereum", "stock", "stocks",
            "cooking", "recipe", "cricket", "ipl", "football",
            "election", "medicine", "disease"
        ])
        if out_of_scope:
            return IntentType.CLARIFICATION_NEEDED.value, 0.20

        # 0. Help / Platform Guide (High Priority)
        for pat in HELP_PATTERNS:
            if re.search(pat, clean):
                return IntentType.ASK_HELP.value, 0.96

        # 1. System Design & Architectural Inquiries
        for pat in SYSTEM_DESIGN_PATTERNS:
            if re.search(pat, clean):
                if any(k in clean for k in ["section 52", "legal", "easements", "tenancy", "escrow", "refund"]):
                    return IntentType.LEGAL_SAFETY.value, 0.95
                return IntentType.ASK_HELP.value, 0.95

        # 2. Host Monetization / Create Listing Intent
        for pat in HOST_MONETIZE_PATTERNS:
            if re.search(pat, clean):
                return IntentType.CREATE_LISTING.value, 0.95

        # 3. Rules & Policies Query Intent
        for pat in RULES_PATTERNS:
            if re.search(pat, clean):
                return IntentType.ASK_RULES.value, 0.94

        # 4. Amenities Query Intent (only if not an active marketplace search with pricing/room constraints)
        for pat in AMENITIES_PATTERNS:
            if re.search(pat, clean):
                if any(p in clean for p in ["under", "below", "max", "₹", "/hr", "per hour", "need", "find", "show me", "khojo"]):
                    return IntentType.SEARCH_SPACE.value, 0.90
                return IntentType.ASK_AMENITIES.value, 0.92

        # 5. Legal & Platform Safety / Escrow
        for pat in LEGAL_SAFETY_PATTERNS:
            if re.search(pat, clean):
                return IntentType.LEGAL_SAFETY.value, 0.93

        # 6. Booking Action Intent
        for pat in BOOKING_PATTERNS:
            if re.search(pat, clean):
                return IntentType.BOOK_SPACE.value, 0.94

        # 6. Host Monetization / Create Listing Intent
        for pat in HOST_MONETIZE_PATTERNS:
            if re.search(pat, clean):
                return IntentType.CREATE_LISTING.value, 0.93

        # 7. Compare Spaces Intent
        for pat in COMPARE_PATTERNS:
            if re.search(pat, clean):
                return IntentType.COMPARE_SPACES.value, 0.91

        # 8. Pricing / Cost Estimation Intent
        for pat in PRICING_PATTERNS:
            if re.search(pat, clean):
                return IntentType.ASK_PRICE.value, 0.92

        # 9. Availability Query Intent
        for pat in AVAILABILITY_PATTERNS:
            if re.search(pat, clean):
                return IntentType.CHECK_AVAILABILITY.value, 0.90

        # 10. General Greeting
        for pat in GREETING_PATTERNS:
            if re.search(pat, clean):
                # If greeting contains subsequent space search words, fall through to search
                if not any(k in clean for k in ["need", "looking", "want", "space", "room", "desk", "find", "chahiye", "pahije"]):
                    return IntentType.GENERAL_GREETING.value, 0.95

        # 11. Marketplace Search Intent
        for pat in SEARCH_SPACE_PATTERNS:
            if re.search(pat, clean):
                return IntentType.SEARCH_SPACE.value, 0.89

        # 12. Question/Inquiry Semantic Fallback (Route to RAG ASK_HELP rather than CLARIFICATION_NEEDED)
        question_markers = ["how", "what", "why", "where", "can", "is", "are", "will", "kya", "kaise", "kyun", "kasa", "kay", "kiti", "kuthe", "kakh", "kile"]
        has_question_marker = any(re.search(rf"\b{q}\b", clean) for q in question_markers)
        domain_markers = ["space", "spaceloop", "room", "desk", "host", "guest", "pass", "door", "lock", "wifi", "deposit", "escrow", "refund", "discom", "bill", "scanner", "camera", "food", "eat", "pet", "smoke", "hours", "rate", "cost", "chahiye", "pahije", "allowed", "rules"]
        has_domain_marker = any(d in clean for d in domain_markers)

        if has_question_marker and has_domain_marker:
            return IntentType.ASK_HELP.value, 0.88

        # Fallback heuristic: Check if text contains space/activity keywords
        space_signals = [
            "space", "room", "desk", "studio", "hall", "office", "workspace",
            "film", "recording", "podcast", "study", "meeting", "party", "collab",
            "people", "persons", "hours", "₹", "rs", "kharadi", "delhi", "pune",
            "mumbai", "bengaluru", "dehradun", "metro", "near", "quiet", "cheap",
            "chahiye", "pahije", "khojo", "dhoondo", "kamra", "jaga", "kholi"
        ]
        matched_signals = sum(1 for s in space_signals if s in clean)
        if matched_signals >= 2:
            return IntentType.SEARCH_SPACE.value, 0.78
        elif matched_signals == 1:
            return IntentType.SEARCH_SPACE.value, 0.65

        return IntentType.CLARIFICATION_NEEDED.value, 0.40

    @classmethod
    def canonicalize_intent(cls, intent_str: str) -> str:
        """Translates legacy and alias intent names to canonical IntentType values."""
        if not intent_str:
            return IntentType.CLARIFICATION_NEEDED.value
        mapping = {
            "SEARCH_PROPERTY": IntentType.SEARCH_SPACE.value,
            "SEARCH_SPACE": IntentType.SEARCH_SPACE.value,
            "MARKETPLACE_SEARCH": IntentType.SEARCH_SPACE.value,
            "BOOK_PROPERTY": IntentType.BOOK_SPACE.value,
            "BOOK_SPACE": IntentType.BOOK_SPACE.value,
            "BOOKING_ACTION": IntentType.BOOK_SPACE.value,
            "GET_PRICING": IntentType.ASK_PRICE.value,
            "ASK_PRICE": IntentType.ASK_PRICE.value,
            "PRICING_CALCULATION": IntentType.ASK_PRICE.value,
            "CHECK_AVAILABILITY": IntentType.CHECK_AVAILABILITY.value,
            "AVAILABILITY_QUERY": IntentType.CHECK_AVAILABILITY.value,
            "INQUIRE_AMENITIES": IntentType.ASK_AMENITIES.value,
            "ASK_AMENITIES": IntentType.ASK_AMENITIES.value,
            "RAG_AMENITIES": IntentType.ASK_AMENITIES.value,
            "INQUIRE_RULES": IntentType.ASK_RULES.value,
            "ASK_RULES": IntentType.ASK_RULES.value,
            "RAG_RULES_POLICY": IntentType.ASK_RULES.value,
            "COMPARE_SPACES": IntentType.COMPARE_SPACES.value,
            "HOST_MONETIZE": IntentType.CREATE_LISTING.value,
            "CREATE_LISTING": IntentType.CREATE_LISTING.value,
            "HOST_MONETIZATION": IntentType.CREATE_LISTING.value,
            "LEGAL_SAFETY": IntentType.LEGAL_SAFETY.value,
            "LEGAL_AND_SAFETY": IntentType.LEGAL_SAFETY.value,
            "ASK_HELP": IntentType.ASK_HELP.value,
            "GENERAL_GREETING": IntentType.GENERAL_GREETING.value,
            "GENERAL_CONVERSATION": IntentType.GENERAL_GREETING.value,
            "GENERAL_CHAT": IntentType.GENERAL_GREETING.value,
            "CLARIFICATION_NEEDED": IntentType.CLARIFICATION_NEEDED.value
        }
        return mapping.get(intent_str, intent_str)
