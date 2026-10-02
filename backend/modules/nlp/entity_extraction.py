"""
SpaceLoop Entity Extraction & Normalization Service
Extracts and normalizes structured domain entities (locations, space types, purposes,
capacities, prices, dates, times, durations, amenities, and soft preferences) from multilingual user queries.
Enforces domain range constraints without hallucinations.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple

from backend.modules.nlp.schemas import (
    ExtractedEntities,
    LocationConstraint,
    PriceConstraint,
    CapacityConstraint,
    TimeWindow
)


# Canonical Indian Tech Hubs & Cities (including Uttarakhand, Maharashtra, Delhi NCR, Bengaluru)
KNOWN_HUBS_MAP: Dict[str, Tuple[str, str, str]] = {
    # Key: (Normalized Name, City, State)
    # Pune & Maharashtra
    "kharadi": ("Kharadi, Pune", "Pune", "Maharashtra"),
    "खराडी": ("Kharadi, Pune", "Pune", "Maharashtra"),
    "wagholi": ("Wagholi, Pune", "Pune", "Maharashtra"),
    "वाघोली": ("Wagholi, Pune", "Pune", "Maharashtra"),
    "viman nagar": ("Viman Nagar, Pune", "Pune", "Maharashtra"),
    "विमान नगर": ("Viman Nagar, Pune", "Pune", "Maharashtra"),
    "kothrud": ("Kothrud, Pune", "Pune", "Maharashtra"),
    "कोथरूड": ("Kothrud, Pune", "Pune", "Maharashtra"),
    "aundh": ("Aundh, Pune", "Pune", "Maharashtra"),
    "औंध": ("Aundh, Pune", "Pune", "Maharashtra"),
    "baner": ("Baner, Pune", "Pune", "Maharashtra"),
    "बाणेर": ("Baner, Pune", "Pune", "Maharashtra"),
    "hinjewadi": ("Hinjewadi, Pune", "Pune", "Maharashtra"),
    "hinjawadi": ("Hinjewadi, Pune", "Pune", "Maharashtra"),
    "हिंजवडी": ("Hinjewadi, Pune", "Pune", "Maharashtra"),
    "shivajinagar": ("Shivajinagar, Pune", "Pune", "Maharashtra"),
    "शिवाजीनगर": ("Shivajinagar, Pune", "Pune", "Maharashtra"),
    "pune": ("Pune", "Pune", "Maharashtra"),
    "punyat": ("Pune", "Pune", "Maharashtra"),
    "पुणे": ("Pune", "Pune", "Maharashtra"),
    "पुण्यात": ("Pune", "Pune", "Maharashtra"),
    "mumbai": ("Mumbai", "Mumbai", "Maharashtra"),
    "mumbait": ("Mumbai", "Mumbai", "Maharashtra"),
    "मुंबई": ("Mumbai", "Mumbai", "Maharashtra"),
    "मुंबईत": ("Mumbai", "Mumbai", "Maharashtra"),
    "bandra": ("Bandra, Mumbai", "Mumbai", "Maharashtra"),
    "वांद्रे": ("Bandra, Mumbai", "Mumbai", "Maharashtra"),
    "powai": ("Powai, Mumbai", "Mumbai", "Maharashtra"),
    "पवई": ("Powai, Mumbai", "Mumbai", "Maharashtra"),
    "andheri": ("Andheri, Mumbai", "Mumbai", "Maharashtra"),
    "अंधेरी": ("Andheri, Mumbai", "Mumbai", "Maharashtra"),
    "dadar": ("Dadar, Mumbai", "Mumbai", "Maharashtra"),
    "दादर": ("Dadar, Mumbai", "Mumbai", "Maharashtra"),
    # Delhi NCR
    "hauz khas": ("Hauz Khas, Delhi", "New Delhi", "Delhi"),
    "हौज़ खास": ("Hauz Khas, Delhi", "New Delhi", "Delhi"),
    "iit delhi": ("IIT Delhi, New Delhi", "New Delhi", "Delhi"),
    "iit gate": ("IIT Delhi, New Delhi", "New Delhi", "Delhi"),
    "iit": ("IIT Delhi, New Delhi", "New Delhi", "Delhi"),
    "north campus": ("North Campus, Delhi", "Delhi", "Delhi"),
    "south campus": ("South Campus, Delhi", "Delhi", "Delhi"),
    "connaught place": ("Connaught Place, Delhi", "New Delhi", "Delhi"),
    "cp": ("Connaught Place, Delhi", "New Delhi", "Delhi"),
    "nehru place": ("Nehru Place, Delhi", "New Delhi", "Delhi"),
    "delhi": ("Delhi", "New Delhi", "Delhi"),
    "new delhi": ("New Delhi", "New Delhi", "Delhi"),
    "दिल्ली": ("Delhi", "New Delhi", "Delhi"),
    "noida": ("Noida", "Noida", "Uttar Pradesh"),
    "नोएडा": ("Noida", "Noida", "Uttar Pradesh"),
    "gurgaon": ("Gurgaon", "Gurgaon", "Haryana"),
    "gurugram": ("Gurgaon", "Gurgaon", "Haryana"),
    "गुड़गांव": ("Gurgaon", "Gurgaon", "Haryana"),
    "cyber city": ("Cyber City, Gurgaon", "Gurgaon", "Haryana"),
    # Bengaluru
    "koramangala": ("Koramangala, Bengaluru", "Bengaluru", "Karnataka"),
    "कोरमंगला": ("Koramangala, Bengaluru", "Bengaluru", "Karnataka"),
    "indiranagar": ("Indiranagar, Bengaluru", "Bengaluru", "Karnataka"),
    "इंदिरानगर": ("Indiranagar, Bengaluru", "Bengaluru", "Karnataka"),
    "whitefield": ("Whitefield, Bengaluru", "Bengaluru", "Karnataka"),
    "hsr layout": ("HSR Layout, Bengaluru", "Bengaluru", "Karnataka"),
    "electronic city": ("Electronic City, Bengaluru", "Bengaluru", "Karnataka"),
    "bangalore": ("Bengaluru", "Bengaluru", "Karnataka"),
    "bengaluru": ("Bengaluru", "Bengaluru", "Karnataka"),
    "बेंगळुरू": ("Bengaluru", "Bengaluru", "Karnataka"),
    "बेंगलुरु": ("Bengaluru", "Bengaluru", "Karnataka"),
    # Uttarakhand / Pahari Hubs
    "dehradun": ("Dehradun", "Dehradun", "Uttarakhand"),
    "देहरादून": ("Dehradun", "Dehradun", "Uttarakhand"),
    "rishikesh": ("Rishikesh", "Rishikesh", "Uttarakhand"),
    "ऋषिकेश": ("Rishikesh", "Rishikesh", "Uttarakhand"),
    "mussoorie": ("Mussoorie", "Mussoorie", "Uttarakhand"),
    "मसूरी": ("Mussoorie", "Mussoorie", "Uttarakhand"),
    "nainital": ("Nainital", "Nainital", "Uttarakhand"),
    "नैनीताल": ("Nainital", "Nainital", "Uttarakhand"),
    "haldwani": ("Haldwani", "Haldwani", "Uttarakhand"),
    "almora": ("Almora", "Almora", "Uttarakhand"),
    "haridwar": ("Haridwar", "Haridwar", "Uttarakhand")
}

# Space Type Lexicon
SPACE_TYPES_MAP: Dict[str, str] = {
    # Workspace
    "workspace": "Workspace", "work space": "Workspace", "office": "Workspace",
    "private office": "Workspace", "desk": "Workspace", "coworking": "Workspace",
    "co-working": "Workspace", "desk space": "Workspace", "कार्यालय": "Workspace",
    "दफ्तर": "Workspace", "table": "Workspace", "वर्कस्पेस": "Workspace",
    "ऑफिस": "Workspace", "काम करण्याची जागा": "Workspace",
    # Meeting
    "meeting": "Meeting", "meeting room": "Meeting", "conference": "Meeting",
    "conference room": "Meeting", "boardroom": "Meeting", "collab": "Meeting",
    "discussion": "Meeting", "बैठक": "Meeting", "room": "Meeting",
    "कमरा": "Meeting", "कमरे": "Meeting", "खोली": "Meeting", "खोल्या": "Meeting",
    # Studio
    "studio": "Studio", "podcast": "Studio", "podcast studio": "Studio",
    "recording": "Studio", "photography": "Studio", "photo studio": "Studio",
    "photo": "Studio", "vocal": "Studio", "film": "Studio", "shoot": "Studio",
    "शूट": "Studio", "स्टूडियो": "Studio", "स्टुडिओ": "Studio",
    # Study
    "study": "Study", "study room": "Study", "library": "Study", "quiet pod": "Study",
    "study desk": "Study", "padhai": "Study", "अभ्यास": "Study", "वाचनालय": "Study",
    "कक्षा": "Study", "पुस्तकालय": "Study",
    # Workshop
    "workshop": "Workshop", "maker": "Workshop", "maker space": "Workshop",
    "hardware": "Workshop", "proto": "Workshop", "वर्कशॉप": "Workshop",
    # Retail / Pop-up
    "retail": "Retail", "pop-up": "Retail", "popup": "Retail", "store": "Retail",
    "stall": "Retail", "boutique": "Retail", "दुकान": "Retail", "shop": "Retail",
    "curb": "Retail",
    # Storage / Garage
    "storage": "Storage", "warehouse": "Storage", "garage": "Storage",
    "गैराज": "Storage", "गोदाम": "Storage", "space storage": "Storage",
    # Event / Gathering
    "event": "Event", "hall": "Event", "gathering": "Event", "terrace": "Event",
    "rooftop": "Event", "party": "Event", "birthday": "Event", "cafe": "Event",
    "cafe-like": "Event", "टैरेस": "Event", "सभागृह": "Event", "auditorium": "Event"
}

# Purpose / Activity Mappings
PURPOSE_ACTIVITIES_MAP: Dict[str, Tuple[str, str, List[str]]] = {
    # Key: (Purpose label, Inferred Category, Soft traits)
    "shoot a short film": ("Film Shooting", "Studio", ["good lighting", "quiet", "spacious"]),
    "shoot film": ("Film Shooting", "Studio", ["good lighting", "quiet", "spacious"]),
    "film shoot": ("Film Shooting", "Studio", ["good lighting", "quiet"]),
    "photo shoot": ("Photo Shoot", "Studio", ["good lighting", "sunlit", "backdrop"]),
    "photography": ("Photo Shoot", "Studio", ["good lighting", "sunlit"]),
    "podcast recording": ("Podcast Recording", "Studio", ["quiet", "soundproof", "acoustic"]),
    "podcast": ("Podcast Recording", "Studio", ["quiet", "soundproof", "acoustic"]),
    "record podcast": ("Podcast Recording", "Studio", ["quiet", "soundproof", "acoustic"]),
    "birthday party": ("Birthday Party", "Event", ["cafe-like", "spacious", "festive"]),
    "birthday": ("Birthday Party", "Event", ["cafe-like", "spacious"]),
    "party": ("Event Gathering", "Event", ["spacious", "music friendly"]),
    "team meeting": ("Team Meeting", "Meeting", ["whiteboard", "screen", "wifi"]),
    "board meeting": ("Executive Board Meeting", "Meeting", ["whiteboard", "screen", "quiet"]),
    "study session": ("Study & Exam Prep", "Study", ["quiet", "peaceful", "power outlet"]),
    "hackathon": ("Hackathon & Build", "Workspace", ["fast wifi", "power backup", "whiteboard"]),
    "quiet place to work": ("Focused Work", "Workspace", ["quiet", "peaceful", "wifi"]),
    "silent work": ("Focused Work", "Workspace", ["quiet", "peaceful"]),
    "work remotely": ("Remote Work", "Workspace", ["wifi", "ergonomic", "quiet"]),
    "hardware tinkering": ("Hardware Prototyping", "Workshop", ["tools", "power circuits"]),
}

# Amenities Dictionary
KNOWN_AMENITIES_MAP: Dict[str, str] = {
    "wifi": "High-Speed Wi-Fi", "wi-fi": "High-Speed Wi-Fi", "fiber": "High-Speed Wi-Fi",
    "internet": "High-Speed Wi-Fi", "fast wifi": "High-Speed Wi-Fi",
    "ac": "Air Conditioning", "air condition": "Air Conditioning",
    "air conditioning": "Air Conditioning", "power backup": "Power Backup",
    "inverter": "Power Backup", "generator": "Power Backup", "whiteboard": "Whiteboard",
    "marker": "Whiteboard", "projector": "Projector", "screen": "Presentation Monitor",
    "presentation monitor": "Presentation Monitor", "tv": "Presentation Monitor",
    "monitor": "Presentation Monitor", "parking": "Parking Available",
    "parking spot": "Parking Available", "ergonomic": "Ergonomic Chairs",
    "ergonomic chair": "Ergonomic Chairs", "coffee": "Coffee/Tea Station",
    "tea": "Coffee/Tea Station", "water": "Drinking Water", "drinking water": "Drinking Water",
    "soundproof": "Soundproofing & Acoustic Foam", "acoustic": "Soundproofing & Acoustic Foam",
    "good lighting": "Natural & Studio Lighting", "studio lighting": "Natural & Studio Lighting",
    "lighting": "Natural & Studio Lighting", "sunlit": "Natural Daylight",
    "ev charger": "EV Charging Station",
    # Indic Devanagari Amenities
    "वायफाय": "High-Speed Wi-Fi", "वाईफाई": "High-Speed Wi-Fi", "इंटरनेट": "High-Speed Wi-Fi",
    "एसी": "Air Conditioning", "वातानुकूलित": "Air Conditioning", "वातानुकूलन": "Air Conditioning",
    "पार्किंग": "Parking Available", "व्हाइटबोर्ड": "Whiteboard", "प्रोजेक्टर": "Projector",
    "मॉनिटर": "Presentation Monitor", "स्क्रीन": "Presentation Monitor", "पाणी": "Drinking Water",
    "पानी": "Drinking Water", "चहा": "Coffee/Tea Station", "चाय": "Coffee/Tea Station",
    "कॉफी": "Coffee/Tea Station", "बिजली बैकअप": "Power Backup", "वीज बैकअप": "Power Backup"
}

# Soft Qualitative Traits (Influence Ranking & Similarity rather than Hard Boolean Rejections)
KNOWN_SOFT_TRAITS = [
    "quiet", "silent", "peaceful", "soundproof", "acoustic",
    "good lighting", "sunlit", "bright", "natural light", "ambient",
    "spacious", "huge", "large", "cozy", "compact",
    "cafe-like", "cafe vibe", "chill", "creative",
    "near metro", "near iit", "near station", "central",
    "affordable", "cheap", "budget-friendly", "low cost", "pocket friendly"
]


class EntityExtractionService:
    """
    Extracts and normalizes domain entities from clean normalized text into strongly-typed objects.
    """

    @classmethod
    def extract_entities(cls, text: str, context_data: Optional[Dict[str, Any]] = None) -> ExtractedEntities:
        if not text:
            return ExtractedEntities()

        clean = text.lower().strip()
        entities = ExtractedEntities()

        # ---------------------------------------------------------------------
        # 1. LISTING ID
        # ---------------------------------------------------------------------
        id_match = re.search(r"\b(?:space|room|listing|id)\s*#?\s*(\d+)\b", clean)
        if not id_match:
            id_match = re.search(r"#(\d+)\b", clean)
        if id_match:
            try:
                lid = int(id_match.group(1))
                if 1 <= lid <= 1_000_000:
                    entities.listing_id = lid
            except ValueError:
                pass
        elif context_data and context_data.get("space_id"):
            try:
                entities.listing_id = int(context_data["space_id"])
            except (ValueError, TypeError):
                pass

        # ---------------------------------------------------------------------
        # 2. LOCATION CONSTRAINT
        # ---------------------------------------------------------------------
        loc_constraint = cls._extract_location(clean)
        if loc_constraint:
            entities.location = loc_constraint.normalized_name or loc_constraint.raw_text
            entities.location_details = loc_constraint

        # ---------------------------------------------------------------------
        # 3. CAPACITY CONSTRAINT
        # ---------------------------------------------------------------------
        cap_constraint = cls._extract_capacity(clean)
        if cap_constraint:
            entities.guest_count = cap_constraint.min_capacity
            entities.capacity_details = cap_constraint

        # ---------------------------------------------------------------------
        # 4. PRICE & BUDGET CONSTRAINT
        # ---------------------------------------------------------------------
        price_constraint = cls._extract_price(clean)
        if price_constraint:
            entities.max_price = price_constraint.max_price
            entities.price_details = price_constraint

        # ---------------------------------------------------------------------
        # 5. DATE, TIME WINDOW & DURATION
        # ---------------------------------------------------------------------
        time_window = cls._extract_time_window(clean)
        if time_window:
            entities.date_str = time_window.date_str
            entities.time_range = time_window.time_range_name
            entities.duration_hours = time_window.duration_hours
            entities.time_window_details = time_window

        # ---------------------------------------------------------------------
        # 6. SPACE TYPE, CATEGORY & PURPOSE
        # ---------------------------------------------------------------------
        categories, purposes, inferred_soft = cls._extract_category_and_purpose(clean)
        if categories:
            entities.space_types = categories
            entities.property_type = categories[0]
        if purposes:
            entities.purpose_activities = purposes

        # ---------------------------------------------------------------------
        # 7. AMENITIES
        # ---------------------------------------------------------------------
        found_amenities = cls._extract_amenities(clean)
        if found_amenities:
            entities.amenities = found_amenities

        # ---------------------------------------------------------------------
        # 8. SOFT PREFERENCES / QUALITATIVE TRAITS
        # ---------------------------------------------------------------------
        soft_traits = cls._extract_soft_traits(clean)
        soft_traits.extend(inferred_soft)
        if soft_traits:
            entities.soft_preferences = sorted(list(set(soft_traits)))

        return entities

    @classmethod
    def _extract_location(cls, clean: str) -> Optional[LocationConstraint]:
        # Check known hubs
        for hub_key, (norm_name, city, state) in sorted(KNOWN_HUBS_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if any('\u0900' <= c <= '\u097f' for c in hub_key):
                pat = rf"(?:^|[^\u0900-\u097f]){re.escape(hub_key)}(?:$|[^\u0900-\u097f])"
            else:
                pat = rf"\b{re.escape(hub_key)}\b"

            if re.search(pat, clean):
                is_near = bool(re.search(rf"\b(?:near|around|close\s+to|in)\s+{re.escape(hub_key)}\b", clean))
                return LocationConstraint(
                    raw_text=hub_key,
                    normalized_name=norm_name,
                    city=city,
                    state=state,
                    is_proximity_query=is_near
                )

        # Check generic proximity landmarks (e.g. "near the metro", "around me", "near station")
        if re.search(r"\b(?:near\s+(?:the\s+)?metro|near\s+metro\s+station|metro\s+ke\s+paas)\b", clean):
            return LocationConstraint(
                raw_text="metro",
                normalized_name="Near Metro Station",
                landmark="Metro Station",
                is_proximity_query=True
            )
        if "around me" in clean or "near me" in clean or "pass me" in clean:
            return LocationConstraint(
                raw_text="around me",
                normalized_name="Nearby Current Location",
                is_proximity_query=True
            )

        return None

    @classmethod
    def _extract_capacity(cls, clean: str) -> Optional[CapacityConstraint]:
        # Patterns like "for 6 people", "6 persons", "a group of 10", "team of 12", "need room for around 20", "6 pax"
        cap_match = re.search(
            r"(?:for\s+|group\s+of\s+|team\s+of\s+|around\s+|approx\s+)?(\d+)\s*(?:people|persons?|guests?|members?|attendees?|seats?|pax|log(?:on)?|vyakti(?:yon)?|jan(?:on|oon|ूं)?|mansen|lok|लोकांसाठी|लोकांना|लोकां|लोगों|लोग|जनूं|जना|व्यक्ति|व्यक्तियों)(?!\w)",
            clean
        )
        if cap_match:
            try:
                cap_val = int(cap_match.group(1))
                if 1 <= cap_val <= 500:
                    is_flex = "around" in clean or "approx" in clean or "about" in clean
                    return CapacityConstraint(min_capacity=cap_val, is_flexible=is_flex)
            except ValueError:
                pass

        # Standalone "for 6", "for 10" in space search context
        standalone = re.search(r"\bfor\s+(\d+)\b", clean)
        if standalone:
            try:
                v = int(standalone.group(1))
                if 1 <= v <= 200:
                    return CapacityConstraint(min_capacity=v)
            except ValueError:
                pass

        return None

    @classmethod
    def _extract_price(cls, clean: str) -> Optional[PriceConstraint]:
        # 1. Price range: "between 1000 and 3000", "1000 to 3000 rs"
        range_match = re.search(r"\b(?:between|from)\s*(?:₹)?\s*(\d+)\s*(?:and|to|-)\s*(?:₹)?\s*(\d+)\b", clean)
        if range_match:
            try:
                min_p = float(range_match.group(1))
                max_p = float(range_match.group(2))
                if min_p > max_p:
                    min_p, max_p = max_p, min_p
                return PriceConstraint(min_price=min_p, max_price=max_p, currency="INR")
            except ValueError:
                pass

        # 2. Upper bound max price: "under ₹3000", "below 2000", "under 2k", "upto ₹2000", "max ₹3000"
        price_match = re.search(r"₹\s*(\d+(?:\.\d+)?)", clean)
        if not price_match:
            price_match = re.search(
                r"\b(?:under|below|max|budget(?:\s+of)?|upto|less\s+than|within|around)\s*(?:₹)?\s*(\d+(?:\.\d+)?)\b",
                clean
            )
        if price_match:
            try:
                price_val = float(price_match.group(1))
                if price_val >= 5.0:
                    is_hr = "/hr" in clean or "per hour" in clean or "hourly" in clean or price_val <= 1500
                    return PriceConstraint(max_price=price_val, currency="INR", is_hourly=is_hr)
            except ValueError:
                pass

        # 3. Qualitative budget terms (e.g. "cheap", "affordable", "budget-friendly", "low cost")
        for tag in ["affordable", "cheap", "budget-friendly", "low cost", "budget", "सस्ता", "स्वस्त"]:
            if tag in clean:
                return PriceConstraint(
                    is_qualitative_budget=True,
                    qualitative_tag=tag,
                    currency="INR"
                )

        return None

    @classmethod
    def _extract_time_window(cls, clean: str) -> Optional[TimeWindow]:
        tw = TimeWindow()
        has_data = False
        now = datetime.now(timezone.utc)

        # Date extraction
        if "tomorrow" in clean or "kal" in clean or "udya" in clean or "bhol" in clean:
            tw.date_str = "tomorrow"
            tw.target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            has_data = True
        elif "today" in clean or "aaj" in clean:
            tw.date_str = "today"
            tw.target_date = now.strftime("%Y-%m-%d")
            has_data = True
        elif "weekend" in clean or "shaniwar" in clean or "ravivar" in clean:
            tw.date_str = "weekend"
            days_to_sat = (5 - now.weekday()) % 7
            if days_to_sat == 0 and now.hour > 18:
                days_to_sat = 7
            tw.target_date = (now + timedelta(days=days_to_sat)).strftime("%Y-%m-%d")
            has_data = True
        else:
            iso_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", clean)
            if iso_match:
                tw.date_str = iso_match.group(1)
                tw.target_date = iso_match.group(1)
                has_data = True

        # Time of day / range names
        if "morning" in clean or "subah" in clean or "sakali" in clean:
            tw.time_range_name = "morning"
            tw.start_hour = 9
            tw.end_hour = 12
            has_data = True
        elif "afternoon" in clean or "dopahar" in clean or "dupari" in clean:
            tw.time_range_name = "afternoon"
            tw.start_hour = 13
            tw.end_hour = 17
            has_data = True
        elif "evening" in clean or "shaam" in clean or "sandhyakali" in clean:
            tw.time_range_name = "evening"
            tw.start_hour = 17
            tw.end_hour = 21
            has_data = True
        elif "night" in clean or "raat" in clean or "ratri" in clean or "late night" in clean:
            tw.time_range_name = "night"
            tw.start_hour = 20
            tw.end_hour = 23
            has_data = True

        # Explicit time range (e.g. "from 5 to 8", "between 5 and 8", "5pm to 8pm", "5:00 to 8:00")
        range_match = re.search(r"\b(?:from\s+)?(\d{1,2})(?::\d{2})?\s*(pm|am)?\s*(?:to|-)\s*(\d{1,2})(?::\d{2})?\s*(pm|am)?\b", clean)
        if range_match:
            try:
                start_h = int(range_match.group(1))
                start_m = range_match.group(2)
                end_h = int(range_match.group(3))
                end_m = range_match.group(4)

                # Convert to 24-hour clock
                if (start_m == "pm" or end_m == "pm") and start_h < 12 and (start_m == "pm" or (start_h in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11) and end_m == "pm" and start_h < end_h)):
                    start_h += 12
                elif (start_h in (5, 6, 7, 8, 9, 10, 11) and "evening" in clean and start_h < 12):
                    start_h += 12
                elif start_h in (1, 2, 3, 4, 5, 6, 7, 8) and ("afternoon" in clean or "evening" in clean or start_h <= 8):
                    if start_h < 12:
                        start_h += 12

                if (end_m == "pm" or start_m == "pm") and end_h < 12:
                    end_h += 12
                elif end_h <= start_h and end_h < 12:
                    end_h += 12
                elif end_h in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11) and ("afternoon" in clean or "evening" in clean or end_h <= 8):
                    if end_h < 12:
                        end_h += 12

                if 0 <= start_h <= 24 and 0 <= end_h <= 24 and end_h > start_h:
                    tw.start_hour = start_h
                    tw.end_hour = end_h
                    tw.start_time_str = f"{start_h:02d}:00"
                    tw.end_time_str = f"{end_h:02d}:00"
                    tw.duration_hours = float(end_h - start_h)
                    has_data = True
            except ValueError:
                pass

        # "After 6 PM", "after 18:00"
        after_match = re.search(r"\bafter\s+(\d{1,2})\s*(?:pm|am|:00)?\b", clean)
        if after_match and not tw.start_hour:
            try:
                h = int(after_match.group(1))
                if "pm" in clean and h < 12:
                    h += 12
                elif h in (5, 6, 7, 8, 9, 10, 11) and h < 12:
                    h += 12
                tw.start_hour = h
                tw.start_time_str = f"{h:02d}:00"
                tw.duration_hours = 2.0
                tw.end_hour = min(23, h + 2)
                tw.end_time_str = f"{tw.end_hour:02d}:00"
                has_data = True
            except ValueError:
                pass

        # Explicit duration hours: "for 3 hours", "for a 4-hour", "about 3 hours", "3 hrs"
        dur_match = re.search(r"\b(?:for\s+(?:a\s+)?|about\s+|around\s+)?(\d+(?:\.\d+)?)\s*[-\s]?(?:hours?|hrs?|ghante|taas|ghant)\b", clean)
        if dur_match and not tw.duration_hours:
            try:
                dur = float(dur_match.group(1))
                if 0.5 <= dur <= 168.0:
                    tw.duration_hours = dur
                    has_data = True
            except ValueError:
                pass
        elif "half day" in clean or "aadha din" in clean:
            tw.duration_hours = 4.0
            has_data = True
        elif "full day" in clean or "pura din" in clean or "purna divas" in clean:
            tw.duration_hours = 8.0
            has_data = True

        if has_data:
            tw.raw_text = clean
            return tw
        return None

    @classmethod
    def _extract_category_and_purpose(cls, clean: str) -> Tuple[List[str], List[str], List[str]]:
        categories = []
        purposes = []
        soft_inferred = []

        # Check purpose activities first
        for purpose_key, (purpose_name, inferred_cat, softs) in sorted(PURPOSE_ACTIVITIES_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if purpose_key in clean:
                purposes.append(purpose_name)
                if inferred_cat not in categories:
                    categories.append(inferred_cat)
                soft_inferred.extend(softs)

        # Check category map
        for type_key, canonical_type in sorted(SPACE_TYPES_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if any('\u0900' <= c <= '\u097f' for c in type_key):
                pat = rf"(?:^|[^\u0900-\u097f]){re.escape(type_key)}(?:$|[^\u0900-\u097f])"
            else:
                pat = rf"\b{re.escape(type_key)}\b"

            if re.search(pat, clean):
                if canonical_type not in categories:
                    categories.append(canonical_type)

        return categories, purposes, soft_inferred

    @classmethod
    def _extract_amenities(cls, clean: str) -> List[str]:
        found = set()
        for kw, canonical_name in KNOWN_AMENITIES_MAP.items():
            if any('\u0900' <= c <= '\u097f' for c in kw):
                pat = rf"(?:^|[^\u0900-\u097f]){re.escape(kw)}(?:$|[^\u0900-\u097f])"
            else:
                pat = rf"\b{re.escape(kw)}\b"

            if re.search(pat, clean):
                found.add(canonical_name)
        if "High-Speed Wi-Fi" in found:
            found.add("Wi-Fi")
        if "Air Conditioning" in found:
            found.add("AC")
        return sorted(list(found))

    @classmethod
    def _extract_soft_traits(cls, clean: str) -> List[str]:
        traits = []
        for trait in KNOWN_SOFT_TRAITS:
            if re.search(rf"\b{re.escape(trait)}\b", clean):
                traits.append(trait)
        return traits
