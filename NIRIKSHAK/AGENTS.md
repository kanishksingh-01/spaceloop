# NIRIKSHAK (निरीक्षक) — AGENT OPERATING INSTRUCTIONS

> **MANDATORY INSTRUCTIONS FOR ANTIGRAVITY AND ALL AI AGENTS WORKING ON THIS REPOSITORY**  
> This file establishes persistent, non-negotiable architectural rules, security boundaries, coding standards, and operational guidelines for NIRIKSHAK.

---

## 1. System Role & Core Purpose

NIRIKSHAK is a **Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework**. It serves as a defensive cybersecurity decision-support prototype.

### The Foundational Axiom
$$\text{Unusual Activity} \neq \text{Confirmed Malicious Activity}$$

* NIRIKSHAK is a **Decision Support System**, never an autonomous accusation or automated disciplinary platform.
* The primary operational goal is: *To continuously evaluate whether access to sensitive information remains contextually reasonable, even when the user is technically authenticated and authorized.*
* All high-risk decisions require human security review.

---

## 2. Absolute Prohibitions (Zero Tolerance)

You MUST NOT under any circumstance:
1. **Never create an operating system shell in the browser or terminal interface.** The frontend terminal is an application command console (AST/allowlist parser) communicating with standard REST APIs. Never execute `sh`, `bash`, `rm`, `sudo`, `curl`, or sub-processes from the browser.
2. **Never hard-code secrets, passwords, or tokens** in code, tests, or seeds. Always read from environment variables via configuration modules.
3. **Never automatically accuse or discipline users.** Output signals must be phrased objectively (e.g., `UNUSUAL_HOURS_DEVIATION`, `ELEVATED_RISK_SCORE`), never accusatory.
4. **Never use real defense networks, real classified data, real cryptographic keys, or real employee surveillance.** All identities (`USER-001`, etc.) and resources (`Operational Repository A`, etc.) must be 100% synthetic.
5. **Never bypass backend authorization.** The terminal and dashboard must invoke the exact same authenticated REST endpoints with identical RBAC enforcement.
6. **Never put complex business logic in API route handlers.** Adhere strictly to the 4-tier backend architecture: `API Layer` $\rightarrow$ `Service Layer` $\rightarrow$ `Repository Layer` $\rightarrow$ `Database`.
7. **Never pass unstructured strings between analytical engines.** All pipeline handoffs must use strongly typed Pydantic models.
8. **Never install untested or unpinned dependencies.** Consult `docs/COMPATIBILITY_MATRIX.md` before introducing any library.
9. **Never skip testing or verification.** No feature is complete without passing unit, integration, and security tests.

---

## 3. Seven Conceptual Architectural Layers

Every event processed by NIRIKSHAK must traverse the seven defined layers:

```text
1. Identity Confidence      ──> Authenticated state, MFA status, credential freshness
2. Device & Env Trust       ──> Known hardware, trust score, network locality
3. Data Sensitivity         ──> Classification tier (LOW -> CRITICAL), department ownership
4. Behavioral Context       ──> Comparison against user & role historical baselines
5. Event Correlation        ──> Multi-event sliding windows across sessions and resources
6. Explainable Risk Scoring ──> Deterministic normalization (0-100) + factor attribution
7. Human Security Review    ──> Case workflow, proportional recommendation, audit trail
```

---

## 4. Hybrid UI & Terminal Architectural Rules

The user interface combines a **Modern SOC Dashboard** with an integrated **Analyst Command Console**:

```text
┌──────────────────────────────────────────────────────────────┐
│ NIRIKSHAK     SYSTEM STATUS     ENVIRONMENT     USER PROFILE    │
├──────────────┬───────────────────────────────────────────────┤
│ NAVIGATION   │             MAIN ANALYST VIEW                 │
│ Overview     │                                               │
│ Live Events  │   Risk Metrics / Cases / Charts / Timeline    │
│ Investigate  │                                               │
│ Cases        │                                               │
│ Analytics    │                                               │
│ Policies     │                                               │
├──────────────┴───────────────────────────────────────────────┤
│ NIRIKSHAK COMMAND CONSOLE                                      │
│ > investigate USER-104                                      │
│ > show timeline                                              │
│ > explain CASE-0021                                         │
│ [structured tabular / semantic output]                       │
└──────────────────────────────────────────────────────────────┘
```

### The Terminal is NOT a Backdoor
* **Command Allowlist**: Only explicit commands are permitted: `help`, `clear`, `status`, `events`, `cases`, `investigate <id>`, `timeline <id>`, `explain <id>`, `risk <id>`, `search <query>`.
* **Shared Client**: Terminal commands translate directly into client-side API requests using the exact same Axios/Fetch API client and bearer tokens as the graphical buttons.
* **Unified Authorization**: If an analyst does not have permission to view a resource via the UI, the terminal will return `403 Forbidden`.

---

## 5. Risk Scoring & Explainability Standards

Risk scoring must remain **deterministic, policy-driven, and transparent**:

$$\text{Final Risk} = w_1 I + w_2 D + w_3 S + w_4 B + w_5 A + w_6 C$$

* Normalized to the range $[0, 100]$.
* Risk Tiers:
  * `0 - 30`: **LOW** (Log and background monitor)
  * `31 - 60`: **MODERATE** (Recommend secondary verification)
  * `61 - 80`: **HIGH** (Generate analyst security case)
  * `81 - 100`: **CRITICAL** (Recommend temporary session restriction)
* Weights are configurable in policy (`WEIGHT_IDENTITY`, `WEIGHT_DEVICE`, etc.) and must never be opaque magic constants in code.
* **Explainability Requirement**: Every computed score must output an array of `RiskFactor` objects with quantified percentage/point contributions and human-readable rationale.

---

## 6. Machine Learning Boundary

* Initial ML implementation uses **Isolation Forest** from `scikit-learn`.
* ML is **strictly one anomaly signal** amongst multiple deterministic factors; it never independently convicts or accuses.
* The ML module must expose standard methods: `train()`, `evaluate()`, `predict()`, `explain_input_features()`.
* Model artifacts must be versioned, immutable, and tracked with metadata (training timestamp, feature schema version, evaluation metrics).

---

## 7. Phased Implementation Cadence

Agents must execute the roadmap strictly in order. Do not skip phases:

1. **Phase 1: Foundation** (Docker Compose, PostgreSQL, Redis, FastAPI skeleton, Next.js skeleton, Healthchecks)
2. **Phase 2: Core Data Model** (Entities, SQLAlchemy models, Alembic migrations, Seeds, Tests)
3. **Phase 3: Event Ingestion** (REST Ingestion API, Pydantic schemas, Auth, Rate-limiting, OpenSearch logging)
4. **Phase 4: Deterministic Risk Engine** (Identity, Device, Sensitivity, Behavior engines)
5. **Phase 5: Behavior Baselines** (Historical baseline profiles, typical hour/device/volume distributions)
6. **Phase 6: Anomaly Detection** (Feature extraction pipeline, Isolation Forest training, model versioning)
7. **Phase 7: Correlation Engine** (Sliding windows, multi-event chains, session clustering)
8. **Phase 8: Explainability** (Factor contribution breakdown, visual timelines)
9. **Phase 9: Case Management** (Case workflows, analyst assignment, audited disposition actions)
10. **Phase 10: Frontend Dashboard** (Overview, metrics, live events, case investigation, Recharts)
11. **Phase 11: Hybrid Terminal** (Command parser, autocomplete, history, structured output, API bindings)
12. **Phase 12: Hardening & Auditing** (Security testing, Playwright E2E, load testing, privacy audit)

---

## 8. Definition of Done (DoD)

A task or phase is considered complete ONLY when:
1. Code is fully implemented according to specifications without placeholders.
2. Unit and integration tests are written and pass cleanly.
3. Security constraints (input sanitization, auth checks, error suppression) are verified.
4. API contracts and documentation match the implementation.
5. All database operations are wrapped in safe transactions/migrations.
6. Verification logs or test outputs are produced.
