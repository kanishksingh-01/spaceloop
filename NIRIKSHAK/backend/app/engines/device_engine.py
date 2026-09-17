from typing import List, Tuple
from app.models.user import User
from app.models.device import Device
from app.schemas.risk import FactorDetail


class DeviceEngine:
    """Evaluates Endpoint Trust and Environmental Posture."""

    @staticmethod
    def evaluate(
        user: User,
        device: Device,
        source_context: dict,
        weight: float = 0.25,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []
        score = 0.0

        # 1. Device Registration Check
        if not device.registered:
            sub = 70.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="UNREGISTERED_DEVICE",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"Endpoint '{device.device_identifier}' is not enrolled in corporate device management.",
                    details={"device_identifier": device.device_identifier, "registered": False},
                )
            )

        # 2. Trust Level Assessment
        if device.trust_level == "REVOKED":
            sub = 95.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="REVOKED_DEVICE_ACCESS",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"Endpoint '{device.device_identifier}' has been revoked by security operations.",
                    details={"trust_level": device.trust_level},
                )
            )
        elif device.trust_level in ["LOW", "UNKNOWN"]:
            sub = 50.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="LOW_DEVICE_TRUST_POSTURE",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"Endpoint trust posture evaluated as '{device.trust_level}'.",
                    details={"trust_level": device.trust_level},
                )
            )

        # 3. Cross-User Ownership Check
        if device.owner_user_id and device.owner_user_id != user.id:
            sub = 40.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="SHARED_OR_UNOWNED_DEVICE_ACCESS",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation="Device is registered to a different employee account.",
                    details={"device_owner_id": device.owner_user_id, "accessing_user_id": user.id},
                )
            )

        # 4. External IP Locality Check
        client_ip = source_context.get("client_ip", "")
        is_corp = source_context.get("corporate_network", True)
        if not is_corp or (client_ip and not (client_ip.startswith("10.") or client_ip.startswith("192.168."))):
            sub = 25.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="UNTRUSTED_NETWORK_LOCALITY",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"Access originated from untrusted external network address '{client_ip}'.",
                    details={"client_ip": client_ip},
                )
            )

        normalized_score = min(100.0, max(0.0, score))
        return normalized_score, factors
