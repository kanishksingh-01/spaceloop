"""
SpaceLoop NLP Core Processing Layer - Schemas & Data Models
Defines canonical enums, dataclasses, and serialization utilities for the SpaceLoop NLP pipeline.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, time


class LanguageCode(str, Enum):
    EN = "en"               # English
    ENGLISH = "en"
    HI = "hi"               # Hindi (Devanagari)
    HINDI = "hi"
    MR = "mr"               # Marathi (Devanagari)
    MARATHI = "mr"
    GBM = "gbm"             # Garhwali (Central Pahari)
    GARHWALI = "gbm"
    KFY = "kfy"             # Kumaoni (Central Pahari)
    KUMAONI = "kfy"
    JNS = "jns"             # Jaunsari (Central Pahari)
    JAUNSARI = "jns"
    HI_LATN = "hi-Latn"     # Hinglish / Romanized Hindi
    HINGLISH = "hi-Latn"
    MR_LATN = "mr-Latn"     # Marathi-English / Romanized Marathi
    GBM_LATN = "gbm-Latn"   # Romanized Garhwali
    KFY_LATN = "kfy-Latn"   # Romanized Kumaoni
    UNKNOWN = "und"         # Undetermined


class IntentType(str, Enum):
    # Canonical SpaceLoop Marketplace Intents
    SEARCH_SPACE = "SEARCH_SPACE"                 # Search for space/room/desk/studio
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"     # Availability/slots for date/time
    BOOK_SPACE = "BOOK_SPACE"                     # Reserve, booking link, checkout
    ASK_PRICE = "ASK_PRICE"                       # Cost, rate calculations, pricing
    ASK_LOCATION = "ASK_LOCATION"                 # Address, neighborhood, map, directions
    ASK_AMENITIES = "ASK_AMENITIES"               # Wi-Fi, AC, screen, parking, etc.
    ASK_RULES = "ASK_RULES"                       # House rules, food, pets, cancellation
    CREATE_LISTING = "CREATE_LISTING"             # Host earnings, listing spaces
    EDIT_LISTING = "EDIT_LISTING"                 # Update existing listing, pricing, photos
    ASK_BOOKING_STATUS = "ASK_BOOKING_STATUS"     # Active booking, PIN, check-in status
    ASK_PAYMENT_STATUS = "ASK_PAYMENT_STATUS"     # UPI escrow deposit, refund status
    REPORT_FRAUD = "REPORT_FRAUD"                 # Suspicious behavior, dispute report
    LEGAL_SAFETY = "LEGAL_SAFETY"                 # Section 52, platform help, guidelines
    ASK_HELP = "ASK_HELP"                         # Help, platform overview, how it works
    COMPARE_SPACES = "COMPARE_SPACES"             # Compare spaces
    GENERAL_GREETING = "GENERAL_GREETING"         # Hello, hi, namaste, general chat
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED" # Low confidence / ambiguous query

    # Backward compatibility aliases
    SEARCH_PROPERTY = "SEARCH_SPACE"
    BOOK_PROPERTY = "BOOK_SPACE"
    GET_PRICING = "ASK_PRICE"
    INQUIRE_AMENITIES = "ASK_AMENITIES"
    INQUIRE_RULES = "ASK_RULES"
    HOST_MONETIZE = "CREATE_LISTING"
    GENERAL_CONVERSATION = "GENERAL_GREETING"


@dataclass
class LocationConstraint:
    raw_text: Optional[str] = None
    normalized_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    landmark: Optional[str] = None
    is_proximity_query: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PriceConstraint:
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    currency: str = "INR"
    is_hourly: bool = True
    is_qualitative_budget: bool = False
    qualitative_tag: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CapacityConstraint:
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    is_flexible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TimeWindow:
    date_str: Optional[str] = None          # "today", "tomorrow", "weekend", "2026-10-10"
    target_date: Optional[str] = None       # ISO YYYY-MM-DD
    time_range_name: Optional[str] = None   # "morning", "afternoon", "evening", "night"
    start_time_str: Optional[str] = None    # "17:00", "5 PM"
    end_time_str: Optional[str] = None      # "20:00", "8 PM"
    start_hour: Optional[int] = None        # 17
    end_hour: Optional[int] = None          # 20
    duration_hours: Optional[float] = None  # 3.0
    raw_text: Optional[str] = None

    @property
    def start_time(self) -> Optional[str]:
        return self.start_time_str

    @start_time.setter
    def start_time(self, val: Optional[str]):
        self.start_time_str = val

    @property
    def end_time(self) -> Optional[str]:
        return self.end_time_str

    @end_time.setter
    def end_time(self, val: Optional[str]):
        self.end_time_str = val

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


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
    # Rich structured details
    space_types: List[str] = field(default_factory=list)
    purpose_activities: List[str] = field(default_factory=list)
    soft_preferences: List[str] = field(default_factory=list)
    location_details: Optional[LocationConstraint] = None
    price_details: Optional[PriceConstraint] = None
    capacity_details: Optional[CapacityConstraint] = None
    time_window_details: Optional[TimeWindow] = None

    @property
    def capacity(self) -> Optional[int]:
        return self.guest_count

    @capacity.setter
    def capacity(self, val: Optional[int]):
        self.guest_count = val

    @property
    def price(self) -> Optional[float]:
        return self.max_price

    @price.setter
    def price(self, val: Optional[float]):
        self.max_price = val

    @property
    def primary_category(self) -> Optional[str]:
        return self.property_type

    @primary_category.setter
    def primary_category(self, val: Optional[str]):
        self.property_type = val

    @property
    def time_window(self) -> Optional[TimeWindow]:
        return self.time_window_details

    @time_window.setter
    def time_window(self, val: Optional[TimeWindow]):
        self.time_window_details = val

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.price_details and self.price_details.qualitative_tag:
            d["qualitative_price"] = self.price_details.qualitative_tag
        if self.price_details and self.price_details.max_price:
            d["budget_max"] = self.price_details.max_price
        elif self.max_price:
            d["budget_max"] = self.max_price
        # Omit None or empty fields for clean API responses
        return {k: v for k, v in d.items() if v is not None and v != [] and v != {}}


@dataclass
class QueryUnderstanding:
    """
    Intermediate Representation (IR) contract between NLP understanding and Search/Marketplace execution.
    """
    raw_query: str
    normalized_query: str
    semantic_query: str
    intent: str
    intent_confidence: float = 0.90
    language: str = "en"
    is_code_mixed: bool = False
    entities: ExtractedEntities = field(default_factory=ExtractedEntities)
    hard_constraints: Dict[str, Any] = field(default_factory=dict)
    soft_preferences: List[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)
    overall_confidence: float = 0.85
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "semantic_query": self.semantic_query,
            "intent": self.intent,
            "intent_confidence": round(self.intent_confidence, 4),
            "language": self.language,
            "is_code_mixed": self.is_code_mixed,
            "entities": self.entities.to_dict(),
            "hard_constraints": self.hard_constraints,
            "soft_preferences": self.soft_preferences,
            "needs_clarification": self.needs_clarification,
            "clarification_prompt": self.clarification_prompt,
            "missing_fields": self.missing_fields,
            "overall_confidence": round(self.overall_confidence, 4),
            "metadata": self.metadata
        }


@dataclass
class StructuredNLPResult:
    language: str
    secondary_languages: List[str] = field(default_factory=list)
    is_code_mixed: bool = False
    normalized_text: str = ""
    intent: str = IntentType.CLARIFICATION_NEEDED.value
    confidence: float = 0.50
    entities: Dict[str, Any] = field(default_factory=dict)
    query_understanding: Optional[QueryUnderstanding] = None
    raw_query: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res = {
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
        if self.query_understanding:
            res["queryUnderstanding"] = self.query_understanding.to_dict()
        return res
