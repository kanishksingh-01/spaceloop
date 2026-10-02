"""
SpaceLoop NLP Pipeline Orchestrator
Coordinates multi-stage natural language understanding:
Raw Query -> Text Normalization -> Language Detection -> Intent Detection -> Entity Extraction & Normalization
-> Context State Merging -> QueryUnderstanding Object Construction -> Ambiguity Assessment -> Router / Dispatch.
"""
import re
from typing import Optional, Dict, Any, List

from backend.modules.nlp.schemas import (
    StructuredNLPResult,
    QueryUnderstanding,
    ExtractedEntities,
    IntentType,
    LanguageCode
)
from backend.modules.nlp.language_detection import LanguageDetectionService
from backend.modules.nlp.text_normalization import TextNormalizationService
from backend.modules.nlp.intent_service import IntentService
from backend.modules.nlp.entity_extraction import EntityExtractionService
from backend.modules.nlp.context import ConversationalContextManager


class NLPPipeline:
    """
    Unified entry point for SpaceLoop natural language processing and query understanding.
    """

    @classmethod
    def process(cls, raw_text: str, context_data: Optional[Dict[str, Any]] = None) -> StructuredNLPResult:
        """
        Executes end-to-end NLP analysis on raw user text and returns a StructuredNLPResult with QueryUnderstanding.
        """
        context_data = context_data or {}
        if not raw_text or not raw_text.strip():
            empty_entities = ExtractedEntities()
            empty_ir = QueryUnderstanding(
                raw_query="",
                normalized_query="",
                semantic_query="",
                intent=IntentType.CLARIFICATION_NEEDED.value,
                intent_confidence=0.0,
                language=LanguageCode.UNKNOWN.value,
                entities=empty_entities,
                needs_clarification=True,
                clarification_prompt="How can I help you find or manage a space today?",
                overall_confidence=0.0,
                metadata={"reason": "empty_input"}
            )
            return StructuredNLPResult(
                language=LanguageCode.UNKNOWN.value,
                secondary_languages=[],
                is_code_mixed=False,
                normalized_text="",
                intent=IntentType.CLARIFICATION_NEEDED.value,
                confidence=0.0,
                entities={},
                query_understanding=empty_ir,
                raw_query="",
                metadata={"reason": "empty_input"}
            )

        # Stage 1: Multilingual Text Normalization
        normalized_text = TextNormalizationService.normalize(raw_text)

        # Stage 2: Language & Code-Mixing Detection
        primary_lang, sec_langs, is_cm, lang_conf = LanguageDetectionService.detect_language(raw_text)

        # Stage 3: Intent Extraction with confidence grading
        intent, intent_conf = IntentService.extract_intent(normalized_text, context_data=context_data)

        # Stage 4: Entity Extraction & Range Validation
        extracted_entities = EntityExtractionService.extract_entities(normalized_text, context_data=context_data)

        # Stage 5: Conversational History State Merging (if multi-turn dialogue present)
        history = context_data.get("history", [])
        if history:
            extracted_entities = ConversationalContextManager.merge_with_history(
                extracted_entities, history, context_data.get("session_state")
            )

        entities_dict = extracted_entities.to_dict()

        # Intent Guardrail: Promote to SEARCH_SPACE if valid space entities or signals are present
        if intent == IntentType.CLARIFICATION_NEEDED.value:
            norm_lower = normalized_text.lower()
            out_of_scope = any(w in norm_lower for w in [
                "weather", "temperature", "forecast", "rain",
                "bitcoin", "crypto", "cryptocurrency", "ethereum", "eth", "solana", "stock", "share market", "trading",
                "recipe", "cricket", "ipl", "politics", "election",
                "disease", "medicine", "doctor", "song", "movie", "lyrics"
            ])
            if not out_of_scope:
                has_space_signal = bool(extracted_entities.space_types or extracted_entities.location or extracted_entities.guest_count or extracted_entities.capacity_details) or any(
                    k in norm_lower for k in ["space", "room", "desk", "hall", "office", "studio", "rent", "find", "search", "looking for", "need a", "chahiye", "pahije", "around me", "near"]
                )
                if has_space_signal:
                    intent = IntentType.SEARCH_SPACE.value
                    intent_conf = 0.82

        # Stage 6: Build QueryUnderstanding Intermediate Representation (IR)
        query_understanding = cls._build_query_understanding(
            raw_query=raw_text,
            normalized_query=normalized_text,
            intent=intent,
            intent_confidence=intent_conf,
            language=primary_lang,
            is_code_mixed=is_cm,
            entities=extracted_entities,
            context_data=context_data
        )

        return StructuredNLPResult(
            language=primary_lang,
            secondary_languages=sec_langs,
            is_code_mixed=is_cm,
            normalized_text=normalized_text,
            intent=intent,
            confidence=intent_conf,
            entities=entities_dict,
            query_understanding=query_understanding,
            raw_query=raw_text,
            metadata={
                "language_confidence": round(lang_conf, 3),
                "has_entities": bool(entities_dict),
                "needs_clarification": query_understanding.needs_clarification
            }
        )

    @classmethod
    def _build_query_understanding(
        cls,
        raw_query: str,
        normalized_query: str,
        intent: str,
        intent_confidence: float,
        language: str,
        is_code_mixed: bool,
        entities: ExtractedEntities,
        context_data: Dict[str, Any]
    ) -> QueryUnderstanding:
        """
        Constructs the intermediate representation contract between NLP and downstream search.
        """
        # Formulate hard constraints dictionary
        hard_constraints: Dict[str, Any] = {}
        if entities.location:
            hard_constraints["location"] = entities.location
            if entities.location_details:
                if entities.location_details.city:
                    hard_constraints["city"] = entities.location_details.city
                if entities.location_details.is_proximity_query:
                    hard_constraints["is_proximity"] = True
        if entities.property_type:
            hard_constraints["category"] = entities.property_type
        elif entities.space_types:
            hard_constraints["category"] = entities.space_types[0]

        if entities.guest_count:
            hard_constraints["min_capacity"] = entities.guest_count
        elif entities.capacity_details and entities.capacity_details.min_capacity:
            hard_constraints["min_capacity"] = entities.capacity_details.min_capacity

        if entities.max_price:
            hard_constraints["max_price"] = entities.max_price
        if entities.price_details:
            if entities.price_details.max_price and "max_price" not in hard_constraints:
                hard_constraints["max_price"] = entities.price_details.max_price
            if entities.price_details.min_price:
                hard_constraints["min_price"] = entities.price_details.min_price

        if entities.time_window_details:
            tw = entities.time_window_details
            if tw.date_str:
                hard_constraints["date"] = tw.date_str
            if tw.target_date:
                hard_constraints["target_date"] = tw.target_date
            if tw.start_time_str:
                hard_constraints["start_time"] = tw.start_time_str
            if tw.end_time_str:
                hard_constraints["end_time"] = tw.end_time_str
            if tw.duration_hours:
                hard_constraints["duration_hours"] = tw.duration_hours
        elif entities.date_str:
            hard_constraints["date"] = entities.date_str
            if entities.duration_hours:
                hard_constraints["duration_hours"] = entities.duration_hours

        if entities.amenities:
            hard_constraints["amenities"] = entities.amenities

        # Formulate soft preferences list
        soft_preferences = list(entities.soft_preferences)
        if entities.purpose_activities:
            soft_preferences.extend(entities.purpose_activities)
        if entities.price_details and entities.price_details.is_qualitative_budget:
            soft_preferences.append("budget-friendly")

        # Formulate clean semantic query (strip out noisy hard constraint tokens)
        semantic_query = cls._clean_semantic_query(normalized_query, entities)

        # Check Ambiguity & Missing Fields for SEARCH_SPACE queries
        needs_clarification = False
        clarification_prompt = None
        missing_fields = []

        if intent in (IntentType.SEARCH_SPACE.value, IntentType.SEARCH_PROPERTY.value):
            if not entities.location:
                missing_fields.append("location")
            if not entities.guest_count and not (entities.capacity_details and entities.capacity_details.min_capacity):
                missing_fields.append("capacity")
            if not entities.date_str and not (entities.time_window_details and entities.time_window_details.date_str):
                missing_fields.append("date")

            # If user query is super terse (e.g. "I need a meeting room tomorrow" with no capacity or location)
            # generate helpful clarification without blocking search
            if "capacity" in missing_fields and "location" in missing_fields and len(normalized_query.split()) <= 6:
                needs_clarification = True
                clarification_prompt = "Sure! Which city or neighborhood are you looking in, and how many people is this space for?"
            elif "capacity" in missing_fields and len(normalized_query.split()) <= 5:
                needs_clarification = True
                clarification_prompt = "Got it. How many people will be using the space?"
        elif intent == IntentType.CLARIFICATION_NEEDED.value:
            needs_clarification = True
            clarification_prompt = "Could you tell me what kind of space you are looking for (e.g., meeting room, podcast studio, private workspace)?"

        overall_conf = round(min(0.99, max(0.40, (intent_confidence * 0.6) + (0.35 if hard_constraints else 0.15) + 0.05)), 3)

        return QueryUnderstanding(
            raw_query=raw_query,
            normalized_query=normalized_query,
            semantic_query=semantic_query,
            intent=intent,
            intent_confidence=intent_confidence,
            language=language,
            is_code_mixed=is_code_mixed,
            entities=entities,
            hard_constraints=hard_constraints,
            soft_preferences=sorted(list(set(soft_preferences))),
            needs_clarification=needs_clarification,
            clarification_prompt=clarification_prompt,
            missing_fields=missing_fields,
            overall_confidence=overall_conf,
            metadata={"extracted_count": len(hard_constraints)}
        )

    @classmethod
    def _clean_semantic_query(cls, text: str, entities: ExtractedEntities) -> str:
        """Removes hard number tokens and boilerplate words to make semantic vector search cleaner."""
        clean = text.lower()
        # Remove common introductory filler words
        clean = re.sub(r"\b(?:i\s+need|looking\s+for|look\s+for|find\s+me|find|search\s+for|can\s+i\s+find|show\s+me|want\s+a|need\s+a|give\s+me)\b", "", clean)
        # Remove price tokens already captured
        clean = re.sub(r"\b(?:under|below|budget|upto|max|for)\s*₹?\d+(?:\s*(?:/hr|rs|rupees|k))?\b", "", clean)
        # Remove standalone ₹ numbers
        clean = re.sub(r"₹\d+", "", clean)
        # Clean extra spacing
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean if clean else text

    @classmethod
    def dispatch(cls, query: str, context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Unified 3-branch NLP router connecting:
          - LoopBot / RAG (grounded questions, rules, amenities, assistance)
          - Semantic Search (property search queries against live listings)
          - Listing Assistance (natural language space drafts for hosts)
        """
        context_data = context_data or {}
        nlp_result = cls.process(query, context_data=context_data)
        canonical_intent = IntentService.canonicalize_intent(nlp_result.intent)
        explicit_action = context_data.get("action")

        # 1. Listing Assistance Branch
        if explicit_action == "assist_listing" or canonical_intent == IntentType.CREATE_LISTING.value:
            from backend.modules.nlp.listing_assistance import ListingAssistanceService
            draft_res = ListingAssistanceService.assist_listing(query, target_language=nlp_result.language)
            return {
                "success": True,
                "route": "listing_assistance",
                "nlp_result": nlp_result.to_dict(),
                "listing_draft": draft_res,
                "clean_response": draft_res.get("generated_description", ""),
            }

        # 2. Semantic Search Branch
        elif explicit_action == "search" or canonical_intent in (IntentType.SEARCH_SPACE.value, IntentType.SEARCH_PROPERTY.value):
            from backend.modules.search.hybrid_search import hybrid_search_spaces
            entities = nlp_result.entities or {}
            search_res = hybrid_search_spaces(
                raw_query=query,
                location=entities.get("location"),
                category=entities.get("property_type") or entities.get("space_type"),
                min_capacity=entities.get("capacity") or entities.get("guest_count"),
                max_price=entities.get("price") or entities.get("max_price"),
                limit=context_data.get("limit", 10),
            )
            return {
                "success": True,
                "route": "semantic_search",
                "nlp_result": nlp_result.to_dict(),
                "search_results": search_res,
                "clean_response": search_res.get("match_summary", ""),
            }

        # 3. LoopBot / RAG Branch (Conversational, amenities, policies, pricing, help)
        else:
            from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query
            loopbot_res = orchestrate_loopbot_query(
                query,
                history=context_data.get("history", []),
                context_data=context_data,
                return_dict=True,
            )
            reply = loopbot_res.get("reply", "") if isinstance(loopbot_res, dict) else str(loopbot_res)
            return {
                "success": True,
                "route": "loopbot",
                "nlp_result": nlp_result.to_dict(),
                "loopbot_result": loopbot_res if isinstance(loopbot_res, dict) else {"reply": reply},
                "clean_response": reply,
            }
