# NIRIKSHAK Risk Scoring Model & Formulation

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: APPROVED RISK FORMULATION DRAFT

---

## 1. Core Mathematical Formulation

NIRIKSHAK rejects opaque "black-box" risk numbers. The overall risk score for any given access event $E$ is computed deterministically as a linear combination of six normalized component scores, augmented by correlation amplification:

$$\text{Risk}_{\text{composite}}(E) = \sum_{i \in \mathcal{F}} w_i \cdot S_i(E)$$

Where:
* $\mathcal{F} = \{\text{Identity}, \text{Device}, \text{Sensitivity}, \text{Behavior}, \text{Anomaly}, \text{Correlation}\}$
* $S_i(E) \in [0, 100]$ represents the normalized sub-score produced by analytical engine $i$.
* $w_i \in [0, 1]$ represents the policy-configured weight for factor $i$, strictly subject to:
  $$\sum_{i \in \mathcal{F}} w_i = 1.0$$

Therefore, $\text{Risk}_{\text{composite}}(E)$ is strictly bounded in the range $[0.0, 100.0]$.

---

## 2. Default Policy Weights

Weights are stored in the database (`policies` table) and loaded dynamically by the `RiskEngine`. No hardcoded magic numbers are allowed:

| Factor ($i$) | Weight ($w_i$) | Engine Source | Evaluated Context |
| :--- | :---: | :--- | :--- |
| **Identity ($I$)** | `0.15` | `IdentityEngine` | MFA presence, credential age, session concurrency |
| **Device ($D$)** | `0.15` | `DeviceEngine` | Known/registered status, trust posture, network locality |
| **Sensitivity ($S$)**| `0.20` | `SensitivityEngine` | Resource classification tier, departmental boundary |
| **Behavior ($B$)** | `0.20` | `BehaviorEngine` | Deviation from working hours, volume Z-score, category |
| **Anomaly ($A$)** | `0.15` | `AnomalyEngine` | Isolation Forest unsupervised outlier probability |
| **Correlation ($C$)**| `0.15` | `CorrelationEngine` | Sliding-window multi-event sequence amplification |
| **Total** | **1.00** | — | — |

---

## 3. Sub-Score Derivations

### 3.1. Identity Sub-Score ($S_{\text{Identity}}$)
* Base score: $0$ (Normal active session with fresh MFA).
* $+30$ points: Session missing MFA when accessing sensitive repository.
* $+40$ points: Concurrent active sessions detected across disparate IP subnets.
* $+30$ points: Account status marked as probationary or pending credential rotation.
* Clamped to $[0, 100]$.

### 3.2. Device Sub-Score ($S_{\text{Device}}$)
* Base score: $0$ (Registered corporate workstation with verified posture).
* $+35$ points: Unenrolled or unregistered device identifier.
* $+25$ points: Device trust level evaluated as `LOW` or `UNKNOWN`.
* $+40$ points: Access originating from non-corporate VPN egress or unexpected geo-locality.
* Clamped to $[0, 100]$.

### 3.3. Sensitivity Sub-Score ($S_{\text{Sensitivity}}$)
Derived from resource classification level and organizational ownership:
$$S_{\text{Sensitivity}} = \text{BaseTierScore} + \text{CrossDepartmentPenalty}$$
* `PUBLIC`: Base $10$
* `INTERNAL`: Base $25$
* `CONFIDENTIAL`: Base $50$
* `RESTRICTED`: Base $75$
* `CRITICAL`: Base $90$
* Cross-Department Access (e.g. Finance user accessing Defense R&D code): $+15$ points.
* Clamped to $[0, 100]$.

### 3.4. Behavioral Deviation Sub-Score ($S_{\text{Behavior}}$)
Evaluated against user and role baselines:
$$S_{\text{Behavior}} = \min\left(100, \, 30 \cdot \mathbb{I}_{\text{off-hours}} + 35 \cdot \max\left(0, \frac{V - \mu_V}{\sigma_V}\right) + 35 \cdot \mathbb{I}_{\text{unfamiliar-resource}}\right)$$
Where $V$ is the transferred data volume, $\mu_V$ is the historical daily mean, and $\sigma_V$ is the standard deviation.

### 3.5. ML Anomaly Sub-Score ($S_{\text{Anomaly}}$)
Derived from Scikit-Learn's Isolation Forest decision function:
$$S_{\text{Anomaly}} = 100 \cdot \left(1.0 - \text{normalized\_score}\right)$$
Maps raw decision score to a continuous outlier scale where $0$ is perfectly typical and $100$ is extreme statistical outlier.

### 3.6. Multi-Event Correlation Sub-Score ($S_{\text{Correlation}}$)
Evaluated across a sliding window of duration $T$ (default: 15 minutes):
$$S_{\text{Correlation}} = \min\left(100, \, \sum_{k=1}^{K} \text{Severity}(E_k) \cdot \gamma^{\Delta t_k}\right)$$
Where $\gamma \in (0, 1]$ is a temporal decay factor, rewarding rapid sequential clustering.

---

## 4. Operational Risk Classification Tiers

| Score Range | Risk Tier | System Action & Human Review Cadence |
| :---: | :--- | :--- |
| **0 – 30** | **LOW** | Normal activity. Logged to PostgreSQL and OpenSearch for baseline tracking. No analyst intervention required. |
| **31 – 60** | **MODERATE** | Contextual deviation. Recommend step-up verification (e.g. secondary push challenge). Flagged on dashboard metrics. |
| **61 – 80** | **HIGH** | Significant anomalous pattern. Automatically generates a `SecurityCase`. Assigned to security analyst queue for review. |
| **81 – 100**| **CRITICAL** | Severe multi-factor deviation or correlated threat. Generates high-priority case; recommends temporary sensitive-action restriction. |

---

## 5. Explainable Decomposition Output

Every computed score generates a structured explanation payload guaranteeing full transparency:
```json
{
  "total_score": 76.5,
  "risk_level": "HIGH",
  "factor_breakdown": [
    {
      "factor": "ROLE_RESOURCE_DEVIATION",
      "raw_subscore": 90.0,
      "weight": 0.20,
      "weighted_contribution": 18.0,
      "explanation": "User department (FINANCE) accessed CRITICAL engineering repository."
    },
    {
      "factor": "VOLUME_EXCEEDS_BASELINE",
      "raw_subscore": 85.0,
      "weight": 0.20,
      "weighted_contribution": 17.0,
      "explanation": "Data payload (2.1 GB) is 5.4 standard deviations above user average."
    },
    {
      "factor": "UNREGISTERED_DEVICE",
      "raw_subscore": 70.0,
      "weight": 0.15,
      "weighted_contribution": 10.5,
      "explanation": "Device DEV-9912 is not enrolled in corporate device management."
    }
  ]
}
```
