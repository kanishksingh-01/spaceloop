"""
SpaceLoop Query Understanding Engine
Extracts structured factual constraints (capacity, price, location, space type, dates, hours)
and separates them from the semantic query.
Follows Rule 5: Fast Deterministic NLP Pipeline -> Groq -> Gemini -> Schema Validation.
Never invents missing values.
"""
import re
import json
import logging
from space_ai import _call_groq, _call_gemini
from security import sanitize_string

logger = logging.getLogger("spaceloop.search.query_understanding")


def _deterministic_extract_constraints(query: str) -> dict:
    """
    Robust rule-based parser that deterministically extracts structured constraints from natural language
    using the unified SpaceLoop NLPPipeline.
    """
    from backend.modules.nlp.pipeline import NLPPipeline
    
    nlp_res = NLPPipeline.process(query)
    ir = nlp_res.query_understanding
    
    if ir:
        hc = ir.hard_constraints
        loc = hc.get("location")
        if ir.entities and ir.entities.location_details:
            if any('\u0900' <= c <= '\u097f' for c in ir.entities.location_details.raw_text):
                loc = ir.entities.location_details.city or loc
            elif ir.entities.location_details.raw_text:
                loc = ir.entities.location_details.raw_text.title()
        cap = hc.get("min_capacity")
        price = hc.get("max_price")
        stype = hc.get("category")
        amenities = hc.get("amenities", [])
        date_val = hc.get("date")
        trange = ir.entities.time_range if ir.entities.time_range else (ir.entities.time_window_details.time_range_name if ir.entities.time_window_details else None)
        hours = hc.get("duration_hours")
        
        return {
            "semantic_query": ir.semantic_query or query,
            "location": loc,
            "capacity": cap,
            "max_price": price,
            "space_type": stype,
            "amenities": amenities,
            "date": date_val,
            "time_range": trange,
            "hours": hours,
            "soft_preferences": ir.soft_preferences,
            "needs_clarification": ir.needs_clarification,
            "clarification_prompt": ir.clarification_prompt,
            "overall_confidence": ir.overall_confidence
        }
    
    return {
        "semantic_query": query,
        "location": None,
        "capacity": None,
        "max_price": None,
        "space_type": None,
        "amenities": [],
        "date": None,
        "time_range": None,
        "hours": None,
        "soft_preferences": [],
        "needs_clarification": False,
        "clarification_prompt": None,
        "overall_confidence": 0.50
    }


def understand_search_query(query: str, context_data: dict | None = None) -> dict:
    """
    Primary Query Understanding function.
    Combines high-speed deterministic NLP pipeline with LLM reasoning (Groq -> Gemini).
    Always validates and normalizes output into a safe structured constraint dictionary.
    """
    if not query or not query.strip():
        return {
            "semantic_query": "",
            "location": None,
            "capacity": None,
            "max_price": None,
            "space_type": None,
            "amenities": [],
            "date": None,
            "time_range": None,
            "hours": None,
            "soft_preferences": []
        }

    query_clean = sanitize_string(query.strip(), max_length=300)

    # Step 1: Fast & Robust Local NLP Pipeline
    pipeline_res = _deterministic_extract_constraints(query_clean)

    # If deterministic pipeline extracted rich structured constraints or query is direct,
    # return immediately without paying LLM latency cost
    has_meaningful_entities = bool(
        pipeline_res.get("location") or 
        pipeline_res.get("capacity") or 
        pipeline_res.get("max_price") or 
        pipeline_res.get("space_type") or 
        pipeline_res.get("date") or 
        pipeline_res.get("hours")
    )
    if has_meaningful_entities and pipeline_res.get("overall_confidence", 0) >= 0.80:
        return pipeline_res

    # Step 2: Multi-Tier LLM Query Parsing (for deeply conversational / complex queries)
    prompt = f"""
You are the SpaceLoop Natural Language Query Understanding engine.
Extract structured search constraints from the user query.
SpaceLoop space types: Workspace, Meeting, Studio, Workshop, Retail, Storage, Study, Event.

CRITICAL INSTRUCTIONS:
- Do NOT invent or assume values not present in the query. If not mentioned, return null/empty.
- 'semantic_query': text representing the core vibe/purpose with hard filter numbers/locations removed.
- 'location': city, hub, or neighborhood (e.g. "Kharadi, Pune", "Hauz Khas, Delhi", "Bandra, Mumbai", "Dehradun").
- 'capacity': integer minimum guest count (e.g. 6).
- 'max_price': float maximum price in INR (e.g. 2000.0).
- 'space_type': one of [Workspace, Meeting, Studio, Workshop, Retail, Storage, Study, Event] or null.
- 'amenities': list of string amenities requested (e.g. ["High-Speed Wi-Fi", "Air Conditioning", "Whiteboard", "Parking Available"]).
- 'date': string date expression (e.g. "tomorrow", "today", "weekend", "2026-10-10").
- 'time_range': "morning", "afternoon", "evening", or "night" or null.
- 'hours': float duration in hours (e.g. 3.0) or null.

<user_query>
{query_clean}
</user_query>

Return ONLY valid JSON:
{{
  "semantic_query": "quiet place to work with good lighting",
  "location": "Kharadi, Pune",
  "capacity": 6,
  "max_price": 3000.0,
  "space_type": "Workspace",
  "amenities": ["High-Speed Wi-Fi"],
  "date": "tomorrow",
  "time_range": "evening",
  "hours": 3.0
}}
"""

    # Tier 1: Groq LLM
    groq_res = _call_groq([
        {"role": "system", "content": "You are a query constraint parser. Return only JSON."},
        {"role": "user", "content": prompt}
    ], json_mode=True)

    if groq_res:
        try:
            m = re.search(r'\{.*\}', groq_res, re.DOTALL)
            parsed = json.loads(m.group(0) if m else groq_res)
            if isinstance(parsed, dict) and "semantic_query" in parsed:
                merged = _normalize_parsed_query(parsed, query_clean)
                merged["soft_preferences"] = pipeline_res.get("soft_preferences", [])
                return merged
        except Exception:
            pass

    # Tier 2: Google Gemini LLM
    gemini_res = _call_gemini(prompt)
    if gemini_res:
        try:
            m = re.search(r'\{.*\}', gemini_res, re.DOTALL)
            parsed = json.loads(m.group(0) if m else gemini_res)
            if isinstance(parsed, dict) and "semantic_query" in parsed:
                merged = _normalize_parsed_query(parsed, query_clean)
                merged["soft_preferences"] = pipeline_res.get("soft_preferences", [])
                return merged
        except Exception:
            pass

    # Tier 3: Return Deterministic Pipeline Result
    return pipeline_res


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
        "hours": hours,
        "soft_preferences": []
    }
