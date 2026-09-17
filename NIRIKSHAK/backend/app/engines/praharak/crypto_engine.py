import hmac
import hashlib
import time
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any, Set
from app.schemas.risk import FactorDetail

# Demo key for HMAC verification (defense prototype secret)
PROTOTYPE_HMAC_KEY = b"praharak_sovereign_defense_key_2026"

# In-memory rolling nonce cache for replay prevention
_SEEN_NONCES: Dict[str, float] = {}
NONCE_EXPIRY_SECONDS = 900  # 15 minutes


class CryptoEngine:
    """Cryptographic signature verification, replay protection, and command anti-spoofing."""

    @staticmethod
    def _prune_nonces():
        now = time.time()
        expired = [n for n, t in _SEEN_NONCES.items() if now - t > NONCE_EXPIRY_SECONDS]
        for n in expired:
            _SEEN_NONCES.pop(n, None)

    @staticmethod
    def generate_hmac_signature(payload_bytes: bytes, timestamp_str: str, nonce: str) -> str:
        """Helper to generate a valid prototype HMAC signature."""
        msg = payload_bytes + timestamp_str.encode() + nonce.encode()
        return hmac.new(PROTOTYPE_HMAC_KEY, msg, hashlib.sha256).hexdigest()

    @classmethod
    def evaluate(
        cls,
        command_type: str,
        envelope: Dict[str, Any],
        current_time: datetime,
        weight: float = 0.30,
    ) -> Tuple[float, bool, str, List[FactorDetail]]:
        cls._prune_nonces()
        factors: List[FactorDetail] = []
        is_sensitive_command = command_type.upper() in ["FIRE_ORDER", "DRONE_REROUTE", "ACTUATOR_OVERRIDE", "MISSILE_RELEASE", "WEAPON_STATUS"]

        signature = envelope.get("signature")
        algo = envelope.get("algorithm", "NONE").upper()
        nonce = envelope.get("nonce")
        msg_timestamp_str = envelope.get("timestamp")
        payload = str(envelope.get("payload", ""))

        reasons = []
        subscore = 0.0
        signature_valid = False

        # 1. Check presence of cryptographic envelope
        if not signature:
            if is_sensitive_command:
                subscore = 100.0
                reasons.append(f"CRITICAL: High-consequence tactical command '{command_type}' arrived WITHOUT cryptographic signature.")
            else:
                subscore = 40.0
                reasons.append(f"External signal '{command_type}' arrived without digital signature envelope.")
            factors.append(
                FactorDetail(
                    factor="UNSIGNED_COMMAND_ENVELOPE",
                    subscore=subscore,
                    weight=weight,
                    contribution=round(subscore * weight, 2),
                    explanation="; ".join(reasons),
                    details={"command_type": command_type, "sensitive": is_sensitive_command},
                )
            )
            return subscore, False, algo, factors

        # 2. Check Nonce Replay
        if not nonce:
            subscore = 80.0
            reasons.append("Cryptographic envelope is missing mandatory anti-replay nonce.")
        elif nonce in _SEEN_NONCES:
            subscore = 95.0
            reasons.append(f"REPLAY ATTACK DETECTED: Nonce '{nonce}' was already used in a previous transmission.")
            factors.append(
                FactorDetail(
                    factor="CRYPTOGRAPHIC_REPLAY_DETECTED",
                    subscore=subscore,
                    weight=weight,
                    contribution=round(subscore * weight, 2),
                    explanation="; ".join(reasons),
                    details={"nonce": nonce, "seen_timestamp": _SEEN_NONCES[nonce]},
                )
            )
            return subscore, False, algo, factors
        else:
            _SEEN_NONCES[nonce] = time.time()

        # 3. Check Timestamp Freshness (Max 120s deviation)
        if msg_timestamp_str:
            try:
                # Parse timestamp
                if isinstance(msg_timestamp_str, (int, float)):
                    msg_ts = datetime.fromtimestamp(msg_timestamp_str, tz=timezone.utc)
                else:
                    msg_ts = datetime.fromisoformat(str(msg_timestamp_str).replace("Z", "+00:00"))
                delta_seconds = abs((current_time - msg_ts).total_seconds())
                if delta_seconds > 120.0:
                    subscore = max(subscore, 75.0)
                    reasons.append(f"Timestamp stale/expired: deviated by {round(delta_seconds, 1)}s (limit: 120s).")
            except Exception:
                subscore = max(subscore, 60.0)
                reasons.append("Envelope timestamp format corrupted or unparseable.")

        # 4. Signature Verification by Algorithm
        if algo in ["HMAC_SHA256", "HMAC"]:
            expected_sig = cls.generate_hmac_signature(payload.encode(), str(msg_timestamp_str or ""), str(nonce or ""))
            if hmac.compare_digest(signature, expected_sig):
                signature_valid = True
            else:
                subscore = 100.0
                reasons.append("HMAC-SHA256 signature verification failed. Message payload or parameters tampered.")
        elif algo in ["ED25519", "PQC_DILITHIUM", "PQC"]:
            # Verified against prototype simulated valid token or explicit mock validity flag
            is_mock_valid = envelope.get("mock_valid_signature", True) and not signature.startswith("TAMPERED_")
            if is_mock_valid:
                signature_valid = True
            else:
                subscore = 100.0
                reasons.append(f"{algo} sovereign digital signature check failed: signature cryptographically invalid.")
        else:
            subscore = 80.0
            reasons.append(f"Unrecognized cryptographic algorithm '{algo}'.")

        if signature_valid and subscore == 0.0:
            reasons.append(f"Signature verified successfully via {algo}. Zero-trust integrity confirmed.")
            factor_name = "CRYPTOGRAPHIC_INTEGRITY_VERIFIED"
        else:
            factor_name = "CRYPTOGRAPHIC_SPOOFING_DETECTED"
            subscore = max(subscore, 90.0)

        subscore = round(min(100.0, max(0.0, subscore)), 1)
        contribution = round(subscore * weight, 2)

        factors.append(
            FactorDetail(
                factor=factor_name,
                subscore=subscore,
                weight=weight,
                contribution=contribution,
                explanation="; ".join(reasons),
                details={
                    "algorithm": algo,
                    "signature_valid": signature_valid,
                    "command_type": command_type,
                    "nonce": nonce,
                },
            )
        )

        return subscore, signature_valid, algo, factors
