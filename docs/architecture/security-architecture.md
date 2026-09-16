# Security Architecture
- **DPDP Act 2023 Section 8 Compliance**: Zero raw 12-digit Aadhaar numbers or biometrics stored. Salted SHA-256 tokens (`sha256(aadhaar + salt)`) only.
- **Server-Side Recomputation**: Client price parameters completely ignored. Positive rate bounds clamped.
- **Sliding-Window AI Rate Limiter**: 20 requests per minute per IP.
- **Defensive Headers**: Content-Security-Policy, HSTS, X-Content-Type-Options: nosniff.
