from typing import Tuple, List, Dict, Any
from app.schemas.risk import FactorDetail

RECON_COMMAND_PATTERNS = {
    "PORT_SCAN": ("T1595.001", "Port Scanning & Network Sweeping", 85.0),
    "ENDPOINT_ENUMERATION": ("T1595.002", "Vulnerability Scanning & Route Fuzzing", 75.0),
    "AUTH_BRUTE_FORCE": ("T1110.001", "Password Guessing & Credential Spraying", 90.0),
    "SQL_INJECTION_PROBE": ("T1190", "Exploit Public-Facing Application (Injection Probe)", 95.0),
    "C2_BEACON": ("T1071.001", "Web Protocols C2 Beaconing Pattern", 70.0),
}


class ReconEngine:
    """Detects reconnaissance, probing patterns, and maps them to MITRE ATT&CK tactics."""

    @staticmethod
    def evaluate(
        command_type: str,
        target_service: str,
        raw_envelope: Dict[str, Any],
        weight: float = 0.20,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []
        cmd_upper = command_type.upper()
        payload = str(raw_envelope.get("payload", "")).lower()

        matched_tactic = None
        for pattern_key, (mitre_id, desc, score) in RECON_COMMAND_PATTERNS.items():
            if pattern_key in cmd_upper or pattern_key.lower() in payload:
                matched_tactic = (mitre_id, desc, score)
                break

        # Check for typical fuzzing / injection payload markers
        if not matched_tactic:
            fuzz_markers = ["/etc/passwd", "' or 1=1", "nmap", "<script>", "../..", "union select"]
            for marker in fuzz_markers:
                if marker in payload:
                    matched_tactic = ("T1190", f"Exploit Public-Facing Application: Parameter fuzzing marker '{marker}'", 90.0)
                    break

        if matched_tactic:
            mitre_id, desc, subscore = matched_tactic
            explanation = f"MITRE ATT&CK {mitre_id} detected: {desc} targeting service '{target_service}'."
            factor_name = f"RECON_PATTERN_{mitre_id.replace('.', '_')}"
        else:
            subscore = 0.0
            explanation = f"No hostile reconnaissance or vulnerability scan patterns detected for '{command_type}'."
            factor_name = "BENIGN_EXTERNAL_PATTERN"

        contribution = round(subscore * weight, 2)
        factors.append(
            FactorDetail(
                factor=factor_name,
                subscore=subscore,
                weight=weight,
                contribution=contribution,
                explanation=explanation,
                details={
                    "command_type": command_type,
                    "target_service": target_service,
                    "mitre_id": matched_tactic[0] if matched_tactic else None,
                },
            )
        )

        return subscore, factors
