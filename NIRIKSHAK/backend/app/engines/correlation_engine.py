import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Any
from app.schemas.risk import FactorDetail

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Evaluates multi-event sequences across temporal sliding windows (5m, 15m, 30m)."""

    @staticmethod
    def evaluate(
        current_action: str,
        current_resource_id: str,
        current_time: datetime,
        recent_events: List[Any],
        weight: float = 0.10,
    ) -> Tuple[float, float, List[FactorDetail]]:
        """
        Evaluates temporal correlation against recent events.
        Returns: (correlation_subscore, multiplier, factors)
        """
        factors: List[FactorDetail] = []
        if not recent_events:
            sub = 0.0
            factors.append(
                FactorDetail(
                    factor="ISOLATED_EVENT",
                    subscore=sub,
                    weight=weight,
                    contribution=0.0,
                    explanation="No preceding suspicious events detected in recent sliding window.",
                    details={"recent_event_count": 0},
                )
            )
            return sub, 1.0, factors

        # Filter events in sliding 15-minute window
        window_15m = current_time - timedelta(minutes=15)
        window_events = [
            e for e in recent_events
            if (e.timestamp if getattr(e, "timestamp", None) else current_time) >= window_15m
        ]

        distinct_resources = set(e.resource_id for e in window_events if getattr(e, "resource_id", None))
        distinct_resources.add(current_resource_id)

        actions_in_window = [e.action.upper() for e in window_events if getattr(e, "action", None)]
        actions_in_window.append(current_action.upper())

        subscore = 15.0
        multiplier = 1.0
        chain_signals = []

        # 1. Rapid Cross-Repository Hopping Check
        if len(distinct_resources) >= 3:
            subscore += 45.0
            multiplier = max(multiplier, 1.25)
            chain_signals.append(f"Rapid traversal across {len(distinct_resources)} distinct repositories within 15m")

        # 2. Reconnaissance to Exfiltration Kill Chain
        has_read = any(a in ["READ", "LIST"] for a in actions_in_window[:-1])
        is_exfil = current_action.upper() in ["EXPORT", "DOWNLOAD", "DELETE"]
        if has_read and is_exfil:
            subscore += 40.0
            multiplier = max(multiplier, 1.35)
            chain_signals.append("Temporal kill-chain detected: Reconnaissance/Read followed by bulk Exfiltration")

        # 3. High Event Velocity
        if len(window_events) >= 5:
            subscore += 30.0
            multiplier = max(multiplier, 1.20)
            chain_signals.append(f"High event frequency burst ({len(window_events) + 1} events in window)")

        if chain_signals:
            normalized_subscore = round(min(100.0, max(50.0, subscore)), 1)
            explanation = "Sliding-window correlation detected sequential kill-chain patterns: " + "; ".join(chain_signals)
            factors.append(
                FactorDetail(
                    factor="MULTI_EVENT_KILL_CHAIN_CORRELATION",
                    subscore=normalized_subscore,
                    weight=weight,
                    contribution=round(normalized_subscore * weight, 2),
                    explanation=explanation,
                    details={
                        "recent_events_count": len(window_events),
                        "distinct_resources_count": len(distinct_resources),
                        "actions_in_window": actions_in_window,
                        "multiplier": multiplier,
                        "chain_signals": chain_signals,
                    },
                )
            )
            return normalized_subscore, multiplier, factors
        else:
            factors.append(
                FactorDetail(
                    factor="NORMAL_EVENT_PACE",
                    subscore=0.0,
                    weight=weight,
                    contribution=0.0,
                    explanation=f"Event frequency is within normal range ({len(window_events)} events in past 15 minutes).",
                    details={"recent_events_count": len(window_events)},
                )
            )
            return 0.0, 1.0, factors
