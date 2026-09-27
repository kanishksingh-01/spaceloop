"""
SpaceLoop Feature Extraction Layer - Account Features
Extracts account age, creation velocity, login frequency, device changes, location changes,
profile modification frequency, and shared identifier signals.
"""
from datetime import datetime, timedelta
from typing import Optional, Set
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models import User, DeviceSession, FraudEventRecord, AuditLog
from fraud_engine.schemas import FraudEventInput, FraudEventType
from fraud_engine.features.base import BaseFeatureExtractor, FeatureTrace, FeatureExtractionResult
from fraud_engine.features.similarity import is_disposable_email, compute_haversine_distance_km


class AccountFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts account-level integrity, velocity, and multi-account linkage features.
    """

    @classmethod
    def extract(cls, event: FraudEventInput, db: Session, result: FeatureExtractionResult) -> None:
        now = datetime.utcnow()
        payload = event.payload or {}
        user_id = event.user_id
        ip = event.ip_address or ""
        fp = event.device_fingerprint or ""

        # Fetch user record if user_id is provided
        user = db.query(User).filter(User.id == user_id).first() if user_id else None

        # -------------------------------------------------------------
        # 1. Account Age
        # -------------------------------------------------------------
        if user and user.created_at:
            delta = now - user.created_at
            age_hours = max(0.0, float(delta.total_seconds() / 3600.0))
            age_days = max(0.0, float(delta.total_seconds() / 86400.0))
        else:
            age_hours = 0.0
            age_days = 0.0

        result.add(FeatureTrace(
            name="account_age_hours",
            value=float(round(age_hours, 2)),
            source="db.users.created_at",
            category="account",
            description="Number of elapsed hours since the user registered on SpaceLoop."
        ))
        result.add(FeatureTrace(
            name="account_age_days",
            value=float(round(age_days, 2)),
            source="db.users.created_at",
            category="account",
            description="Number of elapsed days since user account creation."
        ))

        # -------------------------------------------------------------
        # 2. Account Creation Velocity (IP & Subnet based)
        # -------------------------------------------------------------
        if ip:
            window_1h = now - timedelta(hours=1)
            window_24h = now - timedelta(hours=24)
            ip_creations_1h = db.query(FraudEventRecord.id).filter(
                FraudEventRecord.ip_address == ip,
                FraudEventRecord.event_type == FraudEventType.ACCOUNT_CREATED.value,
                FraudEventRecord.created_at >= window_1h
            ).count()
            ip_creations_24h = db.query(FraudEventRecord.id).filter(
                FraudEventRecord.ip_address == ip,
                FraudEventRecord.event_type == FraudEventType.ACCOUNT_CREATED.value,
                FraudEventRecord.created_at >= window_24h
            ).count()
        else:
            ip_creations_1h = 0
            ip_creations_24h = 0

        # Legacy alias compatibility for RuleEngine
        result.add(FeatureTrace(
            name="ip_creation_velocity_1h",
            value=ip_creations_1h,
            source="db.fraud_events.ip_address[window=1h, type=account_created]",
            category="account",
            description="Count of account_created events originating from the same IP address in rolling 1 hour."
        ))
        result.add(FeatureTrace(
            name="account_creation_velocity_1h",
            value=ip_creations_1h,
            source="db.fraud_events.ip_address[window=1h, type=account_created]",
            category="account",
            description="Account registrations observed from the client IP address in rolling 1 hour."
        ))
        result.add(FeatureTrace(
            name="account_creation_velocity_24h",
            value=ip_creations_24h,
            source="db.fraud_events.ip_address[window=24h, type=account_created]",
            category="account",
            description="Account registrations observed from the client IP address in rolling 24 hours."
        ))

        # -------------------------------------------------------------
        # 3. Login Frequency
        # -------------------------------------------------------------
        login_1h = 0
        login_24h = 0
        login_7d = 0
        if user_id:
            window_1h = now - timedelta(hours=1)
            window_24h = now - timedelta(hours=24)
            window_7d = now - timedelta(days=7)

            login_events = db.query(FraudEventRecord.created_at).filter(
                FraudEventRecord.user_id == user_id,
                FraudEventRecord.event_type == FraudEventType.LOGIN.value,
                FraudEventRecord.created_at >= window_7d
            ).all()

            if login_events:
                login_times = [r[0] for r in login_events if r[0]]
                login_7d = len(login_times)
                login_24h = sum(1 for t in login_times if t >= window_24h)
                login_1h = sum(1 for t in login_times if t >= window_1h)
            else:
                # Fallback to device_sessions
                sessions = db.query(DeviceSession.created_at).filter(
                    DeviceSession.user_id == user_id,
                    DeviceSession.created_at >= window_7d
                ).all()
                sess_times = [s[0] for s in sessions if s[0]]
                login_7d = len(sess_times)
                login_24h = sum(1 for t in sess_times if t >= window_24h)
                login_1h = sum(1 for t in sess_times if t >= window_1h)

        result.add(FeatureTrace(
            name="login_frequency_1h",
            value=login_1h,
            source="db.fraud_events[type=login] + db.device_sessions[window=1h]",
            category="account",
            description="Number of authentication logins performed by the user in rolling 1 hour."
        ))
        result.add(FeatureTrace(
            name="login_frequency_24h",
            value=login_24h,
            source="db.fraud_events[type=login] + db.device_sessions[window=24h]",
            category="account",
            description="Number of authentication logins performed by the user in rolling 24 hours."
        ))
        result.add(FeatureTrace(
            name="login_frequency_7d",
            value=login_7d,
            source="db.fraud_events[type=login] + db.device_sessions[window=7d]",
            category="account",
            description="Number of authentication logins performed by the user in rolling 7 days."
        ))

        # -------------------------------------------------------------
        # 4. Device Changes & Fingerprint Diversity
        # -------------------------------------------------------------
        distinct_devices = 1
        is_new_device = False
        if user_id:
            window_30d = now - timedelta(days=30)
            user_fps = db.query(DeviceSession.device_fingerprint).filter(
                DeviceSession.user_id == user_id,
                DeviceSession.last_seen_at >= window_30d
            ).distinct().all()
            fp_set = {f[0] for f in user_fps if f[0]}
            if fp:
                is_new_device = fp not in fp_set
                fp_set.add(fp)
            distinct_devices = max(1, len(fp_set))

        result.add(FeatureTrace(
            name="device_changes_count_30d",
            value=distinct_devices,
            source="db.device_sessions.device_fingerprint[user_id, window=30d]",
            category="account",
            description="Total distinct hardware device fingerprints utilized by this user within 30 days."
        ))
        result.add(FeatureTrace(
            name="is_new_device",
            value=is_new_device,
            source="db.device_sessions.device_fingerprint",
            category="account",
            description="Boolean flag indicating whether the event fingerprint has never been seen for this user."
        ))

        # -------------------------------------------------------------
        # 5. Location Changes & Geo-Velocity (Impossible Travel)
        # -------------------------------------------------------------
        distinct_locations = 1
        geo_velocity_kmh = 0.0
        if user_id:
            window_30d = now - timedelta(days=30)
            recent_locs = db.query(
                FraudEventRecord.ip_address,
                FraudEventRecord.created_at
            ).filter(
                FraudEventRecord.user_id == user_id,
                FraudEventRecord.created_at >= window_30d
            ).all()
            loc_ips = {r[0] for r in recent_locs if r[0]}
            if ip:
                loc_ips.add(ip)
            distinct_locations = max(1, len(loc_ips))

            # Consecutive event geo-velocity check if coordinates available
            if event.location and event.location.lat is not None and event.location.lng is not None:
                last_loc_event = db.query(
                    FraudEventRecord.payload_json,
                    FraudEventRecord.created_at
                ).filter(
                    FraudEventRecord.user_id == user_id,
                    FraudEventRecord.created_at >= now - timedelta(hours=24)
                ).order_by(FraudEventRecord.created_at.desc()).first()

                if last_loc_event and last_loc_event[0] and isinstance(last_loc_event[0], dict):
                    prev_loc = last_loc_event[0].get("location") or {}
                    prev_lat = prev_loc.get("lat")
                    prev_lng = prev_loc.get("lng")
                    if prev_lat is not None and prev_lng is not None:
                        dist_km = compute_haversine_distance_km(
                            event.location.lat, event.location.lng,
                            float(prev_lat), float(prev_lng)
                        )
                        hours_diff = max(0.01, (now - last_loc_event[1]).total_seconds() / 3600.0)
                        geo_velocity_kmh = float(round(dist_km / hours_diff, 1))

        result.add(FeatureTrace(
            name="location_changes_count_30d",
            value=distinct_locations,
            source="db.fraud_events.ip_address[user_id, window=30d]",
            category="account",
            description="Number of distinct IP/geographic regions accessed by user in rolling 30 days."
        ))
        result.add(FeatureTrace(
            name="impossible_geo_velocity_kmh",
            value=geo_velocity_kmh,
            source="db.fraud_events.location[haversine / delta_hours]",
            category="account",
            description="Physical travel speed (km/h) required to traverse consecutive events."
        ))

        # -------------------------------------------------------------
        # 6. Profile Modification Frequency
        # -------------------------------------------------------------
        profile_mutations_24h = 0
        profile_mutations_7d = 0
        if user_id:
            window_24h = now - timedelta(hours=24)
            window_7d = now - timedelta(days=7)
            profile_events = db.query(FraudEventRecord.created_at).filter(
                FraudEventRecord.user_id == user_id,
                FraudEventRecord.event_type == FraudEventType.PROFILE_UPDATED.value,
                FraudEventRecord.created_at >= window_7d
            ).all()
            profile_mutations_7d = len(profile_events)
            profile_mutations_24h = sum(1 for p in profile_events if p[0] and p[0] >= window_24h)

        is_sudden_mutation = bool(payload.get("profile_mutated_recently", False))

        result.add(FeatureTrace(
            name="profile_modification_count_24h",
            value=profile_mutations_24h,
            source="db.fraud_events[type=profile_updated, window=24h]",
            category="account",
            description="Count of profile modification events within the last 24 hours."
        ))
        result.add(FeatureTrace(
            name="profile_modification_count_7d",
            value=profile_mutations_7d,
            source="db.fraud_events[type=profile_updated, window=7d]",
            category="account",
            description="Count of profile modification events within the last 7 days."
        ))
        result.add(FeatureTrace(
            name="is_sudden_profile_mutation",
            value=is_sudden_mutation,
            source="db.fraud_events[profile_updated] + event.payload.profile_mutated_recently",
            category="account",
            description="Flag indicating recent rapid alteration of critical user profile attributes."
        ))

        # -------------------------------------------------------------
        # 7. Number of Accounts Sharing Identifiers
        # -------------------------------------------------------------
        accounts_sharing_device = 1
        if fp:
            dev_sessions = db.query(DeviceSession.user_id).filter(
                DeviceSession.device_fingerprint == fp
            ).distinct().all()
            sharing_uids = {s[0] for s in dev_sessions if s[0] is not None}
            if user_id:
                sharing_uids.add(user_id)
            accounts_sharing_device = max(1, len(sharing_uids))

        accounts_sharing_phone = 1
        accounts_sharing_aadhaar = 1
        accounts_sharing_upi = 1
        if user:
            if user.phone:
                p_count = db.query(User.id).filter(User.phone == user.phone).count()
                accounts_sharing_phone = max(1, p_count)
            if user.aadhaar_token_hash:
                a_count = db.query(User.id).filter(User.aadhaar_token_hash == user.aadhaar_token_hash).count()
                accounts_sharing_aadhaar = max(1, a_count)
            if user.upi_vpa_masked:
                u_count = db.query(User.id).filter(User.upi_vpa_masked == user.upi_vpa_masked).count()
                accounts_sharing_upi = max(1, u_count)

        accounts_sharing_ip = 1
        if ip:
            window_24h = now - timedelta(hours=24)
            ip_users = db.query(FraudEventRecord.user_id).filter(
                FraudEventRecord.ip_address == ip,
                FraudEventRecord.created_at >= window_24h,
                FraudEventRecord.user_id != None
            ).distinct().all()
            ip_uids = {u[0] for u in ip_users if u[0]}
            if user_id:
                ip_uids.add(user_id)
            accounts_sharing_ip = max(1, len(ip_uids))

        # Legacy alias for RuleEngine compatibility
        result.add(FeatureTrace(
            name="device_user_overlap_count",
            value=accounts_sharing_device,
            source="db.device_sessions.device_fingerprint[distinct_users]",
            category="account",
            description="Number of distinct user accounts associated with this hardware device fingerprint."
        ))
        result.add(FeatureTrace(
            name="accounts_sharing_device_count",
            value=accounts_sharing_device,
            source="db.device_sessions.device_fingerprint[distinct_users]",
            category="account",
            description="Total distinct accounts bound to this device fingerprint."
        ))
        result.add(FeatureTrace(
            name="accounts_sharing_phone_count",
            value=accounts_sharing_phone,
            source="db.users.phone",
            category="account",
            description="Total accounts sharing the same telephone contact identifier."
        ))
        result.add(FeatureTrace(
            name="accounts_sharing_aadhaar_count",
            value=accounts_sharing_aadhaar,
            source="db.users.aadhaar_token_hash",
            category="account",
            description="Total accounts sharing the same DigiLocker Aadhaar token hash."
        ))
        result.add(FeatureTrace(
            name="accounts_sharing_upi_count",
            value=accounts_sharing_upi,
            source="db.users.upi_vpa_masked",
            category="account",
            description="Total accounts sharing the same UPI VPA payment destination."
        ))
        result.add(FeatureTrace(
            name="accounts_sharing_ip_count",
            value=accounts_sharing_ip,
            source="db.fraud_events.ip_address[window=24h, distinct_users]",
            category="account",
            description="Distinct accounts transacting from the same IP within 24 hours."
        ))

        # -------------------------------------------------------------
        # 8. Email & Identity Verification State
        # -------------------------------------------------------------
        email = str(payload.get("email") or (user.email if user else "")).strip().lower()
        is_disp = is_disposable_email(email)
        domain = email.split("@")[-1] if "@" in email else ""

        result.add(FeatureTrace(
            name="email_is_disposable",
            value=is_disp,
            source="payload.email or db.users.email",
            category="account",
            description="Boolean flag indicating if the email domain matches disposable/burner domains."
        ))
        result.add(FeatureTrace(
            name="email_domain",
            value=domain,
            source="payload.email or db.users.email",
            category="account",
            description="Domain part of the user's primary email address."
        ))
        result.add(FeatureTrace(
            name="is_host_verified",
            value=bool(user.is_host_verified) if user else False,
            source="db.users.is_host_verified",
            category="account",
            description="Host verification KYC status (BESCOM electricity CA & penny drop)."
        ))
        result.add(FeatureTrace(
            name="is_aadhaar_verified",
            value=bool(user.is_aadhaar_verified) if user else False,
            source="db.users.is_aadhaar_verified",
            category="account",
            description="User Aadhaar DigiLocker verification status."
        ))
        result.add(FeatureTrace(
            name="is_student_verified",
            value=bool(user.is_student_verified) if user else False,
            source="db.users.is_student_verified",
            category="account",
            description="User college campus student accreditation status."
        ))
        result.add(FeatureTrace(
            name="user_trust_score",
            value=float(user.objective_trust_score or 98.5) if user else 98.5,
            source="db.users.objective_trust_score",
            category="account",
            description="SpaceLoop Objective Telemetry Index (OTI) baseline score."
        ))
