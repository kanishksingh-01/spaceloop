# NIRIKSHAK Dependency & Component Compatibility Matrix

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: VERIFIED AND LOCKED  
> **Last Verified**: September 2026

---

## 1. Primary Component Compatibility Table

| Component | Target Version | Depends On | Compatible With | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Python Runtime** | `3.11.9` | CPython / OS libc | Linux, macOS, Docker `python:3.11-slim` | `python --version` returns `3.11.x` |
| **FastAPI** | `0.111.0` | Starlette `0.37.2`, Pydantic `2.7.4` | Python 3.10+, Uvicorn 0.30+ | `uvicorn app.main:app` initializes without warnings |
| **Pydantic** | `2.7.4` | `pydantic-core 2.18.4` | FastAPI 0.111.0, Python 3.11 | `python -c "import pydantic; assert pydantic.__version__.startswith('2.')"` |
| **pydantic-settings**| `2.3.0` | Pydantic 2.7+ | Python 3.11 | Import and validate `.env` parsing |
| **SQLAlchemy** | `2.0.31` | `typing-extensions >= 4.6.0` | `asyncpg 0.29.0`, `psycopg 3.1.19` | Async database session tests pass |
| **asyncpg** | `0.29.0` | PostgreSQL protocol | PostgreSQL 14 - 16 | Connects and executes async SQL queries |
| **psycopg (v3)** | `3.1.19` | libpq / Python 3.11 | PostgreSQL 16, Alembic 1.13 | Migration DDL execution |
| **Alembic** | `1.13.1` | SQLAlchemy 2.0+ | PostgreSQL 16 | `alembic upgrade head` runs cleanly |
| **PostgreSQL** | `16.3-alpine` | Docker container | Docker Compose, Linux x86/ARM | `pg_isready -h localhost -p 5432` |
| **Redis Server** | `7.2.5-alpine` | Docker container | Docker Compose, Linux x86/ARM | `redis-cli ping` returns `PONG` |
| **redis-py** | `5.0.6` | Python 3.11, hiredis (opt) | Redis 6.2 - 7.2 | Async ping and key set/get operations |
| **OpenSearch** | `2.12.0` | JDK 21 (bundled in image) | Docker Compose | `curl -s http://localhost:9200` returns 200 |
| **opensearch-py** | `2.5.0` | Python 3.11, urllib3 | OpenSearch 2.x | Test cluster health query |
| **scikit-learn** | `1.4.2` | NumPy 1.26.4, SciPy 1.13.1 | Python 3.11 | Fit and predict Isolation Forest model |
| **NumPy** | `1.26.4` | CPython 3.11 | scikit-learn 1.4.2, pandas 2.2.2 | Avoids NumPy 2.0 binary C-ABI breakages |
| **Pandas** | `2.2.2` | NumPy 1.26.4, python-dateutil | Python 3.11 | DataFrame manipulations and baseline stats |
| **Node.js** | `20.14.0 (LTS)` | OS / Docker `node:20-alpine` | macOS, Linux | `node --version` returns `v20.x` |
| **Next.js** | `14.2.4` | Node.js 18.17+, React 18.3.1 | App Router, TypeScript 5.4 | `next build` generates production bundle |
| **React / React-DOM**| `18.3.1` | Node.js 20 | Next.js 14.2.4 | Renders App Router components without hydration errors |
| **TypeScript** | `5.4.5` | Node.js 20 | Next.js 14.2, React 18.3 | `tsc --noEmit` completes with 0 errors |
| **Tailwind CSS** | `3.4.4` | PostCSS 8.4+, Autoprefixer | Next.js 14.2 | Styles compile and render correctly |
| **Lucide React** | `0.395.0` | React 18 | Next.js 14.2 | Icon component tree compilation |
| **Recharts** | `2.12.7` | React 18 | Next.js 14.2 (Client components) | Renders risk charts without canvas errors |
| **Docker Engine** | `26.1.0+` | OS Linux/macOS host | Docker Compose v2.27+ | `docker version` check |
| **Docker Compose** | `2.27.0+` | Docker Engine | Compose spec v3.8+ | `docker compose config` validates |
| **pytest** | `8.2.2` | Python 3.11 | pytest-asyncio 0.23.7 | Unit tests run and pass |
| **Playwright** | `1.44.1` | Node.js 20, Chromium browser | Next.js 14.2 | E2E browser test execution |

---

## 2. Key Architectural Decisions & Conflict Prevention

### Why Python 3.11.x?
Python 3.11 offers a 10–60% performance improvement over 3.10 and has 100% pre-compiled binary wheel support for `scikit-learn`, `numpy`, `pandas`, `asyncpg`, and `pydantic-core` across both Apple Silicon (ARM64) and Linux (x86_64/ARM64).

### Why NumPy 1.26.4 instead of NumPy 2.x?
NumPy 2.0 (released mid-2024) introduced major C-API breaking changes that break binary ABI compatibility with certain compiled extensions not yet recompiled for 2.0. Pinning `numpy==1.26.4` ensures rock-solid stability with `scikit-learn==1.4.2` and `scipy`.

### Why Pydantic v2 (`2.7.4`)?
Pydantic v2 brings up to 5–20x faster validation using its Rust-based `pydantic-core`. This is crucial for the high-throughput telemetry ingestion pipeline where thousands of events per minute are schema-validated.

### Why Next.js 14.2 (App Router) + React 18.3?
Next.js 14.2 is the battle-tested LTS foundation for modern enterprise dashboards. React 18.3 provides rock-solid server-side and client-side rendering compatibility for Recharts, shadcn/ui, and the interactive terminal console without experimental React 19 breaking changes.

---

## 3. Dependency Conflict Resolution Protocol

If any dependency conflict emerges during implementation:
1. **STOP IMMEDIATELY**: Do not use `--force` or `--legacy-peer-deps` blindly.
2. **DOCUMENT THE CONFLICT**: Record the exact package version and conflicting dependency trace.
3. **PROPOSE THE SAFEST COMPATIBLE VERSION**: Identify the common version constraint that satisfies both packages.
4. **UPDATE THIS MATRIX**: Record the change and justification.
5. **VERIFY AND PROCEED**: Run integration tests to ensure no regression.
