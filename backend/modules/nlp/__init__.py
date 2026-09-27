"""
SpaceLoop NLP Core Processing Layer
Provides multilingual natural language understanding, script detection,
normalization, intent classification, and entity extraction.
"""
from backend.modules.nlp.schemas import (
    LanguageCode,
    IntentType,
    ExtractedEntities,
    StructuredNLPResult
)
from backend.modules.nlp.language_detection import LanguageDetectionService
from backend.modules.nlp.text_normalization import TextNormalizationService
from backend.modules.nlp.intent_service import IntentService
from backend.modules.nlp.entity_extraction import EntityExtractionService
from backend.modules.nlp.pipeline import NLPPipeline
from backend.modules.nlp.i18n import MultilingualService, LANGUAGE_METADATA

__all__ = [
    "LanguageCode",
    "IntentType",
    "ExtractedEntities",
    "StructuredNLPResult",
    "LanguageDetectionService",
    "TextNormalizationService",
    "IntentService",
    "EntityExtractionService",
    "NLPPipeline",
    "MultilingualService",
    "LANGUAGE_METADATA"
]
