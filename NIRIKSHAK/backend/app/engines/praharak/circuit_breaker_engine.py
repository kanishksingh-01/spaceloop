from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Dict, Optional
from app.schemas.risk import FactorDetail

# Sliding window rate thresholds
WINDOW_FAST_SECONDS = 10
BURST_THRESHOLD = 15  # requests per 10s
SUSTAINED_THRESHOLD = 50  # requests per 60s
QUARANTINE_DURATION_MINUTES = 15

# In-memory tracking cache for high-speed evaluation (can be backed by Redis in production)
_REQUEST_HISTORY: Dict[str, List[datetime]] = {}
_CIRCUIT_STATES: Dict[str, Dict] = {}


class CircuitBreakerEngine:
    """Sliding-window velocity inspection and automated graduated circuit breaking."""

    @classmethod
    def reset_state(cls, source_identifier: str):
        """Manually reset the circuit breaker for a source."""
        _CIRCUIT_STATES.pop(source_identifier, None)
        _REQUEST_HISTORY.pop(source_identifier, None)

    @classmethod
    def get_state(cls, source_identifier: str) -> Dict:
        """Returns the current state dictionary for a source."""
        return _CIRCUIT_STATES.get(source_identifier, {
            "state": "CLOSED",
            "request_count": 0,
            "is_quarantined": False,
            "trip_expires_at": None,
        })

    @classmethod
    def evaluate(
        cls,
        source_identifier: str,
        current_time: datetime,
        weight: float = 0.15,
    ) -> Tuple[float, bool, str, List[FactorDetail]]:
        factors: List[FactorDetail] = []

        # Check existing tripped state
        cached_state = _CIRCUIT_STATES.get(source_identifier)
        if cached_state and cached_state.get("state") == "OPEN":
            trip_expires_at = cached_state.get("trip_expires_at")
            if trip_expires_at and current_time < trip_expires_at:
                # Still within active quarantine
                subscore = 100.0
                factors.append(
                    FactorDetail(
                        factor="CIRCUIT_BREAKER_ACTIVE_QUARANTINE",
                        subscore=subscore,
                        weight=weight,
                        contribution=round(subscore * weight, 2),
                        explanation=f"Traffic source is currently QUARANTINED until {trip_expires_at.isoformat()} due to prior mass flood.",
                        details={"state": "OPEN", "trip_expires_at": trip_expires_at.isoformat()},
                    )
                )
                return subscore, True, "OPEN", factors
            else:
                # Quarantine expired -> transition to HALF-OPEN to re-test
                cached_state["state"] = "HALF-OPEN"

        # Record current event in sliding history
        if source_identifier not in _REQUEST_HISTORY:
            _REQUEST_HISTORY[source_identifier] = []

        history = _REQUEST_HISTORY[source_identifier]
        history.append(current_time)

        # Prune older than 60s
        cutoff_60s = current_time - timedelta(seconds=60)
        _REQUEST_HISTORY[source_identifier] = [t for t in history if t >= cutoff_60s]
        current_60s_count = len(_REQUEST_HISTORY[source_identifier])

        # Check 10s burst count
        cutoff_10s = current_time - timedelta(seconds=WINDOW_FAST_SECONDS)
        current_10s_count = len([t for t in _REQUEST_HISTORY[source_identifier] if t >= cutoff_10s])

        # Evaluate thresholds
        is_tripped = False
        if current_10s_count >= BURST_THRESHOLD or current_60s_count >= SUSTAINED_THRESHOLD:
            new_state = "OPEN"
            is_tripped = True
            subscore = 100.0
            trip_expires_at = current_time + timedelta(minutes=QUARANTINE_DURATION_MINUTES)
            explanation = (
                f"MASS-ATTACK / FLOOD DETECTED: Source generated {current_10s_count} requests in 10s "
                f"(burst threshold {BURST_THRESHOLD}) and {current_60s_count} in 60s. "
                f"Circuit breaker TRIPPED to OPEN. Automated 15-minute quarantine enforced."
            )
            factor_name = "CIRCUIT_BREAKER_TRIPPED"
        elif current_10s_count >= (BURST_THRESHOLD * 0.6):
            new_state = "HALF-OPEN"
            subscore = 60.0
            trip_expires_at = None
            explanation = (
                f"Elevated velocity burst ({current_10s_count} req/10s). Circuit breaker transitioned to HALF-OPEN. "
                "Secondary proof-of-work or rate-limiting challenge recommended."
            )
            factor_name = "VELOCITY_BURST_WARNING"
        else:
            new_state = "CLOSED"
            subscore = 0.0
            trip_expires_at = None
            explanation = f"Velocity is within normal limits ({current_10s_count} req/10s)."
            factor_name = "NORMAL_TRAFFIC_VELOCITY"

        # Update cache
        _CIRCUIT_STATES[source_identifier] = {
            "state": new_state,
            "request_count": current_60s_count,
            "window_start": cutoff_60s,
            "trip_expires_at": trip_expires_at,
            "is_quarantined": is_tripped,
        }

        contribution = round(subscore * weight, 2)
        factors.append(
            FactorDetail(
                factor=factor_name,
                subscore=subscore,
                weight=weight,
                contribution=contribution,
                explanation=explanation,
                details={
                    "state": new_state,
                    "burst_count_10s": current_10s_count,
                    "sustained_count_60s": current_60s_count,
                    "is_tripped": is_tripped,
                },
            )
        )

        return subscore, is_tripped, new_state, factors
