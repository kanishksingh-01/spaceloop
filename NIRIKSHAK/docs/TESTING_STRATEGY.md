# NIRIKSHAK Comprehensive Testing Strategy

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: APPROVED TESTING STRATEGY DRAFT

---

## 1. Testing Philosophy & Test Pyramid

In accordance with Section 26 of the master instruction, **no feature is complete without tests**. The testing pyramid encompasses four rigorous levels:

```text
       ▲
      / \        Level 4: Security & Penetration Tests (pytest, OWASP ZAP)
     /   \       Level 3: End-to-End Visual & User Journey (Playwright)
    /     \      Level 2: Integration Tests (FastAPI TestClient, DB/Redis testcontainers)
   /       \     Level 1: Unit & Mathematical Engine Tests (pytest, vitest)
  ───────────
```

---

## 2. Test Level Specifications

### Level 1: Unit & Engine Tests
* **Framework**: `pytest` (Backend) / `vitest` or `jest` (Frontend).
* **Scope**:
  * Individual analytical engines (`IdentityEngine`, `DeviceEngine`, `SensitivityEngine`, `BehaviorEngine`, `AnomalyEngine`, `CorrelationEngine`, `RiskEngine`, `ExplanationEngine`).
  * Terminal command parser (`frontend/components/terminal/parser.ts`): Tests lexical tokenization, argument validation, allowlist enforcement, and rejection of shell metacharacters.
  * Pydantic schemas: UTC enforcement, UUID validation, negative volume rejection.

### Level 2: Integration Tests
* **Framework**: `pytest` with `pytest-asyncio` and test database transactions.
* **Scope**:
  * Event ingestion $\rightarrow$ Persistence $\rightarrow$ Risk calculation.
  * Correlated multi-event sequences triggering case creation.
  * Analyst case review updating status and appending atomic audit logs.
  * Redis rate limiter token bucket behavior under burst traffic.

### Level 3: End-to-End (E2E) Browser Tests
* **Framework**: `Playwright` with Chromium/Firefox.
* **Scope**:
  * Analyst login and JWT cookie/header verification.
  * SOC Dashboard metrics rendering, live event stream updates, and Recharts rendering.
  * Hybrid Command Console: Typing `investigate USER-104` and verifying structured table rendering.
  * Completing a case review workflow (`ESCALATE` with mandatory justification text).

### Level 4: Security & Hardening Tests
* **Framework**: Dedicated security test suite in `tests/security/`.
* **Scope**:
  * **Authentication**: Expired JWT tokens, invalid signatures, algorithm substitution (`alg: none`).
  * **Authorization (RBAC)**: Calling admin endpoints (`PUT /api/v1/policies`) with analyst or viewer credentials.
  * **Injection Protection**: Sending SQL injection payloads (`' OR 1=1 --`) in filters and search parameters.
  * **Terminal Sandboxing**: Entering shell breakout sequences (`investigate USER-1; rm -rf /`, `$(cat /etc/passwd)`).
  * **Error Sanitization**: Triggering unhandled server exceptions and asserting that stack traces are suppressed.

---

## 3. Continuous Integration (CI) Verification Commands

```bash
# 1. Run all backend unit and engine tests
docker compose run --rm backend pytest backend/app/tests/

# 2. Run backend integration tests
docker compose run --rm backend pytest tests/integration/

# 3. Run automated security test suite
docker compose run --rm backend pytest tests/security/

# 4. Run frontend unit tests and typecheck
docker compose run --rm frontend npm run test:unit
docker compose run --rm frontend npm run typecheck

# 5. Run end-to-end Playwright tests
docker compose run --rm frontend npx playwright test
```
