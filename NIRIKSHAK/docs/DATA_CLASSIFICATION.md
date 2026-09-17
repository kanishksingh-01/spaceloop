# NIRIKSHAK Synthetic Data Classification & Access Policies

> **NIRIKSHAK**: Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework  
> **Status**: APPROVED DATA CLASSIFICATION SPECIFICATION

---

## 1. Classification Tiers & Sensitivity Multipliers

NIRIKSHAK defines five standard data classification tiers, each associated with an intrinsic base sensitivity score:

| Level | Base Sensitivity Score | Description & Handling Constraints | Example Synthetic Repository |
| :--- | :---: | :--- | :--- |
| **PUBLIC** | `10` | Publicly releasable information. No operational impact if disclosed. | Synthetic Public Documentation Portal |
| **INTERNAL** | `25` | Standard internal operational data. Accessible to all authenticated personnel. | General Synthetic Knowledge Base |
| **CONFIDENTIAL** | `50` | Proprietary engineering designs and commercial telemetry. Requires departmental need-to-know. | Engineering Repository B |
| **RESTRICTED** | `75` | Highly sensitive personnel records and threat intelligence models. Strict access controls. | Personnel Security Repository D |
| **CRITICAL** | `90` | Core operational algorithms and defense-related simulation data. Elevated monitoring mandatory. | Operational Repository A |

---

## 2. Departmental Authorization Matrix

Synthetic departments:
* `DEFENSE_RD` (Defense Research & Development)
* `ENGINEERING` (Core Systems Engineering)
* `SECURITY` (Information Security & SOC Operations)
* `FINANCE` (Corporate Accounting & Budgeting)
* `HUMAN_RESOURCES` (Personnel Administration)

| Synthetic Repository | Classification | Owning Dept | Permitted Departments | Cross-Department Access Result |
| :--- | :--- | :--- | :--- | :--- |
| **Operational Repository A** | `CRITICAL` | `DEFENSE_RD` | `DEFENSE_RD`, `SECURITY` (Read-only) | Elevated Sensitivity Flag (+30) |
| **Engineering Repository B** | `CONFIDENTIAL` | `ENGINEERING` | `ENGINEERING`, `DEFENSE_RD` | Moderate Sensitivity Flag (+15) |
| **Threat Assessment Rep C** | `RESTRICTED` | `SECURITY` | `SECURITY` | High Sensitivity Flag (+25) |
| **Personnel Security Rep D** | `RESTRICTED` | `HUMAN_RESOURCES`| `HUMAN_RESOURCES` | High Sensitivity Flag (+30) |
| **Public Documentation E** | `PUBLIC` | All | All | Benign Context (0) |
