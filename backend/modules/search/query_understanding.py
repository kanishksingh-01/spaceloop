"""
SpaceLoop Query Understanding Engine
Extracts structured factual constraints (capacity, price, location, space type, dates, hours)
and separates them from the semantic query.
Follows Rule 5: Groq -> Gemini -> Deterministic Regex/Keyword parser.
Never invents missing values.
"""
import re
import json
import logging
from space_ai import _call_groq, _call_gemini
from security import sanitize_string

logger = logging.getLogger("spaceloop.search.query_understanding")

# Known categories in SpaceLoop
KNOWN_CATEGORIES = {
    "workspace": "Workspace",
    "office": "Workspace",
    "desk": "Workspace",
    "coworking": "Workspace",
    "कार्यालय": "Workspace",
    "दफ्तर": "Workspace",
    "वर्कस्पेस": "Workspace",
    "ऑफिस": "Workspace",
    "काम करण्याची जागा": "Workspace",
    "meeting": "Meeting",
    "conference": "Meeting",
    "boardroom": "Meeting",
    "बैठक": "Meeting",
    "कमरा": "Meeting",
    "कमरे": "Meeting",
    "खोली": "Meeting",
    "खोल्या": "Meeting",
    "studio": "Studio",
    "podcast": "Studio",
    "recording": "Studio",
    "photography": "Studio",
    "photo": "Studio",
    "स्टुडिओ": "Studio",
    "स्टूडियो": "Studio",
    "study": "Study",
    "library": "Study",
    "quiet pod": "Study",
    "अभ्यास": "Study",
    "वाचनालय": "Study",
    "कक्षा": "Study",
    "workshop": "Workshop",
    "maker": "Workshop",
    "hardware": "Workshop",
    "retail": "Retail",
    "pop-up": "Retail",
    "store": "Retail",
    "stall": "Retail",
    "दुकान": "Retail",
    "storage": "Storage",
    "warehouse": "Storage",
    "गैराज": "Storage",
    "गोदाम": "Storage",
    "event": "Event",
    "hall": "Event",
    "gathering": "Event",
    "सभागृह": "Event"
}

# Known locations & tech hubs
KNOWN_HUBS = [
    "kharadi", "wagholi", "viman nagar", "kothrud", "aundh", "baner", "hinjewadi", "shivajinagar", "pune",
    "पुणे", "पुण्यात", "बाणेर", "खराडी", "कोथरूड", "वाघोली",
    "hauz khas", "iit delhi", "north campus", "south campus", "connaught place", "nehru place", "delhi", "new delhi",
    "दिल्ली", "दिल्लीत", "noida", "sector 62", "gurgaon", "cyber city",
    "koramangala", "indiranagar", "whitefield", "hanyur", "hsr layout", "electronic city", "bangalore", "bengaluru",
    "बेंगलुरु", "बेंगळुरू", "bandra", "powai", "andheri", "dadar", "mumbai", "मुंबई", "मुंबईत",
    "dehradun", "देहरादून", "rishikesh", "ऋषिकेश", "nainital", "नैनीताल", "mussoorie", "मसूरी"
]


def _deterministic_extract_constraints(query: str) -> dict:
    """
    Robust rule-based parser that deterministically extracts structured constraints from natural language.
    Does NOT invent missing values.
    """
    clean_q = query.strip()
    lower_q = clean_q.lower()
    
    extracted = {
        "semantic_query": clean_q,
        "location": None,
        "capacity": None,
        "max_price": None,
        "space_type": None,
        "amenities": [],
        "date": None,
        "time_range": None,
        "hours": None
    }
    
    # Track portions of text to remove from semantic query
    to_strip = []

    # 1. Capacity extraction (e.g. "for 6 people", "5 persons", "team of 10", "4 seats", "4 लोगों के लिए", "4 लोकांसाठी")
    cap_match = re.search(r'(?:for\s+)?(\d+)\s*(?:people|persons?|guests?|members?|attendees?|seats?|pax|लोगों|लोग|व्यक्तियों|व्यक्ती|लोकांसाठी|लोकांना|माणस)(?!\w)', lower_q)
    if cap_match:
        try:
            extracted["capacity"] = int(cap_match.group(1))
            to_strip.append(cap_match.group(0))
        except ValueError:
            pass
    else:
        team_match = re.search(r'\bteam\s+of\s+(\d+)\b', lower_q)
        if team_match:
            try:
                extracted["capacity"] = int(team_match.group(1))
                to_strip.append(team_match.group(0))
            except ValueError:
                pass

    # 2. Duration hours extraction (e.g. "4-hour", "4 hours", "2 hr", "half day", "4 तास", "4 घंटे")
    hours_match = re.search(r'\b(\d+)(?:\s*|-)(?:hours?|hrs?|घंटे|तास)\b', lower_q)
    if hours_match:
        try:
            extracted["hours"] = float(hours_match.group(1))
            to_strip.append(hours_match.group(0))
        except ValueError:
            pass
    elif "half day" in lower_q or "आधा दिन" in lower_q:
        extracted["hours"] = 4.0
        to_strip.append("half day")
    elif "full day" in lower_q or "पूरा दिन" in lower_q:
        extracted["hours"] = 8.0
        to_strip.append("full day")

    # 3. Max price budget extraction (e.g. "under 1000", "under ₹500/hr", "below 800", "budget 1200")
    price_match = re.search(r'\b(?:under|below|max(?:imum)?|budget(?:\s+of)?|upto|up\s+to)\s*(?:₹|rs\.?|inr)?\s*(\d+)(?:\s*(?:/hr|per\s+hour|rs))?\b', lower_q)
    if price_match:
        try:
            extracted["max_price"] = float(price_match.group(1))
            to_strip.append(price_match.group(0))
        except ValueError:
            pass

    # 4. Location extraction
    # Check known hubs first
    matched_hub = None
    for hub in sorted(KNOWN_HUBS, key=len, reverse=True):
        if any('\u0900' <= c <= '\u097f' for c in hub):
            if re.search(rf"(?:^|[^\u0900-\u097f]){re.escape(hub)}(?:$|[^\u0900-\u097f])", lower_q):
                matched_hub = hub.title()
                to_strip.append(hub)
                break
        else:
            pattern = rf'\b(?:in|near|at|around)?\s*({re.escape(hub)})\b'
            loc_search = re.search(pattern, lower_q)
            if loc_search:
                matched_hub = hub.title()
                to_strip.append(loc_search.group(0))
                break
    
    if matched_hub:
        from backend.modules.nlp.entity_extraction import KNOWN_HUBS_MAP
        canonical_loc = KNOWN_HUBS_MAP.get(matched_hub.lower()) or KNOWN_HUBS_MAP.get(matched_hub)
        if canonical_loc:
            # e.g. "Kharadi, Pune" -> "Kharadi" or "Pune" -> "Pune"
            extracted["location"] = canonical_loc.split(",")[0].strip() if "," in canonical_loc and matched_hub.lower() in ("kharadi", "बाणेर", "baner", "वाघोली", "wagholi", "kothrud", "कोथरूड") else canonical_loc
        else:
            extracted["location"] = matched_hub
    else:
        # Generic "near <Location>" or "in <Location>"
        generic_loc = re.search(r'\b(?:in|near|around|at)\s+([A-Z][a-zA-Z0-9_\-\s]+?)(?=\s+(?:for|under|below|with|tomorrow|today|\d)|$)', clean_q)
        if generic_loc:
            loc_candidate = generic_loc.group(1).strip()
            if len(loc_candidate) > 2 and loc_candidate.lower() not in ("a", "an", "the", "my", "our"):
                extracted["location"] = loc_candidate
                to_strip.append(generic_loc.group(0))

    # 5. Space Type extraction
    for keyword, cat_name in KNOWN_CATEGORIES.items():
        if any('\u0900' <= c <= '\u097f' for c in keyword):
            if re.search(rf"(?:^|[^\u0900-\u097f]){re.escape(keyword)}(?:$|[^\u0900-\u097f])", lower_q):
                extracted["space_type"] = cat_name
                break
        else:
            if re.search(rf'\b{re.escape(keyword)}\b', lower_q):
                extracted["space_type"] = cat_name
                break

    # 6. Date extraction
    if re.search(r'\btomorrow\b', lower_q) or "कल" in lower_q or "उद्या" in lower_q:
        extracted["date"] = "tomorrow"
        to_strip.append("tomorrow")
    elif re.search(r'\btoday\b', lower_q) or "आज" in lower_q:
        extracted["date"] = "today"
        to_strip.append("today")
    elif re.search(r'\bthis\s+weekend\b', lower_q):
        extracted["date"] = "this weekend"
        to_strip.append("this weekend")

    # 7. Time range extraction
    if re.search(r'\bafternoon\b', lower_q) or "दोपहर" in lower_q or "दुपारी" in lower_q:
        extracted["time_range"] = "afternoon"
        to_strip.append("afternoon")
    elif re.search(r'\bmorning\b', lower_q) or "सुबह" in lower_q or "सकाळी" in lower_q:
        extracted["time_range"] = "morning"
        to_strip.append("morning")
    elif re.search(r'\bevening\b', lower_q) or "शाम" in lower_q or "संध्याकाळी" in lower_q:
        extracted["time_range"] = "evening"
        to_strip.append("evening")
    elif re.search(r'\bnight\b', lower_q) or "रात" in lower_q or "रात्री" in lower_q:
        extracted["time_range"] = "night"
        to_strip.append("night")

    # 8. Amenities extraction
    amenity_keywords = {
        "wifi": "Wi-Fi",
        "wi-fi": "Wi-Fi",
        "internet": "Wi-Fi",
        "whiteboard": "Whiteboard",
        "projector": "Projector",
        "parking": "Parking",
        "ac": "Air Conditioning",
        "air conditioning": "Air Conditioning",
        "power": "Power Outlets",
        "monitor": "External Monitor",
        "वायफाय": "Wi-Fi",
        "वाईफाई": "Wi-Fi",
        "एसी": "Air Conditioning",
        "वातानुकूलित": "Air Conditioning",
        "पार्किंग": "Parking",
        "व्हाइटबोर्ड": "Whiteboard"
    }
    for kw, label in amenity_keywords.items():
        if any('\u0900' <= c <= '\u097f' for c in kw):
            if re.search(rf"(?:^|[^\u0900-\u097f]){re.escape(kw)}(?:$|[^\u0900-\u097f])", lower_q):
                if label not in extracted["amenities"]:
                    extracted["amenities"].append(label)
        else:
            if re.search(rf'\b{re.escape(kw)}\b', lower_q):
                if label not in extracted["amenities"]:
                    extracted["amenities"].append(label)

    # Integrate SpaceLoop NLPPipeline entities (Multilingual & Code-Mixed awareness)
    try:
        from backend.modules.nlp.pipeline import NLPPipeline
        nlp_res = NLPPipeline.process(clean_q)
        nlp_entities = nlp_res.entities or {}
        if nlp_entities.get("location") and not extracted["location"]:
            extracted["location"] = nlp_entities["location"]
        if (nlp_entities.get("guest_count") or nlp_entities.get("capacity")) and not extracted["capacity"]:
            extracted["capacity"] = nlp_entities.get("guest_count") or nlp_entities.get("capacity")
        if (nlp_entities.get("price") or nlp_entities.get("max_price")) and not extracted["max_price"]:
            extracted["max_price"] = nlp_entities.get("price") or nlp_entities.get("max_price")
        if (nlp_entities.get("property_type") or nlp_entities.get("space_type")) and not extracted["space_type"]:
            st = nlp_entities.get("property_type") or nlp_entities.get("space_type")
            if isinstance(st, str) and st.title() in ("Workspace", "Meeting", "Studio", "Workshop", "Retail", "Storage", "Study", "Event"):
                extracted["space_type"] = st.title()
        if nlp_entities.get("amenities") and not extracted["amenities"]:
            extracted["amenities"] = nlp_entities["amenities"]
        if nlp_entities.get("date") and not extracted["date"]:
            extracted["date"] = nlp_entities["date"]
        if (nlp_entities.get("duration_hours") or nlp_entities.get("hours")) and not extracted["hours"]:
            extracted["hours"] = nlp_entities.get("duration_hours") or nlp_entities.get("hours")
    except Exception as e:
        logger.debug(f"NLPPipeline constraint enrichment skipped: {e}")

    # Clean semantic query by stripping out extracted factual phrases
    semantic_cleaned = clean_q
    for s in to_strip:
        # Case insensitive substitution
        semantic_cleaned = re.sub(re.escape(s), " ", semantic_cleaned, flags=re.IGNORECASE)

    # Clean residual filler words like "I need a", "looking for a", "place for", "near"
    semantic_cleaned = re.sub(r'\b(?:i\s+need|looking\s+for|want|searching\s+for|a|an|the|near|in|at|for|के लिए|साठी)\b', " ", semantic_cleaned, flags=re.IGNORECASE)
    semantic_cleaned = re.sub(r'\s+', " ", semantic_cleaned).strip()

    # If query contains Devanagari, bridge semantic query with English concepts so vector & keyword search against English listings succeed
    if any('\u0900' <= c <= '\u097f' for c in clean_q):
        bridge_tokens = []
        if extracted.get("space_type"):
            bridge_tokens.append(extracted["space_type"])
        if extracted.get("amenities"):
            bridge_tokens.extend(extracted["amenities"])
        if any(w in clean_q for w in ["शांत", "शांतता", "एकांत"]):
            bridge_tokens.append("Quiet")
        if any(w in clean_q for w in ["सस्ता", "स्वस्त", "बजट"]):
            bridge_tokens.append("Affordable")
        if bridge_tokens:
            extracted["semantic_query"] = f"{semantic_cleaned} {' '.join(bridge_tokens)}".strip()
        else:
            extracted["semantic_query"] = semantic_cleaned if len(semantic_cleaned) > 2 else clean_q
    else:
        extracted["semantic_query"] = semantic_cleaned if len(semantic_cleaned) > 2 else clean_q
    return extracted


def understand_search_query(raw_query: str) -> dict:
    """
    Parses a user search query into structured constraints and semantic intent.
    Uses multi-tier routing: Groq -> Gemini -> Deterministic rules.
    """
    query_clean = sanitize_string(raw_query or "", max_length=300).strip()
    if not query_clean:
        return {
            "semantic_query": "",
            "location": None,
            "capacity": None,
            "max_price": None,
            "space_type": None,
            "amenities": [],
            "date": None,
            "time_range": None,
            "hours": None
        }

    # Prompt for LLM extraction
    prompt = f"""
You are the SpaceLoop Search Query Understanding Engine.
Analyze the user's natural language search query and extract structured factual constraints versus semantic search intent.

Input query:
"{query_clean}"

CRITICAL RULES:
1. Extract ONLY facts explicitly stated or clearly implied by the query.
2. DO NOT invent missing values. If not stated, return null.
3. Keep the "semantic_query" focused on the qualitative vibe, atmosphere, activity, and purpose (e.g. "quiet collaborative work", "soundproof acoustic podcasting", "bright photography portrait session").
4. "space_type" must be one of: Workspace, Meeting, Studio, Workshop, Retail, Storage, Study, Event, or null.
5. "capacity" must be an integer or null.
6. "max_price" must be a number in INR/hr or null.
7. "hours" must be a number representing duration or null.
8. "date" must be a string (e.g. "tomorrow", "today", "2026-09-27") or null.
9. "time_range" must be "morning", "afternoon", "evening", "night", or null.

Return ONLY a valid JSON object matching this schema:
{{
  "semantic_query": "string",
  "location": "string or null",
  "capacity": 0,
  "max_price": 0.0,
  "space_type": "string or null",
  "amenities": ["string"],
  "date": "string or null",
  "time_range": "string or null",
  "hours": 0.0
}}
"""
    # Tier 1: Groq LLM
    groq_res = _call_groq([
        {"role": "system", "content": "You are a precise search query parser. Return strictly valid JSON."},
        {"role": "user", "content": prompt}
    ], json_mode=True)

    if groq_res:
        try:
            m = re.search(r'\{.*\}', groq_res, re.DOTALL)
            parsed = json.loads(m.group(0) if m else groq_res)
            if isinstance(parsed, dict) and "semantic_query" in parsed:
                return _normalize_parsed_query(parsed, query_clean)
        except Exception:
            pass

    # Tier 2: Google Gemini LLM
    gemini_res = _call_gemini(prompt)
    if gemini_res:
        try:
            m = re.search(r'\{.*\}', gemini_res, re.DOTALL)
            parsed = json.loads(m.group(0) if m else gemini_res)
            if isinstance(parsed, dict) and "semantic_query" in parsed:
                return _normalize_parsed_query(parsed, query_clean)
        except Exception:
            pass

    # Tier 3: Deterministic Rule Engine
    return _deterministic_extract_constraints(query_clean)


def _normalize_parsed_query(parsed: dict, original_query: str) -> dict:
    """Sanitizes and normalizes the parsed JSON from LLMs to adhere strictly to schema."""
    semantic = sanitize_string(parsed.get("semantic_query") or original_query, max_length=200)
    
    loc = parsed.get("location")
    if loc and isinstance(loc, str):
        loc = sanitize_string(loc, max_length=80).strip() or None
    else:
        loc = None

    cap = parsed.get("capacity")
    try:
        cap = int(cap) if cap and int(cap) > 0 else None
    except (ValueError, TypeError):
        cap = None

    price = parsed.get("max_price")
    try:
        price = float(price) if price and float(price) > 0 else None
    except (ValueError, TypeError):
        price = None

    stype = parsed.get("space_type")
    if stype and isinstance(stype, str):
        stype = stype.strip().title()
        if stype not in ("Workspace", "Meeting", "Studio", "Workshop", "Retail", "Storage", "Study", "Event"):
            stype = None
    else:
        stype = None

    amenities = parsed.get("amenities") or []
    if isinstance(amenities, list):
        clean_amenities = [sanitize_string(a, max_length=50) for a in amenities if isinstance(a, str) and a.strip()]
    else:
        clean_amenities = []

    date_val = parsed.get("date")
    if date_val and isinstance(date_val, str):
        date_val = sanitize_string(date_val, max_length=40).strip() or None
    else:
        date_val = None

    trange = parsed.get("time_range")
    if trange and isinstance(trange, str):
        trange = trange.strip().lower()
        if trange not in ("morning", "afternoon", "evening", "night"):
            trange = None
    else:
        trange = None

    hours = parsed.get("hours")
    try:
        hours = float(hours) if hours and float(hours) > 0 else None
    except (ValueError, TypeError):
        hours = None

    return {
        "semantic_query": semantic or original_query,
        "location": loc,
        "capacity": cap,
        "max_price": price,
        "space_type": stype,
        "amenities": clean_amenities,
        "date": date_val,
        "time_range": trange,
        "hours": hours
    }
