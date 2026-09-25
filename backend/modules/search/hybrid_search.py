"""
SpaceLoop Lightweight Hybrid Search Engine
Combines:
1. Query Understanding (structured constraints + semantic query)
2. Deterministic Hard Filtering (Capacity, Budget, Category, Location Proximity)
3. Real-Time Booking Availability (from actual Booking database records)
4. Semantic Vector Similarity Search (Cosine similarity over dense embeddings)
5. Keyword Relevance Match (Token overlap)
6. Composite Ranking & Result Formulation
7. Seamless Fallback to Keyword/Filter search on provider failure
"""
import re
from datetime import datetime, timedelta, timezone
from models import db, Space, Booking
from backend.core.geo import haversine_distance, resolve_location_coordinates
from backend.modules.search.embedding import generate_embedding, cosine_similarity, build_searchable_representation
from backend.modules.search.query_understanding import understand_search_query
from backend.app.api.v1.bookings import check_booking_overlap


def _resolve_query_time_window(date_str: str | None, time_range_str: str | None, duration_hours: float | None) -> tuple[datetime | None, datetime | None]:
    """
    Deterministically computes start and end datetime from extracted date, time_range, and hours.
    Returns (start_time, end_time) in UTC, or (None, None) if not specified.
    """
    if not date_str and not time_range_str:
        return None, None

    now = datetime.utcnow()
    target_date = now.date()

    if date_str:
        d_clean = date_str.lower().strip()
        if "tomorrow" in d_clean:
            target_date = (now + timedelta(days=1)).date()
        elif "today" in d_clean:
            target_date = now.date()
        elif "weekend" in d_clean:
            # Days until next Saturday (weekday 5)
            days_until_sat = (5 - now.weekday()) % 7
            if days_until_sat == 0 and now.hour > 18:
                days_until_sat = 7
            target_date = (now + timedelta(days=days_until_sat)).date()
        else:
            try:
                # Try parsing ISO or YYYY-MM-DD
                parsed_d = datetime.fromisoformat(d_clean).date()
                target_date = parsed_d
            except Exception:
                pass

    # Determine hour of day
    start_hour = 14  # Default 2:00 PM if time range not specified
    if time_range_str:
        tr = time_range_str.lower().strip()
        if "morning" in tr:
            start_hour = 9
        elif "afternoon" in tr:
            start_hour = 14
        elif "evening" in tr:
            start_hour = 17
        elif "night" in tr:
            start_hour = 20

    start_dt = datetime(target_date.year, target_date.month, target_date.day, start_hour, 0, 0)
    dur = float(duration_hours) if duration_hours and 0.5 <= duration_hours <= 24.0 else 2.0
    end_dt = start_dt + timedelta(hours=dur)

    return start_dt, end_dt


def _compute_keyword_relevance(query_text: str, space: Space) -> float:
    """
    Calculates keyword overlap relevance score between query tokens and listing attributes.
    Returns a normalized float in range [0.0, 1.0].
    """
    if not query_text:
        return 0.5

    clean_q = query_text.lower()
    tokens = [t for t in re.findall(r'\b[a-zA-Z0-9]{3,}\b', clean_q) if t not in ("for", "and", "the", "with", "near", "place", "need")]
    if not tokens:
        return 0.5

    space_text = f"{space.title} {space.category} {space.neighborhood} {space.city} {space.description} {' '.join(space.amenities)} {' '.join(space.ai_tags)} {space.ai_recommended_uses}".lower()

    matches = 0
    title_matches = 0
    for token in tokens:
        if token in space.title.lower():
            title_matches += 1
            matches += 1
        elif token in space_text:
            matches += 1

    ratio = matches / len(tokens)
    if title_matches > 0:
        ratio = min(1.0, ratio + 0.2)
    return round(ratio, 4)


def _compute_completeness_score(space: Space) -> float:
    """Computes a quality score based on photos, host verification, premise verification, and ratings."""
    score = 0.5
    if space.photos and len(space.photos) > 0:
        score += 0.15
    if space.owner and space.owner.is_host_verified:
        score += 0.15
    if space.discom_ca_number:
        score += 0.10
    if space.average_rating() >= 4.7:
        score += 0.10
    return min(1.0, score)


def hybrid_search_spaces(
    raw_query: str = "",
    location: str | None = None,
    category: str | None = None,
    min_capacity: int | None = None,
    max_price: float | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
    date: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    amenities: list[str] | None = None,
    current_user_id: int | None = None,
    limit: int = 30,
    candidate_spaces: list | None = None
) -> dict:
    """
    Executes hybrid semantic search:
    1. Extracts structured constraints from natural language query.
    2. Merges query constraints with explicit user filter parameters (explicit overrides query).
    3. Deterministically applies hard filters (Capacity, Price, Category, Radius, Booking Availability).
    4. Generates query vector embedding and computes cosine similarity with listing embeddings.
    5. Calculates keyword relevance and composite ranking.
    6. Formats explainable search results with real availability.
    """
    # Step 1: Query understanding
    parsed_query = understand_search_query(raw_query) if raw_query else {}
    semantic_query = parsed_query.get("semantic_query") or raw_query

    # Step 2: Merge explicit overrides with extracted constraints
    effective_loc = location or parsed_query.get("location")
    effective_cat = category if (category and category.lower() not in ("all", "any")) else parsed_query.get("space_type")
    effective_cap = min_capacity or parsed_query.get("capacity")
    effective_max_price = max_price or parsed_query.get("max_price")
    effective_amenities = amenities or parsed_query.get("amenities") or []

    # Resolve date/time for real availability check
    req_start = None
    req_end = None
    if start_time and end_time:
        try:
            st_str = str(start_time).strip()
            et_str = str(end_time).strip()
            if "T" not in st_str and date:
                if len(st_str) == 5:
                    st_str = f"{st_str}:00"
                st_str = f"{date}T{st_str}"
            if "T" not in et_str and date:
                if len(et_str) == 5:
                    et_str = f"{et_str}:00"
                et_str = f"{date}T{et_str}"

            req_start = datetime.fromisoformat(st_str.replace("Z", "+00:00"))
            req_end = datetime.fromisoformat(et_str.replace("Z", "+00:00"))
            if req_start.tzinfo:
                req_start = req_start.astimezone(timezone.utc).replace(tzinfo=None)
            if req_end.tzinfo:
                req_end = req_end.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            req_start, req_end = None, None

    if not req_start or not req_end:
        extracted_date = date or parsed_query.get("date")
        extracted_trange = parsed_query.get("time_range")
        extracted_hours = parsed_query.get("hours")
        req_start, req_end = _resolve_query_time_window(extracted_date, extracted_trange, extracted_hours)

    # Resolve location coordinates
    resolved_lat, resolved_lng, resolved_name = resolve_location_coordinates(effective_loc, lat, lng)

    # Step 3: Base Query / Candidates with Hard Deterministic Filters
    if candidate_spaces is not None:
        candidates = []
        for s in candidate_spaces:
            if not getattr(s, "is_active", True):
                continue
            if current_user_id and getattr(s, "owner_id", None) == current_user_id:
                continue
            if effective_cap is not None and effective_cap > 0 and (s.max_capacity or 0) < effective_cap:
                continue
            price = getattr(s, "price_hourly", None) or getattr(s, "hourly_rate", None) or 0
            if effective_max_price is not None and effective_max_price > 0 and price > effective_max_price:
                continue
            if effective_cat and effective_cat.lower() not in ("all", "any"):
                cat_lower = effective_cat.lower()
                c_match = (s.category and cat_lower in s.category.lower()) or (s.title and cat_lower in s.title.lower())
                if not c_match:
                    continue
            candidates.append(s)
        candidate_spaces = candidates
    else:
        query = Space.query.filter_by(is_active=True)

        # Exclude user's own listings if authenticated
        if current_user_id:
            query = query.filter(Space.owner_id != current_user_id)

        # Hard Filter: Minimum Capacity
        if effective_cap is not None and effective_cap > 0:
            query = query.filter(Space.max_capacity >= effective_cap)

        # Hard Filter: Maximum Price Ceiling
        if effective_max_price is not None and effective_max_price > 0:
            query = query.filter(Space.price_hourly <= effective_max_price)

        # Hard Filter: Category / Space Type
        if effective_cat and effective_cat.lower() not in ("all", "any"):
            cat_lower = effective_cat.lower()
            query = query.filter(
                db.or_(
                    Space.category.ilike(f"%{cat_lower}%"),
                    Space.title.ilike(f"%{cat_lower}%")
                )
            )

        # Hard Filter: Location keyword match if coordinates could not be resolved
        if effective_loc and not (resolved_lat is not None and resolved_lng is not None and radius_km is not None):
            clean_loc = effective_loc.split("(")[0].strip()
            loc_tokens = [t.strip() for t in re.split(r"[,/]+", clean_loc) if len(t.strip()) > 1]
            if loc_tokens:
                loc_conds = []
                for lt in loc_tokens:
                    loc_conds.append(Space.city.ilike(f"%{lt}%"))
                    loc_conds.append(Space.neighborhood.ilike(f"%{lt}%"))
                    loc_conds.append(Space.address.ilike(f"%{lt}%"))
                query = query.filter(db.or_(*loc_conds))

        candidate_spaces = query.all()

    # Step 4: Secondary Deterministic Filters (Radius & Real Booking Availability)
    surviving_spaces = []
    for s in candidate_spaces:
        # Distance calculation
        dist_km = None
        if resolved_lat is not None and resolved_lng is not None and s.latitude and s.longitude:
            dist_m = haversine_distance(resolved_lat, resolved_lng, s.latitude, s.longitude)
            dist_km = round(dist_m / 1000.0, 1)
            if radius_km is not None and dist_km > radius_km:
                continue  # Excluded by hard radius constraint

        # Hard Filter: Mandatory Amenities
        if effective_amenities:
            space_amenities_lower = [a.lower() for a in (s.amenities or [])]
            missing_mandatory = False
            for req_amenity in effective_amenities:
                if not any(req_amenity.lower() in sa for sa in space_amenities_lower):
                    missing_mandatory = True
                    break
            if missing_mandatory:
                continue

        # Hard Filter: Real Booking Availability Check
        # Never allow an LLM to invent or infer availability
        is_available_for_window = True
        if req_start and req_end:
            overlap = check_booking_overlap(s.id, req_start, req_end)
            if overlap:
                is_available_for_window = False
                continue  # Hard filter: exclude occupied spaces during requested time

        surviving_spaces.append((s, dist_km, is_available_for_window))

    # If all candidate spaces were filtered out by hard constraints, return empty result set
    if not surviving_spaces:
        return {
            "status": "success",
            "results": [],
            "spaces": [],
            "query": raw_query,
            "semantic_query": semantic_query,
            "extracted_constraints": parsed_query,
            "effective_filters": {
                "location": effective_loc,
                "category": effective_cat,
                "min_capacity": effective_cap,
                "max_price": effective_max_price,
                "amenities": effective_amenities,
                "date": req_start.strftime("%Y-%m-%d") if req_start else None,
                "time_window": f"{req_start.strftime('%I:%M %p')} - {req_end.strftime('%I:%M %p')}" if req_start and req_end else None
            },
            "total_matches": 0,
            "matched_count": 0,
            "fallback_mode": False,
            "match_summary": "No spaces available matching these specific criteria or time window."
        }

    # Step 5: Semantic Embedding & Vector Cosine Similarity
    query_vector = None
    embedding_failed = False
    if semantic_query:
        try:
            query_vector = generate_embedding(semantic_query)
        except Exception as e:
            embedding_failed = True

    # Step 6: Hybrid Scoring & Ranking
    ranked_results = []
    for s, dist_km, is_avail in surviving_spaces:
        # 1. Semantic Similarity
        semantic_sim = 0.5
        if query_vector:
            # Ensure listing embedding exists in DB; compute and store if missing
            listing_vector = s.embedding
            if not listing_vector:
                try:
                    searchable_txt = build_searchable_representation(s)
                    listing_vector = generate_embedding(searchable_txt)
                    s.embedding = listing_vector
                    db.session.commit()
                except Exception:
                    listing_vector = None

            if listing_vector:
                semantic_sim = cosine_similarity(query_vector, listing_vector)

        # 2. Keyword Relevance
        keyword_rel = _compute_keyword_relevance(semantic_query or raw_query, s)

        # 3. Location Proximity Score
        if dist_km is not None:
            location_score = round(1.0 / (1.0 + (dist_km / 10.0)), 4)
        elif effective_loc and (effective_loc.lower() in (s.neighborhood or "").lower() or effective_loc.lower() in (s.city or "").lower()):
            location_score = 0.95
        else:
            location_score = 0.60

        # 4. Availability Score
        avail_score = 1.0 if is_avail else 0.5

        # 5. Listing Quality & Completeness
        completeness = _compute_completeness_score(s)

        # Composite Ranking Formula:
        # Semantic (45%) + Keyword (25%) + Location (15%) + Completeness (10%) + Availability (5%)
        if embedding_failed or not query_vector:
            # Keyword/Deterministic fallback ranking
            composite_score = (0.50 * keyword_rel) + (0.25 * location_score) + (0.15 * completeness) + (0.10 * avail_score)
        else:
            composite_score = (0.45 * semantic_sim) + (0.25 * keyword_rel) + (0.15 * location_score) + (0.10 * completeness) + (0.05 * avail_score)

        # Build explainable match reasoning without exposing raw scores
        reasons = []
        if effective_cap and s.max_capacity >= effective_cap:
            reasons.append(f"Fits {effective_cap}+ people (capacity: {s.max_capacity})")
        if dist_km is not None and dist_km <= 5.0:
            reasons.append(f"Conveniently close ({dist_km} km away)")
        elif effective_loc and effective_loc.lower() in (s.location or "").lower():
            reasons.append(f"Located in {s.location}")
        if s.ai_recommended_uses:
            reasons.append(f"Ideal for {s.ai_recommended_uses.split(',')[0].strip()}")
        if not reasons:
            reasons.append(f"Verified {s.category} with instant check-in")

        match_badge = "Available Now"
        if composite_score >= 0.78:
            match_badge = "Top Pick"
        elif composite_score >= 0.65:
            match_badge = "Best Match"

        s_dict = s.to_dict()
        if dist_km is not None:
            s_dict["distance_km"] = dist_km
        s_dict["ai_match_score"] = round(composite_score * 100)
        s_dict["ai_match_reasoning"] = " • ".join(reasons[:2])
        s_dict["is_available"] = is_avail
        s_dict["availability_status"] = "Available Now" if is_avail else "Occupied"

        ranked_results.append({
            "space": s_dict,
            "composite_score": round(composite_score, 4),
            "match_score": int(round(composite_score * 100)),
            "match_badge": match_badge,
            "match_reasons": reasons,
            "is_available": is_avail,
            "availability_status": "Available Now" if is_avail else "Occupied"
        })

    # Sort descending by composite ranking score
    ranked_results.sort(key=lambda x: x["composite_score"], reverse=True)
    top_results = ranked_results[:limit]
    flattened_spaces = [r["space"] for r in top_results]

    return {
        "status": "success",
        "results": top_results,
        "spaces": flattened_spaces,
        "query": raw_query,
        "semantic_query": semantic_query,
        "extracted_constraints": parsed_query,
        "effective_filters": {
            "location": effective_loc,
            "category": effective_cat,
            "min_capacity": effective_cap,
            "max_price": effective_max_price,
            "amenities": effective_amenities,
            "date": req_start.strftime("%Y-%m-%d") if req_start else None,
            "time_window": f"{req_start.strftime('%I:%M %p')} - {req_end.strftime('%I:%M %p')}" if req_start and req_end else None
        },
        "total_matches": len(flattened_spaces),
        "matched_count": len(flattened_spaces),
        "fallback_mode": embedding_failed,
        "match_summary": f"Found {len(flattened_spaces)} verified spaces matching your request."
    }
