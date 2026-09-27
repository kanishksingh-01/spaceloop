"""
SpaceLoop Feature Extraction Layer - Listing Features
Extracts listing creation velocity, text/photo duplicate signals, description similarity,
suspicious pricing, conflicting listing info, and host/listing relationship signals.
"""
from datetime import datetime, timedelta
import hashlib
from typing import Optional, List, Tuple
import numpy as np
from sqlalchemy.orm import Session

from models import Space, User, FraudEventRecord
from fraud_engine.schemas import FraudEventInput, FraudEventType
from fraud_engine.features.base import BaseFeatureExtractor, FeatureTrace, FeatureExtractionResult
from fraud_engine.features.similarity import (
    calculate_jaccard_similarity,
    calculate_ngram_similarity,
    calculate_modified_zscore,
    compute_haversine_distance_km,
    check_conflicting_city_coordinates
)


class ListingFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts catalog integrity, duplicate detection, content similarity, and listing anomaly features.
    """

    @classmethod
    def extract(cls, event: FraudEventInput, db: Session, result: FeatureExtractionResult) -> None:
        now = datetime.utcnow()
        payload = event.payload or {}
        user_id = event.user_id

        # Target space identification
        space_id = payload.get("space_id") or (event.entity_id if event.entity_type in ("space", "listing") else None)
        space = db.query(Space).filter(Space.id == space_id).first() if space_id else None

        title = str(payload.get("title") or (space.title if space else "")).strip()
        description = str(payload.get("description") or (space.description if space else "")).strip()
        address = str(payload.get("address") or (space.address if space else "")).strip().lower()
        city = str(payload.get("city") or (space.city if space else "New Delhi")).strip()
        state = str(payload.get("state") or (space.state if space else "Delhi")).strip()
        category = str(payload.get("category") or (space.category if space else "Storage")).strip()

        price_hourly = float(payload.get("price_hourly") or (space.price_hourly if space else 0.0))
        price_daily = float(payload.get("price_daily") or (space.price_daily if space else 0.0))
        sqft = int(payload.get("sqft") or (space.sqft if space else 200))
        max_capacity = int(payload.get("max_capacity") or (space.max_capacity if space else 4))
        discom_ca = str(payload.get("discom_ca_number") or (space.discom_ca_number if space else "")).strip()
        room_qr = str(payload.get("room_qr_token") or (space.room_qr_token if space else "")).strip()
        owner_id = int(payload.get("owner_id") or (space.owner_id if space else (user_id or 0)))

        lat = float(payload.get("latitude") or (space.latitude if space and space.latitude else 0.0))
        lng = float(payload.get("longitude") or (space.longitude if space and space.longitude else 0.0))

        # -------------------------------------------------------------
        # 1. Listing Creation Velocity
        # -------------------------------------------------------------
        host_listings_1h = 0
        host_listings_24h = 0
        host_listings_7d = 0
        active_listings_count = 0

        if owner_id:
            window_1h = now - timedelta(hours=1)
            window_24h = now - timedelta(hours=24)
            window_7d = now - timedelta(days=7)

            host_spaces = db.query(Space.created_at, Space.is_active).filter(
                Space.owner_id == owner_id
            ).all()

            active_listings_count = sum(1 for s in host_spaces if s[1])
            created_times = [s[0] for s in host_spaces if s[0]]
            host_listings_7d = sum(1 for t in created_times if t >= window_7d)
            host_listings_24h = sum(1 for t in created_times if t >= window_24h)
            host_listings_1h = sum(1 for t in created_times if t >= window_1h)

        if event.event_type == FraudEventType.LISTING_CREATED:
            host_listings_1h += 1
            host_listings_24h += 1
            host_listings_7d += 1
            active_listings_count += 1

        result.add(FeatureTrace(
            name="listing_creation_velocity_1h",
            value=host_listings_1h,
            source="db.spaces[owner_id, window=1h]",
            category="listing",
            description="Count of spaces published by host in rolling 1 hour."
        ))
        result.add(FeatureTrace(
            name="listing_creation_velocity_24h",
            value=host_listings_24h,
            source="db.spaces[owner_id, window=24h]",
            category="listing",
            description="Count of spaces published by host in rolling 24 hours."
        ))
        result.add(FeatureTrace(
            name="active_listings_count",
            value=active_listings_count,
            source="db.spaces[owner_id, is_active=True]",
            category="listing",
            description="Total active spaces published by this host on SpaceLoop."
        ))

        # -------------------------------------------------------------
        # 2. Duplicate / Similar Content Signals & Repeated Listings
        # -------------------------------------------------------------
        dup_title_count = 0
        dup_address_count = 0
        max_desc_jaccard = 0.0
        max_desc_ngram = 0.0

        all_spaces_query = db.query(
            Space.id, Space.title, Space.description, Space.address
        ).filter(Space.is_active == True)
        if space_id:
            all_spaces_query = all_spaces_query.filter(Space.id != space_id)

        candidate_spaces = all_spaces_query.all()

        norm_title = title.lower()
        norm_addr = address.lower()

        for c_id, c_title, c_desc, c_addr in candidate_spaces:
            if c_title and c_title.strip().lower() == norm_title and norm_title != "":
                dup_title_count += 1
            if c_addr and c_addr.strip().lower() == norm_addr and norm_addr != "":
                dup_address_count += 1
            if description and c_desc:
                j_sim = calculate_jaccard_similarity(description, c_desc)
                if j_sim > max_desc_jaccard:
                    max_desc_jaccard = j_sim
                if j_sim > 0.4:
                    ng_sim = calculate_ngram_similarity(description, c_desc)
                    if ng_sim > max_desc_ngram:
                        max_desc_ngram = ng_sim

        result.add(FeatureTrace(
            name="duplicate_title_count",
            value=dup_title_count,
            source="db.spaces.title[exact_match]",
            category="listing",
            description="Number of other active spaces sharing the exact normalized title."
        ))
        result.add(FeatureTrace(
            name="duplicate_address_count",
            value=dup_address_count,
            source="db.spaces.address[exact_match]",
            category="listing",
            description="Number of other spaces claiming the exact physical premise address."
        ))
        result.add(FeatureTrace(
            name="max_description_jaccard_similarity",
            value=float(round(max_desc_jaccard, 3)),
            source="NLP word-level Jaccard set overlap across catalog",
            category="listing",
            description="Maximum word-level text similarity between this description and other listings."
        ))
        result.add(FeatureTrace(
            name="max_description_ngram_similarity",
            value=float(round(max_desc_ngram, 3)),
            source="NLP character 3-gram Dice overlap across catalog",
            category="listing",
            description="Maximum character n-gram text similarity against existing space descriptions."
        ))

        # -------------------------------------------------------------
        # 3. Repeated Hardware / Token Access Identifiers
        # -------------------------------------------------------------
        repeated_qr = False
        repeated_ca = False
        if room_qr:
            qr_match = db.query(Space.id).filter(Space.room_qr_token == room_qr)
            if space_id:
                qr_match = qr_match.filter(Space.id != space_id)
            repeated_qr = qr_match.first() is not None

        if discom_ca:
            ca_match = db.query(Space.id).filter(Space.discom_ca_number == discom_ca)
            if space_id:
                ca_match = ca_match.filter(Space.id != space_id)
            repeated_ca = ca_match.first() is not None

        result.add(FeatureTrace(
            name="repeated_room_qr_token",
            value=repeated_qr,
            source="db.spaces.room_qr_token[uniqueness]",
            category="listing",
            description="Boolean flag indicating whether the printable door QR token is duplicated."
        ))
        result.add(FeatureTrace(
            name="repeated_discom_ca",
            value=repeated_ca,
            source="db.spaces.discom_ca_number[uniqueness]",
            category="listing",
            description="Boolean flag indicating whether the Discom utility CA number is claimed elsewhere."
        ))

        # -------------------------------------------------------------
        # 4. Suspicious Pricing & Category Deviation
        # -------------------------------------------------------------
        category_prices = [
            s[0] for s in db.query(Space.price_hourly).filter(
                Space.category == category,
                Space.is_active == True,
                Space.price_hourly > 0
            ).all()
        ]
        if not category_prices:
            category_prices = [s[0] for s in db.query(Space.price_hourly).filter(Space.is_active == True, Space.price_hourly > 0).all()]

        cat_zscore = calculate_modified_zscore(price_hourly, category_prices)
        med_price = float(np.median(category_prices)) if category_prices else 25.0

        is_extreme_low = (price_hourly > 0 and price_hourly < 5.0) or (price_hourly > 0 and price_hourly < 0.15 * med_price)
        is_extreme_high = (price_hourly > 5000.0) or (price_hourly > 10.0 * med_price)

        result.add(FeatureTrace(
            name="price_hourly",
            value=float(round(price_hourly, 2)),
            source="db.spaces.price_hourly or payload",
            category="listing",
            description="Published hourly rate for the space in INR."
        ))
        result.add(FeatureTrace(
            name="price_zscore_vs_category",
            value=cat_zscore,
            source="NumPy modified Z-score vs active category spaces",
            category="listing",
            description="Statistical modified Z-score of space hourly price against category peers."
        ))
        result.add(FeatureTrace(
            name="is_extreme_price_low",
            value=is_extreme_low,
            source="price_hourly < 5.0 or price_hourly < 0.15 * median",
            category="listing",
            description="Flag identifying suspiciously below-market or probing pricing."
        ))
        result.add(FeatureTrace(
            name="is_extreme_price_high",
            value=is_extreme_high,
            source="price_hourly > 5000.0 or price_hourly > 10.0 * median",
            category="listing",
            description="Flag identifying astronomical rates indicative of money laundering or testing."
        ))

        # -------------------------------------------------------------
        # 5. Conflicting Listing Information
        # -------------------------------------------------------------
        has_geo_mismatch, geo_mismatch_km = check_conflicting_city_coordinates(city, lat, lng)
        impossible_sqft = bool((sqft < 25 and max_capacity > 10) or (max_capacity <= 0) or (sqft <= 0))

        result.add(FeatureTrace(
            name="conflicting_geo_city",
            value=has_geo_mismatch,
            source="Haversine distance between coordinates and canonical city centroid",
            category="listing",
            description="Flag indicating geolocation coordinates contradict the claimed city by > 80km."
        ))
        result.add(FeatureTrace(
            name="geo_city_discrepancy_km",
            value=geo_mismatch_km,
            source="Haversine distance between coordinates and claimed city centroid",
            category="listing",
            description="Geographic discrepancy distance in kilometers between claimed city and GPS."
        ))
        result.add(FeatureTrace(
            name="impossible_sqft_capacity_ratio",
            value=impossible_sqft,
            source="spaces.sqft vs spaces.max_capacity",
            category="listing",
            description="Flag identifying physical impossibilities in area and occupancy specs."
        ))

        # -------------------------------------------------------------
        # 6. Host / Listing Relationship Signals
        # -------------------------------------------------------------
        host = db.query(User).filter(User.id == owner_id).first() if owner_id else None
        host_age_days = 0.0
        is_host_ver = False
        is_aadhaar_ver = False

        if host:
            if host.created_at:
                host_age_days = max(0.0, float((now - host.created_at).total_seconds() / 86400.0))
            is_host_ver = bool(host.is_host_verified)
            is_aadhaar_ver = bool(host.is_aadhaar_verified)

        unverified_high_val = (not is_host_ver and not is_aadhaar_ver) and (price_hourly >= 200.0 or price_daily >= 1500.0)

        result.add(FeatureTrace(
            name="host_account_age_days_at_listing",
            value=float(round(host_age_days, 1)),
            source="db.users.created_at[owner_id]",
            category="listing",
            description="Elapsed days since host registered when creating/updating listing."
        ))
        result.add(FeatureTrace(
            name="unverified_high_value_listing",
            value=unverified_high_val,
            source="not is_host_verified and price_hourly >= 200",
            category="listing",
            description="Flag when unverified host creates listing with elevated commercial tariff."
        ))

        # Legacy aliases for RuleEngine
        is_self_tx = bool(owner_id and user_id and owner_id == user_id and event.event_type in (
            FraudEventType.BOOKING_CREATED, FraudEventType.PAYMENT_COMPLETED, FraudEventType.REFUND_REQUESTED
        ))
        result.add(FeatureTrace(
            name="is_self_transaction",
            value=is_self_tx,
            source="event.user_id == space.owner_id",
            category="listing",
            description="Collusive self-transaction where renter and premise host are identical."
        ))
        result.add(FeatureTrace(
            name="space_id",
            value=space_id,
            source="payload.space_id or event.entity_id",
            category="listing",
            description="SpaceLoop space identifier."
        ))

        # Geo-distance between client event and space location
        geo_dist_km = 0.0
        if event.location and event.location.lat is not None and event.location.lng is not None and lat and lng:
            geo_dist_km = compute_haversine_distance_km(event.location.lat, event.location.lng, lat, lng)

        result.add(FeatureTrace(
            name="geo_distance_km",
            value=float(round(geo_dist_km, 1)),
            source="compute_haversine_distance_km(event.location, space.coords)",
            category="listing",
            description="Physical distance in kilometers between event coordinates and space premise."
        ))
