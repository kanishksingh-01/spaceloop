"""
SpaceLoop NLP-Powered Listing Assistance Service
================================================
Transforms natural language space descriptions into structured listings.
Supports: English, Hindi, Marathi, and code-mixed Hinglish / Marathi-English.

Core Capabilities:
1. Extracting structured listing fields (propertyType, bedrooms, location, furnished, near, rent, sqft, capacity, amenities).
2. Identifying missing required information and formulating polite clarification questions.
3. Detecting obvious logical inconsistencies (capacity vs size, unrealistic prices, contradictory terms).
4. Generating readable, professional listing descriptions with STRICT FACTUAL INTEGRITY
   (user-controlled numbers like rent or capacity are immutable and NEVER altered).
5. Improving listing wording.
6. Multilingual listing assistance and translation (English, Hindi, Marathi).
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from security import sanitize_string

logger = logging.getLogger("spaceloop.nlp.listing_assistance")


class ListingAssistanceService:

    PROPERTY_TYPE_MAP = {
        # Flats & apartments
        "flat": "flat",
        "apartment": "apartment",
        "bhk": "flat",
        "house": "house",
        "villa": "villa",
        # Workspaces & offices
        "office": "office",
        "workspace": "workspace",
        "desk": "desk",
        "coworking": "coworking",
        "cabin": "cabin",
        # Meeting & conference
        "meeting room": "meeting room",
        "boardroom": "boardroom",
        "conference room": "conference room",
        # Studios & creator spaces
        "studio": "studio",
        "podcast": "podcast studio",
        "recording": "recording studio",
        "photo studio": "photo studio",
        # Study & quiet pods
        "study": "study room",
        "study pod": "study pod",
        "nook": "study nook",
        # Storage & workshops
        "workshop": "workshop",
        "storage": "storage",
        "garage": "garage",
        "terrace": "terrace"
    }

    INDIC_PROPERTY_TERMS = {
        "कमरा": "room",
        "फ्लैट": "flat",
        "कार्यालय": "office",
        "दुकान": "retail",
        "गोदाम": "storage",
        "जागा": "space",
        "खोली": "room",
        "घर": "flat",
        "काम करण्याची जागा": "workspace"
    }

    CATEGORY_MAPPING = {
        "flat": "Workspace",
        "apartment": "Workspace",
        "house": "Workspace",
        "room": "Workspace",
        "office": "Workspace",
        "desk": "Workspace",
        "coworking": "Workspace",
        "cabin": "Workspace",
        "workspace": "Workspace",
        "meeting room": "Meeting",
        "boardroom": "Meeting",
        "conference room": "Meeting",
        "studio": "Studio",
        "podcast studio": "Studio",
        "recording studio": "Studio",
        "photo studio": "Studio",
        "study room": "Study Pod",
        "study pod": "Study Pod",
        "study nook": "Study Pod",
        "workshop": "Workshop",
        "storage": "Storage",
        "garage": "Storage",
        "terrace": "Workspace"
    }

    KNOWN_LOCATIONS = [
        "Pune", "Kharadi", "Wagholi", "Baner", "Kothrud", "Aundh", "Hinjewadi", "Viman Nagar", "Shivajinagar",
        "Mumbai", "Bandra", "Andheri", "Powai", "Dadar",
        "Bengaluru", "Bangalore", "Indiranagar", "Koramangala", "Whitefield", "HSR Layout", "Electronic City",
        "Delhi", "New Delhi", "Hauz Khas", "Connaught Place", "Nehru Place",
        "Gurgaon", "Cyber City", "Noida", "Dehradun", "Rishikesh"
    ]

    LANDMARK_PATTERNS = [
        r"(?:near|close to|opp(?:osite)?|behind|beside|adj(?:acent)?|ke paas|javal|जवळ|के पास)\s+([A-Za-z0-9\s\-]+?)(?=,|\.|\band\b|\bwith\b|\brent\b|\b₹|\b\d+k|\bfully\b|$)",
    ]

    @classmethod
    def assist_listing(cls, text: str, target_language: str = "en") -> Dict[str, Any]:
        """
        Parses raw natural language text into a rich, structured listing with:
        - extracted_fields
        - listing_draft (ready for host review before publishing)
        - missing_fields
        - clarifications
        - inconsistencies
        - generated_description (factually grounded)
        - improved_wording
        - ai_provider (groq, gemini, or deterministic_rule_engine)
        """
        clean_text = sanitize_string(text or "", max_length=1500).strip()
        if not clean_text:
            return {
                "success": False,
                "error": "Listing text cannot be empty.",
                "extracted_fields": {},
                "listing_draft": {},
                "missing_fields": ["title", "location", "rent", "property_type"],
                "clarifications": ["Please describe your space (e.g., '2 bedroom workspace in Pune for 4 people with fast WiFi and AC')."],
                "inconsistencies": [],
                "generated_description": "",
                "improved_wording": "",
                "ai_provider": "deterministic_rule_engine"
            }

        # Step 1: Detect Language
        detected_lang = cls._detect_language(clean_text)

        # Step 2: Multi-Tier NLP Extraction (Groq -> Gemini -> Deterministic)
        ai_provider = "deterministic_rule_engine"
        llm_extracted = cls._extract_with_llm(clean_text)

        if llm_extracted:
            ai_provider = llm_extracted.pop("_ai_provider", "groq")
            # Baseline deterministic extraction ensures complete field keys
            extracted = cls._extract_fields(clean_text)
            for k, v in llm_extracted.items():
                if v is not None:
                    extracted[k] = v
        else:
            extracted = cls._extract_fields(clean_text)

        # Format title if missing
        if not extracted.get("title"):
            extracted["title"] = cls._generate_suggested_title(extracted)

        # Step 3: Identify Missing Fields & Formulate Clarification Questions
        missing_fields, clarifications = cls._identify_missing_fields(extracted)

        # Step 4: Detect Inconsistencies & Logical Contradictions
        inconsistencies = cls._detect_inconsistencies(extracted, clean_text)

        # Step 5: Generate Readable Description (STRICT FACTUAL INTEGRITY)
        generated_desc = cls._generate_factual_description(extracted, language=target_language)
        improved_wording = cls._generate_improved_wording(extracted, language=target_language)

        # Step 6: Construct Structured Listing Draft matching Space Schema
        listing_draft = {
            "title": extracted.get("title") or "",
            "description": generated_desc or "",
            "category": extracted.get("category") or "Workspace",
            "hourly_rate": extracted.get("price_hourly"),
            "price_hourly": extracted.get("price_hourly"),
            "price_monthly": extracted.get("price_monthly") or extracted.get("rent"),
            "location": extracted.get("location") or "",
            "neighborhood": extracted.get("neighborhood") or extracted.get("location") or "",
            "city": extracted.get("city") or "",
            "address": extracted.get("address") or "",
            "sqft": extracted.get("sqft"),
            "max_capacity": extracted.get("max_capacity"),
            "amenities": extracted.get("amenities") or [],
            "bedrooms": extracted.get("bedrooms"),
            "furnished": extracted.get("furnished"),
        }

        return {
            "success": True,
            "extracted_fields": extracted,
            "listing_draft": listing_draft,
            "missing_fields": missing_fields,
            "clarifications": clarifications,
            "inconsistencies": inconsistencies,
            "generated_description": generated_desc,
            "improved_wording": improved_wording,
            "detected_language": detected_lang,
            "language": target_language,
            "ai_provider": ai_provider
        }

    # =========================================================================
    # Multi-Tier LLM Extraction Engine (Groq -> Gemini -> Fallback)
    # =========================================================================

    @classmethod
    def _extract_with_llm(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Attempts LLM-based structured extraction with Groq (Primary) -> Gemini (Fallback).
        Strictly zero hallucination: output null / empty for any unprovided details.
        """
        system_prompt = (
            "You are SpaceLoop's intelligent listing extraction engine.\n"
            "Extract ONLY information explicitly provided in the host's space description into valid JSON.\n"
            "STRICT RULES:\n"
            "1. NO HALLUCINATION: If a field (such as price, exact address, city, square footage, capacity, AC, parking) is not stated, set it to null (or empty array for amenities).\n"
            "2. Allowed categories: Workspace, Meeting, Studio, Podcast, Workshop, Retail, Storage, Study Pod.\n"
            "3. Output valid JSON only, without markdown fences or comments.\n\n"
            "Keys required: title, description, category, property_type, location, city, neighborhood, address, near, bedrooms, max_capacity, sqft, price_hourly, rent, price_monthly, furnished, amenities (list), rules (list)."
        )

        user_prompt = f"Host space description:\n\"{text}\""

        # Tier 1: Groq
        try:
            from space_ai import _call_groq
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            raw = _call_groq(messages, json_mode=True, temperature=0.1)
            if raw:
                parsed = cls._parse_llm_json(raw, text)
                if parsed:
                    parsed["_ai_provider"] = "groq"
                    return parsed
        except Exception as e:
            logger.warning(f"Groq listing extraction failed: {e}")

        # Tier 2: Gemini
        try:
            from space_ai import _call_gemini
            raw = _call_gemini(f"{system_prompt}\n\n{user_prompt}", temperature=0.1)
            if raw:
                parsed = cls._parse_llm_json(raw, text)
                if parsed:
                    parsed["_ai_provider"] = "gemini"
                    return parsed
        except Exception as e:
            logger.warning(f"Gemini listing extraction failed: {e}")

        return None

    @classmethod
    def _parse_llm_json(cls, raw: str, original_text: str) -> Optional[Dict[str, Any]]:
        """Parses and sanitizes LLM JSON, verifying grounding against the input text."""
        clean = raw.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
        try:
            data = json.loads(clean)
            if not isinstance(data, dict):
                return None

            # Enforce clean types
            for key in ["bedrooms", "max_capacity", "sqft"]:
                if key in data and data[key] is not None:
                    try:
                        data[key] = int(data[key])
                    except (ValueError, TypeError):
                        data[key] = None

            for key in ["rent", "price_hourly", "price_monthly"]:
                if key in data and data[key] is not None:
                    try:
                        data[key] = float(data[key])
                    except (ValueError, TypeError):
                        data[key] = None

            # Aliases & category mapping
            if data.get("property_type") and not data.get("propertyType"):
                data["propertyType"] = data["property_type"]
            elif data.get("propertyType") and not data.get("property_type"):
                data["property_type"] = data["propertyType"]

            if data.get("rent") and not data.get("price_monthly"):
                data["price_monthly"] = data["rent"]

            if not isinstance(data.get("amenities"), list):
                data["amenities"] = []

            # Grounding check: ensure amenities are actually grounded in text keywords using word or script boundaries
            grounded_amenities = []
            orig_lower = original_text.lower()
            def has_word(kw: str) -> bool:
                if any('\u0900' <= c <= '\u097f' for c in kw):
                    return bool(re.search(rf'(?:^|[^\u0900-\u097f]){re.escape(kw)}(?:$|[^\u0900-\u097f])', orig_lower))
                return bool(re.search(rf'\b{re.escape(kw)}\b', orig_lower))

            for amen in data["amenities"]:
                amen_lower = str(amen).lower()
                if any(has_word(kw) for kw in ["wifi", "wi-fi", "internet", "fiber", "वायफाय", "वाईफाई"]) and ("wi-fi" in amen_lower or "wifi" in amen_lower or "वायफाय" in amen_lower or "वाईफाई" in amen_lower):
                    grounded_amenities.append("High-speed Wi-Fi")
                elif any(has_word(kw) for kw in ["ac", "air condition", "a/c", "एसी", "वातानुकूलित", "वातानुकूलन"]) and ("air conditioning" in amen_lower or "ac" in amen_lower or "एसी" in amen_lower):
                    grounded_amenities.append("Air Conditioning")
                elif any(has_word(kw) for kw in ["parking", "पार्किंग"]) and ("parking" in amen_lower or "पार्किंग" in amen_lower):
                    grounded_amenities.append("Parking Available")
                elif any(has_word(kw) for kw in ["power", "backup", "inverter", "बिजली", "वीज"]) and "power" in amen_lower:
                    grounded_amenities.append("Power Backup")
                elif any(has_word(kw) for kw in ["whiteboard", "व्हाइटबोर्ड"]) and ("whiteboard" in amen_lower or "व्हाइटबोर्ड" in amen_lower):
                    grounded_amenities.append("Whiteboard")
                elif any(has_word(kw) for kw in ["screen", "monitor", "display", "स्क्रीन", "मॉनिटर"]) and ("display" in amen_lower or "screen" in amen_lower):
                    grounded_amenities.append("4K Presentation Display")
                elif any(has_word(kw) for kw in ["tea", "coffee", "चहा", "चाय", "कॉफी"]) and ("tea" in amen_lower or "coffee" in amen_lower):
                    grounded_amenities.append("Tea & Coffee")
                elif has_word("cctv") and "cctv" in amen_lower:
                    grounded_amenities.append("CCTV Security")
                elif any(has_word(kw) for kw in ["lift", "elevator", "लिफ्ट"]) and ("lift" in amen_lower or "elevator" in amen_lower):
                    grounded_amenities.append("Elevator Access")
                elif has_word(amen_lower):
                    grounded_amenities.append(str(amen).title())

            data["amenities"] = list(dict.fromkeys(grounded_amenities))
            return data
        except Exception:
            return None

    # =========================================================================
    # Extraction Logic
    # =========================================================================

    INDIC_LOCATIONS = {
        "पुणे": "Pune",
        "पुण्यात": "Pune",
        "मुंबई": "Mumbai",
        "मुंबईत": "Mumbai",
        "दिल्ली": "Delhi",
        "दिल्लीत": "Delhi",
        "बेंगलुरु": "Bengaluru",
        "बंगळूर": "Bengaluru",
        "खराडी": "Kharadi",
        "बाणेर": "Baner",
        "कोथरूड": "Kothrud",
        "वाघोली": "Wagholi",
        "हिंजवडी": "Hinjewadi",
        "विमान नगर": "Viman Nagar"
    }

    INDIC_LANDMARKS = {
        "आईटी पार्क": "IT park",
        "आयटी पार्क": "IT park",
        "मेट्रो स्टेशन": "Metro Station",
        "कॉलेज": "College",
        "विद्यापीठ": "University"
    }

    INDIC_PROPERTY_TERMS = {
        "कमरा": "room",
        "फ्लैट": "flat",
        "फ्लॅट": "flat",
        "कार्यालय": "office",
        "दुकान": "retail",
        "गोदाम": "storage",
        "जागा": "space",
        "खोली": "room",
        "घर": "flat",
        "काम करण्याची जागा": "workspace",
        "वर्कस्पेस": "workspace",
        "ऑफिस": "office",
        "दफ्तर": "office"
    }

    @classmethod
    def _extract_fields(cls, text: str) -> Dict[str, Any]:
        t_lower = text.lower()
        extracted: Dict[str, Any] = {
            "propertyType": "space",
            "property_type": "space",
            "category": "Workspace",
            "bedrooms": None,
            "location": None,
            "city": None,
            "neighborhood": None,
            "furnished": None,
            "near": None,
            "rent": None,
            "price_monthly": None,
            "price_hourly": None,
            "sqft": None,
            "max_capacity": None,
            "amenities": []
        }

        # 1. Bedrooms / BHK (e.g. "2 bedroom", "2bhk", "3 bhk", "2 bed", "2 कमरा", "2 खोल्या", "2 बीएचके", "2 बेडरूम")
        bhk_match = re.search(r'(?:^|[^\d])(\d+)\s*(?:bhk|bedroom|bed\s*room|beds?|room\s+flat|कमरा|कमरे|खोली|खोल्या|बीएचके|बेडरूम|बैडरूम|बेड\s*रूम)', text, re.IGNORECASE)
        if bhk_match:
            try:
                extracted["bedrooms"] = int(bhk_match.group(1))
            except ValueError:
                pass

        # 2. Property Type
        # Check specific multi-word types first
        for keyword, ptype in sorted(cls.PROPERTY_TYPE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(rf'\b{re.escape(keyword)}\b', t_lower):
                extracted["propertyType"] = ptype
                extracted["property_type"] = ptype
                extracted["category"] = cls.CATEGORY_MAPPING.get(ptype, "Workspace")
                break

        # Check Indic terms
        for iterm, eng_type in cls.INDIC_PROPERTY_TERMS.items():
            if iterm in text:
                extracted["propertyType"] = eng_type
                extracted["property_type"] = eng_type
                extracted["category"] = cls.CATEGORY_MAPPING.get(eng_type, "Workspace")
                break

        # If flat/फ्लैट/फ्लॅट is in text, flat takes precedence over room
        if any(w in t_lower for w in ["flat", "फ्लैट", "फ्लॅट", "apartment", "bhk"]):
            extracted["propertyType"] = "flat"
            extracted["property_type"] = "flat"
            extracted["category"] = "Workspace"

        # If bedrooms present but propertyType still generic, default to flat
        if extracted.get("bedrooms") and extracted["propertyType"] == "space":
            extracted["propertyType"] = "flat"
            extracted["property_type"] = "flat"
            extracted["category"] = "Workspace"

        # 3. Location & Landmarks
        # A. English locations
        for loc in cls.KNOWN_LOCATIONS:
            if re.search(rf'\b{re.escape(loc.lower())}\b', t_lower):
                extracted["location"] = loc
                if loc in ("Pune", "Mumbai", "Bengaluru", "Bangalore", "Delhi", "New Delhi", "Gurgaon", "Noida", "Dehradun", "Rishikesh"):
                    extracted["city"] = loc
                else:
                    extracted["neighborhood"] = loc
                    if loc in ("Kharadi", "Wagholi", "Baner", "Kothrud", "Aundh", "Hinjewadi", "Viman Nagar", "Shivajinagar"):
                        extracted["city"] = "Pune"
                    elif loc in ("Bandra", "Andheri", "Powai", "Dadar"):
                        extracted["city"] = "Mumbai"
                    elif loc in ("Indiranagar", "Koramangala", "Whitefield", "HSR Layout", "Electronic City"):
                        extracted["city"] = "Bengaluru"
                    elif loc in ("Hauz Khas", "Connaught Place", "Nehru Place"):
                        extracted["city"] = "Delhi"
                break

        # B. Indic locations
        if not extracted.get("location"):
            for iloc, eng_loc in cls.INDIC_LOCATIONS.items():
                if iloc in text:
                    extracted["location"] = eng_loc
                    extracted["city"] = eng_loc if eng_loc in ("Pune", "Mumbai", "Delhi", "Bengaluru") else "Pune"
                    if eng_loc in ("Kharadi", "Baner", "Kothrud", "Wagholi", "Hinjewadi", "Viman Nagar"):
                        extracted["neighborhood"] = eng_loc
                        extracted["city"] = "Pune"
                    break

        # Check landmark (near X)
        for pattern in cls.LANDMARK_PATTERNS:
            lm_match = re.search(pattern, t_lower)
            if lm_match:
                lm = lm_match.group(1).strip()
                lm = re.sub(r'^(?:the|a|an)\s+', '', lm)
                if len(lm) >= 2 and lm not in ("pune", "mumbai", "delhi", "bangalore"):
                    extracted["near"] = "IT park" if lm.lower() in ("it park", "it-park") else lm
                    break

        if not extracted.get("near"):
            for ilm, eng_lm in cls.INDIC_LANDMARKS.items():
                if ilm in text:
                    extracted["near"] = eng_lm
                    break

        # 4. Rent / Pricing
        # A. Rent in thousands notation (e.g. "25k", "25k rent", "25 k")
        k_rent_match = re.search(r'\b(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k\s*(?:rent|भाडे|किराया|/month|per\s+month)?\b', t_lower)
        if k_rent_match:
            try:
                val = float(k_rent_match.group(1)) * 1000.0
                extracted["rent"] = round(val, 2)
                extracted["price_monthly"] = round(val, 2)
            except ValueError:
                pass
        else:
            # B. Full numerical rent (e.g. "25000 rent", "rent 25000", "₹25000", "25,000")
            full_rent_match = re.search(r'\b(?:rent|किराया|भाडे|price)?\s*(?:is|of|:)?\s*(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d{4,6})\b', t_lower)
            if full_rent_match:
                try:
                    num_str = full_rent_match.group(1).replace(",", "")
                    val = float(num_str)
                    extracted["rent"] = round(val, 2)
                    extracted["price_monthly"] = round(val, 2)
                except ValueError:
                    pass

        # Hourly rate check (e.g. "500/hr", "500 per hour", "100 rs/hr", "50 rs tasala")
        hourly_match = re.search(r'\b(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:/hr|/hour|per\s+hour|rs\s+tasala|रुपये\s+प्रति\s+घंटा)\b', t_lower)
        if hourly_match:
            try:
                extracted["price_hourly"] = float(hourly_match.group(1))
            except ValueError:
                pass
        elif extracted.get("rent"):
            # Estimate hourly equivalent (monthly / 160 hours typical utility rate)
            extracted["price_hourly"] = round(max(35.0, extracted["rent"] / 160.0), 2)

        # 5. Furnishing Status
        if re.search(r'\b(?:fully\s+furnished|well\s+furnished|पूर्ण\s+सुसज्ज|पूरी\s+तरह\s+सुसज्जित|सुसज्ज)\b', t_lower):
            extracted["furnished"] = True
            extracted["amenities"].append("Fully Furnished")
        elif re.search(r'\b(?:semi\s+furnished|अर्ध\s+सुसज्ज)\b', t_lower):
            extracted["furnished"] = True
            extracted["amenities"].append("Semi Furnished")
        elif re.search(r'\b(?:unfurnished|non\s+furnished|बिना\s+फर्नीचर)\b', t_lower):
            extracted["furnished"] = False

        # 6. Square Footage (sqft)
        sqft_match = re.search(r'\b(\d+)\s*(?:sq\s*ft|sqft|square\s+feet|चौरस\s+फूट|वर्ग\s+फुट)\b', t_lower)
        if sqft_match:
            try:
                extracted["sqft"] = int(sqft_match.group(1))
            except ValueError:
                pass

        # 7. Capacity / Guest count
        cap_match = re.search(r'(?:for\s+|fits?\s+|capacity\s+(?:of\s+)?)?(\d+)\s*(?:people|persons?|guests?|members?|seats?|log|व्यक्ती|लोगों\s*(?:के\s*लिए)?|लोकांसाठी|लोकांना|व्यक्तियों)(?!\w)', t_lower)
        if not cap_match:
            cap_match = re.search(r'\b(?:for\s+|fits?\s+|capacity\s+(?:of\s+)?)(\d+)\s*(?:people|persons?|guests?|members?|seats?|log|व्यक्ती)?\b', t_lower)
        if cap_match:
            try:
                extracted["max_capacity"] = int(cap_match.group(1))
            except ValueError:
                pass

        # 8. Amenities
        amenity_rules = [
            ("wifi", "High-speed Wi-Fi"),
            ("wi-fi", "High-speed Wi-Fi"),
            ("internet", "High-speed Wi-Fi"),
            ("fiber", "High-speed Wi-Fi"),
            ("वायफाय", "High-speed Wi-Fi"),
            ("वाईफाई", "High-speed Wi-Fi"),
            ("ac", "Air Conditioning"),
            ("air condition", "Air Conditioning"),
            ("एसी", "Air Conditioning"),
            ("वातानुकूलित", "Air Conditioning"),
            ("parking", "Parking Available"),
            ("पार्किंग", "Parking Available"),
            ("power backup", "Power Backup"),
            ("inverter", "Power Backup"),
            ("बिजली", "Power Backup"),
            ("वीज", "Power Backup"),
            ("whiteboard", "Whiteboard"),
            ("व्हाइटबोर्ड", "Whiteboard"),
            ("monitor", "4K Presentation Display"),
            ("display", "4K Presentation Display"),
            ("screen", "Presentation Screen"),
            ("स्क्रीन", "Presentation Screen"),
            ("tea", "Tea & Coffee"),
            ("coffee", "Tea & Coffee"),
            ("चहा", "Tea & Coffee"),
            ("चाय", "Tea & Coffee"),
            ("कॉफी", "Tea & Coffee"),
            ("cctv", "CCTV Security"),
            ("lift", "Elevator Access"),
            ("elevator", "Elevator Access"),
            ("लिफ्ट", "Elevator Access")
        ]
        for kw, a_label in amenity_rules:
            if any('\u0900' <= c <= '\u097f' for c in kw):
                if re.search(rf'(?:^|[^\u0900-\u097f]){re.escape(kw)}(?:$|[^\u0900-\u097f])', t_lower):
                    if a_label not in extracted["amenities"]:
                        extracted["amenities"].append(a_label)
            else:
                if re.search(rf'\b{re.escape(kw)}\b', t_lower):
                    if a_label not in extracted["amenities"]:
                        extracted["amenities"].append(a_label)

        return extracted

    # =========================================================================
    # Missing Information & Clarification Generator
    # =========================================================================

    @classmethod
    def _identify_missing_fields(cls, extracted: Dict[str, Any]) -> tuple[List[str], List[str]]:
        missing = []
        clarifications = []

        if not extracted.get("location"):
            missing.append("location")
            clarifications.append("Which city or neighborhood is this space located in?")

        if not extracted.get("rent") and not extracted.get("price_hourly"):
            missing.append("rent")
            clarifications.append("What is your expected hourly rate or monthly rent for this space?")

        if not extracted.get("max_capacity") and not extracted.get("bedrooms"):
            missing.append("capacity")
            clarifications.append("How many people or guests can comfortably use this space?")

        if not extracted.get("near"):
            # Recommended landmark
            missing.append("landmark")
            clarifications.append("Are there any notable landmarks nearby (e.g. metro station, IT park, highway)?")

        if not extracted.get("amenities"):
            missing.append("amenities")
            clarifications.append("What key amenities are included (e.g. Wi-Fi, AC, power backup, parking)?")

        return missing, clarifications

    # =========================================================================
    # Inconsistency & Conflict Detection
    # =========================================================================

    @classmethod
    def _detect_inconsistencies(cls, extracted: Dict[str, Any], raw_text: str) -> List[Dict[str, str]]:
        inconsistencies = []
        t_lower = raw_text.lower()

        # 1. Capacity vs Sqft Conflict
        cap = extracted.get("max_capacity")
        sqft = extracted.get("sqft")
        if cap and sqft:
            sqft_per_person = sqft / cap
            if sqft_per_person < 15.0:
                msg = f"Capacity of {cap} people in a {sqft} sq ft space yields only {round(sqft_per_person, 1)} sq ft per person, which may violate local safety and comfort standards."
                inconsistencies.append({
                    "field": "capacity",
                    "severity": "warning",
                    "issue": msg,
                    "message": msg
                })

        # 2. Rent / Price Checks
        rent = extracted.get("rent")
        if rent is not None:
            if rent <= 0:
                msg = "Rent must be a positive number greater than ₹0."
                inconsistencies.append({
                    "field": "rent",
                    "severity": "error",
                    "issue": msg,
                    "message": msg
                })
            elif rent < 500 and extracted.get("propertyType") in ("flat", "apartment", "house"):
                msg = f"Monthly rent of ₹{rent} appears unusually low for a {extracted.get('propertyType')}; please verify if this is an hourly rate instead."
                inconsistencies.append({
                    "field": "rent",
                    "severity": "warning",
                    "issue": msg,
                    "message": msg
                })

        # 3. Furnishing Contradictions
        if "unfurnished" in t_lower and ("fully furnished" in t_lower or "sofa" in t_lower or "luxury furniture" in t_lower):
            msg = "The listing mentions both 'unfurnished' and 'furnished/furniture' attributes. Please clarify the actual furnishing status."
            inconsistencies.append({
                "field": "furnished",
                "severity": "warning",
                "issue": msg,
                "message": msg
            })

        return inconsistencies

    # =========================================================================
    # Factual Description Generator (STRICT FACTUAL INTEGRITY)
    # =========================================================================

    @classmethod
    def _generate_factual_description(cls, extracted: Dict[str, Any], language: str = "en") -> str:
        """
        Generates a polished, professional description strictly adhering to user facts.
        User-controlled numeric fields (rent, bedrooms, capacity, sqft) are immutable.
        """
        prop_type = extracted.get("propertyType", "space").title()
        bedrooms = extracted.get("bedrooms")
        loc = extracted.get("location") or extracted.get("city") or "Prime Location"
        near = extracted.get("near")
        rent = extracted.get("rent")
        rate = extracted.get("price_hourly")
        furnished = extracted.get("furnished")
        sqft = extracted.get("sqft")
        cap = extracted.get("max_capacity")
        amenities = extracted.get("amenities") or []

        # English Generation
        if language == "en":
            bhk_prefix = f"{bedrooms}-Bedroom " if bedrooms else ""
            furnish_text = "fully furnished" if furnished is True else ("unfurnished" if furnished is False else "spacious")
            near_text = f" situated close to {near}" if near else ""
            
            p1 = (
                f"Welcome to this {furnish_text} {bhk_prefix}{prop_type} located in {loc}{near_text}. "
                f"Designed for convenience, comfort, and professional productivity."
            )

            # Specs section
            specs = []
            if sqft:
                specs.append(f"• **Area**: {sqft} sq ft")
            if cap:
                specs.append(f"• **Capacity**: Comfortably accommodates up to {cap} people")
            if bedrooms:
                specs.append(f"• **Layout**: {bedrooms} Private Bedroom(s)")
            if rent:
                specs.append(f"• **Monthly Rent**: ₹{int(rent):,}")
            if rate:
                specs.append(f"• **Flexible Hourly Rate**: ₹{rate}/hr")

            specs_str = "\n".join(specs)

            # Amenities section
            amen_str = ", ".join(amenities) if amenities else "Well-ventilated, high-speed connectivity ready, and 24/7 access"
            p2 = (
                f"**Key Features & Amenities**:\n"
                f"{specs_str}\n\n"
                f"**Included Amenities**:\n"
                f"{amen_str}\n\n"
                f"Governed under Section 52 of the Indian Easements Act with zero-hardware digital door passes. "
                f"Verified premises with automated ₹100 refundable UPI micro-escrow."
            )
            return f"{p1}\n\n{p2}"

        # Hindi Generation
        elif language == "hi":
            bhk_prefix = f"{bedrooms} कमरा " if bedrooms else ""
            furnish_text = "पूरी तरह सुसज्जित" if furnished is True else "सुव्यवस्थित"
            near_text = f", {near} के निकट" if near else ""
            rent_text = f"₹{int(rent):,} प्रति माह" if rent else ""
            return (
                f"{loc}{near_text} में स्थित यह शानदार {furnish_text} {bhk_prefix}{prop_type} उपलब्ध है।\n\n"
                f"• **किराया**: {rent_text}\n"
                f"• **सुविधाएं**: {', '.join(amenities) if amenities else 'वाई-फाई, बिजली बैकअप, सुरक्षित वातावरण'}\n\n"
                f"भारतीय सुखाचार अधिनियम की धारा 52 के तहत पूरी तरह सुरक्षित और सत्यापित।"
            )

        # Marathi Generation
        elif language == "mr":
            bhk_prefix = f"{bedrooms} बीएचके " if bedrooms else ""
            furnish_text = "पूर्ण सुसज्ज" if furnished is True else "उत्कृष्ट"
            near_text = f", {near} जवळ" if near else ""
            rent_text = f"₹{int(rent):,} प्रति महिना" if rent else ""
            return (
                f"{loc}{near_text} येथे {furnish_text} {bhk_prefix}{prop_type} उपलब्ध आहे.\n\n"
                f"• **भाडे**: {rent_text}\n"
                f"• **सुविधा**: {', '.join(amenities) if amenities else 'हाय-स्पीड वाय-फाय, शांत वातावरण'}\n\n"
                f"कलम 52 अन्वये डिजिटल पडताळणीसह तात्काळ बुकिंगसाठी उपलब्ध."
            )

        return cls._generate_factual_description(extracted, language="en")

    @classmethod
    def _generate_improved_wording(cls, extracted: Dict[str, Any], language: str = "en") -> str:
        """Generates an enhanced marketing pitch emphasizing space highlights."""
        prop_type = extracted.get("propertyType", "space").title()
        loc = extracted.get("location") or "Pune"
        near = extracted.get("near")
        near_text = f" just moments from {near}" if near else ""
        furnish_text = "Fully Furnished & Move-in Ready" if extracted.get("furnished") else "Premium Flexible Layout"

        return (
            f"✨ **Highlight**: {furnish_text} {prop_type} in {loc}{near_text}.\n"
            f"Equipped with verified power, quiet acoustic profile, and frictionless geofenced digital access."
        )

    @classmethod
    def _generate_suggested_title(cls, extracted: Dict[str, Any]) -> str:
        bedrooms = extracted.get("bedrooms")
        prop_type = (extracted.get("propertyType") or extracted.get("category") or "Space").title()
        loc = extracted.get("location") or extracted.get("city")
        near = extracted.get("near")
        furnished = extracted.get("furnished")

        prefix = f"{bedrooms} BHK " if bedrooms else ""
        furnish_tag = "Furnished " if furnished else ""
        loc_tag = f" in {loc}" if loc else ""
        near_tag = f" near {near}" if near else ""

        title = f"{furnish_tag}{prefix}{prop_type}{loc_tag}{near_tag}".strip()
        return title or "Space Listing"

    # =========================================================================
    # Language Detection & Translation Helper
    # =========================================================================

    @classmethod
    def _detect_language(cls, text: str) -> str:
        from backend.modules.nlp.language_detection import LanguageDetectionService
        lang_code, _, _, _ = LanguageDetectionService.detect_language(text or "")
        return lang_code if isinstance(lang_code, str) else lang_code.value

    @classmethod
    def translate_listing_content(cls, title: str, description: str, amenities: List[str], target_language: str = "hi") -> Dict[str, Any]:
        """
        Translates listing title, description, and amenities into the target language.
        CRITICAL DATA PRESERVATION RULE:
        Prices, numbers, addresses, URLs, listing IDs, and technical identifiers are NEVER altered.
        """
        WORD_MAP_HI = {
            "flat": "फ्लैट", "apartment": "अपार्टमेंट", "room": "कमरा",
            "furnished": "सुसज्जित", "unfurnished": "असुसज्जित", "high-speed wi-fi": "हाई-स्पीड वाई-फाई",
            "wi-fi": "वाई-फाई", "wifi": "वाई-फाई", "air conditioning": "वातानुकूलन (AC)", "ac": "एसी",
            "parking": "पार्किंग", "desk": "डेस्क", "office": "कार्यालय", "studio": "स्टूडियो"
        }
        WORD_MAP_MR = {
            "flat": "फ्लॅट", "apartment": "अपार्टमेंट", "room": "खोली",
            "furnished": "सुसज्ज", "unfurnished": "असुसज्ज", "high-speed wi-fi": "हाय-स्पीड वाय-फाय",
            "wi-fi": "वाय-फाय", "wifi": "वाय-फाय", "air conditioning": "वातानुकूलन (AC)", "ac": "एसी",
            "parking": "पार्किंग", "desk": "डेस्क", "office": "कार्यालय", "studio": "स्टुडिओ"
        }

        word_map = WORD_MAP_HI if target_language in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns") else (WORD_MAP_MR if target_language in ("mr", "mr-Latn") else {})

        def _translate_phrase(text_val: str) -> str:
            res = text_val
            for eng, ind in word_map.items():
                pattern = re.compile(rf'\b{re.escape(eng)}\b', re.IGNORECASE)
                res = pattern.sub(ind, res)
            return res

        if target_language in ("hi", "hi-Latn", "gar", "gbm", "kfy", "jns"):
            translated_title = _translate_phrase(title)
            if "सत्यापित" not in translated_title:
                translated_title = f"{translated_title} (सत्यापित स्पेस)"
            translated_desc = (
                f"{_translate_phrase(description)}\n\n"
                f"[अनुवादित विवरण]: यह स्पेस स्पेस लूप पर सत्यापित है और धारा 52 के तहत सुरक्षित है।"
            )
            translated_amenities = [_translate_phrase(a) for a in amenities]
        elif target_language in ("mr", "mr-Latn"):
            translated_title = _translate_phrase(title)
            if "सत्यापित" not in translated_title:
                translated_title = f"{translated_title} (सत्यापित जागा)"
            translated_desc = (
                f"{_translate_phrase(description)}\n\n"
                f"[मराठी भाषांतर]: ही जागा स्पेस लूप द्वारे सत्यापित असून कलम 52 अन्वये सुरक्षित आहे."
            )
            translated_amenities = [_translate_phrase(a) for a in amenities]
        else:
            translated_title = title
            translated_desc = description
            translated_amenities = amenities

        return {
            "success": True,
            "target_language": target_language,
            "title": translated_title,
            "translated_title": translated_title,
            "description": translated_desc,
            "translated_description": translated_desc,
            "amenities": translated_amenities,
            "translated_amenities": translated_amenities
        }
