"""
SpaceLoop Conversational Context & State Management
Tracks multi-turn marketplace query refinement and maintains structured session constraints across chat turns.
Example:
  Turn 1: "Find me a workspace in Kharadi" -> Location: Kharadi, Type: Workspace
  Turn 2: "For 6 people" -> Capacity: 6, Location: Kharadi, Type: Workspace
  Turn 3: "Tomorrow evening" -> Date: tomorrow, Time: evening, Capacity: 6, Location: Kharadi
"""
from typing import Dict, Any, List, Optional
from backend.modules.nlp.schemas import (
    ExtractedEntities,
    LocationConstraint,
    CapacityConstraint,
    PriceConstraint,
    TimeWindow
)


from typing import Dict, Any, List, Optional
import re
from backend.modules.nlp.schemas import (
    ExtractedEntities,
    LocationConstraint,
    CapacityConstraint,
    PriceConstraint,
    TimeWindow
)


class ConversationalContextManager:
    """
    Manages stateful constraint merging and entity reference resolution across conversational dialogue turns.
    """

    @classmethod
    def extract_recent_candidate_spaces(cls, history: List[Dict[str, Any]]) -> List[int]:
        """
        Extracts space IDs referenced in recent conversation messages (user or assistant).
        Returns unique IDs in chronological order of appearance in recent turns.
        """
        found_ids: List[int] = []
        for turn in reversed(history or []):
            if not isinstance(turn, dict):
                continue
            content = turn.get("content", "")
            # Look for /space/{id} or Space #{id} or #(\d+)
            space_links = re.findall(r"/space/(\d+)", content)
            space_hashes = re.findall(r"(?:space|listing|#)\s*#?(\d+)", content, flags=re.IGNORECASE)
            for sid_str in space_links + space_hashes:
                try:
                    sid = int(sid_str)
                    if sid not in found_ids and 0 < sid < 100000:
                        found_ids.append(sid)
                except (ValueError, TypeError):
                    pass
            if len(found_ids) >= 5:
                break
        return found_ids

    @classmethod
    def resolve_referenced_space_id(
        cls,
        text: str,
        history: List[Dict[str, Any]],
        context_data: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Resolves anaphoric and ordinal space references (e.g. "first one", "space #2", "second", "that space")
        to a concrete space ID from conversation history.
        """
        clean = (text or "").lower().strip()
        
        # 1. Direct explicit ID match (e.g. "space 4", "#4", "listing 2")
        explicit = re.search(r"(?:space|listing|#)\s*#?(\d+)", clean)
        if explicit:
            try:
                return int(explicit.group(1))
            except (ValueError, TypeError):
                pass

        # 2. Check candidate spaces from recent history
        candidate_ids = cls.extract_recent_candidate_spaces(history)

        # Ordinal mapping
        first_patterns = [r"\bfirst\b", r"\b1st\b", r"\bpehla\b", r"\bpehle\b", r"पहला", r"पहिली", r"पहिले"]
        second_patterns = [r"\bsecond\b", r"\b2nd\b", r"\bdoosra\b", r"\bdoosre\b", r"दूसरा", r"दुसरी", r"दुसरे"]
        third_patterns = [r"\bthird\b", r"\b3rd\b", r"\bteesra\b", r"\bteesre\b", r"तीसरा", r"तिसरी"]

        if any(re.search(p, clean) for p in first_patterns):
            if candidate_ids:
                return candidate_ids[0]

        if any(re.search(p, clean) for p in second_patterns):
            if len(candidate_ids) >= 2:
                return candidate_ids[1]
            elif candidate_ids:
                return candidate_ids[-1]

        if any(re.search(p, clean) for p in third_patterns):
            if len(candidate_ids) >= 3:
                return candidate_ids[2]
            elif candidate_ids:
                return candidate_ids[-1]

        # Anaphoric references ("that one", "that space", "there", "usme", "tethe")
        anaphoric = [r"\bthat\s+(?:one|space|room|desk|place)\b", r"\bthis\s+(?:one|space|room|desk)\b", r"\bthere\b", r"\busme\b", r"\btethe\b", r"उसमें", r"त्यामध्ये"]
        if any(re.search(p, clean) for p in anaphoric):
            if candidate_ids:
                return candidate_ids[0]
            if context_data and context_data.get("space_id"):
                try:
                    return int(context_data["space_id"])
                except (ValueError, TypeError):
                    pass

        return None

    @classmethod
    def merge_with_history(
        cls,
        current_entities: ExtractedEntities,
        history: List[Dict[str, Any]],
        session_state: Optional[Dict[str, Any]] = None
    ) -> ExtractedEntities:
        """
        Merges current turn entities with accumulated constraints from conversation history.
        """
        accumulated = cls._extract_accumulated_state(history, session_state)
        merged = ExtractedEntities()

        # 1. Location: Current overrides previous, else inherit previous
        if current_entities.location:
            merged.location = current_entities.location
        elif accumulated.get("location"):
            merged.location = accumulated["location"]

        # 2. Capacity: Current overrides previous, else inherit previous
        if current_entities.capacity:
            merged.capacity = current_entities.capacity
        elif accumulated.get("capacity"):
            merged.capacity = accumulated["capacity"]

        # 3. Price: Current overrides previous, else inherit previous
        if current_entities.price:
            merged.price = current_entities.price
        elif accumulated.get("price"):
            merged.price = accumulated["price"]

        # 4. Time Window & Date: Merge fields intelligently
        merged_tw = TimeWindow()
        prev_tw = accumulated.get("time_window")
        curr_tw = current_entities.time_window

        if prev_tw:
            merged_tw.date_str = prev_tw.date_str
            merged_tw.target_date = prev_tw.target_date
            merged_tw.time_range_name = prev_tw.time_range_name
            merged_tw.start_hour = prev_tw.start_hour
            merged_tw.end_hour = prev_tw.end_hour
            merged_tw.duration_hours = prev_tw.duration_hours

        if curr_tw:
            if curr_tw.date_str:
                merged_tw.date_str = curr_tw.date_str
                merged_tw.target_date = curr_tw.target_date
            if curr_tw.time_range_name:
                merged_tw.time_range_name = curr_tw.time_range_name
            if curr_tw.start_hour:
                merged_tw.start_hour = curr_tw.start_hour
            if curr_tw.end_hour:
                merged_tw.end_hour = curr_tw.end_hour
            if curr_tw.duration_hours:
                merged_tw.duration_hours = curr_tw.duration_hours

        if merged_tw.date_str or merged_tw.time_range_name or merged_tw.duration_hours or merged_tw.start_hour:
            merged.time_window = merged_tw

        # 5. Space Types: If current turn introduces a new type, replace old; else inherit
        if current_entities.space_types:
            merged.space_types = current_entities.space_types
            merged.primary_category = current_entities.primary_category
        elif accumulated.get("space_types"):
            merged.space_types = accumulated["space_types"]
            merged.primary_category = accumulated.get("primary_category")

        # 6. Purpose & Activities: Union
        all_purposes = set(current_entities.purpose_activities)
        if accumulated.get("purpose_activities"):
            all_purposes.update(accumulated["purpose_activities"])
        merged.purpose_activities = list(all_purposes)

        # 7. Amenities: Union
        all_amenities = set(current_entities.amenities)
        if accumulated.get("amenities"):
            all_amenities.update(accumulated["amenities"])
        merged.amenities = sorted(list(all_amenities))

        # 8. Soft Preferences: Union
        all_soft = set(current_entities.soft_preferences)
        if accumulated.get("soft_preferences"):
            all_soft.update(accumulated["soft_preferences"])
        merged.soft_preferences = sorted(list(all_soft))

        # 9. Listing ID
        merged.listing_id = current_entities.listing_id or accumulated.get("listing_id")

        return merged

    @classmethod
    def _extract_accumulated_state(
        cls,
        history: List[Dict[str, Any]],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        if session_state and isinstance(session_state, dict):
            state.update(session_state)

        from backend.modules.nlp.entity_extraction import EntityExtractionService
        from backend.modules.nlp.text_normalization import TextNormalizationService

        for turn in (history or []):
            if isinstance(turn, dict) and turn.get("role") == "user":
                msg = turn.get("content", "")
                if msg:
                    norm = TextNormalizationService.normalize(msg)
                    ent = EntityExtractionService.extract_entities(norm)
                    if ent.location:
                        state["location"] = ent.location
                    if ent.guest_count:
                        state["capacity"] = ent.guest_count
                    if ent.max_price:
                        state["price"] = ent.max_price
                    if ent.time_window_details:
                        state["time_window"] = ent.time_window_details
                    if ent.space_types:
                        state["space_types"] = ent.space_types
                        state["primary_category"] = ent.property_type
                    if ent.amenities:
                        state["amenities"] = ent.amenities
                    if ent.soft_preferences:
                        state["soft_preferences"] = ent.soft_preferences
                    if ent.purpose_activities:
                        state["purpose_activities"] = ent.purpose_activities
                    if ent.listing_id:
                        state["listing_id"] = ent.listing_id

        return state

