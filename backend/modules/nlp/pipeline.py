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

        # If intent is generic or low confidence, but explicit entities like location + type exist,
        # adjust intent to SEARCH_SPACE with appropriate confidence
        if intent == IntentType.CLARIFICATION_NEEDED.value:
            if "location" in entities_dict or "property_type" in entities_dict:
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
