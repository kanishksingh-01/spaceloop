# Security Rules
- DPDP Act 2023: Zero raw Aadhaar storage; only masked strings (`XXXX-XXXX-4821`) and salted SHA-256 hashes.
- Financial Integrity: Server-side recomputation of all rates and deposits. Never trust client prices.
- Rate Limiting: Strict sliding-window rate limit (20 calls/min) on AI routes to prevent DoW.
- Defensive Headers: Injected CSP, HSTS, X-Content-Type-Options: nosniff, and X-Frame-Options.
