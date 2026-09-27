"""
SpaceLoop Fraud Engine Feature Extraction Layer
Extracts behavioural, temporal, geographic, and financial features using Pandas and NumPy.
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models import User, Space, Booking, DeviceSession, FraudEventRecord
from fraud_engine.schemas import FraudEventInput, FraudEventType

# Canonical disposable email domains
DISPOSABLE_DOMAINS = frozenset([
    "mailinator.com", "guerrillamail.com", "tempmail.com", "10minutemail.com",
    "throwawaymail.com", "trashmail.com", "sharklasers.com", "yopmail.com",
    "dispostable.com", "getairmail.com", "temp-mail.org", "fakeinbox.com",
    "inboxkitten.com", "burnermail.io", "mytemp.email"
])


def is_disposable_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.strip().lower().split("@")[-1]
    return domain in DISPOSABLE_DOMAINS


def compute_haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Computes great-circle distance between two GPS coordinates using NumPy."""
    try:
        r = 6371.0  # Earth radius in kilometers
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lng2 - lng1)

        a = np.sin(dphi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0)**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        return float(r * c)
    except Exception:
        return 0.0


class FeatureExtractor:
    """
    Extracts high-dimensional risk features from events and historical state.
    """

    @classmethod
    def extract(cls, event: FraudEventInput, db: Session) -> Dict[str, Any]:
        features: Dict[str, Any] = {}
        now = datetime.utcnow()

        # -------------------------------------------------------------
        # 1. Payload & Identity Core Features
        # -------------------------------------------------------------
        payload = event.payload or {}
        email = str(payload.get("email") or "").strip().lower()
        if not email and event.user_id:
            user = db.query(User).filter(User.id == event.user_id).first()
            if user:
                email = user.email

        features["email_is_disposable"] = is_disposable_email(email)
        features["email_domain"] = email.split("@")[-1] if "@" in email else ""

        # -------------------------------------------------------------
        # 2. IP & Device Velocity Features
        # -------------------------------------------------------------
        ip = event.ip_address or ""
        fp = event.device_fingerprint or ""

        # IP account creation velocity in last 1 hour
        if ip:
            window_1h = now - timedelta(hours=1)
            ip_creations = db.query(FraudEventRecord.id).filter(
                FraudEventRecord.ip_address == ip,
                FraudEventRecord.event_type == FraudEventType.ACCOUNT_CREATED.value,
                FraudEventRecord.created_at >= window_1h
            ).all()
            features["ip_creation_velocity_1h"] = len(ip_creations)
        else:
            features["ip_creation_velocity_1h"] = 0

        # Device fingerprint multi-account overlap
        if fp:
            sessions = db.query(DeviceSession.user_id).filter(
                DeviceSession.device_fingerprint == fp
            ).distinct().all()
            distinct_users = {s[0] for s in sessions if s[0] is not None}
            if event.user_id:
                distinct_users.add(event.user_id)
            features["device_user_overlap_count"] = len(distinct_users)
        else:
            features["device_user_overlap_count"] = 1

        # -------------------------------------------------------------
        # 3. User Historical Behavior & Churn (Pandas vectorized)
        # -------------------------------------------------------------
        if event.user_id:
            # Query recent events for velocity
            recent_events = db.query(
                FraudEventRecord.event_type,
                FraudEventRecord.created_at
            ).filter(
                FraudEventRecord.user_id == event.user_id,
                FraudEventRecord.created_at >= now - timedelta(days=7)
            ).all()

            if recent_events:
                df_events = pd.DataFrame(recent_events, columns=["event_type", "created_at"])
                df_events["created_at"] = pd.to_datetime(df_events["created_at"])

                # Events in last 15 min
                window_15m = pd.Timestamp(now - timedelta(minutes=15))
                features["user_event_count_15m"] = int((df_events["created_at"] >= window_15m).sum())

                # Bookings in last 15 min
                is_booking = df_events["event_type"] == FraudEventType.BOOKING_CREATED.value
                features["user_booking_count_15m"] = int(((df_events["created_at"] >= window_15m) & is_booking).sum())

                # Payment failures in last 15 min
                is_pay_fail = df_events["event_type"] == FraudEventType.PAYMENT_FAILED.value
                features["failed_payment_count_15m"] = int(((df_events["created_at"] >= window_15m) & is_pay_fail).sum())
            else:
                features["user_event_count_15m"] = 0
                features["user_booking_count_15m"] = 0
                features["failed_payment_count_15m"] = 0

            # Cancellation Churn ratio over last 7 days (from Booking table)
            user_bookings = db.query(Booking.status, Booking.created_at).filter(
                Booking.renter_id == event.user_id,
                Booking.created_at >= now - timedelta(days=7)
            ).all()

            if len(user_bookings) >= 2:
                df_b = pd.DataFrame(user_bookings, columns=["status", "created_at"])
                cancelled_count = (df_b["status"] == "cancelled").sum()
                features["user_cancellation_ratio_7d"] = float(cancelled_count / len(df_b))
                features["user_total_bookings_7d"] = int(len(df_b))
            else:
                features["user_cancellation_ratio_7d"] = 0.0
                features["user_total_bookings_7d"] = len(user_bookings)

            # Profile changes recency
            user_rec = db.query(User).filter(User.id == event.user_id).first()
            if user_rec:
                features["is_host_verified"] = bool(user_rec.is_host_verified)
                features["is_aadhaar_verified"] = bool(user_rec.is_aadhaar_verified)
                features["is_student_verified"] = bool(user_rec.is_student_verified)
                features["user_trust_score"] = float(user_rec.objective_trust_score or 98.5)
            else:
                features["is_host_verified"] = False
                features["is_aadhaar_verified"] = False
                features["is_student_verified"] = False
                features["user_trust_score"] = 98.5
        else:
            features["user_event_count_15m"] = 0
            features["user_booking_count_15m"] = 0
            features["failed_payment_count_15m"] = 0
            features["user_cancellation_ratio_7d"] = 0.0
            features["user_total_bookings_7d"] = 0
            features["is_host_verified"] = False
            features["is_aadhaar_verified"] = False
            features["is_student_verified"] = False
            features["user_trust_score"] = 98.5

        # -------------------------------------------------------------
        # 4. Financial & Price Anomaly Features (NumPy)
        # -------------------------------------------------------------
        amount = float(payload.get("amount") or payload.get("total_price") or payload.get("price") or 0.0)
        features["transaction_amount"] = amount

        space_id = payload.get("space_id") or (event.entity_id if event.entity_type in ("space", "listing") else None)
        features["space_id"] = space_id

        # Self-booking check
        if space_id and event.user_id:
            sp = db.query(Space.owner_id).filter(Space.id == space_id).first()
            features["is_self_transaction"] = bool(sp and sp[0] == event.user_id)
        else:
            features["is_self_transaction"] = False

        # Statistical Price Deviation (Modified Z-Score via NumPy)
        if amount > 0:
            all_prices = [s[0] for s in db.query(Space.price_hourly).filter(Space.is_active == True, Space.price_hourly > 0).all()]
            if len(all_prices) >= 5:
                arr = np.array(all_prices, dtype=np.float64)
                med = np.median(arr)
                mad = np.median(np.abs(arr - med))
                if mad > 0:
                    mod_z = 0.6745 * (amount - med) / mad
                    features["price_zscore"] = float(round(mod_z, 2))
                else:
                    features["price_zscore"] = 0.0
            else:
                features["price_zscore"] = 0.0
        else:
            features["price_zscore"] = 0.0

        # -------------------------------------------------------------
        # 5. Geo-Velocity & Distance Discrepancy
        # -------------------------------------------------------------
        if event.location and event.location.lat is not None and event.location.lng is not None and space_id:
            target_space = db.query(Space.latitude, Space.longitude).filter(Space.id == space_id).first()
            if target_space and target_space[0] and target_space[1]:
                dist_km = compute_haversine_distance_km(
                    event.location.lat, event.location.lng,
                    target_space[0], target_space[1]
                )
                features["geo_distance_km"] = float(round(dist_km, 1))
            else:
                features["geo_distance_km"] = 0.0
        else:
            features["geo_distance_km"] = 0.0

        # Rapid Profile Mutation Check
        features["is_sudden_profile_mutation"] = bool(payload.get("profile_mutated_recently", False))

        return features
