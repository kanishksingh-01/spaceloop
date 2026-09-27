"""
SpaceLoop NLP Core Processing Layer - Schemas & Data Models
Defines canonical enums, dataclasses, and serialization utilities for the NLP pipeline.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


class LanguageCode(str, Enum):
    EN = "en"               # English
    HI = "hi"               # Hindi (Devanagari)
    MR = "mr"               # Marathi (Devanagari)
    GBM = "gbm"             # Garhwali (Central Pahari)
    KFY = "kfy"             # Kumaoni (Central Pahari)
    JNS = "jns"             # Jaunsari (Central Pahari)
    HI_LATN = "hi-Latn"     # Hinglish / Romanized Hindi
    MR_LATN = "mr-Latn"     # Marathi-English / Romanized Marathi
    GBM_LATN = "gbm-Latn"   # Romanized Garhwali
    KFY_LATN = "kfy-Latn"   # Romanized Kumaoni
    UNKNOWN = "und"         # Undetermined


class IntentType(str, Enum):
    # Canonical SpaceLoop Part 4 Intents
    SEARCH_PROPERTY = "SEARCH_PROPERTY"           # Search for space/room/desk
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"     # Availability/slots for date/time
    BOOK_PROPERTY = "BOOK_PROPERTY"               # Reserve, booking link, checkout
    ASK_PRICE = "ASK_PRICE"                       # Cost, rate calculations
    ASK_LOCATION = "ASK_LOCATION"                 # Address, neighborhood, map, directions
    ASK_AMENITIES = "ASK_AMENITIES"               # Wi-Fi, AC, screen, parking, etc.
    CREATE_LISTING = "CREATE_LISTING"             # Host earnings, listing spaces
    EDIT_LISTING = "EDIT_LISTING"                 # Update existing listing, pricing, photos
    ASK_BOOKING_STATUS = "ASK_BOOKING_STATUS"     # Active booking, PIN, check-in status
    ASK_PAYMENT_STATUS = "ASK_PAYMENT_STATUS"     # UPI escrow deposit, refund status
    REPORT_FRAUD = "REPORT_FRAUD"                 # Suspicious behavior, dispute report
    ASK_HELP = "ASK_HELP"                         # Section 52, platform help, guidelines
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION" # Hello, hi, namaste, general chat
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED" # Low confidence / ambiguous query

    # Backward compatibility aliases for Part 2 & Part 3 suites
    SEARCH_SPACE = "SEARCH_SPACE"
    BOOK_SPACE = "BOOK_SPACE"
    GET_PRICING = "GET_PRICING"
    INQUIRE_AMENITIES = "INQUIRE_AMENITIES"
    INQUIRE_RULES = "INQUIRE_RULES"
    COMPARE_SPACES = "COMPARE_SPACES"
    HOST_MONETIZE = "HOST_MONETIZE"
    LEGAL_SAFETY = "LEGAL_SAFETY"
    GENERAL_GREETING = "GENERAL_GREETING"


@dataclass
class ExtractedEntities:
    location: Optional[str] = None
    property_type: Optional[str] = None
    guest_count: Optional[int] = None
    max_price: Optional[float] = None
    duration_hours: Optional[float] = None
    date_str: Optional[str] = None
    time_range: Optional[str] = None
    listing_id: Optional[int] = None
    amenities: List[str] = field(default_factory=list)
    unrecognized_tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Omit None fields for clean API responses
        return {k: v for k, v in d.items() if v is not None and v != []}


@dataclass
class StructuredNLPResult:
    language: str
    secondary_languages: List[str] = field(default_factory=list)
    is_code_mixed: bool = False
    normalized_text: str = ""
    intent: str = IntentType.CLARIFICATION_NEEDED.value
    confidence: float = 0.50
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_query: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "secondaryLanguages": self.secondary_languages,
            "isCodeMixed": self.is_code_mixed,
            "normalizedText": self.normalized_text,
            "intent": self.intent,
            "confidence": round(self.confidence, 4),
            "entities": self.entities,
            "rawQuery": self.raw_query,
            "metadata": self.metadata
        }
