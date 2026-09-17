from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np


FEATURE_NAMES = [
    "hour_deviation",
    "volume_z_score",
    "resource_sensitivity",
    "device_familiarity",
    "department_mismatch",
    "action_severity",
]


class FeatureExtractor:
    """Extracts standardized 6D numerical feature vectors for ML anomaly detection."""

    @staticmethod
    def extract_vector(
        user_department: str,
        user_baseline: Optional[Any],
        device_id: str,
        device_registered: bool,
        device_owner_user_id: Optional[str],
        user_id: str,
        resource_classification_level: str,
        resource_owner_dept: str,
        action: str,
        timestamp: datetime,
        data_volume: int,
    ) -> np.ndarray:
        # 1. Hour deviation
        hour = timestamp.hour + (timestamp.minute / 60.0)
        start_h = 9.0
        end_h = 18.0
        if user_baseline and getattr(user_baseline, "typical_hours", None):
            bh = user_baseline.typical_hours
            if isinstance(bh, dict):
                start_h = float(bh.get("start", 9))
                end_h = float(bh.get("end", 18))

        if start_h <= hour <= end_h:
            hour_deviation = 0.0
        else:
            diff1 = (start_h - hour) % 24
            diff2 = (hour - end_h) % 24
            hour_deviation = float(min(diff1, diff2))

        # 2. Volume Z-Score
        avg_vol = 15728640.0  # 15 MB default
        std_vol = 5242880.0   # 5 MB default
        if user_baseline and getattr(user_baseline, "avg_daily_volume", None):
            avg_vol = float(user_baseline.avg_daily_volume)
            std_vol = float(user_baseline.std_daily_volume or 5242880.0)

        raw_z = (float(data_volume) - avg_vol) / max(std_vol, 1.0)
        volume_z_score = float(np.clip(raw_z, 0.0, 10.0))

        # 3. Resource Sensitivity
        sens_map = {
            "PUBLIC": 10.0,
            "INTERNAL": 25.0,
            "CONFIDENTIAL": 50.0,
            "RESTRICTED": 75.0,
            "CRITICAL": 90.0,
        }
        resource_sensitivity = sens_map.get(resource_classification_level.upper(), 50.0)

        # 4. Device Familiarity
        if not device_registered:
            device_familiarity = 1.0
        elif user_baseline and getattr(user_baseline, "typical_devices", None):
            if device_id in user_baseline.typical_devices or (device_owner_user_id and device_owner_user_id == user_id):
                device_familiarity = 0.0
            else:
                device_familiarity = 0.5
        elif device_owner_user_id == user_id:
            device_familiarity = 0.0
        else:
            device_familiarity = 0.5

        # 5. Department Mismatch
        department_mismatch = 0.0 if user_department.upper() == resource_owner_dept.upper() else 1.0

        # 6. Action Severity
        action_map = {
            "READ": 10.0,
            "LIST": 15.0,
            "WRITE": 30.0,
            "MODIFY": 40.0,
            "EXPORT": 80.0,
            "DOWNLOAD": 80.0,
            "DELETE": 90.0,
        }
        action_severity = action_map.get(action.upper(), 30.0)

        vec = np.array([
            hour_deviation,
            volume_z_score,
            resource_sensitivity,
            device_familiarity,
            department_mismatch,
            action_severity,
        ], dtype=np.float64)

        return vec
