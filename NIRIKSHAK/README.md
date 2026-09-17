# NIRIKSHAK (निरीक्षक)

> **Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework**

NIRIKSHAK is a defensive cybersecurity and insider-risk decision support prototype designed to continuously evaluate whether access to sensitive information remains contextually reasonable—even when an actor is technically authenticated and authorized.

---

## 1. Core Philosophy & Guiding Principles

- **Decision Support, Not Autonomous Accusation**:  
  NIRIKSHAK is strictly a decision support system. It distinguishes clearly between:
  $$\text{Unusual Activity} \neq \text{Confirmed Malicious Activity}$$
  It never automatically accuses or punishes individuals. Every high-risk decision must support human review and transparent explanation.
- **Explainable Multi-Factor Scoring**:  
  Risk is not a black-box opaque output. Every score is decomposed into explainable factor contributions (identity confidence, device trust, resource sensitivity, behavioral deviation, anomaly signal, multi-event correlation).
- **Synthetic Data Boundary**:  
  NIRIKSHAK is built and validated purely on synthetic data (`USER-001`, `USER-002`, `Operational Repository A`, etc.). No classified, sensitive real-world, or intrusive surveillance data is utilized.
- **Privacy by Design**:  
  Strict data minimization, role-based pseudonymization in the UI, purpose limitation, and immutable audit logging.

---

## 2. Conceptual Layer Architecture

The evaluation pipeline processes access telemetry through seven distinct architectural layers:

```text
┌─────────────────────────────────────────────────────────┐
│ 1. Identity Confidence                                  │
│    (Authentication status, credential age, MFA level)   │
├─────────────────────────────────────────────────────────┤
│ 2. Device & Environment Trust                           │
│    (Known/registered device, posture, IP locality)      │
├─────────────────────────────────────────────────────────┤
│ 3. Data Sensitivity Awareness                           │
│    (Resource classification, department ownership)      │
├─────────────────────────────────────────────────────────┤
│ 4. Behavioral Context                                   │
│    (Historical working hours, normal volumes, peers)    │
├─────────────────────────────────────────────────────────┤
│ 5. Event Correlation                                    │
│    (Multi-event sequences across time and sessions)     │
├─────────────────────────────────────────────────────────┤
│ 6. Explainable Risk Scoring                             │
│    (Normalized 0-100 score with factor contributions)   │
├─────────────────────────────────────────────────────────┤
│ 7. Human Security Review                                │
│    (Proportional case management & audited actions)     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Recharts, Lucide React |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (AsyncIO), Alembic, Uvicorn |
| **Database & Cache** | PostgreSQL 16 (System of Record), Redis 7.2 (Sessions, Baselines, Cache) |
| **Telemetry & Search**| OpenSearch 2.12 (Telemetry event indexing and free-text audit search) |
| **Machine Learning** | Scikit-Learn (Isolation Forest), NumPy, Pandas |
| **Infrastructure** | Docker, Docker Compose, GitHub Actions, pytest, Playwright |

---

## 4. Repository Structure

```text
NIRIKSHAK/
├── AGENTS.md                  # Autonomous agent development instructions & operational rules
├── README.md                  # Project overview & quickstart
├── docker-compose.yml         # Container orchestration configuration
├── .env.example               # Environment variables template
├── docs/                      # Architectural, threat, security, and API documentation
│   ├── ARCHITECTURE.md        # Deep architectural design and pipeline flow
│   ├── THREAT_MODEL.md        # STRIDE & insider-threat risk analysis
│   ├── SECURITY_MODEL.md      # RBAC, encryption, secret handling, authentication
│   ├── COMPATIBILITY_MATRIX.md# Dependency compatibility table and verification rules
│   ├── API_CONTRACT.md        # RESTful API schemas and OpenAPI specs
│   ├── DATABASE_DESIGN.md     # PostgreSQL relational schema and data dictionary
│   ├── DATA_CLASSIFICATION.md # Sensitivity tiers and access policies
│   ├── RISK_MODEL.md          # Scoring formulas, weights, and normalization
│   ├── PRIVACY_MODEL.md       # Privacy preservation and pseudonymization rules
│   ├── DEPLOYMENT.md          # Operational deployment instructions
│   ├── TESTING_STRATEGY.md    # Unit, integration, e2e, and security test plans
│   ├── ROADMAP.md             # 12-phase implementation roadmap
│   └── DOCKER_SERVICE_PLAN.md # Container topology and service dependencies
├── backend/                   # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API route handlers (REST endpoints)
│   │   ├── core/              # Config, security (JWT/hash), logging, dependencies
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic coordinators
│   │   ├── repositories/      # Database query abstraction layer
│   │   ├── engines/           # 8 specialized risk and explanation engines
│   │   └── tests/             # Backend unit and engine tests
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend container image definition
├── frontend/                  # Next.js analyst dashboard & command console
│   ├── app/                   # App Router pages and layouts
│   ├── components/
│   │   ├── dashboard/         # Visual risk metrics, cards, and charts
│   │   ├── terminal/          # Hybrid analyst command console
│   │   ├── cases/             # Security case review & workflow management
│   │   ├── analytics/         # Longitudinal and trend analysis
│   │   └── shared/            # Common UI elements (shadcn/ui primitives)
│   ├── lib/                   # API clients and utilities
│   ├── types/                 # TypeScript interfaces and contracts
│   ├── package.json           # Node.js dependencies
│   └── Dockerfile             # Frontend container image definition
├── database/                  # Database management
│   ├── schema/                # DDL scripts and table blueprints
│   ├── migrations/            # Alembic migration scripts
│   └── seeds/                 # Synthetic baseline seed fixtures
├── telemetry/                 # Ingestion pipeline specifications & mock streams
├── simulator/                 # Synthetic event and anomaly scenario generators
├── ml/                        # Isolation Forest feature extraction and model training
├── tests/                     # System-wide test suites (integration, e2e, security)
└── scripts/                   # Developer automation and database utilities
```

---

## 5. Development Workflow & Rules

All development follows the strict phased methodology:
$$\text{PLAN} \longrightarrow \text{IMPLEMENT} \longrightarrow \text{TEST} \longrightarrow \text{VERIFY} \longrightarrow \text{DOCUMENT} \longrightarrow \text{PROCEED}$$

See [AGENTS.md](file:///Users/kanishksingh/Downloads/hack2ignite/NIRIKSHAK/AGENTS.md) for strict operational instructions for AI agents and developers.
