# ADR-003: Multi-Tier AI Provider Routing
## Status: Accepted
## Context: External LLM APIs can face rate limits, network outages, or latency spikes.
## Decision: Multi-tier fallback hierarchy: Tier 1 Groq LLaMA 3.3 70B -> Tier 2 Google Gemini Flash -> Tier 3 Deterministic Heuristics.
## Consequences: Guarantees 100% platform uptime and reliable offline testing.
