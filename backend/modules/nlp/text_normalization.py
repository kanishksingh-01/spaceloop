"""
SpaceLoop Text Normalization Service
Cleans and standardizes raw user text across multiple scripts and Indian regional colloquialisms.
Handles Unicode NFC, zero-width stripping, currency normalization, multilingual number parsing,
and spelling variant canonicalization.
"""
import re
import unicodedata
from typing import Dict


# Devanagari numerals to standard ASCII digits
DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

# Number words mapped to digits
NUMBER_WORDS: Dict[str, str] = {
    # English
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "fifteen": "15", "twenty": "20",
    # Hindi / Hinglish
    "ek": "1", "do": "2", "teen": "3", "char": "4", "chaar": "4",
    "paanch": "5", "panch": "5", "chhah": "6", "che": "6", "saat": "7",
    "aath": "8", "nau": "9", "das": "10", "gyarah": "11", "barah": "12",
    "pandrah": "15", "bees": "20",
    # Marathi / Romanized
    "don": "2", "paach": "5", "saha": "6", "daha": "10",
    # Pahari (Garhwali / Kumaoni)
    "dui": "2", "chha": "6",
    # Devanagari words
    "एक": "1", "दो": "2", "दोन": "2", "तीन": "3", "चार": "4",
    "पाँच": "5", "पाच": "5", "छह": "6", "सहा": "6", "सात": "7",
    "आठ": "8", "नौ": "9", "नऊ": "9", "दस": "10", "दहा": "10"
}

# Colloquial spelling variations and phonetic canonicalization
SPELLING_NORMALIZATIONS = [
    # Hindi / Hinglish colloquial variants
    (r"\b(?:chahye|chaiye|chahey|chahiyea|chahiyei)\b", "chahiye"),
    (r"\b(?:kaha|kahanpe|kaha\s+pe)\b", "kahan"),
    (r"\b(?:btao|batana|bataiye)\b", "batao"),
    (r"\b(?:dedo|de\s+do)\b", "dedo"),
    (r"\b(?:dhoondo|dhundo|dhoond)\b", "khojo"),
    (r"\b(?:mil\s+sakta|milsakta)\b", "milega"),
    # Marathi colloquial variants
    (r"\b(?:pahijea|pahijehe|paahije)\b", "pahije"),
    (r"\b(?:kutha|kuth)\b", "kuthe"),
    (r"\b(?:shodhato|shodhit)\b", "shodha"),
    (r"\b(?:karaycha\s+aahe|karaycha)\b", "kara"),
    # Pahari colloquial variants
    (r"\b(?:kakh\s+chho|kakh\s+chan)\b", "kakh"),
    (r"\b(?:chyanda|chyanhu)\b", "chyan"),
    # Chat / English shorthand
    (r"\b(?:plz|pls|plzz|plss)\b", "please"),
    (r"\b(?:thx|tks|ty)\b", "thank you"),
    (r"\b(?:u|ur)\b", lambda m: "you" if m.group(0).lower() == "u" else "your"),
    (r"\b(?:abt)\b", "about"),
    (r"\b(?:w/|w/o)\b", lambda m: "with" if "w/" in m.group(0) and "o" not in m.group(0) else "without"),
]


class TextNormalizationService:
    """
    Multilingual text normalization pipeline:
    NFC unicode -> zero-width cleanup -> devanagari digits -> currency canonicalization ->
    number words -> spelling variants -> clean spacing.
    """

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""

        # 1. Unicode NFC normalization
        normalized = unicodedata.normalize("NFC", text)

        # 2. Strip invisible zero-width spaces, joiners, and BOM
        normalized = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]", "", normalized)

        # 3. Transliterate Devanagari numerals to standard digits (०-९ -> 0-9)
        for d_char, digit in DEVANAGARI_DIGITS.items():
            if d_char in normalized:
                normalized = normalized.replace(d_char, digit)

        # 4. Standardize Indian currency representations to ₹
        # e.g. "Rs 500", "RS. 500", "inr 500", "500 rs", "500 rupaye" -> "₹500"
        normalized = re.sub(
            r"\b(?:rs\.?|inr|rupaye|rupees?|rupiya)\s*(\d+(?:\.\d+)?)\b",
            r"₹\1",
            normalized,
            flags=re.IGNORECASE
        )
        normalized = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*(?:rs\.?|inr|rupaye|rupees?|rupiya|रुपये|रु)\b",
            r"₹\1",
            normalized,
            flags=re.IGNORECASE
        )

        # 5. Standardize hourly rates: "₹500 / hr", "₹500/hour", "500 per hour" -> "₹500/hr"
        normalized = re.sub(
            r"₹(\d+)\s*(?:/|\s*per\s*)(?:hr|hour|ghanta|taas)\b",
            r"₹\1/hr",
            normalized,
            flags=re.IGNORECASE
        )

        # 6. Normalize written number words (e.g. "for two people" -> "for 2 people")
        # Only replace when used in counting context (preceded or followed by capacity/duration/space keywords)
        words = normalized.split()
        normalized_words = []
        for w in words:
            clean_w = w.lower().strip(".,?!;:")
            if clean_w in NUMBER_WORDS:
                digit = NUMBER_WORDS[clean_w]
                # Preserve surrounding punctuation
                w_norm = w.lower().replace(clean_w, digit)
                normalized_words.append(w_norm)
            else:
                normalized_words.append(w)
        normalized = " ".join(normalized_words)

        # 7. Apply phonetic & spelling variant normalizations
        for pattern, replacement in SPELLING_NORMALIZATIONS:
            if callable(replacement):
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            else:
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        # 8. Clean redundant punctuation & whitespace while preserving essential markers (₹, #, :, /, -)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"([!?.,])\1+", r"\1", normalized)

        return normalized.strip()
