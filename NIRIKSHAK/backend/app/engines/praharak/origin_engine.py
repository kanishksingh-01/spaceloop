import ipaddress
from typing import Tuple, List, Optional
from app.schemas.risk import FactorDetail

# Synthetic high-risk ASNs and malicious IP prefixes for demo/defense testing
SYNTHETIC_MALICIOUS_SUBNETS = [
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
]
SYNTHETIC_KNOWN_GATEWAYS = [
    "10.0.0.1", "10.0.0.2", "192.168.1.1", "172.16.0.1"
]
HIGH_RISK_ASNS = {"AS40065", "AS9009", "AS13335_ANON", "AS-BULLETPROOF"}


class OriginEngine:
    """Evaluates source IP locality, ASN reputation, and gateway enrollment."""

    @staticmethod
    def evaluate(
        source_ip: str,
        source_asn: Optional[str] = None,
        weight: float = 0.20,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []
        subscore = 0.0
        reasons = []

        try:
            ip_obj = ipaddress.ip_address(source_ip)
            is_private = ip_obj.is_private
        except ValueError:
            is_private = False

        if source_ip in SYNTHETIC_KNOWN_GATEWAYS or is_private:
            subscore = 0.0
            reasons.append("Source verified as enrolled defense gateway / secure subnet.")
        else:
            subscore = 35.0
            reasons.append("Access originates from external public IP space.")

        # Check synthetic malicious subnets
        is_blacklisted = False
        try:
            ip_obj = ipaddress.ip_address(source_ip)
            for net in SYNTHETIC_MALICIOUS_SUBNETS:
                if ip_obj in net:
                    is_blacklisted = True
                    break
        except ValueError:
            pass

        if is_blacklisted:
            subscore = max(subscore, 85.0)
            reasons.append(f"Source IP {source_ip} matches threat intelligence malicious subnet range.")

        # Check ASN reputation
        if source_asn and source_asn.upper() in HIGH_RISK_ASNS:
            subscore = max(subscore, 75.0)
            reasons.append(f"Origin ASN '{source_asn}' identified with anonymization proxy / untrusted hosting infrastructure.")

        subscore = round(min(100.0, max(0.0, subscore)), 1)
        contribution = round(subscore * weight, 2)

        factor_name = "TRUSTED_ORIGIN" if subscore <= 20.0 else "UNTRUSTED_EXTERNAL_ORIGIN"
        factors.append(
            FactorDetail(
                factor=factor_name,
                subscore=subscore,
                weight=weight,
                contribution=contribution,
                explanation="; ".join(reasons),
                details={"source_ip": source_ip, "source_asn": source_asn, "is_private": is_private},
            )
        )

        return subscore, factors
