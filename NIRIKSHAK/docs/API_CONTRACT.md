# NIRIKSHAK API Contract (Trimmed 7-Day MVP)

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Base URL**: `/api/v1`  
> **Status**: APPROVED REVISED MVP CONTRACT

---

## 1. Authentication (Simple Seeded Login)

### `POST /api/v1/auth/login`
Authenticates with pre-seeded demo credentials (`analyst_sarah` / `analyst123` or `admin_vikram` / `admin123`).
* **Request**:
  ```json
  {
    "username": "analyst_sarah",
    "password": "analyst123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "018f2f4e-1111-7000-8000-000000000001",
      "username": "analyst_sarah",
      "role": "ANALYST"
    }
  }
  ```

---

## 2. Event Ingestion & Scenarios

### `POST /api/v1/events`
Ingests an access telemetry event and runs immediate deterministic risk scoring.
* **Request**:
  ```json
  {
    "event_id": "evt_demo_001",
    "timestamp": "2026-09-09T02:30:00Z",
    "user_id": "018f2f4e-1234-7000-8000-000000000002",
    "device_id": "018f2f4e-5678-7000-8000-000000000003",
    "resource_id": "018f2f4e-9abc-7000-8000-000000000004",
    "session_id": "sess_demo_101",
    "action": "READ",
    "result": "SUCCESS",
    "data_volume": 15728640,
    "source_context": {
      "client_ip": "192.168.1.50",
      "mfa_verified": false
    }
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "event_id": "evt_demo_001",
    "risk_score": 75.0,
    "risk_level": "HIGH",
    "case_created": true,
    "case_id": "018f2f4e-aaaa-7000-8000-000000000005"
  }
  ```

### `POST /api/v1/scenarios/trigger`
On-demand trigger for demo scenarios directly from the UI or test scripts.
* **Request**:
  ```json
  {
    "scenario": "exfiltration"
  }
  ```
  Options: `"normal"`, `"off_hours"`, `"exfiltration"`
* **Response (200 OK)**:
  ```json
  {
    "scenario": "exfiltration",
    "event_id": "evt_exfil_99",
    "risk_score": 88.5,
    "risk_level": "CRITICAL",
    "summary": "USER-003 accessed Personnel Repository D from unregistered device outside normal hours."
  }
  ```

---

## 3. Events & Factor Explanations

### `GET /api/v1/events`
Returns list of recent events with risk summary and classification badges.
* **Query Params**: `limit` (default: 50), `risk_level` (optional: `LOW`, `MODERATE`, `HIGH`, `CRITICAL`)
* **Response (200 OK)**: List of events.

### `GET /api/v1/events/{id}/explanation`
Returns detailed mathematical factor breakdown showing why an event was flagged.
* **Response (200 OK)**:
  ```json
  {
    "event_id": "evt_demo_001",
    "total_score": 75.0,
    "risk_level": "HIGH",
    "factors": [
      {
        "factor": "OFF_HOURS_ACCESS",
        "subscore": 80.0,
        "weight": 0.25,
        "contribution": 20.0,
        "explanation": "Event occurred at 02:30 UTC, outside user's normal 09:00-18:00 working window."
      },
      {
        "factor": "HIGH_SENSITIVITY_RESOURCE",
        "subscore": 90.0,
        "weight": 0.25,
        "contribution": 22.5,
        "explanation": "Target resource is classified as CRITICAL sensitivity tier."
      },
      {
        "factor": "MISSING_MFA",
        "subscore": 70.0,
        "weight": 0.25,
        "contribution": 17.5,
        "explanation": "Critical access initiated without second-factor authentication."
      },
      {
        "factor": "UNREGISTERED_DEVICE",
        "subscore": 60.0,
        "weight": 0.25,
        "contribution": 15.0,
        "explanation": "Endpoint is not enrolled in corporate device inventory."
      }
    ]
  }
  ```

---

## 4. Case Management & Review

### `GET /api/v1/cases`
Lists all security cases requiring human review.
* **Response (200 OK)**: Array of cases (`status`: `OPEN`, `DISMISSED`, `ESCALATED`).

### `POST /api/v1/cases/{id}/review`
Submits a human review action: Dismiss or Escalate.
* **Request**:
  ```json
  {
    "action": "ESCALATE",
    "justification": "Confirmed unexpected bulk access outside shifts from an unmanaged endpoint."
  }
  ```
  Action values: `"DISMISS"` or `"ESCALATE"`
* **Response (200 OK)**:
  ```json
  {
    "case_id": "018f2f4e-aaaa-7000-8000-000000000005",
    "status": "ESCALATED",
    "reviewed_by": "analyst_sarah",
    "audit_logged": true
  }
  ```

---

## 5. Policy & Scoring Configuration

### `GET /api/v1/policies`
Returns active scoring weights and decision tier thresholds.

### `PUT /api/v1/policies/{key}`
Updates a policy weight or threshold (Admin role required) with mandatory justification.

---

## 6. Device Inventory & Trust Management

### `GET /api/v1/devices`
Lists enrolled corporate endpoints with registration and trust levels (`TRUSTED`, `MONITORED`, `REVOKED`).

### `PATCH /api/v1/devices/{device_id}/trust`
Updates device trust posture with audit trail tracking.

---

## 7. PRAHARAK (प्रहारक) — Perimeter & Outsider Risk API

### `POST /api/v1/praharak/signals`
Ingests an external perimeter signal (REST, gRPC, MQTT, Modbus, Webhook), evaluates cryptographic anti-spoofing, rate-limiting, and MITRE ATT&CK reconnaissance patterns.
* **Request**:
  ```json
  {
    "source_ip": "198.51.100.42",
    "protocol": "HTTPS",
    "endpoint_target": "/api/v1/operations/dispatch",
    "payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "auth_type": "HMAC-SHA256",
    "signature": "3045022100...",
    "nonce": "nonce_20260910_001",
    "timestamp": 1757481600.0,
    "http_headers": {
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "x-forwarded-for": "198.51.100.42"
    }
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "signal_id": "sig_a1b2c3d4",
    "source_ip": "198.51.100.42",
    "final_risk_score": 12.5,
    "risk_tier": "LOW",
    "disposition": "ALLOWED",
    "crypto_valid": true,
    "recon_detected": false,
    "recon_tactics": [],
    "circuit_state": "CLOSED",
    "factors": [
      {
        "factor": "CRYPTO_VERIFIED",
        "subscore": 0.0,
        "weight": 0.35,
        "contribution": 0.0,
        "explanation": "Valid cryptographic signature and fresh nonce."
      }
    ]
  }
  ```

### `GET /api/v1/praharak/signals`
Returns telemetry list of external ingress signals.
* **Query Params**: `limit` (int, default: 50), `risk_tier` (optional), `disposition` (optional: `ALLOWED`, `THROTTLED`, `BLOCKED`, `ALERT`)
* **Response (200 OK)**: Array of signal records with risk attribution factors.

### `GET /api/v1/praharak/signals/{signal_id}`
Returns full dossier of an external signal including cryptographic verification results, MITRE recon tactics, and SHA-256 hash chaining.

### `GET /api/v1/praharak/circuit-breaker`
Returns active token-bucket velocity counters and quarantine status for all tracked external sources.
* **Response (200 OK)**:
  ```json
  [
    {
      "source_identifier": "198.51.100.42",
      "fast_counter": 3,
      "slow_counter": 12,
      "state": "CLOSED",
      "is_quarantined": false,
      "quarantined_until": null
    }
  ]
  ```

### `POST /api/v1/praharak/circuit-breaker/reset`
Manually clears quarantine and resets token-bucket counters for a specific IP.
* **Request**: `{"source_identifier": "198.51.100.42"}`
* **Response (200 OK)**: Updated circuit breaker state.

### `GET /api/v1/praharak/incidents`
Lists cross-domain incidents correlated between PRAHARAK perimeter probes and NIRIKSHAK insider access anomalies within the shared 30-minute sliding window.

### `POST /api/v1/praharak/scenarios/trigger`
Simulates synthetic perimeter threat vectors on-demand.
* **Request**: `{"scenario": "hybrid_coordinated_attack"}`
  Options: `"normal_telemetry"`, `"spoofed_command"`, `"ddos_flood"`, `"hybrid_coordinated_attack"`
* **Response (200 OK)**: Detailed execution report including signal dispositions and cross-domain incident links.

