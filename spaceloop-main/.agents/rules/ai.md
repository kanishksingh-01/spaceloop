---
trigger: always_on
---

# AI Engine Rules
- Multi-Tier Resilience: Route to Groq (Llama 3.3 70B) -> Gemini Flash -> Heuristic Engine fallback.
- Security: Always enclose untrusted user/host notes inside `<user_untrusted_notes>` tags to stop prompt injection.
- Determinism: Guarantee fallback heuristic outputs for all endpoints when external LLMs are unreachable.
# SpaceLoop AI Rules

## AI Architecture

All AI functionality must use the centralized AI layer:

backend/ai/

Feature modules must NOT directly call Groq or Gemini.

Use:

Feature
    ↓
AI Service
    ↓
AI Router
    ↓
Provider

## Provider Routing

The preferred provider hierarchy is:

1. Groq Llama 3.3 70B
2. Gemini fallback
3. Deterministic/rule-based fallback

Provider selection must be handled by the AI Router.

Feature modules must not contain provider-specific fallback logic.

## Provider Abstraction

AI providers must implement a common interface.

Provider-specific code belongs in:

backend/ai/providers/

Adding or replacing a provider should not require changes to feature modules.

## Structured Output

Use schemas/models to validate AI responses.

Never blindly trust LLM output.

Validate:

- required fields
- data types
- ranges
- enums
- business constraints

## Prompt Management

Prompts belong in:

backend/ai/prompts/

Do not scatter large prompts throughout business logic.

Keep system instructions separate from user-provided content.

## Prompt Injection

Treat all user input, uploaded text, host notes and external content as untrusted.

Never allow user-provided content to override system instructions.

Use the AI safety layer for:

- input validation
- prompt boundaries
- injection detection where appropriate
- output validation

## Business-Critical Decisions

AI must not be the sole authority for:

- payments
- authorization
- identity verification
- access control
- escrow release
- legal acceptance
- security decisions

AI may recommend or analyze.

Deterministic backend rules must enforce final business constraints.

## Failure Handling

AI failure must not crash the application.

Use appropriate fallback behavior.

Do not silently fabricate AI results.

Log technical failures without logging sensitive user data.

## Token Efficiency

Avoid unnecessary LLM calls.

Reuse deterministic logic where possible.

Do not send large amounts of repository data or unrelated context to an LLM.

Prefer structured, concise prompts and responses.
