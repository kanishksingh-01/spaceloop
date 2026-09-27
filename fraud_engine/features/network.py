"""
SpaceLoop Feature Extraction Layer - Network & Graph Features
Extracts shared device networks, shared identifiers, shared payment identities,
connected accounts, graph degrees, and suspicious cluster signals.
"""
from datetime import datetime, timedelta
from typing import Optional, Set, Dict, List
from sqlalchemy.orm import Session

from models import User, Space, Booking, DeviceSession, FraudEventRecord, FraudAlertRecord
from fraud_engine.schemas import FraudEventInput
from fraud_engine.features.base import BaseFeatureExtractor, FeatureTrace, FeatureExtractionResult


class NetworkFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts multi-entity relationship graph signals, identity clusters, and collusion topologies.
    """

    @classmethod
    def extract(cls, event: FraudEventInput, db: Session, result: FeatureExtractionResult) -> None:
        now = datetime.utcnow()
        user_id = event.user_id
        fp = event.device_fingerprint or ""

        user = db.query(User).filter(User.id == user_id).first() if user_id else None

        connected_accounts: Set[int] = set()
        shared_device_accounts: Set[int] = set()
        shared_payment_accounts: Set[int] = set()
        shared_identity_count = 0

        # -------------------------------------------------------------
        # 1. Shared Devices Degree
        # -------------------------------------------------------------
        user_fps: Set[str] = set()
        if user_id:
            db_fps = db.query(DeviceSession.device_fingerprint).filter(
                DeviceSession.user_id == user_id
            ).distinct().all()
            user_fps = {f[0] for f in db_fps if f[0]}
        if fp:
            user_fps.add(fp)

        if user_fps:
            overlap_sessions = db.query(DeviceSession.user_id).filter(
                DeviceSession.device_fingerprint.in_(list(user_fps))
            ).distinct().all()
            for s in overlap_sessions:
                if s[0] and s[0] != user_id:
                    shared_device_accounts.add(s[0])
                    connected_accounts.add(s[0])

        shared_device_degree = len(shared_device_accounts)

        result.add(FeatureTrace(
            name="network_shared_device_degree",
            value=shared_device_degree,
            source="db.device_sessions.device_fingerprint[cross-account]",
            category="network",
            description="Count of distinct other accounts sharing hardware device fingerprints."
        ))

        # -------------------------------------------------------------
        # 2. Shared Identifiers (Phone, Aadhaar, Email)
        # -------------------------------------------------------------
        shared_phone_degree = 0
        shared_aadhaar_degree = 0

        if user:
            if user.phone:
                p_users = db.query(User.id).filter(User.phone == user.phone, User.id != user_id).all()
                shared_phone_degree = len(p_users)
                for u in p_users:
                    connected_accounts.add(u[0])
                if shared_phone_degree > 0:
                    shared_identity_count += shared_phone_degree

            if user.aadhaar_token_hash:
                a_users = db.query(User.id).filter(User.aadhaar_token_hash == user.aadhaar_token_hash, User.id != user_id).all()
                shared_aadhaar_degree = len(a_users)
                for u in a_users:
                    connected_accounts.add(u[0])
                if shared_aadhaar_degree > 0:
                    shared_identity_count += shared_aadhaar_degree

        result.add(FeatureTrace(
            name="network_shared_phone_degree",
            value=shared_phone_degree,
            source="db.users.phone[cross-account]",
            category="network",
            description="Other user accounts bound to the exact same telephone number."
        ))
        result.add(FeatureTrace(
            name="network_shared_aadhaar_degree",
            value=shared_aadhaar_degree,
            source="db.users.aadhaar_token_hash[cross-account]",
            category="network",
            description="Other user accounts sharing the exact same Aadhaar identity token."
        ))
        result.add(FeatureTrace(
            name="network_shared_identifiers_count",
            value=shared_identity_count + shared_device_degree,
            source="sum(shared_phone + shared_aadhaar + shared_device)",
            category="network",
            description="Cumulative multi-account identity collision count across phone, Aadhaar, and device."
        ))

        # -------------------------------------------------------------
        # 3. Shared Payment Identities (UPI VPA & Bank Beneficiary)
        # -------------------------------------------------------------
        shared_upi_degree = 0
        if user and user.upi_vpa_masked:
            upi_users = db.query(User.id).filter(
                User.upi_vpa_masked == user.upi_vpa_masked,
                User.id != user_id
            ).all()
            shared_upi_degree = len(upi_users)
            for u in upi_users:
                shared_payment_accounts.add(u[0])
                connected_accounts.add(u[0])

        result.add(FeatureTrace(
            name="network_shared_payment_degree",
            value=shared_upi_degree,
            source="db.users.upi_vpa_masked[cross-account]",
            category="network",
            description="Count of other accounts sharing identical UPI payment destination credentials."
        ))

        # -------------------------------------------------------------
        # 4. Shared Listings & Mutual / Cyclical Bookings
        # -------------------------------------------------------------
        mutual_booking_count = 0
        if user_id:
            # Check if user has bookings on spaces where the host also booked this user's spaces
            user_space_ids = [s[0] for s in db.query(Space.id).filter(Space.owner_id == user_id).all()]
            if user_space_ids:
                # Find users who booked our spaces
                inbound_renters = {
                    b[0] for b in db.query(Booking.renter_id).filter(
                        Booking.space_id.in_(user_space_ids),
                        Booking.renter_id != user_id
                    ).distinct().all()
                }
                # Check if we also booked any spaces owned by those inbound renters
                if inbound_renters:
                    outbound_spaces = db.query(Booking.space_id).filter(
                        Booking.renter_id == user_id
                    ).distinct().all()
                    outbound_space_ids = [s[0] for s in outbound_spaces]
                    if outbound_space_ids:
                        reciprocal_hosts = db.query(Space.owner_id).filter(
                            Space.id.in_(outbound_space_ids),
                            Space.owner_id.in_(list(inbound_renters))
                        ).all()
                        mutual_booking_count = len(reciprocal_hosts)

        result.add(FeatureTrace(
            name="network_shared_space_degree",
            value=mutual_booking_count,
            source="db.bookings[reciprocal booking loops between host and seeker]",
            category="network",
            description="Count of reciprocal wash-booking collusion loops between user and counterparty."
        ))

        # -------------------------------------------------------------
        # 5. Connected Accounts & Graph Degrees
        # -------------------------------------------------------------
        graph_in_degree = 0
        graph_out_degree = 0

        if user_id:
            # In-degree: unique users who transacted on user's spaces
            owned_spaces = [s[0] for s in db.query(Space.id).filter(Space.owner_id == user_id).all()]
            if owned_spaces:
                in_renters = db.query(Booking.renter_id).filter(
                    Booking.space_id.in_(owned_spaces),
                    Booking.renter_id != user_id
                ).distinct().all()
                graph_in_degree = len(in_renters)
                for r in in_renters:
                    connected_accounts.add(r[0])

            # Out-degree: unique hosts user has transacted with
            user_bookings = db.query(Booking.space_id).filter(
                Booking.renter_id == user_id
            ).distinct().all()
            booked_spaces = [b[0] for b in user_bookings]
            if booked_spaces:
                out_hosts = db.query(Space.owner_id).filter(
                    Space.id.in_(booked_spaces),
                    Space.owner_id != user_id
                ).distinct().all()
                graph_out_degree = len(out_hosts)
                for h in out_hosts:
                    connected_accounts.add(h[0])

        graph_total_degree = graph_in_degree + graph_out_degree + len(shared_device_accounts)

        result.add(FeatureTrace(
            name="graph_in_degree",
            value=graph_in_degree,
            source="db.bookings.renter_id[spaces owned by user]",
            category="network",
            description="Number of unique counterparties transacting into user's listings."
        ))
        result.add(FeatureTrace(
            name="graph_out_degree",
            value=graph_out_degree,
            source="db.spaces.owner_id[spaces booked by user]",
            category="network",
            description="Number of unique host counterparties user has booked with."
        ))
        result.add(FeatureTrace(
            name="graph_total_degree",
            value=graph_total_degree,
            source="graph_in_degree + graph_out_degree + shared_device_degree",
            category="network",
            description="Combined relational degree centrality of this entity."
        ))
        result.add(FeatureTrace(
            name="network_connected_accounts_count",
            value=len(connected_accounts),
            source="distinct(connected_accounts via identity, device, and transactions)",
            category="network",
            description="First-degree adjacent accounts linked in the SpaceLoop transaction graph."
        ))

        # -------------------------------------------------------------
        # 6. Suspicious Clusters & Sybil Density
        # -------------------------------------------------------------
        cluster_size = 1 + len(connected_accounts)
        alert_count_in_cluster = 0

        if connected_accounts:
            alert_count_in_cluster = db.query(FraudAlertRecord.id).filter(
                FraudAlertRecord.user_id.in_(list(connected_accounts))
            ).count()

        risk_density = float(round(alert_count_in_cluster / max(1, len(connected_accounts)), 2))
        is_sybil = bool(len(shared_device_accounts) >= 2 or (shared_upi_degree >= 1 and len(shared_device_accounts) >= 1))

        result.add(FeatureTrace(
            name="network_cluster_size",
            value=cluster_size,
            source="1 + len(connected_accounts)",
            category="network",
            description="Size of connected entity sub-graph cluster."
        ))
        result.add(FeatureTrace(
            name="network_cluster_risk_density",
            value=risk_density,
            source="fraud_alerts in cluster / cluster_size",
            category="network",
            description="Proportion of accounts in the cluster with prior active fraud alerts."
        ))
        result.add(FeatureTrace(
            name="is_in_sybil_cluster",
            value=is_sybil,
            source="shared_device_degree >= 2 or (shared_payment and shared_device)",
            category="network",
            description="Flag identifying high-density multi-account Sybil cluster collusion."
        ))
