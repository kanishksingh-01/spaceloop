# NIRIKSHAK Privacy Model & Data Governance

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: APPROVED PRIVACY MODEL DRAFT

---

## 1. Privacy-by-Design Philosophy

Insider-risk detection platforms operate in sensitive operational domains where employee trust and personal dignity must be safeguarded. NIRIKSHAK embeds strict privacy-by-design principles:
1. **No Real Surveillance Data**: The prototype uses 100% synthetic identities, artificial event streams, and synthetic enterprise repositories.
2. **Data Minimization**: The platform records only operational metadata strictly necessary to determine contextual access reasonableness (timestamps, resource IDs, device hashes, bytes transferred).
3. **No Intrusive Content Inspection**: The system **never** collects, stores, or inspects:
   * Personal communications (emails, chat messages, phone calls).
   * Personal browser history or non-work-related internet traffic.
   * Keystroke logging or screen video recordings.
   * Biometric or personal physiological telemetry.

---

## 2. Pseudonymization & UI Presentation

* **Pseudonymous Identifiers**: In all primary analyst dashboards, event feeds, and terminal outputs, individuals are represented exclusively by synthetic pseudonymous IDs (`USER-104`, `USER-042`).
* **De-pseudonymization Controls**: Resolving a pseudonymous ID to real employee record details requires explicit privilege (`users:read`), generates an immutable entry in the `audit_logs` table, and requires a documented operational justification.

---

## 3. Behavioral Baseline Privacy Controls

* **Aggregation Over Granularity**: User baselines store statistical aggregates (e.g. mean working hours $\mu$, volume distribution $\sigma$, category affinities) rather than minute-by-minute behavioral surveillance trails.
* **Access Scoping**: Tier-1 analysts can view aggregated risk scores and factor contributions, but cannot browse raw longitudinal behavioral baseline distributions.

---

## 4. Retention & Data Purging Policies

| Telemetry Type | Retention Period | Purging / Archival Mechanism |
| :--- | :--- | :--- |
| **Raw Access Events** | 90 Days | Automatic partition drop or OpenSearch index rollover |
| **Risk Scores & Factors**| 180 Days | Historical aggregation; details retained for open cases |
| **Security Cases** | 365 Days | Retained for institutional compliance & incident audit |
| **Audit Logs** | 730 Days (2 Years) | Immutable append-only storage; write-once read-many (WORM) |
