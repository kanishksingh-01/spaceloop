from datetime import datetime
from typing import Dict, Any, List, Tuple
from app.schemas.risk import FactorDetail
from app.engines.praharak.origin_engine import OriginEngine
from app.engines.praharak.crypto_engine import CryptoEngine
from app.engines.praharak.recon_engine import ReconEngine
from app.engines.praharak.circuit_breaker_engine import CircuitBreakerEngine


class PraharakRiskEngine:
    """Computes deterministic external risk and assigns proportional operational disposition."""

    WEIGHT_ORIGIN = 0.20
    WEIGHT_INTEGRITY = 0.30
    WEIGHT_RECON = 0.20
    WEIGHT_VELOCITY = 0.15
    WEIGHT_INTEL = 0.15

    @classmethod
    def evaluate(
        cls,
        source_ip: str,
        source_asn: str | None,
        target_service: str,
        command_type: str,
        raw_envelope: Dict[str, Any],
        current_time: datetime,
    ) -> Tuple[float, str, str, bool, str, bool, List[FactorDetail]]:
        all_factors: List[FactorDetail] = []

        # 1. Velocity & Circuit Breaker Check (Fast Path)
        vel_score, is_tripped, cb_state, vel_factors = CircuitBreakerEngine.evaluate(
            source_identifier=source_ip,
            current_time=current_time,
            weight=cls.WEIGHT_VELOCITY,
        )
        all_factors.extend(vel_factors)

        # 2. Cryptographic Anti-Spoofing Check
        crypto_score, sig_valid, sig_algo, crypto_factors = CryptoEngine.evaluate(
            command_type=command_type,
            envelope=raw_envelope,
            current_time=current_time,
            weight=cls.WEIGHT_INTEGRITY,
        )
        all_factors.extend(crypto_factors)

        # 3. Origin & Threat Intel Check
        origin_score, origin_factors = OriginEngine.evaluate(
            source_ip=source_ip,
            source_asn=source_asn,
            weight=cls.WEIGHT_ORIGIN,
        )
        all_factors.extend(origin_factors)

        # 4. Reconnaissance Pattern Recognition
        recon_score, recon_factors = ReconEngine.evaluate(
            command_type=command_type,
            target_service=target_service,
            raw_envelope=raw_envelope,
            weight=cls.WEIGHT_RECON,
        )
        all_factors.extend(recon_factors)

        # 5. External Threat Intel Feed Score
        # For prototype, Intel is elevated if source is known malicious
        intel_score = origin_score if origin_score >= 80.0 else 0.0
        intel_contrib = round(intel_score * cls.WEIGHT_INTEL, 2)
        all_factors.append(
            FactorDetail(
                factor="THREAT_INTEL_REPUTATION",
                subscore=intel_score,
                weight=cls.WEIGHT_INTEL,
                contribution=intel_contrib,
                explanation=(
                    "Known malicious IOC match in threat intel database."
                    if intel_score > 0
                    else "No active threat intelligence matches on external IP."
                ),
                details={"source_ip": source_ip, "intel_score": intel_score},
            )
        )

        # Composite score
        raw_composite = (
            (origin_score * cls.WEIGHT_ORIGIN)
            + (crypto_score * cls.WEIGHT_INTEGRITY)
            + (recon_score * cls.WEIGHT_RECON)
            + (vel_score * cls.WEIGHT_VELOCITY)
            + (intel_score * cls.WEIGHT_INTEL)
        )

        # Hard security override: If signature is tampered or circuit breaker tripped, force critical
        if not sig_valid and command_type.upper() in ["FIRE_ORDER", "DRONE_REROUTE", "ACTUATOR_OVERRIDE"]:
            total_score = max(raw_composite, 92.0)
        elif is_tripped:
            total_score = max(raw_composite, 88.0)
        else:
            total_score = raw_composite

        total_score = round(min(100.0, max(0.0, total_score)), 1)

        # Assign Tier & Proportional Disposition
        if total_score >= 81.0:
            risk_tier = "CRITICAL"
            disposition = "BLOCKED"
        elif total_score >= 61.0:
            risk_tier = "HIGH"
            disposition = "THROTTLED"
        elif total_score >= 31.0:
            risk_tier = "MODERATE"
            disposition = "CHALLENGED"
        else:
            risk_tier = "LOW"
            disposition = "ALLOWED"

        return total_score, risk_tier, disposition, sig_valid, sig_algo, is_tripped, all_factors
