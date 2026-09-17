# NIRIKSHAK Security Model & RBAC Specification

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: APPROVED SECURITY MODEL DRAFT

---

## 1. Principles of Defensive Design

Security is an intrinsic architectural property of NIRIKSHAK, implemented across all communication boundaries:
1. **Least Privilege**: Components operate with minimal required access; analysts are assigned strictly scoped RBAC permissions.
2. **Zero Trust Inside the Application**: Telemetry events, terminal commands, and GUI interactions undergo identical authentication and authorization checks.
3. **Defense in Depth**: Multi-layer security encompassing network isolation, token verification, schema validation, rate-limiting, and ORM parameterization.
4. **Tamper-Evident Auditing**: Security-critical actions generate immutable audit records.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Permission Code | Description | `ANALYST_TIER_1` | `ANALYST_TIER_2` | `ADMIN` | `SERVICE_ACCOUNT` |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `events:ingest` | Ingest new telemetry events | ❌ | ❌ | ❌ | ✅ |
| `events:read` | View and filter access events | ✅ | ✅ | ✅ | ❌ |
| `cases:read` | View active security cases | ✅ | ✅ | ✅ | ❌ |
| `cases:triage` | Assign and change case status | ✅ | ✅ | ✅ | ❌ |
| `cases:review` | Submit formal review & escalate | ❌ | ✅ | ✅ | ❌ |
| `risks:read` | View risk scores & factor details | ✅ | ✅ | ✅ | ❌ |
| `users:read` | View user profiles & baselines | ❌ | ✅ | ✅ | ❌ |
| `devices:write` | Modify device trust posture | ❌ | ✅ | ✅ | ❌ |
| `policies:read` | Inspect risk weights & thresholds | ✅ | ✅ | ✅ | ❌ |
| `policies:write` | Modify risk weights & policies | ❌ | ❌ | ✅ | ❌ |
| `audit:read` | Inspect system audit trail | ❌ | ❌ | ✅ | ❌ |

---

## 3. Cryptographic Standards & Token Management

* **Password Hashing**: `Argon2id` or `bcrypt` with work factor $\ge 12$. Plaintext passwords are never stored or logged.
* **Token Architecture**:
  * **Access Tokens**: Short-lived JSON Web Tokens (JWT), signed using HMAC-SHA256 (`HS256`) with a 256-bit secret key. Lifetime: 30 minutes.
  * **Claims**: Standard claims (`sub`, `exp`, `iat`, `iss`) plus minimal authorization metadata (`role`, `permissions`). Sensitive personally identifiable details are never placed inside token claims.
  * **Refresh Tokens**: Cryptographically random 64-byte tokens stored in Redis with 7-day TTL and rotation upon usage.

---

## 4. API Gateway & Transport Security

* **Transport**: All inter-service communications enforce TLS 1.3 in production environments.
* **Rate Limiting**: Redis-backed sliding-window token bucket algorithm enforced per IP and per API key on `/api/v1/events` and `/api/v1/auth/login`.
* **Input Validation**: Strict typing enforced by Pydantic v2. Payloads containing unexpected attributes are rejected (`extra = "forbid"`).
* **Output Sanitization**: Error handlers suppress stack traces and database internal error codes, returning uniform RFC 7807 problem details.
* **Security Headers**: All HTTP responses include `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Strict-Transport-Security`.
