"""
SpaceLoop Spaces REST Blueprint
Handles space exploration, AI scanning, space registration, editing, and semantic matchmaking.
"""
import re
from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Space, User
from backend.modules.auth import authorize, Permission, ForbiddenError, set_active_context
from backend.core.geo import haversine_distance, resolve_location_coordinates
from space_ai import analyze_space_features, match_spaces_with_ai
from security import rate_limit_ai, sanitize_string, validate_numeric, validate_image_url

api_v1_spaces = Blueprint("api_v1_spaces", __name__)


@api_v1_spaces.route("/api/spaces", methods=["GET"])
def get_spaces():
    category = sanitize_string(request.args.get("category"), max_length=50)
    city = sanitize_string(request.args.get("city", ""), max_length=100)
    loc = sanitize_string(request.args.get("loc", ""), max_length=100) or city
    q = sanitize_string(request.args.get("q", ""), max_length=150)
    raw_lat = request.args.get("lat")
    raw_lng = request.args.get("lng")
    raw_radius = request.args.get("radius")
    raw_max_price = request.args.get("max_price")

    radius_km = None
    if raw_radius and str(raw_radius).lower() not in ("all", "any", ""):
        try:
            radius_km = float(raw_radius)
        except (ValueError, TypeError):
            radius_km = None

    max_price = None
    if raw_max_price and str(raw_max_price).lower() not in ("all", "any", ""):
        try:
            max_price = float(raw_max_price)
        except (ValueError, TypeError):
            max_price = None

    lat, lng, resolved_loc_name = resolve_location_coordinates(loc, raw_lat, raw_lng)

    query = Space.query.filter_by(is_active=True)

    # 1. Category filtering with aliases
    if category and category.lower() not in ("all", "any"):
        cat_lower = category.lower().strip().replace(" pod", "")
        cat_aliases = [cat_lower]
        if "studio" in cat_lower or "creative" in cat_lower:
            cat_aliases.extend(["studio", "creative", "podcast", "vocal", "photo", "audio"])
        elif "work" in cat_lower:
            cat_aliases.extend(["work", "workspace", "desk", "office", "hackathon", "incubator"])
        elif "meet" in cat_lower:
            cat_aliases.extend(["meet", "meeting", "conference", "board", "discussion", "sprint"])
        elif "study" in cat_lower:
            cat_aliases.extend(["study", "pod", "library", "quiet"])
        elif "workshop" in cat_lower or "maker" in cat_lower:
            cat_aliases.extend(["workshop", "maker", "hardware", "proto", "creative"])
        elif "retail" in cat_lower or "store" in cat_lower:
            cat_aliases.extend(["retail", "pop-up", "store", "stall", "boutique"])
        elif "storage" in cat_lower:
            cat_aliases.extend(["storage", "warehouse", "gear", "unit"])
        elif "event" in cat_lower:
            cat_aliases.extend(["event", "hall", "gathering"])

        cat_filters = []
        for alias in set(cat_aliases):
            cat_filters.append(Space.category.ilike(f"%{alias}%"))
            cat_filters.append(Space.title.ilike(f"%{alias}%"))
        query = query.filter(db.or_(*cat_filters))

    # 2. Location / Hub tokenized search
    # If coordinates are resolved and radius is specified, distance calculation does precision filtering
    # If no radius, or coordinates unresolved, tokenize location by comma/space
    if loc and loc.lower() not in ("all", "all cities", "any"):
        if not (lat is not None and lng is not None and radius_km is not None):
            clean_loc = loc.split("(")[0].strip()
            tokens = [t.strip() for t in re.split(r"[,/]+", clean_loc) if len(t.strip()) > 1]
            if tokens:
                loc_conditions = []
                for token in tokens:
                    loc_conditions.append(Space.city.ilike(f"%{token}%"))
                    loc_conditions.append(Space.neighborhood.ilike(f"%{token}%"))
                    loc_conditions.append(Space.address.ilike(f"%{token}%"))
                    loc_conditions.append(Space.title.ilike(f"%{token}%"))
                query = query.filter(db.or_(*loc_conditions))

    # 3. Free text search
    if q:
        q_clean = q.lower().strip()
        query = query.filter(db.or_(
            Space.title.ilike(f"%{q_clean}%"),
            Space.description.ilike(f"%{q_clean}%"),
            Space.category.ilike(f"%{q_clean}%"),
            Space.city.ilike(f"%{q_clean}%"),
            Space.neighborhood.ilike(f"%{q_clean}%"),
            Space.address.ilike(f"%{q_clean}%")
        ))

    # 4. Max price budget filter
    if max_price is not None:
        query = query.filter(Space.price_hourly <= max_price)

    all_spaces = query.all()
    spaces_data = []

    for s in all_spaces:
        s_dict = s.to_dict()
        if lat is not None and lng is not None and s.latitude and s.longitude:
            dist_m = haversine_distance(lat, lng, s.latitude, s.longitude)
            dist_km = round(dist_m / 1000.0, 1)
            s_dict["distance_km"] = dist_km
            if radius_km is not None and dist_km > radius_km:
                continue
        spaces_data.append(s_dict)

    if lat is not None and lng is not None:
        spaces_data.sort(key=lambda x: x.get("distance_km", 999999))

    return jsonify(spaces_data)


@api_v1_spaces.route("/api/spaces/<int:space_id>", methods=["GET"])
def get_space(space_id):
    space = Space.query.get_or_404(space_id)
    return jsonify(space.to_dict())


@api_v1_spaces.route("/api/spaces/ai-scan", methods=["POST"])
@rate_limit_ai
def ai_scan_space():
    data = request.get_json(silent=True) or {}
    image_url = sanitize_string(data.get("photo_url", ""), max_length=500)
    if image_url and not validate_image_url(image_url):
        image_url = ""

    analysis = analyze_space_features(data, image_url)
    return jsonify(analysis)


@api_v1_spaces.route("/api/spaces", methods=["POST"])
@login_required
def create_space():
    """Creates a new space listing bound to the authenticated host. Requires Host authentication."""
    if not current_user.is_host:
        return jsonify({
            "success": False,
            "error": "Host authentication and property verification required to list spaces. Please complete Host Property KYC."
        }), 403

    try:
        authorize(current_user, Permission.SPACE_CREATE)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json(silent=True) or {}
    
    title = sanitize_string(data.get("title"), max_length=150)
    category = sanitize_string(data.get("category", "Studio"), max_length=50)
    address = sanitize_string(data.get("address"), max_length=200)
    neighborhood = sanitize_string(data.get("neighborhood") or data.get("location") or "Downtown", max_length=100)
    city = sanitize_string(data.get("city", "Bengaluru"), max_length=100)
    state = sanitize_string(data.get("state", "KA"), max_length=50)
    zip_code = sanitize_string(data.get("zip_code", "560034"), max_length=20)
    description = sanitize_string(data.get("description", "A verified temporary space."), max_length=3000)

    price_hourly = validate_numeric(data.get("price_hourly") or data.get("hourly_rate"), min_val=5.0, max_val=5000.0, default=None)
    price_daily = validate_numeric(data.get("price_daily") or data.get("daily_rate"), min_val=20.0, max_val=25000.0, default=None)
    sqft = int(validate_numeric(data.get("sqft"), min_val=20, max_val=50000, default=200))
    max_capacity = int(validate_numeric(data.get("max_capacity"), min_val=1, max_val=500, default=4))
    minimum_hours = int(validate_numeric(data.get("minimum_hours"), min_val=1, max_val=24, default=1))

    if not title or not address or price_hourly is None:
        return jsonify({
            "error": "Validation failed",
            "message": "Title, address, and positive hourly rate are required."
        }), 400

    if price_daily is None:
        price_daily = round(price_hourly * 5.0, 2)

    raw_photos = data.get("photos") or []
    clean_photos = []
    if isinstance(raw_photos, list):
        for p in raw_photos:
            if isinstance(p, str) and validate_image_url(p):
                clean_photos.append(p[:1000000])
    if not clean_photos:
        clean_photos = [
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80"
        ]

    new_space = Space(
        owner_id=current_user.id,
        title=title,
        category=category,
        description=description,
        address=address,
        neighborhood=neighborhood,
        city=city,
        state=state,
        zip_code=zip_code,
        sqft=sqft,
        max_capacity=max_capacity,
        price_hourly=price_hourly,
        price_daily=price_daily,
        minimum_hours=minimum_hours,
        ai_dimensions_summary=sanitize_string(data.get("ai_dimensions_summary", ""), max_length=150),
        ai_lighting=sanitize_string(data.get("ai_lighting", "Natural Light"), max_length=100),
        ai_noise_level=sanitize_string(data.get("ai_noise_level", "Quiet"), max_length=100),
        ai_power_access=sanitize_string(data.get("ai_power_access", "Standard Outlets"), max_length=100),
        ai_safety_notes=sanitize_string(data.get("ai_safety_notes", "Inspected for basic safety."), max_length=300),
        ai_recommended_uses=sanitize_string(data.get("ai_recommended_uses", ""), max_length=200),
        ai_suitability_score=int(validate_numeric(data.get("ai_suitability_score"), 50, 100, 95)),
    )

    lat_val = validate_numeric(data.get("latitude") or data.get("lat"), min_val=-90.0, max_val=90.0, default=None)
    lng_val = validate_numeric(data.get("longitude") or data.get("lng"), min_val=-180.0, max_val=180.0, default=None)
    if lat_val is not None:
        new_space.latitude = float(lat_val)
    if lng_val is not None:
        new_space.longitude = float(lng_val)

    raw_amenities = data.get("amenities") or ["Wi-Fi", "Power Outlets", "Restroom Access"]
    new_space.amenities = [sanitize_string(a, max_length=80) for a in raw_amenities if isinstance(a, str)][:15]

    raw_rules = data.get("rules") or ["No smoking", "Clean up after use", "Respect neighbors"]
    new_space.rules = [sanitize_string(r, max_length=150) for r in raw_rules if isinstance(r, str)][:10]

    new_space.photos = clean_photos[:6]
    new_space.ai_tags = ["Verified Space", "Instant Booking"]

    db.session.add(new_space)
    db.session.commit()
    resp_dict = new_space.to_dict()
    resp_dict["space_id"] = new_space.id
    resp_dict["success"] = True
    return jsonify(resp_dict), 201


@api_v1_spaces.route("/api/spaces/<int:space_id>/edit", methods=["POST"])
@login_required
def api_edit_space(space_id):
    space = Space.query.get_or_404(space_id)
    try:
        authorize(current_user, Permission.SPACE_UPDATE, resource=space)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json(silent=True) or request.form or {}

    if data.get("title"):
        space.title = sanitize_string(data.get("title"), max_length=150)
    if data.get("category"):
        space.category = sanitize_string(data.get("category"), max_length=50)
    if data.get("address"):
        space.address = sanitize_string(data.get("address"), max_length=200)
    if data.get("description"):
        space.description = sanitize_string(data.get("description"), max_length=3000)
    if data.get("price_hourly") is not None and str(data.get("price_hourly")).strip() != "":
        space.price_hourly = float(validate_numeric(data.get("price_hourly"), min_val=5.0, max_val=5000.0, default=space.price_hourly))
    if data.get("price_daily") is not None and str(data.get("price_daily")).strip() != "":
        space.price_daily = float(validate_numeric(data.get("price_daily"), min_val=20.0, max_val=25000.0, default=space.price_daily))
    if data.get("sqft") is not None and str(data.get("sqft")).strip() != "":
        space.sqft = int(validate_numeric(data.get("sqft"), min_val=20, max_val=50000, default=space.sqft))
    if data.get("max_capacity") is not None and str(data.get("max_capacity")).strip() != "":
        space.max_capacity = int(validate_numeric(data.get("max_capacity"), min_val=1, max_val=500, default=space.max_capacity))
    if data.get("amenities") and isinstance(data.get("amenities"), list):
        space.amenities = [sanitize_string(a, max_length=80) for a in data.get("amenities") if isinstance(a, str)][:15]
    if data.get("rules") and isinstance(data.get("rules"), list):
        space.rules = [sanitize_string(r, max_length=150) for r in data.get("rules") if isinstance(r, str)][:10]

    db.session.commit()
    if request.is_json:
        return jsonify({"success": True, "message": f"Space '{space.title}' updated successfully!", "space": space.to_dict()}), 200
    return redirect(url_for("dashboard_page"))


@api_v1_spaces.route("/api/spaces/<int:space_id>/toggle-status", methods=["POST"])
@login_required
def toggle_space_status(space_id):
    space = Space.query.get_or_404(space_id)
    try:
        authorize(current_user, Permission.SPACE_UPDATE, resource=space)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    space.is_active = not space.is_active
    db.session.commit()
    if request.is_json:
        return jsonify({"success": True, "is_active": space.is_active, "space_id": space.id})
    flash(f"Space '{space.title}' is now {'Active & Discoverable' if space.is_active else 'Paused'}.", "success")
    return redirect(request.referrer or url_for("dashboard_page"))


@api_v1_spaces.route("/api/spaces/ai-match", methods=["POST"])
@rate_limit_ai
def ai_match_spaces():
    data = request.get_json(silent=True) or {}
    query_text = sanitize_string(data.get("query", ""), max_length=300)
    loc = sanitize_string(data.get("loc", ""), max_length=100)
    raw_lat = data.get("lat")
    raw_lng = data.get("lng")
    raw_radius = data.get("radius")

    radius_km = None
    if raw_radius and raw_radius != "All":
        try:
            radius_km = float(raw_radius)
        except (ValueError, TypeError):
            radius_km = None

    lat, lng, resolved_loc_name = resolve_location_coordinates(loc, raw_lat, raw_lng)

    all_spaces = [s.to_dict() for s in Space.query.filter_by(is_active=True).all()]
    candidate_spaces = []

    for s in all_spaces:
        if lat is not None and lng is not None and s.get("latitude") and s.get("longitude"):
            dist_m = haversine_distance(lat, lng, s["latitude"], s["longitude"])
            dist_km = round(dist_m / 1000.0, 1)
            s["distance_km"] = dist_km
            if radius_km is not None and dist_km > radius_km:
                continue
        candidate_spaces.append(s)

    spaces_to_rank = candidate_spaces if candidate_spaces else all_spaces
    ranked = match_spaces_with_ai(query_text, spaces_to_rank)

    flattened_spaces = []
    for r in ranked:
        sp = dict(r.get("space", {}))
        if "distance_km" in sp:
            r["distance_km"] = sp["distance_km"]
        sp["ai_match_score"] = r.get("match_score")
        reasons = r.get("match_reasons", [])
        sp["ai_match_reasoning"] = reasons[0] if reasons else r.get("considerations", "")
        sp["pros"] = r.get("pros", [])
        sp["cons"] = r.get("cons", [])
        flattened_spaces.append(sp)

    return jsonify({
        "results": ranked,
        "spaces": flattened_spaces,
        "query": query_text,
        "location": resolved_loc_name or loc,
        "radius_km": radius_km,
        "total_matches": len(ranked),
        "matched_count": len(ranked),
        "match_summary": f"Matched {len(ranked)} spaces for '{query_text}'"
    })
