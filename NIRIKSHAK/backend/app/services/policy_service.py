import logging
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.policy import RiskPolicy

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "WEIGHT_IDENTITY": 0.23,
    "WEIGHT_DEVICE": 0.23,
    "WEIGHT_SENSITIVITY": 0.23,
    "WEIGHT_BEHAVIOR": 0.23,
    "WEIGHT_ANOMALY": 0.08,
    "WEIGHT_CORRELATION": 0.00,
}

DEFAULT_THRESHOLDS = {
    "THRESHOLD_LOW": 30.0,
    "THRESHOLD_MODERATE": 31.0,
    "THRESHOLD_HIGH": 61.0,
    "THRESHOLD_CRITICAL": 81.0,
}


class PolicyService:
    @staticmethod
    async def get_all_policies(session: AsyncSession) -> Dict[str, float]:
        result = await session.execute(select(RiskPolicy))
        policies = result.scalars().all()
        policy_dict = {**DEFAULT_WEIGHTS, **DEFAULT_THRESHOLDS}
        for p in policies:
            policy_dict[p.key] = p.value
        return policy_dict

    @staticmethod
    async def get_weights(session: AsyncSession) -> Dict[str, float]:
        all_policies = await PolicyService.get_all_policies(session)
        return {
            "identity": all_policies.get("WEIGHT_IDENTITY", 0.20),
            "device": all_policies.get("WEIGHT_DEVICE", 0.20),
            "sensitivity": all_policies.get("WEIGHT_SENSITIVITY", 0.20),
            "behavior": all_policies.get("WEIGHT_BEHAVIOR", 0.20),
            "anomaly": all_policies.get("WEIGHT_ANOMALY", 0.10),
            "correlation": all_policies.get("WEIGHT_CORRELATION", 0.10),
        }

    @staticmethod
    async def update_policy(session: AsyncSession, key: str, value: float, user_name: str) -> RiskPolicy:
        result = await session.execute(select(RiskPolicy).where(RiskPolicy.key == key))
        policy = result.scalar_one_or_none()
        if not policy:
            category = "WEIGHT" if key.startswith("WEIGHT_") else "THRESHOLD"
            policy = RiskPolicy(
                key=key,
                category=category,
                value=value,
                description=f"Configured policy for {key}",
                updated_by=user_name,
            )
            session.add(policy)
        else:
            policy.value = value
            policy.updated_by = user_name

        await session.commit()
        await session.refresh(policy)
        return policy
