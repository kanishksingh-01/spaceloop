from datetime import datetime
from typing import List, Tuple
from app.models.baseline import BehaviorBaseline
from app.models.resource import Resource
from app.models.device import Device
from app.schemas.risk import FactorDetail


class BehaviorEngine:
    """Evaluates Statistical Deviation from Historical User and Role Baselines."""

    @staticmethod
    def evaluate(
        baseline: BehaviorBaseline | None,
        event_time: datetime,
        data_volume: int,
        resource: Resource,
        device: Device,
        weight: float = 0.25,
    ) -> Tuple[float, List[FactorDetail]]:
        factors: List[FactorDetail] = []
        score = 0.0

        if not baseline:
            # If no baseline established yet, return nominal score
            return 20.0, [
                FactorDetail(
                    factor="NO_HISTORICAL_BASELINE",
                    subscore=20.0,
                    weight=weight,
                    contribution=round(20.0 * weight, 2),
                    explanation="No historical baseline profile established for user yet.",
                    details={},
                )
            ]

        # 1. Working Hours Deviation
        typical_hours = baseline.typical_hours or {"start": 9, "end": 18}
        start_hour = typical_hours.get("start", 9)
        end_hour = typical_hours.get("end", 18)
        event_hour = event_time.hour + (event_time.minute / 60.0)

        if event_hour < start_hour or event_hour >= end_hour:
            # Calculate distance from nearest boundary
            dist = min(abs(event_hour - start_hour), abs(event_hour - end_hour))
            sub = min(80.0, 40.0 + dist * 5.0)
            score += sub
            factors.append(
                FactorDetail(
                    factor="OFF_HOURS_ACCESS_DEVIATION",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"Access occurred at {event_time.strftime('%H:%M')} UTC, outside typical window ({start_hour:02d}:00–{end_hour:02d}:00).",
                    details={"event_time_utc": event_time.isoformat(), "typical_window": f"{start_hour:02d}:00-{end_hour:02d}:00"},
                )
            )

        # 2. Data Volume Anomaly (Z-Score)
        avg_vol = baseline.avg_daily_volume or 15728640  # 15 MB
        std_vol = baseline.std_daily_volume or 5242880   # 5 MB

        if data_volume > avg_vol:
            z_score = (data_volume - avg_vol) / max(1, std_vol)
            if z_score >= 3.0:
                sub = min(95.0, 50.0 + z_score * 8.0)
                score += sub
                vol_mb = round(data_volume / (1024 * 1024), 2)
                avg_mb = round(avg_vol / (1024 * 1024), 2)
                factors.append(
                    FactorDetail(
                        factor="VOLUME_EXCEEDS_3_SIGMA",
                        subscore=sub,
                        weight=weight,
                        contribution=round(sub * weight, 2),
                        explanation=f"Data volume ({vol_mb} MB) is {z_score:.1f} standard deviations above normal average ({avg_mb} MB).",
                        details={"data_volume_bytes": data_volume, "z_score": round(z_score, 2), "baseline_mean_bytes": avg_vol},
                    )
                )
            elif z_score >= 1.5:
                sub = 30.0
                score += sub
                vol_mb = round(data_volume / (1024 * 1024), 2)
                factors.append(
                    FactorDetail(
                        factor="ELEVATED_DATA_VOLUME",
                        subscore=sub,
                        weight=weight,
                        contribution=round(sub * weight, 2),
                        explanation=f"Data transfer ({vol_mb} MB) is elevated compared to historical baseline.",
                        details={"data_volume_bytes": data_volume, "z_score": round(z_score, 2)},
                    )
                )

        # 3. Resource Familiarity Check
        typical_resources = baseline.typical_resources or []
        if typical_resources and resource.id not in typical_resources:
            sub = 35.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="UNFAMILIAR_RESOURCE_FOR_USER",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"User has no documented historical access patterns for '{resource.name}'.",
                    details={"resource_id": resource.id, "resource_name": resource.name},
                )
            )

        # 4. Device Familiarity Check
        typical_devices = baseline.typical_devices or []
        if typical_devices and device.id not in typical_devices:
            sub = 25.0
            score += sub
            factors.append(
                FactorDetail(
                    factor="UNFAMILIAR_DEVICE_FOR_USER",
                    subscore=sub,
                    weight=weight,
                    contribution=round(sub * weight, 2),
                    explanation=f"Endpoint '{device.device_identifier}' is not in user's typical historical device list.",
                    details={"device_id": device.id, "device_identifier": device.device_identifier},
                )
            )

        normalized_score = min(100.0, max(0.0, score))
        return normalized_score, factors
