"""
SpaceLoop Search Engine Module
Lightweight Hybrid Semantic AI Search combining:
- Vector similarity search (Cosine distance)
- Structured deterministic filters (Capacity, Location, Price, Category, Amenities)
- Real-time booking availability validation (Booking conflict overlap)
- Explainable ranking
"""
from backend.modules.search.embedding import (
    build_searchable_representation,
    generate_embedding,
    cosine_similarity
)
from backend.modules.search.query_understanding import understand_search_query
from backend.modules.search.hybrid_search import hybrid_search_spaces

__all__ = [
    "build_searchable_representation",
    "generate_embedding",
    "cosine_similarity",
    "understand_search_query",
    "hybrid_search_spaces"
]
