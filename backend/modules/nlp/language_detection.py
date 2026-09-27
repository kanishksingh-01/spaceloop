"""
SpaceLoop Language Detection Service
Accurately identifies natural languages, regional Pahari dialects, and code-mixed Indian queries.
Supports: English, Hindi, Marathi, Garhwali, Kumaoni, Jaunsari, Hinglish, and Marathi-English.
"""
import re
from typing import Dict, List, Tuple
from backend.modules.nlp.schemas import LanguageCode


# -----------------------------------------------------------------------------
# LEXICAL PROFILES (Devanagari & Romanized Transliteration)
# -----------------------------------------------------------------------------

# Marathi distinctive tokens (Devanagari)
MARATHI_DEVANAGARI_TOKENS = {
    "आहे", "नाही", "पाहिजे", "कुठे", "कसे", "किती", "खोली", "जागा", "मला", "कधी",
    "करावे", "मिळेल", "असेल", "नका", "शोधतो", "शोधत", "स्वस्त", "भाडे", "कार्यालय"
}

# Garhwali distinctive tokens (Devanagari - Central Pahari / Uttarakhand)
GARHWALI_DEVANAGARI_TOKENS = {
    "कख", "कन", "कैक", "च्यांद", "च्यांदा", "भैजी", "दीदी", "ह्वैल", "छौ", "छन",
    "छी", "बथौ", "घौर", "कमरो", "डांडा", "गौं", "कौथिग", "थै", "म्येरु", "त्वेरु"
}

# Kumaoni distinctive tokens (Devanagari - Central Pahari / Uttarakhand)
KUMAONI_DEVANAGARI_TOKENS = {
    "कसिक", "कसिकै", "कैले", "कथु", "छ्या", "छौ", "भला", "च्यांहूं", "कौतु",
    "जौ", "मेर", "तेर", "कुकुर", "हिट", "भासा"
}

# Jaunsari distinctive tokens (Devanagari - Western/Central Pahari / Jaunsar-Bawar)
JAUNSARI_DEVANAGARI_TOKENS = {
    "केथा", "किए", "छा", "बासा", "जोड़ा", "रोउं", "ओर", "रोणी", "तेउं", "मेउं"
}

# Hindi standard tokens (Devanagari)
HINDI_DEVANAGARI_TOKENS = {
    "है", "हैं", "हूँ", "हो", "था", "थी", "थे", "कहाँ", "कैसे", "कितना", "कितने",
    "कितनी", "चाहिए", "कमरा", "कमरे", "जगह", "किराया", "बताओ", "मिलेगा", "करो",
    "सकते", "सकता", "सकती", "कृपया", "नमस्ते", "खोजो", "ढूंढो", "घंटे"
}

# Romanized Hinglish tokens (Latin)
HINGLISH_TOKENS = {
    "chahiye", "chaiye", "chahye", "kitna", "kitne", "kitni", "kahan", "kaha",
    "kamra", "kamre", "milega", "kya", "hai", "hain", "hoon", "karo", "hoga",
    "batao", "btao", "pe", "mein", "me", "ka", "ki", "ke", "rupaye", "rupiya",
    "kab", "kaise", "ek", "do", "teen", "char", "paanch", "chhah", "saat", "aath",
    "dhoondo", "khojo", "dedo", "mil", "sakta", "sakate", "namaste", "pranam"
}

# Romanized Marathi tokens (Latin)
MARATHI_ROMANIZED_TOKENS = {
    "pahije", "kuthe", "kiti", "aahe", "ahe", "nahi", "kasa", "kashi", "kase",
    "mala", "kholya", "kholi", "jaga", "kadhi", "karaycha", "shodha", "shodhato",
    "milen", "bhaden", "bhada", "namaskar", "don", "chaar", "paach", "saha"
}

# Romanized Garhwali tokens (Latin)
GARHWALI_ROMANIZED_TOKENS = {
    "kakh", "kile", "bhaiji", "chyan", "chyanda", "chho", "chan", "hwel",
    "kasa", "kamro", "ghaur", "batho", "myeru", "tweru", "didi"
}

# Romanized Kumaoni tokens (Latin)
KUMAONI_ROMANIZED_TOKENS = {
    "kasik", "kaile", "kathu", "chhya", "chhau", "bhal", "bhala", "chyanhun", "kautu"
}

# Romanized Jaunsari tokens (Latin)
JAUNSARI_ROMANIZED_TOKENS = {
    "ketha", "kie", "chha", "basa", "joda", "roun"
}

# English domain markers (used for code-mixing detection)
ENGLISH_TOKENS = {
    "find", "space", "spaces", "room", "rooms", "desk", "desks", "office",
    "hours", "hour", "price", "rate", "cost", "book", "booking", "reserve",
    "available", "tomorrow", "today", "weekend", "quiet", "meeting", "studio",
    "podcast", "wifi", "ac", "parking", "rules", "food", "need", "looking",
    "cheap", "best", "near", "location", "compare", "host", "monetize", "earn",
    "please", "hello", "hi", "hey", "can", "how", "what", "where", "is", "for"
}


class LanguageDetectionService:
    """
    Robust multi-script language and code-mixing detection engine.
    Does NOT depend on external network APIs or heavy C-extensions.
    """

    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, List[str], bool, float]:
        """
        Analyzes the input string and returns:
        (primary_language, secondary_languages, is_code_mixed, confidence)
        """
        if not text or not text.strip():
            return LanguageCode.UNKNOWN.value, [], False, 0.0

        clean_text = text.strip()

        # 1. Measure script distribution
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", clean_text))
        latin_chars = len(re.findall(r"[a-zA-Z]", clean_text))
        total_letters = devanagari_chars + latin_chars

        if total_letters == 0:
            return LanguageCode.UNKNOWN.value, [], False, 0.30

        devanagari_ratio = devanagari_chars / total_letters

        # ---------------------------------------------------------------------
        # BRANCH A: DEVANAGARI SCRIPT (Devanagari Ratio >= 0.40)
        # ---------------------------------------------------------------------
        if devanagari_ratio >= 0.40:
            tokens = set(re.findall(r"[\u0900-\u097F]+", clean_text))
            
            # Check unique Marathi phoneme ळ (U+0933)
            has_marathi_lla = "ळ" in clean_text

            mr_score = len(tokens.intersection(MARATHI_DEVANAGARI_TOKENS)) + (3 if has_marathi_lla else 0)
            gbm_score = len(tokens.intersection(GARHWALI_DEVANAGARI_TOKENS)) * 2
            kfy_score = len(tokens.intersection(KUMAONI_DEVANAGARI_TOKENS)) * 2
            jns_score = len(tokens.intersection(JAUNSARI_DEVANAGARI_TOKENS)) * 2
            hi_score = len(tokens.intersection(HINDI_DEVANAGARI_TOKENS))

            # Distinguish Devanagari languages
            if gbm_score > 0 and gbm_score >= max(hi_score, mr_score, kfy_score, jns_score):
                conf = min(0.98, 0.70 + gbm_score * 0.1)
                return LanguageCode.GBM.value, [LanguageCode.HI.value], False, conf

            if kfy_score > 0 and kfy_score >= max(hi_score, mr_score, gbm_score, jns_score):
                conf = min(0.98, 0.70 + kfy_score * 0.1)
                return LanguageCode.KFY.value, [LanguageCode.HI.value], False, conf

            if jns_score > 0 and jns_score >= max(hi_score, mr_score, gbm_score, kfy_score):
                conf = min(0.98, 0.70 + jns_score * 0.1)
                return LanguageCode.JNS.value, [LanguageCode.HI.value], False, conf

            if mr_score > 0 and mr_score > hi_score:
                conf = min(0.98, 0.75 + mr_score * 0.08)
                return LanguageCode.MR.value, [], False, conf

            # Default Devanagari to Hindi
            conf = min(0.98, 0.75 + hi_score * 0.05) if hi_score > 0 else 0.85
            return LanguageCode.HI.value, [], False, conf

        # ---------------------------------------------------------------------
        # BRANCH B: LATIN SCRIPT (English, Hinglish, Romanized Marathi, Pahari)
        # ---------------------------------------------------------------------
        lower_text = clean_text.lower()
        words = set(re.findall(r"\b[a-zA-Z]{2,}\b", lower_text))

        en_matches = len(words.intersection(ENGLISH_TOKENS))
        hi_matches = len(words.intersection(HINGLISH_TOKENS))
        mr_matches = len(words.intersection(MARATHI_ROMANIZED_TOKENS))
        gbm_matches = len(words.intersection(GARHWALI_ROMANIZED_TOKENS))
        kfy_matches = len(words.intersection(KUMAONI_ROMANIZED_TOKENS))
        jns_matches = len(words.intersection(JAUNSARI_ROMANIZED_TOKENS))

        # Check Romanized Garhwali / Kumaoni / Jaunsari
        if gbm_matches > 0 and gbm_matches >= max(mr_matches, hi_matches):
            is_cm = en_matches > 0
            secondaries = [LanguageCode.EN.value] if is_cm else []
            return LanguageCode.GBM_LATN.value, secondaries, is_cm, 0.90

        if kfy_matches > 0 and kfy_matches >= max(mr_matches, hi_matches):
            is_cm = en_matches > 0
            secondaries = [LanguageCode.EN.value] if is_cm else []
            return LanguageCode.KFY_LATN.value, secondaries, is_cm, 0.90

        if jns_matches > 0 and jns_matches >= max(mr_matches, hi_matches):
            is_cm = en_matches > 0
            secondaries = [LanguageCode.EN.value] if is_cm else []
            return LanguageCode.JNS.value, secondaries, is_cm, 0.90

        # Check Romanized Marathi
        if mr_matches > 0 and mr_matches >= hi_matches:
            is_cm = en_matches > 0
            secondaries = [LanguageCode.EN.value] if is_cm else []
            conf = min(0.96, 0.75 + mr_matches * 0.07)
            return LanguageCode.MR_LATN.value, secondaries, is_cm, conf

        # Check Hinglish
        if hi_matches > 0:
            is_cm = en_matches > 0
            secondaries = [LanguageCode.EN.value] if is_cm else []
            conf = min(0.96, 0.75 + hi_matches * 0.07)
            return LanguageCode.HI_LATN.value, secondaries, is_cm, conf

        # Pure English
        if en_matches > 0:
            conf = min(0.99, 0.80 + en_matches * 0.04)
            return LanguageCode.EN.value, [], False, conf

        # Unrecognized Latin text
        return LanguageCode.EN.value, [], False, 0.50
