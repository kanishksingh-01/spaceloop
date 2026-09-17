# NIRIKSHAK (निरीक्षक) — 5-Minute 4-Person Team Hackathon Demo Script

> **Project**: NIRIKSHAK — Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Duration**: Exactly 5 Minutes + Q&A  
> **Live Demo Target**: `http://localhost:3001` (Dashboard) & `http://localhost:8000` (FastAPI)  
> **Foundational Axiom**: $\text{Unusual Activity} \neq \text{Confirmed Malicious Activity}$

---

## Pre-Flight Checklist Before Presenting
- [ ] Colima & Docker running: `docker compose ps` shows `db`, `backend`, `frontend` healthy.
- [ ] Browser tab open: `http://localhost:3001`
- [ ] Terminal window open: split with simulator ready (`python3 simulator/killchain_generator.py 0.3`)

---

## 5-Minute Speaker Breakdown

```text
┌───────────────────────────┬──────────────────────────────────────────┬──────────┐
│ SPEAKER                   │ SECTION & CORE TOPIC                     │ TIME     │
├───────────────────────────┼──────────────────────────────────────────┼──────────┤
│ Member 1 (Lead / Backend) │ Problem Statement, Architecture & Axiom  │ 0:00-1:00│
│ Member 2 (Detection / ML) │ Live Scenarios & Explainable ML Engine   │ 1:00-2:15│
│ Member 3 (DevOps / Sim)   │ Multi-Stage Kill-Chain & Correlation     │ 2:15-3:30│
│ Member 4 (Frontend / Sec) │ Command Console, Human Review & Audit    │ 3:30-5:00│
└───────────────────────────┴──────────────────────────────────────────┴──────────┘
```

---

### Minute 0:00 – 1:00: Member 1 — Problem Statement & The Axiom
* **Speaking**:
  > *"Judges and engineers, traditional security systems fail at insider threats because they treat authenticated access as trusted access. Once an employee is logged in, legacy tools are either completely blind, or they flood analysts with black-box alert fatigue.*
  >
  > *We built **NIRIKSHAK** (*निरीक्षक* — observer and inspector). It is a Contextual, Human-Supervised, Explainable Decision Support System.*
  >
  > *Our system is governed by one foundational axiom:*  
  > $$\text{Unusual Activity} \neq \text{Confirmed Malicious Activity}$$  
  > *NIRIKSHAK never autonomously accuses or punishes employees. Instead, it computes whether sensitive data access remains **contextually reasonable** across 7 architectural layers—combining deterministic rules, historical baselines, unsupervised Isolation Forests, and temporal correlation."*

---

### Minute 1:00 – 2:15: Member 2 — Deterministic Signals & Explainable ML
* **Action**: Click **"Scenario 1: Normal"** on the dashboard.
* **Speaking**:
  > *"Let's look at live telemetry. An engineer (`USER-001`) reads defense documentation during working hours from their enrolled laptop. NIRIKSHAK evaluates this at **21.7 risk — LOW**.*
  >
  > *(Click **"Inspect Why"**)*  
  > *Notice that NIRIKSHAK does not output an opaque percentage. It outputs a deterministic mathematical attribution: Identity score: 0, Device trust: 0, Sensitivity: 20 pts. Our unsupervised **Isolation Forest model**, trained on historical telemetry, independently confirms this event aligns with the organizational cluster (decision score: +0.19).*
  >
  > *(Now click **"Scenario 2: Off-Hours"**)*  
  > *At 02:30 AM, an employee from Finance reads Operational Defense code without MFA. The risk score immediately jumps to **68.8 — HIGH**. The factor breakdown instantly highlights why: Missing MFA on critical data (+17.25 pts), Off-hours access (+11.5 pts), and Cross-department access (+5.75 pts). No guesswork, complete explainability."*

---

### Minute 2:15 – 3:30: Member 3 — Multi-Stage Kill Chain & Correlation Engine
* **Action**: Click **"Scenario 4: Kill Chain"** OR run in terminal: `python3 simulator/killchain_generator.py`.
* **Speaking**:
  > *"Sophisticated attacks are rarely single isolated actions; they are sequential kill chains. Watch what happens when an attacker executes an Advanced Persistent Threat:*
  >
  > *1. **Stage 1 (Recon)**: Browses public documentation from an external IP (Score: 21.1).*  
  > *2. **Stage 2 (Lateral Crawl)**: Enumerate multiple engineering repositories within 10 minutes (Score: 35.8).*  
  > *3. **Stage 3 (Privilege Bypass)**: Traverses to Critical Operational Repository A without MFA (Score: 51.4).*  
  > *4. **Stage 4 (Exfiltration)**: Initiates an unauthorized 1.8 GB compressed bulk export!*
  >
  > *(Point to Recharts velocity graph on dashboard)*  
  > *Our **Sliding-Window Correlation Engine** tracked this multi-event velocity burst across the 15-minute window. It applied our sequential kill-chain multiplier ($1.35\times$), escalating the event to **CRITICAL (74.4 - 93.9)** and automatically generating a prioritized **Security Case**."*

---

### Minute 3:30 – 5:00: Member 4 — Command Console, PRAHARAK Perimeter & Cross-Domain Correlation
* **Action**: Click the **"PRAHARAK (Perimeter & Outsider Risk)"** tab, then press `Ctrl + ~` to open the Analyst Command Console.
* **Speaking**:
  > *"Every insider threat has an external context. We engineered **PRAHARAK** (प्रहारक — the striker) as NIRIKSHAK's outward-facing twin.*
  >
  > *(Point to the PRAHARAK Dashboard)*  
  > *While NIRIKSHAK evaluates whether an internal employee's access is contextually reasonable, PRAHARAK evaluates whether an external connection or command has any right to exist. It features zero-trust cryptographic signature validation (HMAC-SHA256, Ed25519, and Post-Quantum Dilithium-3), token-bucket DDoS circuit breaking, and MITRE ATT&CK reconnaissance detection.*
  >
  > *(In console, type `praharak trigger hybrid_coordinated_attack` and press Enter)*  
  > *Watch the magic of **Cross-Domain Correlation**: An external adversary probes our API endpoints from `198.51.100.99`. Within seconds, our internal compromised credential `USER-003` initiates abnormal off-hours exfiltration.*
  >
  > *(Type `praharak incidents` and point to the Unified Incident Alert)*  
  > *NIRIKSHAK and PRAHARAK correlate across the shared 30-minute temporal sliding window, creating a unified **CRITICAL Incident (Score: 92.5)** that links the external IP directly to the internal identity!*
  >
  > *(Type `praharak circuit`)*  
  > *Our token-bucket circuit breaker automatically tripped, isolating the attacker into an automated 15-minute quarantine without human delay.*
  >
  > *(Click **"Human Triage"** on the generated case in the UI modal)*  
  > *Because human supervision is mandatory, the analyst reviews the correlated evidence and makes an audited determination with required justification.*
  >
  > *In summary: NIRIKSHAK and PRAHARAK form a complete 360-degree, explainable, and zero-trust cyber defense platform. Thank you, and we welcome your questions!"*

---

## Prepared Judge Q&A Cheat Sheet

1. **Q: How does the ML model differ from the deterministic rules?**  
   *A: The rules evaluate explicit policy constraints (MFA, registration, classification tiers), while the Isolation Forest evaluates multidimensional outlier distance across a 6D feature vector (hours offset, volume Z-score, device familiarity, action severity). The ML signal contributes 8–15% as an additive anomaly indicator—it never autonomously convicts.*

2. **Q: Is there any risk of command injection through the terminal?**  
   *A: Zero. The terminal is strictly a client-side AST lexer/allowlist parser. Commands like `rm`, `sh`, `sudo`, `curl`, or subshell characters (`;`, `&&`, `|`) are rejected before transmission, and backend endpoints enforce strict regex parameter validation (verified by our automated security test suite).*

3. **Q: Can the scoring weights be changed for different environments?**  
   *A: Yes! Through `GET/PUT /api/v1/policies`, security engineers can dynamically configure dimensional weights and threshold tiers directly in PostgreSQL with atomic audit logging.*
