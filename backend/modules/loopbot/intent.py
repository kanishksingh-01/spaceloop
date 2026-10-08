"""
SpaceLoop LoopBot Intent & Entity Classifier
===========================================
Classifies user queries across the 18 canonical intents and extracts
relevant operational slots (location, capacity, dates, duration, budget, etc.).
"""
import re
from typing import Any, Optional
from backend.modules.loopbot.schemas import LoopBotIntent


NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "solo": 1, "pair": 2, "couple": 2
}


class LoopBotIntentClassifier:
    """
    Deterministic regex and keyword-based intent classifier with slot extraction.
    Ensures zero hallucination and high-precision mapping to the 18 platform capabilities.
    """

    @classmethod
    def classify(cls, query: str, context: Optional[dict[str, Any]] = None) -> tuple[LoopBotIntent, dict[str, Any]]:
        clean_q = (query or "").lower().strip()
        context = context or {}
        slots = cls.extract_slots(clean_q, context)

        # 1. Immediate ID references
        has_space_id = bool(slots.get("selected_space_id"))
        has_booking_id = bool(slots.get("selected_booking_id"))

        # 2. Consequential actions: Cancellation
        if any(k in clean_q for k in [
            "cancel booking", "cancel my booking", "cancel reservation", "cancel the booking",
            "cancel my reservation", "cancel slot", "booking cancel karni", "cancel kar do"
        ]):
            return LoopBotIntent.BOOKING_CANCEL, slots

        # 3. Consequential actions: Create Booking
        if any(k in clean_q for k in [
            "book this space", "book space", "book now", "reserve this space",
            "reserve space", "confirm booking", "i want to book", "book for",
            "reserve for", "place booking", "booking karna hai", "book kara"
        ]) or (clean_q.startswith("book ") and not "status" in clean_q):
            return LoopBotIntent.BOOKING_CREATE, slots

        # 4. Access Status vs Access Help
        if any(k in clean_q for k in [
            "access status", "can i enter", "unlock door", "is my pass active",
            "my pass", "door pass", "arrival pin", "my pin", "where is my pin",
            "check in pass", "checkin pass", "enter the space"
        ]):
            return LoopBotIntent.ACCESS_STATUS, slots

        if any(k in clean_q for k in [
            "how to enter", "how does access work", "50m geofence", "zero hardware",
            "geofenced access", "how to unlock", "caretaker pin", "access work",
            "smart access", "how do i check in", "check-in work", "check in work"
        ]):
            return LoopBotIntent.ACCESS_HELP, slots

        # 5. Escrow Status vs Refund Help
        if any(k in clean_q for k in [
            "my escrow", "escrow status", "where is my deposit", "deposit status",
            "where is my 100", "did i get my 100", "my 100 rupees", "100 deposit",
            "deposit refunded", "escrow hold"
        ]):
            return LoopBotIntent.ESCROW_STATUS, slots

        if any(k in clean_q for k in [
            "refund policy", "how do refunds work", "120 second refund", "instant refund",
            "when do i get refund", "refund criteria", "refund rules", "how to get deposit back",
            "refund kaise milta hai", "refund kiti velat"
        ]):
            return LoopBotIntent.REFUND_HELP, slots

        # 6. Booking Status
        if any(k in clean_q for k in [
            "my booking", "booking status", "my reservations", "check my booking",
            "active booking", "upcoming booking", "show booking", "booking details",
            "meri booking", "majhi booking"
        ]):
            return LoopBotIntent.BOOKING_STATUS, slots

        # 7. Space Availability
        if any(k in clean_q for k in [
            "available tomorrow", "is this available", "check availability",
            "open slots", "availability for", "free tomorrow", "free today",
            "when is it open", "slots available", "khali hai", "available ahe ka"
        ]) or ("available" in clean_q and not "search" in clean_q):
            return LoopBotIntent.SPACE_AVAILABILITY, slots

        # 8. Space Details
        if has_space_id and any(k in clean_q for k in [
            "amenities", "rules", "specs", "photos", "about this space", "details of",
            "tell me about space", "view space", "what does space", "lighting", "noise floor"
        ]):
            return LoopBotIntent.SPACE_DETAILS, slots

        if any(k in clean_q for k in [
            "what amenities", "amenities in this space", "can i bring food", "house rules",
            "smoking policy", "noise level", "is there wifi", "power backup"
        ]) and context.get("selected_space_id"):
            return LoopBotIntent.SPACE_DETAILS, slots

        # 9. Legal Information
        if any(k in clean_q for k in [
            "section 52", "easements act", "legal protection", "adverse possession",
            "squatting", "tenancy rights", "rent control", "revocable license",
            "micro-license", "lease vs license", "dhara 52", "kalam 52", "legal safety"
        ]):
            return LoopBotIntent.LEGAL_INFORMATION, slots

        # 10. Trust & Safety
        if any(k in clean_q for k in [
            "discom", "ca number", "meter verification", "electricity bill", "oti score",
            "trust score", "objective trust", "fake listing", "phantom listing",
            "is this verified", "safety guarantee", "verification process"
        ]):
            return LoopBotIntent.TRUST_SAFETY, slots

        # 11. Disputes & Damage
        if any(k in clean_q for k in [
            "dispute", "report damage", "caretaker issue", "overstay", "conflict",
            "file complaint", "broken item", "theft", "unauthorized person", "dispute resolution"
        ]):
            return LoopBotIntent.DISPUTE_HELP, slots

        # 12. Host Help / Monetization
        if any(k in clean_q for k in [
            "list my space", "how to host", "monetize my space", "host earnings",
            "host payout", "95% yield", "host fee", "become a host", "list property",
            "earn passive income", "space kaise list kare", "host banne ke steps",
            "photo scan", "60-second scan"
        ]):
            return LoopBotIntent.HOST_HELP, slots

        # 13. Seeker Help / Platform Overview
        if any(k in clean_q for k in [
            "how to use spaceloop", "how does spaceloop work", "what is spaceloop",
            "seeker requirements", "student discount", "how to book", "booking steps",
            "digilocker kyc", "documents required to book", "id proof needed"
        ]):
            return LoopBotIntent.SEEKER_HELP, slots

        # 14. Account Help
        if any(k in clean_q for k in [
            "my profile", "update upi", "payout vpa", "my account", "change phone",
            "kyc status", "link digilocker", "reset password", "my details"
        ]):
            return LoopBotIntent.ACCOUNT_HELP, slots

        # 15. Support
        if any(k in clean_q for k in [
            "human agent", "talk to support", "customer care", "contact support",
            "help desk", "talk to human", "reach support", "helpline", "support ticket",
            "customer service"
        ]):
            return LoopBotIntent.SUPPORT, slots

        # 16. Space Search
        if any(k in clean_q for k in [
            "find", "search", "looking for", "need a desk", "need a space", "meeting room",
            "study space", "coworking", "studio", "workshop", "quiet space", "space for",
            "places in", "spaces in", "under", "rs", "inr"
        ]) or slots.get("capacity") or slots.get("location") or slots.get("budget"):
            return LoopBotIntent.SPACE_SEARCH, slots

        # 17. Greetings & General conversation
        if any(k in clean_q for k in [
            "hi", "hello", "hey", "greetings", "namaste", "pranam", "sup",
            "good morning", "good evening", "how are you", "who are you",
            "what can you do", "help me"
        ]) and len(clean_q.split()) <= 4:
            return LoopBotIntent.GENERAL, slots

        return LoopBotIntent.GENERAL, slots

    @classmethod
    def extract_slots(cls, clean_q: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Extracts conversational slots from user query string and active context."""
        slots: dict[str, Any] = {}
        context = context or {}

        # 1. Capacity
        # Must explicitly match people/persons/guests/seats/pax OR "capacity of N" OR "for N" (not time range)
        cap_match = re.search(r"\b(?:capacity\s*(?:of|:)?\s*|for\s+)?(\d+)\s*(?:people|persons|guests|pax|folks|seats|members)\b", clean_q)
        if not cap_match:
            # Match "capacity: 4" or "capacity 4"
            cap_match = re.search(r"\bcapacity\s*(?:of|:)?\s*(\d+)\b", clean_q)
        if not cap_match:
            # Match "for 3" only if not followed by "to", "-", "am", "pm", "hours", "hrs", "rs", "inr"
            for_num_match = re.search(r"\bfor\s+(\d+)\b(?!\s*(?:to|-|am|pm|hours|hrs|h|rs|inr|₹|days|weeks))", clean_q)
            if for_num_match:
                cap_match = for_num_match

        if cap_match:
            try:
                num = int(cap_match.group(1))
                if 1 <= num <= 200:
                    slots["capacity"] = num
            except ValueError:
                pass

        if "capacity" not in slots:
            for word, val in NUMBER_WORDS.items():
                if re.search(rf"\b(for\s+)?{word}\s*(people|persons|guests|folks|seats|pax)?\b", clean_q) and not re.search(rf"\b{word}\s*(to|-)\b", clean_q):
                    slots["capacity"] = val
                    break

        # 2. Duration Hours
        # e.g., "for 2 hours", "3 hrs", "4h", "2.5 hours"
        dur_match = re.search(r"\b(\d+(\.\d+)?)\s*(?:hours?|hrs?|h)\b", clean_q)
        if dur_match:
            try:
                slots["duration_hours"] = float(dur_match.group(1))
            except ValueError:
                pass

        # 3. Budget / Maximum Price
        # e.g., "under 500", "below 400 rs", "max 600", "upto 300 inr", "₹450"
        budget_match = re.search(r"(?:under|below|max|upto|within|budget of)?\s*(?:rs\.?|inr|₹)?\s*(\d{2,5})\s*(?:rs\.?|inr|₹|bucks|per hour|/hr)?", clean_q)
        if budget_match and any(b_key in clean_q for b_key in ["under", "below", "max", "upto", "budget", "rs", "inr", "₹", "bucks"]):
            try:
                b_val = float(budget_match.group(1))
                if 20 <= b_val <= 50000:
                    slots["budget"] = b_val
            except ValueError:
                pass

        # 4. Location
        known_locations = [
            "kharadi", "kothrud", "baner", "viman nagar", "hinjewadi", "wakad",
            "aundh", "kalyani nagar", "hadapsar", "magarpatta", "camp", "shivajinagar",
            "pune", "mumbai", "bandra", "andheri", "dehradun", "rajpur road", "delhi", "noida"
        ]
        for loc in known_locations:
            if re.search(rf"\b{re.escape(loc)}\b", clean_q):
                slots["location"] = loc.title()
                break

        # 5. Date
        if "tomorrow" in clean_q:
            slots["date"] = "tomorrow"
        elif "today" in clean_q or "tonight" in clean_q:
            slots["date"] = "today"
        elif "weekend" in clean_q or "this weekend" in clean_q:
            slots["date"] = "weekend"
        else:
            date_match = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", clean_q)
            if date_match:
                slots["date"] = date_match.group(1).title()

        # 6. Time Range / Start Time & End Time
        time_range_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|till|until)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", clean_q)
        if time_range_match:
            slots["start_time"] = time_range_match.group(1).strip()
            slots["end_time"] = time_range_match.group(2).strip()

        # 7. Amenities
        amenities = []
        amenity_keywords = {
            "wifi": "Wi-Fi", "fiber": "Fiber Internet", "ac": "Air Conditioning",
            "air conditioning": "Air Conditioning", "whiteboard": "Whiteboard",
            "coffee": "Tea/Coffee", "parking": "Parking", "power backup": "Power Backup",
            "projector": "Projector"
        }
        for kw, canonical in amenity_keywords.items():
            if re.search(rf"\b{re.escape(kw)}\b", clean_q):
                amenities.append(canonical)
        if amenities:
            slots["amenities"] = amenities

        # 8. Noise Preference
        if any(k in clean_q for k in ["quiet", "silent", "soundproof", "calm", "study"]):
            slots["noise_preference"] = "Ultra Quiet (<32 dB)"
        elif any(k in clean_q for k in ["collab", "meeting", "call", "podcast", "active"]):
            slots["noise_preference"] = "Conversational (45-55 dB)"

        # 9. Space ID
        space_id_match = re.search(r"(?:space|listing|property|room)?\s*#?(\d+)\b", clean_q)
        if any(sk in clean_q for sk in ["space", "listing", "property", "#"]):
            m = re.search(r"#?(\d+)", clean_q)
            if m:
                try:
                    slots["selected_space_id"] = int(m.group(1))
                except ValueError:
                    pass

        # 10. Booking ID
        booking_id_match = re.search(r"(?:booking|reservation)\s*#?(\d+)\b", clean_q)
        if booking_id_match:
            try:
                slots["selected_booking_id"] = int(booking_id_match.group(1))
            except ValueError:
                pass

        return slots
