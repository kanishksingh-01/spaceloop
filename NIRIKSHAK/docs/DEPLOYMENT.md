# NIRIKSHAK Deployment & Operations Guide (Trimmed MVP)

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: APPROVED REVISED DEPLOYMENT GUIDE

---

## 1. Prerequisites

* **Docker Engine**: Version 26.0+
* **Docker Compose**: Version 2.27+
* **Available Ports**: `3000` (Frontend), `8000` (Backend), `5432` (PostgreSQL)

---

## 2. Quickstart Deployment (One Command)

### Step 1: Copy Environment Template
```bash
cp .env.example .env
```

### Step 2: Launch the 3-Service Stack
```bash
docker compose up -d --build
```
> **Automatic Schema & Seed Initialization**:  
> The backend automatically executes `Base.metadata.create_all()` on startup to provision all PostgreSQL tables, and populates initial synthetic seed fixtures (`USER-001` to `USER-010`, classifications, demo accounts). No manual migration tools or Alembic steps are required.

### Step 3: Verify Service Health
```bash
docker compose ps
curl http://localhost:8000/api/v1/health
```

---

## 3. Accessing the Demo

* **SOC Dashboard**: [http://localhost:3000](http://localhost:3000)
  * Pre-seeded Login: `analyst_sarah` / `analyst123`
* **Backend OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Backend Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 4. Triggering Demo Scenarios

You can trigger scenarios directly using the buttons on the dashboard UI, or via CLI:
```bash
# Trigger off-hours access anomaly
docker compose exec backend python -m simulator.event_generator --scenario off_hours

# Trigger exfiltration anomaly
docker compose exec backend python -m simulator.event_generator --scenario exfiltration
```

---

## 5. Teardown

```bash
docker compose down
```
