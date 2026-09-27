"""
SpaceLoop Entity Extraction & Strict Validation Service
Extracts and strictly validates domain entities (locations, space types, capacities,
pricing, durations, dates, and listing IDs) from multilingual normalized queries.
Guarantees zero hallucinations and enforces domain range constraints.
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from backend.modules.nlp.schemas import ExtractedEntities


# Canonical Indian Tech Hubs & Cities (including Uttarakhand & Maharashtra)
KNOWN_HUBS_MAP: Dict[str, str] = {
    # Pune & Maharashtra
    "kharadi": "Kharadi, Pune",
    "wagholi": "Wagholi, Pune",
    "viman nagar": "Viman Nagar, Pune",
    "kothrud": "Kothrud, Pune",
    "aundh": "Aundh, Pune",
    "baner": "Baner, Pune",
    "hinjewadi": "Hinjewadi, Pune",
    "hinjawadi": "Hinjewadi, Pune",
    "shivajinagar": "Shivajinagar, Pune",
    "pune": "Pune",
    "पुणे": "Pune",
    "mumbai": "Mumbai",
    "मुंबई": "Mumbai",
    "bandra": "Bandra, Mumbai",
    "powai": "Powai, Mumbai",
    "andheri": "Andheri, Mumbai",
    "dadar": "Dadar, Mumbai",
    # Delhi NCR
    "hauz khas": "Hauz Khas, Delhi",
    "iit delhi": "IIT Delhi, New Delhi",
    "north campus": "North Campus, Delhi",
    "south campus": "South Campus, Delhi",
    "connaught place": "Connaught Place, Delhi",
    "nehru place": "Nehru Place, Delhi",
    "delhi": "Delhi",
    "new delhi": "New Delhi",
    "दिल्ली": "Delhi",
    "noida": "Noida",
    "gurgaon": "Gurgaon",
    "cyber city": "Cyber City, Gurgaon",
    # Bengaluru
    "koramangala": "Koramangala, Bengaluru",
    "indiranagar": "Indiranagar, Bengaluru",
    "whitefield": "Whitefield, Bengaluru",
    "hsr layout": "HSR Layout, Bengaluru",
    "electronic city": "Electronic City, Bengaluru",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "बेंगळुरू": "Bengaluru",
    # Uttarakhand / Pahari Hubs
    "dehradun": "Dehradun",
    "देहरादून": "Dehradun",
    "rishikesh": "Rishikesh",
    "ऋषिकेश": "Rishikesh",
    "mussoorie": "Mussoorie",
    "मसूरी": "Mussoorie",
    "nainital": "Nainital",
    "नैनीताल": "Nainital",
    "haldwani": "Haldwani",
    "almora": "Almora",
    "haridwar": "Haridwar"
}

# Space Type Lexicon
SPACE_TYPES_MAP: Dict[str, str] = {
    # Workspace
    "workspace": "Workspace", "office": "Workspace", "desk": "Workspace",
    "coworking": "Workspace", "desk space": "Workspace", "कार्यालय": "Workspace",
    "दफ्तर": "Workspace", "table": "Workspace",
    # Meeting
    "meeting": "Meeting", "conference": "Meeting", "boardroom": "Meeting",
    "collab": "Meeting", "discussion": "Meeting", "बैठक": "Meeting",
    # Studio
    "studio": "Studio", "podcast": "Studio", "recording": "Studio",
    "photography": "Studio", "photo": "Studio", "vocal": "Studio",
    # Study
    "study": "Study", "library": "Study", "quiet pod": "Study",
    "study desk": "Study", "padhai": "Study", "अभ्यास": "Study", "वाचनालय": "Study",
    # Workshop
    "workshop": "Workshop", "maker": "Workshop", "hardware": "Workshop", "proto": "Workshop",
    # Retail
    "retail": "Retail", "pop-up": "Retail", "store": "Retail", "stall": "Retail",
    "boutique": "Retail", "दुकान": "Retail", "shop": "Retail",
    # Storage
    "storage": "Storage", "warehouse": "Storage", "garage": "Storage",
    "गोदाम": "Storage", "space storage": "Storage",
    # Event
    "event": "Event", "hall": "Event", "gathering": "Event",
    "सभागृह": "Event", "auditorium": "Event"
}

# Amenities Dictionary
KNOWN_AMENITIES_MAP: Dict[str, str] = {
    "wifi": "High-Speed Wi-Fi", "wi-fi": "High-Speed Wi-Fi", "fiber": "High-Speed Wi-Fi",
    "internet": "High-Speed Wi-Fi", "ac": "Air Conditioning", "air condition": "Air Conditioning",
    "air conditioning": "Air Conditioning", "power backup": "Power Backup", "inverter": "Power Backup",
    "generator": "Power Backup", "whiteboard": "Whiteboard", "marker": "Whiteboard",
    "projector": "Projector", "screen": "Presentation Monitor", "tv": "Presentation Monitor",
    "monitor": "Presentation Monitor", "parking": "Parking Available", "ergonomic": "Ergonomic Chairs",
    "coffee": "Coffee/Tea Station", "tea": "Coffee/Tea Station", "water": "Drinking Water"
}


class EntityExtractionService:
    """
    Extracts and strictly validates entities from normalized text.
    Rejects out-of-bounds numbers and prevents hallucinated locations.
    """

    @classmethod
    def extract_entities(cls, text: str, context_data: Optional[Dict[str, Any]] = None) -> ExtractedEntities:
        if not text:
            return ExtractedEntities()

        clean = text.lower().strip()
        entities = ExtractedEntities()

        # ---------------------------------------------------------------------
        # 1. LISTING ID VALIDATION
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
        # 2. GUEST COUNT / CAPACITY (Bounded: 1 <= guests <= 500)
        # ---------------------------------------------------------------------
        cap_match = re.search(
            r"\b(?:for\s+)?(\d+)\s*(?:people|persons?|guests?|members?|attendees?|seats?|pax|log(?:on)?|vyakti(?:yon)?|jan(?:on)?|mansen|lok)\b",
            clean
        )
        if cap_match:
            try:
                cap_val = int(cap_match.group(1))
                if 1 <= cap_val <= 500:
                    entities.guest_count = cap_val
            except ValueError:
                pass
        else:
            team_match = re.search(r"\bteam\s+of\s+(\d+)\b", clean)
            if team_match:
                try:
                    cap_val = int(team_match.group(1))
                    if 1 <= cap_val <= 500:
                        entities.guest_count = cap_val
                except ValueError:
                    pass

        # ---------------------------------------------------------------------
        # 3. DURATION HOURS (Bounded: 0.5 <= hours <= 168.0)
        # ---------------------------------------------------------------------
        hours_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|ghante|taas|ghant)\b", clean)
        if hours_match:
            try:
                dur = float(hours_match.group(1))
                if 0.5 <= dur <= 168.0:
                    entities.duration_hours = dur
            except ValueError:
                pass
        elif "half day" in clean or "aadha din" in clean:
            entities.duration_hours = 4.0
        elif "full day" in clean or "pura din" in clean or "purna divas" in clean:
            entities.duration_hours = 8.0

        # ---------------------------------------------------------------------
        # 4. PRICING / BUDGET (Bounded: >= ₹5.0)
        # ---------------------------------------------------------------------
        price_match = re.search(
            r"\b(?:under|below|max|budget|upto|less\s+than|₹)\s*(?:₹)?\s*(\d+(?:\.\d+)?)\b",
            clean
        )
        if price_match:
            try:
                price_val = float(price_match.group(1))
                if price_val >= 5.0:
                    entities.max_price = price_val
            except ValueError:
                pass

        # ---------------------------------------------------------------------
        # 5. LOCATION VALIDATION (Checked against verified Hubs)
        # ---------------------------------------------------------------------
        matched_location = None
        for hub_key in sorted(KNOWN_HUBS_MAP.keys(), key=len, reverse=True):
            if re.search(rf"\b{re.escape(hub_key)}\b", clean):
                matched_location = KNOWN_HUBS_MAP[hub_key]
                break

        if matched_location:
            entities.location = matched_location

        # ---------------------------------------------------------------------
        # 6. PROPERTY / SPACE TYPE
        # ---------------------------------------------------------------------
        for type_key, canonical_type in SPACE_TYPES_MAP.items():
            if re.search(rf"\b{re.escape(type_key)}\b", clean):
                entities.property_type = canonical_type
                break

        # ---------------------------------------------------------------------
        # 7. DATE & TIME RANGE
        # ---------------------------------------------------------------------
        if "tomorrow" in clean or "kal" in clean or "udya" in clean or "bhol" in clean:
            entities.date_str = "tomorrow"
        elif "today" in clean or "aaj" in clean:
            entities.date_str = "today"
        elif "weekend" in clean or "shaniwar" in clean or "ravivar" in clean:
            entities.date_str = "weekend"
        else:
            # Check ISO date YYYY-MM-DD
            iso_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", clean)
            if iso_match:
                entities.date_str = iso_match.group(1)

        if "morning" in clean or "subah" in clean or "sakali" in clean:
            entities.time_range = "morning"
        elif "afternoon" in clean or "dopahar" in clean or "dupari" in clean:
            entities.time_range = "afternoon"
        elif "evening" in clean or "shaam" in clean or "sandhyakali" in clean:
            entities.time_range = "evening"
        elif "night" in clean or "raat" in clean or "ratri" in clean:
            entities.time_range = "night"

        # ---------------------------------------------------------------------
        # 8. AMENITIES EXTRACTION
        # ---------------------------------------------------------------------
        found_amenities = set()
        for kw, canonical_amenity in KNOWN_AMENITIES_MAP.items():
            if re.search(rf"\b{re.escape(kw)}\b", clean):
                found_amenities.add(canonical_amenity)
        if found_amenities:
            entities.amenities = sorted(list(found_amenities))

        return entities
