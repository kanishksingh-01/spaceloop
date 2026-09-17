from typing import List, Tuple
from app.models.user import User
from app.models.resource import Resource, ResourceClassification
from app.schemas.risk import FactorDetail


class IdentityEngine:
    """Evaluates Identity Confidence and Authentication Strength."""

    @staticmethod
    def evaluate(
        user: User,
        resource: Resource,
        classification: ResourceClassification,
        source_context: dict,
        weight: float = 0.25,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []
        score = 0.0

        mfa_verified = source_context.get("mfa_verified", False)
        is_sensitive = classification.level in ["CONFIDENTIAL", "RESTRICTED", "CRITICAL"]

        # Check MFA status
        if not mfa_verified:
            if is_sensitive:
                sub = 75.0
                score += sub
                factors.append(
                    FactorDetail(
                        factor="MISSING_MFA_SENSITIVE_ACCESS",
                        subscore=sub,
                        weight=weight,
                        contribution=round(sub * weight, 2),
                        explanation=f"Sensitive resource '{resource.name}' ({classification.level}) accessed without Multi-Factor Authentication.",
                        details={"mfa_verified": False, "classification": classification.level},
                    )
                )
            else:
                sub = 30.0
                score += sub
                factors.append(
                    FactorDetail(
                        factor="MISSING_MFA",
                        subscore=sub,
                        weight=weight,
                        contribution=round(sub * weight, 2),
                        explanation="Access initiated without active second-factor verification.",
                        details={"mfa_verified": False},
                    )
                )

        # Check Account Status
        if user.status != "ACTIVE":
            sub = 50.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="INACTIVE_OR_PROBATIONARY_ACCOUNT",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"User account status is '{user.status}', not ACTIVE.",
                    details={"user_status": user.status},
                )
            )

        # Cap score at 100.0
        normalized_score = min(100.0, max(0.0, score))
        return normalized_score, factors
