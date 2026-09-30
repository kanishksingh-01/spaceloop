"""
SpaceLoop NLP Pipeline Orchestrator
Executes the full 4-stage NLP pipeline:
Language Detection -> Text Normalization -> Intent Extraction -> Entity Extraction -> Structured Result.
Reusable by LoopBot Concierge, Marketplace Search, and Host Listing Assistance.
"""
from typing import Optional, Dict, Any
from backend.modules.nlp.schemas import StructuredNLPResult, IntentType
from backend.modules.nlp.language_detection import LanguageDetectionService
from backend.modules.nlp.text_normalization import TextNormalizationService
from backend.modules.nlp.intent_service import IntentService
from backend.modules.nlp.entity_extraction import EntityExtractionService


class NLPPipeline:
    """
    Unified entry point for SpaceLoop natural language processing.
    """

    @classmethod
    def process(cls, raw_text: str, context_data: Optional[Dict[str, Any]] = None) -> StructuredNLPResult:
        """
        Executes end-to-end NLP analysis on raw user text.
        Returns a strongly-typed StructuredNLPResult.
        """
        if not raw_text or not raw_text.strip():
            return StructuredNLPResult(
                language="und",
                secondary_languages=[],
                is_code_mixed=False,
                normalized_text="",
                intent=IntentType.CLARIFICATION_NEEDED.value,
                confidence=0.0,
                entities={},
                raw_query="",
                metadata={"reason": "empty_input"}
            )

        # Stage 1: Language & Code-Mixing Detection
        primary_lang, sec_langs, is_cm, lang_conf = LanguageDetectionService.detect_language(raw_text)

        # Stage 2: Multilingual Text Normalization
        normalized_text = TextNormalizationService.normalize(raw_text)

        # Stage 3: Multilingual Intent Extraction with low-confidence guardrail
        intent, intent_conf = IntentService.extract_intent(normalized_text, context_data=context_data)

        # Stage 4: Strict Entity Extraction & Range Validation
        extracted_entities = EntityExtractionService.extract_entities(normalized_text, context_data=context_data)
        entities_dict = extracted_entities.to_dict()

        # If intent is low confidence, promote to SEARCH_SPACE only if explicit space keywords
        # or property_type are present (and NOT out-of-scope topics like weather, stocks, crypto)
        if intent == IntentType.CLARIFICATION_NEEDED.value:
            norm_lower = normalized_text.lower()
            out_of_scope = any(w in norm_lower for w in [
                "weather", "temperature", "forecast", "rain",
                "bitcoin", "crypto", "stock", "share market", "trading",
                "recipe", "cricket", "ipl", "politics", "election",
                "disease", "medicine", "doctor", "song", "movie", "lyrics"
            ])
            if not out_of_scope:
                has_space_signal = bool(entities_dict.get("property_type")) or any(
                    k in norm_lower for k in ["space", "room", "desk", "hall", "office", "studio", "rent", "find", "search", "looking for", "need a", "chahiye"]
                )
                if has_space_signal and ("location" in entities_dict or "property_type" in entities_dict):
                    intent = IntentType.SEARCH_SPACE.value
                    intent_conf = 0.82

        return StructuredNLPResult(
            language=primary_lang,
            secondary_languages=sec_langs,
            is_code_mixed=is_cm,
            normalized_text=normalized_text,
            intent=intent,
            confidence=intent_conf,
            entities=entities_dict,
            raw_query=raw_text,
            metadata={
                "language_confidence": round(lang_conf, 3),
                "has_entities": bool(entities_dict)
            }
        )

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

