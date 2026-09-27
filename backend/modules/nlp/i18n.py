"""
SpaceLoop Multilingual Support & Localization Layer
===================================================
Provides language preference negotiation, safe fallback hierarchies, and
centralized verified multilingual response templates across:
1. English (en)
2. Hindi (hi)
3. Marathi (mr)
4. Garhwali (gar / gbm)
5. Kumaoni (kfy)
6. Jaunsari (jns)
7. Code-Mixed: Hinglish (hi-Latn), Marathi-English (mr-Latn)

Safe Fallback Principle:
Local dialects (Garhwali, Kumaoni, Jaunsari) without verified generative coverage
gracefully fall back to Hindi or English. Unsupported foreign languages fall back
to English. Never hallucinate broken dialect text.
"""
from typing import Dict, Any, Optional, Tuple
from backend.modules.nlp.schemas import LanguageCode, IntentType
from backend.modules.nlp.language_detection import LanguageDetectionService
from backend.modules.nlp.text_normalization import TextNormalizationService


# Canonical Language Metadata
LANGUAGE_METADATA: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "script": "Latin", "family": "Indo-European", "fallback": "en"},
    "hi": {"name": "Hindi", "script": "Devanagari", "family": "Indo-Aryan", "fallback": "en"},
    "mr": {"name": "Marathi", "script": "Devanagari", "family": "Indo-Aryan", "fallback": "hi"},
    "gar": {"name": "Garhwali", "script": "Devanagari", "family": "Central Pahari", "fallback": "hi"},
    "gbm": {"name": "Garhwali", "script": "Devanagari", "family": "Central Pahari", "fallback": "hi"},
    "kfy": {"name": "Kumaoni", "script": "Devanagari", "family": "Central Pahari", "fallback": "hi"},
    "jns": {"name": "Jaunsari", "script": "Devanagari", "family": "Central Pahari", "fallback": "hi"},
    "hi-Latn": {"name": "Hinglish", "script": "Latin", "family": "Code-Mixed", "fallback": "hi"},
    "mr-Latn": {"name": "Marathi-English", "script": "Latin", "family": "Code-Mixed", "fallback": "mr"},
}

SUPPORTED_CODES = set(LANGUAGE_METADATA.keys())


# -----------------------------------------------------------------------------
# VERIFIED MULTILINGUAL RESPONSE TEMPLATES
# -----------------------------------------------------------------------------
TEMPLATES: Dict[str, Dict[str, str]] = {
    # 1. GREETING
    "GREETING": {
        "en": "👋 Hi! I'm **LoopBot**, your SpaceLoop AI concierge. I can help you find verified workspaces, book meeting rooms by the hour, explain Section 52 legal protection, or help you monetize unused square footage. How can I help you today?",
        "hi": "👋 नमस्ते! मैं **लूपबॉट** हूँ, आपका SpaceLoop AI कंसीयर्ज। मैं आपको कार्यक्षेत्र खोजने, घंटे के हिसाब से कमरा बुक करने, धारा 52 कानूनी सुरक्षा समझाने या खाली जगह से कमाई करने में मदद कर सकता हूँ। मैं आपकी क्या मदद करूँ?",
        "mr": "👋 नमस्कार! मी **लूपबॉट**, आपला SpaceLoop AI सहाय्यक. मी आपल्याला सुरक्षित वर्कस्पेस शोधण्यात, तासाप्रमाणे खोली बुक करण्यात, कलम ५२ कायदेशीर संरक्षण समजून सांगण्यात किंवा मोकळ्या जागेतून कमाई करण्यात मदत करू शकतो. मी आज आपल्याला कशी मदत करू?",
        "gar": "👋 नमस्कार भैजी! मैं **लूपबॉट** छौं, SpaceLoop AI संगी। आप तैं काम कुणी कमरा बथौण, घंटा का हिसाब से कमरा बुक करौण, धारा 52 कानूनी नियम बथौण या खाली जागा बटि कमाई करौण मा मदद कर सकदुं। बथवा आज क्या काम करौं?",
        "kfy": "👋 पैलाग दाज्यु! मैं **लूपबॉट** छनूं, SpaceLoop AI साथी। तुमकूँ बैठक लगै कमरो खोजण, घंटा का हिसाब से कमरा बुक करन, धारा 52 कानूनी नियम बथूण या आपण खाली जागा बटी कमाई करन मा मदद कर सकूँछ। बथावा आज क्या मदद करूँ?",
        "jns": "👋 नमस्कार दगड्या! मैं **लूपबॉट** छौं, SpaceLoop AI साथी। तुम तैं बैठक कुणी कमरा खोजा, घंटा का हिसाब से कमरा बुक करा, धारा 52 नियम समझा या खाली जागा बटी कमाई करा। बथावा आज क्या काम करौं?",
        "hi-Latn": "👋 Hi! Main **LoopBot** hoon, aapka SpaceLoop AI concierge. Main aapko private workspaces khojne, hourly booking karne, Section 52 legal protection samajhne, ya khali space monetize karne me madad kar sakta hoon. Aaj kaise help karu?",
        "mr-Latn": "👋 Namaskar! Mee **LoopBot**, tumcha SpaceLoop AI concierge. Tumhala workspace shodhayla, hourly booking karayla, Section 52 legal protection samajhayla, kinva khali space monetize karayla mee help karu shakto. Kashi madat karu?"
    },

    # 2. SEARCH_SPACE
    "SEARCH_SPACE": {
        "en": "🔍 Here are verified spaces matching your search for **{location}** (Category: **{property_type}**, Capacity: **{guest_count}** pax, Budget: up to **₹{max_price}**). Instant zero-hardware access enabled.",
        "hi": "🔍 **{location}** में आपकी खोज के अनुसार सत्यापित स्थान (प्रकार: **{property_type}**, क्षमता: **{guest_count}** व्यक्ति, बजट: **₹{max_price}** तक)। बिना किसी हार्डवेयर के तत्काल डिजिटल पास उपलब्ध है।",
        "mr": "🔍 **{location}** मध्ये आपल्या शोधानुसार सत्यापित जागा (प्रकार: **{property_type}**, क्षमता: **{guest_count}** व्यक्ती, बजेट: **₹{max_price}** पर्यंत). कोणत्याही अतिरिक्त उपकरणांशिवाय झटपट डिजिटल पास उपलब्ध आहे.",
        "gar": "🔍 **{location}** मा आपकी खोज का मुताबिक सुरक्षित जागा (प्रकार: **{property_type}**, क्षमता: **{guest_count}** माणस, भाडू: **₹{max_price}** तक)। मोबाइल डिजिटल पास तैय्यार च।",
        "kfy": "🔍 **{location}** मा तुमरी खोज का अनुसार जांचीं जागा (प्रकार: **{property_type}**, क्षमता: **{guest_count}** माणस, भाड: **₹{max_price}** तक)। मोबाइल डिजिटल पास उपलब्ध छ।",
        "jns": "🔍 **{location}** मा खोज अनुसार सुरक्षित जागा (प्रकार: **{property_type}**, क्षमता: **{guest_count}** माणस, भाडू: **₹{max_price}** तक)। माठू डिजिटल पास तैय्यार च।",
        "hi-Latn": "🔍 **{location}** me aapke search ke hisab se verified spaces (Type: **{property_type}**, Capacity: **{guest_count}** log, Budget: **₹{max_price}** tak). Instant digital pass ready hai.",
        "mr-Latn": "🔍 **{location}** madhe tumchya shodhaprame verified spaces (Type: **{property_type}**, Capacity: **{guest_count}** lok, Budget: **₹{max_price}** paryant). Instant digital pass tayar aahe."
    },

    # 3. BOOK_SPACE
    "BOOK_SPACE": {
        "en": "⚡ Ready to reserve! Total calculation includes hourly rate × duration + 5% platform fee + ₹100 refundable UPI escrow hold. Upon checkout, your geofenced digital door pass activates automatically.",
        "hi": "⚡ बुकिंग के लिए तैयार! कुल राशि में प्रति घंटा दर × अवधि + 5% प्लेटफ़ॉर्म शुल्क + ₹100 रिफ़ंडेबल यूपीआई एस्क्रो शामिल है। चेकआउट के तुरंत बाद आपका डिजिटल पास सक्रिय हो जाएगा।",
        "mr": "⚡ बुकिंगसाठी तयार! एकूण शुल्कात प्रति तास दर × वेळ + ५% प्लॅटफॉर्म फी + ₹१०० परत मिळणारी यूपीआय एस्क्रो ठेव समाविष्ट आहे. चेकआउट होताच आपला डिजिटल पास सक्रिय होईल.",
        "gar": "⚡ बुकिंग कुणी तैय्यार! पुरा भाडू घंटा का हिसाब से + 5% मंच शुल्क + ₹100 वापसी यूपीआई एस्क्रो च। चेकआउट हुंदै आपरो डिजिटल पास चालू ह्वे जालो।",
        "kfy": "⚡ बुकिंग लगै तैय्यार! पुरो भाड घंटा का हिसाब + 5% मंच शुल्क + ₹100 वापसी यूपीआई एस्क्रो छ। चेकआउट हुंदै तुमरो डिजिटल पास चालू भई जालो।",
        "jns": "⚡ बुकिंग कुणी तैय्यार! पुरा भाडू घंटा हिसाब + 5% मंच शुल्क + ₹100 वापसी यूपीआई एस्क्रो च। चेकआउट हुंदै डिजिटल पास चालू ह्वे जालो।",
        "hi-Latn": "⚡ Booking ke liye ready! Total amount me hourly rate × duration + 5% platform fee + ₹100 refundable UPI escrow deposit shamil hai. Checkout ke turant baad digital pass activate ho jayega.",
        "mr-Latn": "⚡ Booking sathi ready! Total charges madhe hourly rate × duration + 5% platform fee + ₹100 refundable UPI escrow deposit samavishta aahe. Checkout zalyavar digital pass activate hoil."
    },

    # 4. LEGAL_SAFETY
    "LEGAL_SAFETY": {
        "en": "⚖️ **Section 52 Legal Protection**: All SpaceLoop bookings operate as non-possessory micro-licenses under Section 52 of the Indian Easements Act, 1882. Guests never acquire tenancy rights. Protected with Aadhaar KYC and ₹100 automated UPI micro-escrow.",
        "hi": "⚖️ **धारा 52 कानूनी सुरक्षा**: सभी SpaceLoop बुकिंग भारतीय सुखाधिकार अधिनियम, 1882 की धारा 52 के तहत लाइसेंस के रूप में संचालित होती हैं। मेहमानों को कभी किराएदारी अधिकार नहीं मिलते। आधार सत्यापन और ₹100 यूपीआई एस्क्रो द्वारा सुरक्षित।",
        "mr": "⚖️ **कलम ५२ कायदेशीर संरक्षण**: SpaceLoop वरील सर्व बुकिंग्ज भारतीय सुखाधिकार कायदा, १८८२ च्या कलम ५२ अंतर्गत परवाना म्हणून चालतात. वापरकर्त्यांना कधीही भाडेकरूचे अधिकार मिळत नाहीत. आधार केवायसी आणि ₹१०० यूपीआय एस्क्रो द्वारे पूर्ण सुरक्षितता.",
        "gar": "⚖️ **धारा 52 कानूनी नियम**: SpaceLoop मा सब बुकिंग भारतीय सुखाधिकार कानून 1882 की धारा 52 का तहत अस्थायी अनुमति च। कखि भी किरायेदारी हक नी मिलदु। आधार जांच अर ₹100 यूपीआई एस्क्रो सुरक्षित च।",
        "kfy": "⚖️ **धारा 52 कानूनी नियम**: SpaceLoop मा सब बुकिंग भारतीय सुखाधिकार कानून 1882 की धारा 52 का तहत अनुमति छ। कसै तैं किरायेदारी अधिकार नै मिलन। आधार जांच अर ₹100 यूपीआई एस्क्रो सुरक्षित छ।",
        "jns": "⚖️ **धारा 52 नियम**: SpaceLoop सब बुकिंग सुखाधिकार कानून धारा 52 तहत अनुमति च। किरायेदारी हक नी मिलदु। आधार जांच अर ₹100 यूपीआई एस्क्रो सुरक्षित च।",
        "hi-Latn": "⚖️ **Section 52 Legal Protection**: Saari SpaceLoop bookings Indian Easements Act, 1882 ke Section 52 ke tehat micro-license hoti hain. Guests ko tenancy rights nahi milte. Aadhaar KYC aur ₹100 UPI escrow se fully protected.",
        "mr-Latn": "⚖️ **Section 52 Legal Protection**: Sarva SpaceLoop bookings Indian Easements Act, 1882 chya Section 52 pramane micro-license astat. Guests na tenancy rights milat nahit. Aadhaar KYC aani ₹100 UPI escrow ne fully protected."
    },

    # 5. HOST_MONETIZE
    "HOST_MONETIZE": {
        "en": "🏡 **Monetize Your Idle Space**: Earn passive yield by listing your spare room, garage, terrace, or office on SpaceLoop. Verified hosts earn an estimated ₹8,000 to ₹35,000/month. We handle automated UPI payouts, DigiLocker electricity verification, and digital pass access.",
        "hi": "🏡 **अपनी खाली जगह से कमाएं**: अपने खाली कमरे, गैराज, छत या ऑफिस को SpaceLoop पर लिस्ट करके हर महीने ₹8,000 से ₹35,000 तक कमाएं। हम स्वचालित यूपीआई भुगतान, बिजली बिल सत्यापन और डिजिटल पास की सुविधा देते हैं।",
        "mr": "🏡 **मोकळ्या जागेतून उत्पन्न मिळवा**: आपली रिकामी खोली, गॅरेज, टेरेस किंवा ऑफिस SpaceLoop वर जोडून दरमहा ₹८,००० ते ₹३५,००० पर्यंत कमाई करा. स्वयंचलित यूपीआई पेआउट्स, वीज बिल पडताळणी आणि डिजिटल पासची सोय आम्ही देतो.",
        "gar": "🏡 **अपणी खाली जागा बटि कमावा**: अपणी खाली कमरा, गैराज, छत या दफ्तर तैं SpaceLoop मा जोडि बेर ₹8,000 बटि ₹35,000 महीना तक कमावा। यूपीआई बैंक खाता मा सीधा पईसा अर बिजली बिल जांच सब सुलभ च।",
        "kfy": "🏡 **आपण खाली जागा बटी कमावा**: आपण खाली कमरो, गैराज, छत या दफ्तर तैं SpaceLoop मा जोडि ₹8,000 बटी ₹35,000 महीना तक कमावा। यूपीआई खाता मा सीधा रुपिया अर बिजली बिल जांच सुरक्षित छ।",
        "jns": "🏡 **खाली जागा बटी कमावा**: अपणी खाली कमरा, गैराज, छत या दफ्तर SpaceLoop मा जोडि बेर ₹8,000 बटी ₹35,000 महीना तक कमावा। यूपीआई खाता सीधा पईसा मिलदु।",
        "hi-Latn": "🏡 **Apni Empty Space Monetize Karein**: Apna spare room, garage, terrace ya office SpaceLoop par list karke ₹8,000 se ₹35,000/month tak kamayein. Automated UPI payouts aur electricity bill verification ke sath.",
        "mr-Latn": "🏡 **Moklya Jagevarun Kamva**: Tumchi rikami room, garage, terrace kinva office SpaceLoop var list karun dar mahina ₹8,000 te ₹35,000 kamva. Automated UPI payouts aani digital pass sobat."
    },

    # 6. ESCROW_REFUND
    "ESCROW_REFUND": {
        "en": "💳 **₹100 UPI Escrow Protocol**: Your security deposit of ₹100 is held safely in escrow during your session. Upon zero-incident checkout and electricity turn-off confirmation, the full ₹100 is automatically released back to your UPI VPA within 120 seconds.",
        "hi": "💳 **₹100 यूपीआई एस्क्रो प्रोटोकॉल**: आपका ₹100 का सुरक्षा डिपॉजिट सत्र के दौरान एस्क्रो में सुरक्षित रहता है। चेकआउट और बिजली उपकरण बंद होने की पुष्टि के 120 सेकंड के भीतर पूरी राशि आपके यूपीआई खाते में वापस जमा हो जाती है।",
        "mr": "💳 **₹१०० यूपीआय एस्क्रो प्रोटोकॉल**: आपली ₹१०० सुरक्षा ठेव सत्रादरम्यान एस्क्रो खात्यात सुरक्षित असते. सुरक्षित चेकआउट आणि विजेची उपकरणे बंद असल्याची खात्री झाल्यावर १२० सेकंदांत संपूर्ण ₹१०० आपल्या यूपीआय खात्यात परत जमा होतात.",
        "gar": "💳 **₹100 यूपीआई एस्क्रो नियम**: आपरो ₹100 सुरक्षा रुपिया सत्र मा सुरक्षित रंदु। चेकआउट अर बिजली बत्ती बंद हुण का 120 सेकंड भितर पुरा ₹100 आपरा यूपीआई मा वापस ऐ जांदु।",
        "kfy": "💳 **₹100 यूपीआई एस्क्रो नियम**: तुमरो ₹100 सुरक्षा रुपिया सत्र मा सुरक्षित रूँछ। चेकआउट अर बिजली बत्ती बंद हुण का 120 सेकंड भीतर पुरो ₹100 तुमरा यूपीआई मा वापस ऐ जाँछ।",
        "jns": "💳 **₹100 यूपीआई एस्क्रो**: ₹100 सुरक्षा रुपिया एस्क्रो मा सुरक्षित रंदु। चेकआउट अर बिजली बंद हुण का 120 सेकंड भितर पुरा ₹100 वापस मिलदु।",
        "hi-Latn": "💳 **₹100 UPI Escrow Protocol**: Aapka ₹100 security deposit session ke dauran safe escrow me rehta hai. Checkout aur appliance turn-off verification ke 120 seconds ke andar full ₹100 aapke UPI VPA par instantly refund ho jata hai.",
        "mr-Latn": "💳 **₹100 UPI Escrow Protocol**: Tumchi ₹100 security deposit session darmiyan safe escrow madhe aste. Checkout zalyavar 120 seconds chya aat purna ₹100 tumchya UPI varti refund hote."
    },

    # 7. CLARIFICATION_NEEDED
    "CLARIFICATION_NEEDED": {
        "en": "🤔 I didn't quite catch that. Could you clarify if you're looking to book a workspace, list your unused property, check pricing, or learn about Section 52 legal safety?",
        "hi": "🤔 मुझे आपकी बात पूरी तरह समझ नहीं आई। क्या आप कार्यक्षेत्र खोजना चाहते हैं, अपनी जगह लिस्ट करना चाहते हैं, किराया जानना चाहते हैं या धारा 52 कानूनी सुरक्षा के बारे में पूछना चाहते हैं?",
        "mr": "🤔 मला आपला प्रश्न पूर्णपणे समजला नाही. आपण जागा शोधू इच्छिता, आपली जागा लिस्ट करू इच्छिता, भाडे जाणून घेऊ इच्छिता की कलम ५२ कायदेशीर संरक्षणाबद्दल विचारत आहात?",
        "gar": "🤔 बात पूरी समझ नी ऐ पाई। आप तैं कमरा खोजन च, अपणी जागा लिस्ट करन च, भाडू पूंछन च या धारा 52 कानून बाबत पूंछन च? साफ बथवा।",
        "kfy": "🤔 बात पूरी समझ नै ऐ पाई। तुमकूँ कमरा खोजन छ, आपण जागा जोड़न छ, भाड पूंछन छ या धारा 52 कानून बाबत पूंछन छ? साफ बथावा।",
        "jns": "🤔 बात पूरी समझ नी आई। तुम तैं कमरा खोजना च, जागा जोड़नी च, भाडू पूछना च या धारा 52 नियम पूछना च? साफ बथावा।",
        "hi-Latn": "🤔 Samajh nahi aaya. Kya aap space book karna chahte hain, apni property list karna chahte hain, pricing puch rahe hain ya Section 52 legal protection samajhna chahte hain?",
        "mr-Latn": "🤔 Samjhle nahi. Tumhala space book karaychi aahe, property list karaychi aahe, pricing vicharaychi aahe ki Section 52 legal protection samajhun ghyaychi aahe?"
    }
}


class MultilingualService:
    """
    Coordinates language preference negotiation, safe fallback hierarchies, and
    localized response generation for SpaceLoop.
    """

    @classmethod
    def negotiate_language(
        cls,
        user_message: str,
        explicit_preference: Optional[str] = None
    ) -> Tuple[str, str, bool]:
        """
        Negotiates effective language for response generation:
        1. If user explicitly selected a valid preference, respect it.
        2. If preference is 'auto' or not provided, run fast language detection on message.
        3. Returns (effective_language, detected_language, is_code_mixed).
        """
        # Step A: Detect message language using Part 2 LanguageDetectionService
        det_code, secondary_langs, is_code_mixed, _ = LanguageDetectionService.detect_language(user_message or "")
        detected_lang = det_code if isinstance(det_code, str) else det_code.value

        # Step B: Check explicit preference
        if explicit_preference and explicit_preference.strip().lower() not in ("auto", "none", "", "null"):
            pref_clean = explicit_preference.strip().lower()
            # Normalize synonyms (e.g. 'gar' -> 'gbm')
            if pref_clean in ("gar", "gbm", "garhwal", "garhwali"):
                return "gar", detected_lang, is_code_mixed
            if pref_clean in ("kfy", "kumaon", "kumaoni"):
                return "kfy", detected_lang, is_code_mixed
            if pref_clean in ("jns", "jaunsar", "jaunsari"):
                return "jns", detected_lang, is_code_mixed
            if pref_clean in SUPPORTED_CODES:
                return pref_clean, detected_lang, is_code_mixed

        # Step C: Fallback to detected language if valid, else English
        if detected_lang in SUPPORTED_CODES:
            # Map gbm -> gar for presentation
            eff = "gar" if detected_lang == "gbm" else detected_lang
            return eff, detected_lang, is_code_mixed

        return "en", detected_lang, is_code_mixed

    @classmethod
    def resolve_fallback_language(cls, requested_lang: str) -> str:
        """
        Safe Fallback Hierarchy:
        - Local Himalayan/Pahari dialects (Garhwali, Kumaoni, Jaunsari) -> Hindi
        - Marathi -> Hindi
        - Unsupported foreign languages (French, German, etc.) -> English
        """
        lang = (requested_lang or "").lower()
        if lang in ("gar", "gbm", "kfy", "jns", "mr", "mr-latn"):
            return "hi"
        if lang in ("hi", "hi-latn"):
            return "en"
        return "en"

    @classmethod
    def get_localized_response(
        cls,
        intent_type: str,
        effective_lang: str,
        entities: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Retrieves a verified, grammatically sound template response in the target language.
        If the template is missing in a local dialect, gracefully falls back to Hindi -> English.
        """
        entities = entities or {}
        intent_key = intent_type.upper()

        # Map intent type to template key
        mapped_key = "CLARIFICATION_NEEDED"
        if "GREET" in intent_key:
            mapped_key = "GREETING"
        elif "SEARCH" in intent_key:
            mapped_key = "SEARCH_SPACE"
        elif "BOOK" in intent_key:
            mapped_key = "BOOK_SPACE"
        elif "LEGAL" in intent_key or "SAFETY" in intent_key:
            mapped_key = "LEGAL_SAFETY"
        elif "MONETIZE" in intent_key or "HOST" in intent_key:
            mapped_key = "HOST_MONETIZE"
        elif "ESCROW" in intent_key or "REFUND" in intent_key:
            mapped_key = "ESCROW_REFUND"

        intent_templates = TEMPLATES.get(mapped_key, TEMPLATES["CLARIFICATION_NEEDED"])

        # Try effective language
        target_template = intent_templates.get(effective_lang)

        # Fallback 1: Regional dialect -> Hindi
        if not target_template:
            fallback_lang = cls.resolve_fallback_language(effective_lang)
            target_template = intent_templates.get(fallback_lang)

        # Fallback 2: English canonical
        if not target_template:
            target_template = intent_templates.get("en", "How can I assist you with SpaceLoop today?")

        # Interpolate entities safely
        filled = target_template
        filled = filled.replace("{location}", str(entities.get("location") or "your area"))
        filled = filled.replace("{property_type}", str(entities.get("property_type") or "work/meeting space"))
        filled = filled.replace("{guest_count}", str(entities.get("guest_count") or 1))
        filled = filled.replace("{max_price}", str(entities.get("max_price") or 500))

        return filled

    @classmethod
    def build_multilingual_prompt_guidelines(cls, effective_lang: str) -> str:
        """
        Produces strict LLM prompting instructions to ensure language consistency
        without hallucinating dialect vocabulary.
        """
        lang_info = LANGUAGE_METADATA.get(effective_lang, LANGUAGE_METADATA["en"])
        lang_name = lang_info["name"]

        if effective_lang in ("gar", "gbm", "kfy", "jns"):
            return (
                f"\n[LANGUAGE INSTRUCTION: {lang_name} (Uttarakhand Central Pahari)]\n"
                f"- The user's query or preference is in {lang_name}.\n"
                f"- Use authentic {lang_name} greetings and markers where confident.\n"
                f"- CRITICAL GUARDRAIL: If you are not 100% confident in complex legal, pricing, or technical {lang_name} vocabulary, gracefully explain those specific technical details in clean, polite standard Hindi (the regional lingua franca of Uttarakhand).\n"
                f"- NEVER fabricate or hallucinate broken dialect words.\n"
            )
        elif effective_lang in ("hi", "hi-Latn"):
            return (
                f"\n[LANGUAGE INSTRUCTION: Hindi / Hinglish]\n"
                f"- Respond in natural, polite Hindi or Hinglish matching the user's conversational tone.\n"
                f"- Retain standard marketplace terms (booking, Wi-Fi, pass, Section 52, ₹) clearly.\n"
            )
        elif effective_lang in ("mr", "mr-Latn"):
            return (
                f"\n[LANGUAGE INSTRUCTION: Marathi]\n"
                f"- Respond in natural, polite Marathi (प्रमाण मराठी).\n"
                f"- Retain standard marketplace terms clearly.\n"
            )
        else:
            return (
                f"\n[LANGUAGE INSTRUCTION: English]\n"
                f"- Respond in clear, friendly professional Indian English.\n"
            )
