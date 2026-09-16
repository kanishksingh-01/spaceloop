# AI Engine Rules
- Multi-Tier Resilience: Route to Groq (Llama 3.3 70B) -> Gemini Flash -> Heuristic Engine fallback.
- Security: Always enclose untrusted user/host notes inside `<user_untrusted_notes>` tags to stop prompt injection.
- Determinism: Guarantee fallback heuristic outputs for all endpoints when external LLMs are unreachable.
