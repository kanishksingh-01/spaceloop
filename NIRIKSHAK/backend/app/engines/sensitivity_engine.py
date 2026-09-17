from typing import List, Tuple
from app.models.user import User
from app.models.resource import Resource, ResourceClassification
from app.schemas.risk import FactorDetail


class SensitivityEngine:
    """Evaluates Data Sensitivity Tier and Organizational Clearance Boundaries."""

    BASE_SCORES = {
        "PUBLIC": 10.0,
        "INTERNAL": 25.0,
        "CONFIDENTIAL": 50.0,
        "RESTRICTED": 75.0,
        "CRITICAL": 90.0,
    }

    @classmethod
    def evaluate(
        cls,
        user: User,
        resource: Resource,
        classification: ResourceClassification,
        action: str,
        weight: float = 0.25,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []

        # 1. Base Classification Tier
        tier = classification.level.upper()
        base_score = cls.BASE_SCORES.get(tier, float(classification.base_sensitivity_score))
        score = base_score

        factors.append(
            FactorDetail(
                factor=f"RESOURCE_TIER_{tier}",
                subscore=base_score,
                weight=weight,
                contribution=round(base_score * weight, 2),
                explanation=f"Resource '{resource.name}' is classified under the {tier} sensitivity tier (baseline {base_score} pts).",
                details={"tier": tier, "base_sensitivity": base_score},
            )
        )

        # 2. Cross-Department Boundary Violation
        if tier != "PUBLIC" and user.department != resource.owner_department:
            cross_penalty = 25.0
            score += cross_penalty
            factors.append(
                FactorDetail(
                    factor="CROSS_DEPARTMENT_RESOURCE_ACCESS",
                    subscore=cross_penalty,
                    weight=weight,
                    contribution=round(cross_penalty * weight, 2),
                    explanation=f"User from '{user.department}' accessed repository owned by '{resource.owner_department}'.",
                    details={"user_department": user.department, "resource_department": resource.owner_department},
                )
            )

        # 3. High-Impact Action Penalty (e.g. EXPORT or DELETE on sensitive assets)
        if action.upper() in ["EXPORT", "DELETE", "WRITE"] and tier in ["CONFIDENTIAL", "RESTRICTED", "CRITICAL"]:
            action_penalty = 20.0
            score += action_penalty
            factors.append(
                FactorDetail(
                    factor=f"HIGH_IMPACT_ACTION_{action.upper()}",
                    subscore=action_penalty,
                    weight=weight,
                    contribution=round(action_penalty * weight, 2),
                    explanation=f"High-impact operation '{action.upper()}' executed against {tier} resource.",
                    details={"action": action, "tier": tier},
                )
            )

        normalized_score = min(100.0, max(0.0, score))
        return normalized_score, factors
