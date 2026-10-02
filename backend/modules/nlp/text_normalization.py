"""
SpaceLoop Text Normalization Service
Cleans and standardizes raw user text across multiple scripts, Indian regional colloquialisms,
and shorthand marketplace phrasing.
Handles:
- Unicode NFC & invisible character cleanup
- Devanagari numerals to ASCII digits
- Currency & k-notation normalization ("2k" -> "₹2000", "under 3.5k" -> "under ₹3500")
- Written number words to numeric digits (English, Hindi, Marathi, Pahari)
- Compound time expressions ("from 5 to 8" -> "from 5:00 to 8:00")
- Marketplace abbreviations ("meeting rm" -> "meeting room", "w/" -> "with")
- Colloquial spelling variations and code-mixed phonetic variants
"""
import re
import unicodedata
from typing import Dict, List, Tuple


# Devanagari numerals to standard ASCII digits
DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

# Number words mapped to digits
NUMBER_WORDS: Dict[str, str] = {
    # English units & teens
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
    "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60",
    "seventy": "70", "eighty": "80", "ninety": "90",
    # Hindi / Hinglish units & teens
    "shunya": "0", "ek": "1", "do": "2", "teen": "3", "char": "4", "chaar": "4",
    "paanch": "5", "panch": "5", "chhah": "6", "che": "6", "saat": "7",
    "aath": "8", "nau": "9", "das": "10", "gyarah": "11", "barah": "12",
    "terah": "13", "chaudah": "14", "pandrah": "15", "solah": "16",
    "satrah": "17", "atharah": "18", "unnees": "19", "bees": "20",
    "tees": "30", "chalis": "40", "chalees": "40", "pachas": "50",
    # Marathi / Romanized
    "shunya": "0", "don": "2", "paach": "5", "saha": "6", "daha": "10",
    "vis": "20", "tisa": "30",
    # Pahari (Garhwali / Kumaoni)
    "dui": "2", "chha": "6", "dash": "10",
    # Devanagari words
    "शून्य": "0", "एक": "1", "दो": "2", "दोन": "2", "तीन": "3", "चार": "4",
    "पाँच": "5", "पाच": "5", "छह": "6", "सहा": "6", "सात": "7",
    "आठ": "8", "नौ": "9", "नऊ": "9", "दस": "10", "दहा": "10",
    "ग्यारह": "11", "बारह": "12", "पंद्रह": "15", "बीस": "20",
    "तीस": "30", "चालीस": "40", "पचास": "50"
}

# Multiplier words for magnitude
MULTIPLIER_WORDS = {
    "hundred": 100, "sau": 100, "शौ": 100, "सौ": 100, "शे": 100,
    "thousand": 1000, "hazar": 1000, "hazaar": 1000, "हज़ार": 1000, "हजार": 1000,
    "k": 1000, "lac": 100000, "lakh": 100000, "लाख": 100000
}

# Common marketplace abbreviations and phrase canonicalizations
MARKETPLACE_ABBREVIATIONS = [
    # Room / Space types
    (r"\b(?:meeting\s+rm|meet\s+rm|meet\s+room|conf\s+rm|conf\s+room)\b", "meeting room"),
    (r"\b(?:wrkspace|wrk\s+space|work\s+spc)\b", "workspace"),
    (r"\b(?:cowork|co-working)\b", "coworking"),
    (r"\b(?:photostudio|photo\s+std)\b", "photo studio"),
    (r"\b(?:podcast\s+std|pod\s+studio)\b", "podcast studio"),
    (r"\b(?:conf\s+hall|conference\s+rm)\b", "conference room"),
    (r"\b(?:prkng|prking)\b", "parking"),
    # General chat abbreviations
    (r"\b(?:plz|pls|plzz|plss)\b", "please"),
    (r"\b(?:thx|tks|ty)\b", "thank you"),
    (r"\b(?:u|ur)\b", lambda m: "you" if m.group(0).lower() == "u" else "your"),
    (r"\b(?:abt)\b", "about"),
    (r"\b(?:w/|w/\s+)\b", "with "),
    (r"\b(?:w/o|w/o\s+)\b", "without "),
    (r"\b(?:avail|avlbl)\b", "available"),
    (r"\b(?:wknd|wkend)\b", "weekend"),
    (r"\b(?:tmrw|tmr|2mrw|2moro)\b", "tomorrow"),
    (r"\b(?:evng|eve)\b", "evening"),
    (r"\b(?:mrng|morn)\b", "morning"),
    (r"\b(?:ppl|pax|prs)\b", "people"),
    (r"(?<!/)\b(?:hrs?)\b", "hours"),
    (r"\b(\d+(?:\.\d+)?)-(?:hours?|hrs?)\b", r"\1 hours"),
    (r"\b(?:mins?)\b", "minutes"),
    # Hinglish & Indic colloquial variants
    (r"\b(?:chahye|chaiye|chahey|chahiyea|chahiyei)\b", "chahiye"),
    (r"\b(?:kaha|kahanpe|kaha\s+pe)\b", "kahan"),
    (r"\b(?:btao|batana|bataiye)\b", "batao"),
    (r"\b(?:dedo|de\s+do)\b", "dedo"),
    (r"\b(?:dhoondo|dhundo|dhoond)\b", "khojo"),
    (r"\b(?:mil\s+sakta|milsakta)\b", "milega"),
    (r"\b(?:ke\s+andar|k\s+andar|k\s+under)\b", "under"),
    (r"\b(?:ke\s+liye|k\s+liye)\b", "for"),
    # Marathi colloquial variants
    (r"\b(?:pahijea|pahijehe|paahije|havay|havi|hava)\b", "pahije"),
    (r"\b(?:kutha|kuth)\b", "kuthe"),
    (r"\b(?:shodhato|shodhit)\b", "shodha"),
    (r"\b(?:karaycha\s+aahe|karaycha)\b", "kara"),
    (r"\b(?:sathi|saathi)\b", "for"),
    # Pahari colloquial variants
    (r"\b(?:kakh\s+chho|kakh\s+chan)\b", "kakh"),
    (r"\b(?:chyanda|chyanhu)\b", "chyan"),
]


class TextNormalizationService:
    """
    Unified text normalization pipeline:
    NFC unicode -> zero-width cleanup -> devanagari digits ->
    k-notation / currency canonicalization -> written number words ->
    marketplace abbreviations -> compound time standardization -> clean spacing.
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

        # 4. Standardize Indian currency representations & 'k' shorthand
        # e.g., "2k" -> "₹2000", "2.5k" -> "₹2500", "3.2k" -> "₹3200", "under 2k" -> "under ₹2000"
        normalized = re.sub(
            r"(?:₹)?\b(\d+(?:\.\d+)?)\s*k\b",
            lambda m: f"₹{int(float(m.group(1)) * 1000)}",
            normalized,
            flags=re.IGNORECASE
        )

        # Standardize "2000 rupees", "Rs 2000", "inr 2000", "2000 rs", "2000 rupaye", "2000 रुपये" -> "₹2000"
        normalized = re.sub(
            r"(?:rs\.?|inr|rupaye|rupees?|rupiya|रुपये|रुपया|रुपिया|रु\.?)\s*(\d+(?:\.\d+)?)",
            r"₹\1",
            normalized,
            flags=re.IGNORECASE
        )
        normalized = re.sub(
            r"(\d+(?:\.\d+)?)\s*(?:rs\.?|inr|rupaye|rupees?|rupiya|रुपये|रुपया|रुपिया|रु\.?)(?!\w)",
            r"₹\1",
            normalized,
            flags=re.IGNORECASE
        )

        # Standardize hourly rates: "₹500 / hr", "₹500/hour", "500 per hour" -> "₹500/hr"
        normalized = re.sub(
            r"₹(\d+)\s*(?:/|\s*per\s*)(?:hr|hour|ghanta|taas)\b",
            r"₹\1/hr",
            normalized,
            flags=re.IGNORECASE
        )

        # 5. Compound words and written currency expressions
        # e.g. "two thousand" -> "2000", "three thousand" -> "3000", "do hazar" -> "2000", "teen hazar" -> "3000"
        normalized = re.sub(
            r"\b(?:under|below|budget|max|upto)\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|ek|do|teen|char|paanch)\s+(?:thousand|hazar|hazaar|हज़ार|हजार)\b",
            lambda m: cls._normalize_spoken_thousands(m.group(0)),
            normalized,
            flags=re.IGNORECASE
        )
        normalized = re.sub(
            r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|ek|do|teen|char|paanch)\s+(?:thousand|hazar|hazaar|हज़ार|हजार)\s*(?:rupees|rupaye|rs|₹)?\b",
            lambda m: cls._normalize_spoken_thousands(m.group(0)),
            normalized,
            flags=re.IGNORECASE
        )

        # 6. Normalize written number words (e.g. "for six people" -> "for 6 people", "about 3 hours" -> "about 3 hours")
        words = normalized.split()
        normalized_words = []
        for i, w in enumerate(words):
            clean_w = w.lower().strip(".,?!;:\"'()")
            # Guard English auxiliary verb 'do' (e.g. 'how do i', 'what do you')
            if clean_w == "do":
                prev_w = words[i-1].lower().strip(".,?!;:\"'()") if i > 0 else ""
                next_w = words[i+1].lower().strip(".,?!;:\"'()") if i + 1 < len(words) else ""
                if prev_w in ["how", "what", "where", "when", "why", "who", "which", "can", "could", "would", "should", "please", "pls", "to", "i", "we", "they", "you"] or next_w in ["i", "you", "we", "they", "it", "not", "have", "need", "want", "book", "find", "get", "see", "think"]:
                    normalized_words.append(w)
                    continue
            if clean_w == "don":
                next_w = words[i+1].lower().strip(".,?!;:\"'()") if i + 1 < len(words) else ""
                if next_w in ["t", "know", "have", "need", "care", "want", "worry"]:
                    normalized_words.append(w)
                    continue
            if clean_w in NUMBER_WORDS:
                digit = NUMBER_WORDS[clean_w]
                w_norm = w.lower().replace(clean_w, digit)
                normalized_words.append(w_norm)
            else:
                normalized_words.append(w)
        normalized = " ".join(normalized_words)

        # 7. Apply marketplace abbreviations & phonetic variants
        for pattern, replacement in MARKETPLACE_ABBREVIATIONS:
            if callable(replacement):
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            else:
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        # 8. Standardize time expressions like "from 5 to 8", "between 5 and 8", "5 to 8 pm"
        normalized = re.sub(
            r"\b(?:from\s+)?(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*(?:pm|am|p\.m\.|a\.m\.)?\b",
            lambda m: cls._standardize_time_range(m),
            normalized,
            flags=re.IGNORECASE
        )

        # 9. Clean redundant punctuation & whitespace
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"([!?.,])\1+", r"\1", normalized)

        return normalized.strip()

    @staticmethod
    def _normalize_spoken_thousands(text: str) -> str:
        """Converts expressions like 'under two thousand' -> 'under ₹2000' or '3 hazar' -> '₹3000'."""
        clean = text.lower()
        multiplier = 1000
        digit_val = 1
        for word, val in NUMBER_WORDS.items():
            if re.search(rf"\b{re.escape(word)}\b", clean):
                try:
                    digit_val = int(val)
                    break
                except ValueError:
                    pass
        total = digit_val * multiplier
        if "under" in clean or "below" in clean or "budget" in clean or "max" in clean or "upto" in clean:
            prefix = re.match(r"(under|below|budget|max|upto)", clean).group(1)
            return f"{prefix} ₹{total}"
        return f"₹{total}"

    @staticmethod
    def _standardize_time_range(match: re.Match) -> str:
        """Helper to cleanly format time ranges like '5 to 8' into '5 to 8' with contextual markers."""
        start_h = match.group(1)
        end_h = match.group(2)
        full_match = match.group(0).lower()
        meridiem = "PM" if "pm" in full_match else ("AM" if "am" in full_match else "")
        if meridiem:
            return f"{start_h} {meridiem} to {end_h} {meridiem}"
        return f"{start_h} to {end_h}"
