---
trigger: always_on
---

8. Search, Discovery & Matching
Existing Architecture Only
Use only the existing SpaceLoop search and matching architecture:
AI Components
Gemini for natural-language intent extraction and listing understanding
Deterministic fallback heuristics when AI is unavailable
Ranking Logic
TypeScript-based ranking logic
Haversine proximity scoring
Budget-fit scoring
Tag/keyword overlap
Space-type matching
Existing composite Match Score
Explainable "Why this matches" output
No Parallel Systems
Do not introduce a separate search engine, recommendation system, ranking framework, or competing matching algorithm.
Source of Truth
Existing search and ranking logic is the source of truth. New functionality must extend it rather than create parallel systems.
Deterministic Core
AI may assist with understanding and explanation, but core ranking and matching must remain deterministic, transparent, and reproducible.
Architecture Stability
Do not change these technology or architectural choices unless explicitly instructed by the user.
Rule ID: 8-search-discovery-matching
Priority: Critical
Scope: Search, matching, discovery features