# NIRIKSHAK Threat Model & Security Analysis

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Methodology**: STRIDE + MITRE ATT&CK for Enterprise / Insider Threat  
> **Status**: APPROVED THREAT MODEL DRAFT

---

## 1. Scope & Objective

The objective of this Threat Model is to identify, analyze, and mitigate security threats against the NIRIKSHAK platform. Because NIRIKSHAK operates as an insider-risk and defensive access-governance decision-support system, it constitutes a high-value target: compromising NIRIKSHAK could allow malicious actors to blind security teams, manipulate risk evaluations, or evade detection during sensitive data exfiltration.

---

## 2. Asset Inventory & Criticality

| Asset | Description | Impact of Compromise |
| :--- | :--- | :--- |
| **Access Telemetry Store** | Raw and normalized access events in PostgreSQL/OpenSearch | Loss of forensic truth; fabricated evidence; blinded detection |
| **Risk Scoring Pipeline** | Weights, mathematical algorithms, and Isolation Forest ML models | Suppression of risk alerts; evasion of insider detection |
| **Behavior Baselines** | Historical profile statistics of users and peer groups | Manipulation of baselines to mask anomalous exfiltration |
| **Security Case Records** | Analyst case notes, status dispositions, and review findings | Tampering with active investigations; framing innocent users |
| **System Audit Logs** | Immutable logs of all administrative and analyst actions | Repudiation of unauthorized analyst dispositions or policy tampering |
| **Policy Configurations** | Thresholds, scoring weights, and correlation window parameters | System-wide disabling of detection logic |
| **Authentication Secrets** | JWT private signing keys, API service keys, DB credentials | Complete platform takeover; identity spoofing |

---

## 3. Threat Actor Categorization

1. **Compromised Insider (External Adversary with Valid Creds)**:  
   Holds valid credentials (stolen via phishing or credential stuffing). Seeks to access high-value repositories without triggering alerts.
2. **Malicious Insider (Authorized Employee)**:  
   Legitimately authorized to access some systems, but attempts unauthorized lateral movement, bulk copying of sensitive designs, or reconnaissance.
3. **Compromised or Rogue Analyst**:  
   Possesses security console access. Attempts to dismiss active security cases, adjust scoring weights, or cover tracks of compromised accounts.
4. **Malicious Telemetry Ingestor**:  
   Attacks the event ingestion API endpoint (`POST /api/v1/events`) to inject false telemetry, flood system resources (DoS), or skew ML models.
5. **Unauthenticated External Attacker**:  
   Probes public network ports for unauthenticated APIs, injection vectors, or terminal command breakout vulnerabilities.

---

## 4. STRIDE Threat Analysis & Specific Mitigations

### 4.1. Spoofing Identity (S)

* **Threat S1: Telemetry Event Forgery**:  
  * *Vector*: An attacker sends fabricated access events to `POST /api/v1/events` to artificially trigger alerts against a colleague or cover their own tracks.
  * *Mitigation*: The ingestion API requires mutual authentication or cryptographic Ingestion API keys verified at the API gateway layer. Every event requires valid format and origin verification.
* **Threat S2: Device Identifier Spoofing**:  
  * *Vector*: An attacker spoofs a known trusted device MAC/UUID in telemetry headers.
  * *Mitigation*: The `DeviceEngine` correlates multiple hardware fingerprints, IP subnets, and user association history. Device trust is not a binary trust gate, and anomalous network context flags the score.
* **Threat S3: User Session Hijacking**:  
  * *Vector*: Stolen session tokens used to impersonate analysts.
  * *Mitigation*: Short-lived JWT access tokens (30 minutes), secure HTTP-only cookies where applicable, and mandatory token signature and expiration verification.

---

### 4.2. Tampering with Data (T)

* **Threat T1: Manipulation of Risk Scoring Policies**:  
  * *Vector*: An actor alters policy weights (e.g. reducing `SENSITIVITY_WEIGHT` to 0.0) so that sensitive file downloads produce LOW risk.
  * *Mitigation*: Policy updates require the `ADMIN` role, strict schema bounds ($w \in [0.0, 1.0]$, $\sum w_i = 1.0$), and trigger an immutable `AuditLog` entry.
* **Threat T2: Behavioral Baseline Poisoning**:  
  * *Vector*: A slow-and-low attacker generates gradual abnormal access to bias the user's historical baseline profile.
  * *Mitigation*: Baselines are calculated over long historical sliding windows (30+ days) with statistical outlier dampening; ML Isolation Forest is trained on audited baseline sets.
* **Threat T3: Database Record Modification**:  
  * *Vector*: Direct SQL injection into event or case tables.
  * *Mitigation*: All database queries use SQLAlchemy 2.0 parameterized statements and async ORM mapping. No dynamic SQL string concatenation is permitted anywhere in the codebase.

---

### 4.3. Repudiation (R)

* **Threat R1: Analyst Denial of Case Dismissal**:  
  * *Vector*: An analyst dismisses a critical case involving a real breach, then denies taking the action.
  * *Mitigation*: Every case action (`DISMISS`, `ESCALATE`, `RESOLVE`) requires a structured justification string, records the authenticated `analyst_id` from the JWT token, and writes an atomic record to the append-only `analyst_reviews` and `audit_logs` tables.
* **Threat R2: User Denial of System Access**:  
  * *Vector*: A user claims they never accessed a sensitive document.
  * *Mitigation*: Telemetry records immutable UTC timestamps, device IDs, session identifiers, and payload volumes.

---

### 4.4. Information Disclosure (I)

* **Threat I1: Excessive Profiling / Employee Privacy Leakage**:  
  * *Vector*: Unauthorized staff view sensitive behavioral statistics or personal patterns of employees.
  * *Mitigation*: Default UI pseudonymization (`USER-104`). RBAC restricts full profile inspection to authorized Tier-2/Tier-3 security investigators.
* **Threat I2: Error Stack Trace Exposure**:  
  * *Vector*: Database errors or internal exceptions return stack traces to clients, revealing internal paths, database schemas, or libraries.
  * *Mitigation*: Global FastAPI exception handlers catch unhandled errors and return generic sanitised RFC 7807 error responses (`status: 500`, `message: "Internal server error"`, `correlation_id: <uuid>`).
* **Threat I3: Secrets Committed to Repository**:  
  * *Vector*: Database passwords or JWT secrets accidentally pushed to git.
  * *Mitigation*: Strict `.gitignore`, `.env.example` placeholder usage, environment variable loading via `pydantic-settings`, pre-commit secret scanning.

---

### 4.5. Denial of Service (D)

* **Threat D1: Event Ingestion Flooding**:  
  * *Vector*: Ingestion endpoint hammered with 50,000 events/sec, exhausting database connection pools and CPU.
  * *Mitigation*: Redis-backed token bucket rate limiting on `/api/v1/events`, batch ingestion bounds (maximum 500 events per request), and asynchronous batch processing.
* **Threat D2: Expensive Correlation Queries**:  
  * *Vector*: Large sliding-window correlation queries scanning unindexed historical tables.
  * *Mitigation*: Database indexing on `(user_id, timestamp)`, `(device_id, timestamp)`, and `(session_id)`. Time windows strictly capped to a maximum of 60 minutes.

---

### 4.6. Elevation of Privilege (E)

* **Threat E1: Terminal Command Injection / OS Shell Breakout**:  
  * *Vector*: An analyst types malicious shell commands in the hybrid terminal (`investigate USER-104; rm -rf /` or `investigate $(cat /etc/passwd)`).
  * *Mitigation*: **The terminal is an application command console, not an operating system shell.** The frontend parser uses an AST tokenizer with a strict whitelist of allowed commands. Shell metacharacters (`;`, `|`, `&`, `` ` ``, `$()`, `>`, `<`) are rejected by the parser. On the backend, terminal actions translate to identical REST API calls guarded by standard FastAPI security dependencies.
* **Threat E2: Role Escalation via JWT Tampering**:  
  * *Vector*: A user with `ROLE_VIEWER` modifies the JWT claim to `ROLE_ADMIN`.
  * *Mitigation*: Cryptographic HMAC-SHA256 signature verification on every incoming request. The server rejects tokens signed with `none` algorithm or mismatched secrets.

---

## 5. Security Verification Matrix

| STRIDE Threat | Verification Method | Automated Test Suite |
| :--- | :--- | :--- |
| **S1: Telemetry Forgery** | Send unauthenticated / malformed event payload | `tests/security/test_ingestion_security.py` |
| **S3: JWT Spoofing** | Test expired, invalid signature, `alg: none` tokens | `tests/security/test_jwt_validation.py` |
| **T3: SQL Injection** | Fuzz test search, filter, and user endpoints with SQLi vectors | `tests/security/test_sqli_protection.py` |
| **E1: Terminal Breakout** | Attempt command injection (`rm`, `;`, pipe, shellcode) | `frontend/tests/terminal_parser.test.ts` |
| **E2: Privilege Escalation** | Call admin policy endpoints with viewer credentials | `tests/security/test_rbac_enforcement.py` |
| **I2: Error Leakage** | Trigger 500 errors and verify absence of stack traces | `tests/security/test_error_sanitization.py` |
