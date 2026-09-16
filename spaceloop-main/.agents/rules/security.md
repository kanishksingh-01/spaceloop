---
trigger: always_on
---

# Security Rules
- DPDP Act 2023: Zero raw Aadhaar storage; only masked strings (`XXXX-XXXX-4821`) and salted SHA-256 hashes.
- Financial Integrity: Server-side recomputation of all rates and deposits. Never trust client prices.
- Rate Limiting: Strict sliding-window rate limit (20 calls/min) on AI routes to prevent DoW.
- Defensive Headers: Injected CSP, HSTS, X-Content-Type-Options: nosniff, and X-Frame-Options.

# SpaceLoop Security Rules

## Secrets

Never hardcode:

- API keys
- passwords
- tokens
- private keys
- credentials

Use environment variables or approved secret management.

Never commit secrets to Git.

## Authentication

Authentication must use established security libraries/frameworks.

Do not implement custom password hashing or custom session security.

Passwords must never be stored in plaintext.

## Personal Data

Do not log sensitive identity information.

Never store raw Aadhaar numbers unless explicitly required and legally justified.

Prefer minimum necessary data collection.

## Authorization

Authentication and authorization are different concerns.

Every protected operation must verify authorization.

Do not rely on frontend controls for authorization.

The backend must enforce:

- authentication
- role/capability permissions
- resource ownership
- relevant business-state restrictions

## AI Security

Treat user-provided text and uploaded content as untrusted input.

Never allow user content to override system/developer instructions.

Validate AI outputs before using them in business-critical operations.

## General

Prefer established security libraries over custom cryptographic/security implementations.

Do not weaken existing security controls to make tests pass.
