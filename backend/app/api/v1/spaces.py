"""
SpaceLoop Spaces REST Blueprint
Handles space exploration, AI scanning, space registration, editing, photo uploads, inquiries, and semantic matchmaking.
"""
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Space, User, SpaceInquiry, Booking, Review, AuditLog, AccessLog
from backend.modules.auth import authorize, Permission, AuthError, ForbiddenError, set_active_context
from backend.core.geo import haversine_distance, resolve_location_coordinates
from space_ai import analyze_space_features, match_spaces_with_ai
from security import rate_limit_ai, sanitize_string, validate_numeric, validate_image_url
from backend.core.cache import space_cache

api_v1_spaces = Blueprint("api_v1_spaces", __name__)


@api_v1_spaces.route("/api/spaces", methods=["GET"])
def get_spaces():
    user_id = current_user.id if current_user.is_authenticated else None
    qs = request.query_string.decode("utf-8")
    etag = space_cache.generate_etag("spaces_list", user_id=user_id, extra=qs)

    # 1. HTTP 304 conditional cache
    conditional_resp = space_cache.check_etag_and_respond(etag)
    if conditional_resp:
        return conditional_resp

    # 2. Server-side in-memory cache lookup
    cache_key = f"spaces_list:{user_id or 'anon'}:{qs}"
    cached_resp = space_cache.get_cached_response(cache_key, etag)
    if cached_resp:
        return cached_resp

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

    query = Space.query.options(
        db.joinedload(Space.owner),
        db.selectinload(Space.reviews)
    ).filter_by(is_active=True)

    # Exclude host's own properties when logged in as a host/seeker
    if current_user.is_authenticated:
        query = query.filter(Space.owner_id != current_user.id)

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

    raw_page = request.args.get("page")
    raw_limit = request.args.get("limit")
    page = int(raw_page) if raw_page and raw_page.isdigit() and int(raw_page) > 0 else None
    limit = int(raw_limit) if raw_limit and raw_limit.isdigit() and int(raw_limit) > 0 else None

    if lat is not None and lng is not None:
        spaces_data.sort(key=lambda x: x.get("distance_km", 999999))

    if page or limit:
        page_num = page or 1
        page_limit = min(limit or 12, 100)
        total_items = len(spaces_data)
        start_idx = (page_num - 1) * page_limit
        end_idx = start_idx + page_limit
        paginated = spaces_data[start_idx:end_idx]
        response_payload = {
            "spaces": paginated,
            "total": total_items,
            "page": page_num,
            "limit": page_limit,
            "has_more": end_idx < total_items
        }
        return space_cache.cache_and_respond(cache_key, etag, response_payload)

    return space_cache.cache_and_respond(cache_key, etag, spaces_data)


@api_v1_spaces.route("/api/spaces/<int:space_id>", methods=["GET"])
def get_space(space_id):
    etag = space_cache.generate_etag(f"space_{space_id}")
    conditional_resp = space_cache.check_etag_and_respond(etag)
    if conditional_resp:
        return conditional_resp

    cache_key = f"space_detail:{space_id}"
    cached_resp = space_cache.get_cached_response(cache_key, etag)
    if cached_resp:
        return cached_resp

    space = Space.query.get_or_404(space_id)
    return space_cache.cache_and_respond(cache_key, etag, space.to_dict())


@api_v1_spaces.route("/api/spaces/ai-scan", methods=["POST"])
@rate_limit_ai
def ai_scan_space():
    data = request.get_json(silent=True) or {}
    image_url = sanitize_string(data.get("photo_url", ""), max_length=500)
    if image_url and not validate_image_url(image_url):
        image_url = ""

    analysis = analyze_space_features(data, image_url)
    return jsonify(analysis)


@api_v1_spaces.route("/api/spaces/assist-listing", methods=["POST"])
@rate_limit_ai
def api_assist_listing():
    """
    NLP-powered listing assistance endpoint.
    Converts unstructured natural language into structured space attributes,
    identifies missing fields, checks for physical space inconsistencies,
    and generates factual descriptions.
    """
    data = request.get_json(silent=True) or request.form or {}
    text = sanitize_string(data.get("text") or data.get("description") or data.get("prompt") or "", max_length=2000)
    target_language = sanitize_string(data.get("target_language") or data.get("language") or "en", max_length=10)

    from backend.modules.nlp.listing_assistance import ListingAssistanceService
    result = ListingAssistanceService.assist_listing(text=text, target_language=target_language)
    return jsonify(result), (200 if result.get("success") else 400)


@api_v1_spaces.route("/api/spaces/translate-listing", methods=["POST"])
@rate_limit_ai
def api_translate_listing():
    """
    Translates listing title, description, and amenities into target language.
    """
    data = request.get_json(silent=True) or request.form or {}
    title = sanitize_string(data.get("title", ""), max_length=200)
    description = sanitize_string(data.get("description", ""), max_length=3000)
    raw_amenities = data.get("amenities") or []
    amenities = [sanitize_string(a, max_length=50) for a in raw_amenities if isinstance(a, str)]
    target_language = sanitize_string(data.get("target_language") or "hi", max_length=10)

    from backend.modules.nlp.listing_assistance import ListingAssistanceService
    result = ListingAssistanceService.translate_listing_content(
        title=title,
        description=description,
        amenities=amenities,
        target_language=target_language
    )
    return jsonify(result), 200


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@api_v1_spaces.route("/api/spaces/upload-photo", methods=["POST"])
@login_required
def upload_space_photo():
    """Accepts multipart property photo upload (PNG, JPG, WEBP <= 5MB) and stores it in static/uploads/spaces/."""
    file = None
    if "photo" in request.files:
        file = request.files["photo"]
    elif "file" in request.files:
        file = request.files["file"]

    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file selected. Please select an image to upload."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Unsupported file format. Please upload JPG, PNG, or WEBP."}), 400

    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        return jsonify({"success": False, "error": "Image file exceeds the 5MB size limit."}), 400

    file.seek(0)
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"space_{uuid.uuid4().hex[:12]}.{ext}"

    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "spaces")
    os.makedirs(upload_dir, exist_ok=True)
    dest_path = os.path.join(upload_dir, unique_filename)
    file.save(dest_path)

    photo_url = f"/static/uploads/spaces/{unique_filename}"
    return jsonify({
        "success": True,
        "url": photo_url,
        "photo_url": photo_url,
        "filename": unique_filename
    }), 201


@api_v1_spaces.route("/api/spaces", methods=["POST"])
@login_required
def create_space():
    """Creates a new space listing bound to the authenticated host. Requires verified host KYC and accepted T&C."""
    if not current_user.is_host or not getattr(current_user, "is_host_verified", False):
        return jsonify({
            "success": False,
            "error": "Host authentication and property verification required to list spaces. Please complete Host Property KYC (Discom Utility CA + UPI Penny Drop)."
        }), 403

    try:
        authorize(current_user, Permission.SPACE_CREATE)
    except AuthError as e:
        status_code = getattr(e, "status_code", 403)
        return jsonify({"error": str(e), "success": False}), status_code

    data = request.get_json(silent=True) or {}

    # Mandatory Terms & Conditions acceptance check
    terms_agreed = bool(
        data.get("terms_accepted") or
        data.get("agree_terms") or
        data.get("terms_and_conditions_agreed") or
        data.get("easements_accepted")
    )
    if not terms_agreed:
        return jsonify({
            "success": False,
            "error": "You must review and agree to the SpaceLoop Terms & Conditions and Section 52 Easements Act compliance before publishing your listing."
        }), 400

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

    # Generate dense vector embedding for semantic search
    try:
        from backend.modules.search.embedding import build_searchable_representation, generate_embedding
        txt = build_searchable_representation(new_space)
        new_space.embedding = generate_embedding(txt)
    except Exception:
        pass

    db.session.add(new_space)
    db.session.commit()
    space_cache.bump_catalog_version(new_space.id)

    # Trust & Safety Listing Evaluation
    trust_safety_summary = {
        "risk_level": "normal",
        "recommended_action": "allow",
        "evidence": "Listing evaluation completed with baseline verification."
    }
    try:
        from backend.modules.trust_safety import TrustSafetyEngine
        listing_assessment = TrustSafetyEngine.evaluate_listing(new_space, current_user)
        if listing_assessment:
            if listing_assessment.recommended_action == "restrict_action":
                new_space.is_active = False
                db.session.commit()
            trust_safety_summary = {
                "risk_level": getattr(listing_assessment, "risk_level", "normal"),
                "recommended_action": getattr(listing_assessment, "recommended_action", "allow"),
                "evidence": getattr(listing_assessment, "evidence_text", "Listing evaluated successfully.")
            }
    except Exception as ts_err:
        current_app.logger.warning("Trust & Safety listing evaluation non-fatal exception: %s", type(ts_err).__name__)

    resp_dict = new_space.to_dict()
    resp_dict["space_id"] = new_space.id
    resp_dict["success"] = True
    resp_dict["trust_safety"] = trust_safety_summary
    return jsonify(resp_dict), 201


@api_v1_spaces.route("/api/spaces/<int:space_id>/edit", methods=["POST"])
@api_v1_spaces.route("/api/spaces/<int:space_id>", methods=["PUT", "PATCH"])
@login_required
def api_edit_space(space_id):
    space = Space.query.get_or_404(space_id)
    try:
        authorize(current_user, Permission.SPACE_UPDATE, resource=space)
    except AuthError as e:
        status_code = getattr(e, "status_code", 403)
        return jsonify({"error": str(e), "success": False}), status_code

    data = request.get_json(silent=True) or request.form or {}

    if data.get("title"):
        space.title = sanitize_string(data.get("title"), max_length=150)
    if data.get("category"):
        space.category = sanitize_string(data.get("category"), max_length=50)
    if data.get("address"):
        space.address = sanitize_string(data.get("address"), max_length=200)
    if data.get("neighborhood") or data.get("location"):
        space.neighborhood = sanitize_string(data.get("neighborhood") or data.get("location"), max_length=100)
    if data.get("city"):
        space.city = sanitize_string(data.get("city"), max_length=100)
    if data.get("state"):
        space.state = sanitize_string(data.get("state"), max_length=50)
    if data.get("zip_code"):
        space.zip_code = sanitize_string(data.get("zip_code"), max_length=20)
    if data.get("description"):
        space.description = sanitize_string(data.get("description"), max_length=3000)

    if data.get("price_hourly") is not None and str(data.get("price_hourly")).strip() != "":
        space.price_hourly = float(validate_numeric(data.get("price_hourly"), min_val=5.0, max_val=5000.0, default=space.price_hourly))
    if data.get("hourly_rate") is not None and str(data.get("hourly_rate")).strip() != "":
        space.price_hourly = float(validate_numeric(data.get("hourly_rate"), min_val=5.0, max_val=5000.0, default=space.price_hourly))

    if data.get("price_daily") is not None and str(data.get("price_daily")).strip() != "":
        space.price_daily = float(validate_numeric(data.get("price_daily"), min_val=20.0, max_val=25000.0, default=space.price_daily))
    elif space.price_hourly:
        space.price_daily = round(space.price_hourly * 5.0, 2)

    if data.get("sqft") is not None and str(data.get("sqft")).strip() != "":
        space.sqft = int(validate_numeric(data.get("sqft"), min_val=20, max_val=50000, default=space.sqft))
    if data.get("max_capacity") is not None and str(data.get("max_capacity")).strip() != "":
        space.max_capacity = int(validate_numeric(data.get("max_capacity"), min_val=1, max_val=500, default=space.max_capacity))
    if data.get("minimum_hours") is not None and str(data.get("minimum_hours")).strip() != "":
        space.minimum_hours = int(validate_numeric(data.get("minimum_hours"), min_val=1, max_val=24, default=space.minimum_hours))

    if data.get("amenities"):
        if isinstance(data.get("amenities"), list):
            space.amenities = [sanitize_string(a, max_length=80) for a in data.get("amenities") if isinstance(a, str)][:15]
        elif isinstance(data.get("amenities"), str):
            space.amenities = [sanitize_string(a.strip(), max_length=80) for a in data.get("amenities").split(",") if a.strip()][:15]

    if data.get("rules"):
        if isinstance(data.get("rules"), list):
            space.rules = [sanitize_string(r, max_length=150) for r in data.get("rules") if isinstance(r, str)][:10]
        elif isinstance(data.get("rules"), str):
            space.rules = [sanitize_string(r.strip(), max_length=150) for r in data.get("rules").split(",") if r.strip()][:10]

    if data.get("photos"):
        raw_photos = data.get("photos")
        if isinstance(raw_photos, list):
            clean_p = [p[:1000] for p in raw_photos if isinstance(p, str) and (validate_image_url(p) or p.startswith("/static/"))]
            if clean_p:
                space.photos = clean_p[:6]

    if "is_active" in data:
        space.is_active = bool(data.get("is_active"))
    if "draft" in data:
        space.draft = bool(data.get("draft"))
    if "is_verified" in data and current_user.is_admin:
        space.is_verified = bool(data.get("is_verified"))
    if data.get("operating_hours_start"):
        space.operating_hours_start = sanitize_string(data.get("operating_hours_start"), max_length=10)
    if data.get("operating_hours_end"):
        space.operating_hours_end = sanitize_string(data.get("operating_hours_end"), max_length=10)
    if data.get("buffer_minutes") is not None:
        space.buffer_minutes = int(validate_numeric(data.get("buffer_minutes"), min_val=0, max_val=120, default=15))
    if "instant_booking_enabled" in data:
        space.instant_booking_enabled = bool(data.get("instant_booking_enabled"))

    if data.get("geofence_radius_meters") is not None and str(data.get("geofence_radius_meters")).strip() != "":
        space.geofence_radius_meters = int(validate_numeric(data.get("geofence_radius_meters"), min_val=10, max_val=500, default=space.geofence_radius_meters or 30))
    if data.get("physical_access_type"):
        space.physical_access_type = sanitize_string(data.get("physical_access_type"), max_length=50)
    if data.get("keybox_code") is not None:
        space.keybox_code = sanitize_string(data.get("keybox_code"), max_length=20)
    if data.get("discom_ca_number") is not None:
        space.discom_ca_number = sanitize_string(data.get("discom_ca_number"), max_length=50)
    if data.get("discom_consumer_name") is not None:
        space.discom_consumer_name = sanitize_string(data.get("discom_consumer_name"), max_length=120)
    if data.get("room_qr_token") is not None:
        space.room_qr_token = sanitize_string(data.get("room_qr_token"), max_length=64)
    if data.get("latitude") is not None or data.get("lat") is not None:
        raw_lat = data.get("latitude") if data.get("latitude") is not None else data.get("lat")
        val_lat = validate_numeric(raw_lat, min_val=-90.0, max_val=90.0, default=None)
        if val_lat is not None:
            space.latitude = float(val_lat)
    if data.get("longitude") is not None or data.get("lng") is not None:
        raw_lng = data.get("longitude") if data.get("longitude") is not None else data.get("lng")
        val_lng = validate_numeric(raw_lng, min_val=-180.0, max_val=180.0, default=None)
        if val_lng is not None:
            space.longitude = float(val_lng)

    # Regenerate dense vector embedding for semantic search
    try:
        from backend.modules.search.embedding import build_searchable_representation, generate_embedding
        txt = build_searchable_representation(space)
        space.embedding = generate_embedding(txt)
    except Exception:
        pass

    db.session.commit()
    space_cache.bump_catalog_version(space.id)

    # Record Audit Event
    try:
        from backend.modules.auth.audit import record_audit
        record_audit("space_updated", user_id=current_user.id, details={"space_id": space.id, "title": space.title})
    except Exception:
        pass

    # Trust & Safety Listing Evaluation on update
    from backend.modules.trust_safety import TrustSafetyEngine
    listing_assessment = TrustSafetyEngine.evaluate_listing(space, current_user)
    if listing_assessment.recommended_action == "restrict_action":
        space.is_active = False
        db.session.commit()

    if request.is_json or request.method in ("PUT", "PATCH"):
        return jsonify({
            "success": True,
            "message": f"Space '{space.title}' updated successfully!",
            "space": space.to_dict(),
            "trust_safety": {
                "risk_level": listing_assessment.risk_level,
                "recommended_action": listing_assessment.recommended_action
            }
        }), 200
    return redirect(url_for("dashboard_page"))


@api_v1_spaces.route("/api/host/spaces", methods=["GET"])
@login_required
def get_host_spaces():
    """Returns all spaces owned by the authenticated host, including drafts and inactive spaces, with operational telemetry."""
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    spaces = Space.query.options(
        db.joinedload(Space.owner),
        db.selectinload(Space.reviews),
        db.selectinload(Space.bookings)
    ).filter_by(owner_id=current_user.id).order_by(Space.created_at.desc()).all()
    results = []
    now = datetime.utcnow()

    for s in spaces:
        s_dict = s.to_dict()
        bookings = s.bookings
        confirmed_bookings = [b for b in bookings if b.status in ("confirmed", "active")]
        completed_bookings = [b for b in bookings if b.status == "completed"]
        upcoming_bookings = [b for b in confirmed_bookings if b.start_time and b.start_time > now]
        active_session = next((b for b in bookings if b.session_state == "checked_in" or (b.status == "active" and b.session_state != "checked_out")), None)
        total_revenue = sum(b.total_price for b in completed_bookings)

        s_dict["bookings_count"] = len(bookings)
        s_dict["upcoming_bookings_count"] = len(upcoming_bookings)
        s_dict["active_session"] = active_session.to_dict() if active_session else None
        s_dict["total_revenue"] = round(total_revenue, 2)
        s_dict["is_discom_verified"] = bool(s.discom_ca_number or (s.owner and s.owner.is_host_verified))
        s_dict["status"] = "published" if s.is_active else "unavailable"
        results.append(s_dict)

    return jsonify({
        "success": True,
        "spaces": results,
        "count": len(results)
    }), 200


@api_v1_spaces.route("/api/host/spaces/<int:space_id>", methods=["GET"])
@login_required
def get_host_space_detail(space_id):
    space = Space.query.get_or_404(space_id)
    if space.owner_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Access denied: You do not own this space."}), 403

    bookings = Booking.query.filter_by(space_id=space.id).order_by(Booking.start_time.desc()).all()
    now = datetime.utcnow()
    active_session = next((b for b in bookings if b.session_state == "checked_in" or (b.status == "active" and b.session_state != "checked_out")), None)

    # Activity/audit records for this space
    activity_query = AuditLog.query.filter(
        db.or_(
            AuditLog.details.ilike(f'%space_id": {space.id}%'),
            AuditLog.details.ilike(f'%Space #{space.id}%'),
            AuditLog.action.ilike(f'%space%')
        )
    ).order_by(AuditLog.created_at.desc()).limit(20).all()

    s_dict = space.to_dict()
    s_dict["bookings_count"] = len(bookings)
    s_dict["active_session"] = active_session.to_dict() if active_session else None
    s_dict["is_discom_verified"] = bool(space.discom_ca_number or (space.owner and space.owner.is_host_verified))

    return jsonify({
        "success": True,
        "space": s_dict,
        "bookings": [b.to_dict() for b in bookings],
        "activity": [a.to_dict() for a in activity_query]
    }), 200


@api_v1_spaces.route("/api/spaces/<int:space_id>/toggle-status", methods=["POST"])
@login_required
def toggle_space_status(space_id):
    space = Space.query.get_or_404(space_id)
    try:
        authorize(current_user, Permission.SPACE_UPDATE, resource=space)
    except AuthError as e:
        status_code = getattr(e, "status_code", 403)
        return jsonify({"error": str(e), "success": False}), status_code

    space.is_active = not space.is_active
    db.session.commit()
    space_cache.bump_catalog_version(space.id)
    if request.is_json:
        return jsonify({"success": True, "is_active": space.is_active, "space_id": space.id})
    flash(f"Space '{space.title}' is now {'Active & Discoverable' if space.is_active else 'Paused'}.", "success")
    return redirect(request.referrer or url_for("dashboard_page"))


@api_v1_spaces.route("/api/spaces/<int:space_id>/check-availability", methods=["GET"])
@api_v1_spaces.route("/api/v1/spaces/<int:space_id>/check-availability", methods=["GET"])
def check_space_availability(space_id):
    space = Space.query.get_or_404(space_id)
    raw_st = request.args.get("start_time") or request.args.get("start")
    raw_et = request.args.get("end_time") or request.args.get("end")

    if not raw_st or not raw_et:
        resp = jsonify({
            "available": False,
            "error": "Both start_time and end_time query parameters are required."
        })
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp, 400

    try:
        st = datetime.fromisoformat(str(raw_st).replace("Z", "+00:00"))
        if st.tzinfo:
            st = st.astimezone(timezone.utc).replace(tzinfo=None)
        et = datetime.fromisoformat(str(raw_et).replace("Z", "+00:00"))
        if et.tzinfo:
            et = et.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        resp = jsonify({"available": False, "error": "Invalid ISO format for start_time or end_time."})
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp, 400

    if st >= et:
        resp = jsonify({"available": False, "error": "start_time must be strictly before end_time."})
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp, 400

    # Check for overlapping confirmed or active bookings
    conflict = Booking.query.filter(
        Booking.space_id == space.id,
        Booking.status.in_(["confirmed", "active"]),
        Booking.start_time < et,
        Booking.end_time > st
    ).order_by(Booking.start_time.asc()).first()

    if conflict:
        resp = jsonify({
            "available": False,
            "status": "CONFLICT",
            "space_id": space.id,
            "conflict": {
                "booking_id": conflict.id,
                "start_time": conflict.start_time.isoformat() if conflict.start_time else None,
                "end_time": conflict.end_time.isoformat() if conflict.end_time else None
            }
        })
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp, 409

    resp = jsonify({
        "available": True,
        "status": "AVAILABLE",
        "space_id": space.id,
        "start_time": st.isoformat(),
        "end_time": et.isoformat()
    })
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp, 200


@api_v1_spaces.route("/api/host/spaces/<int:space_id>/publish", methods=["POST"])
@login_required
def publish_host_space(space_id):
    space = Space.query.get_or_404(space_id)
    if space.owner_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Unauthorized: You do not own this space."}), 403

    # Server-side validation of mandatory fields before activating
    missing_fields = []
    if not space.title or len(space.title.strip()) < 3:
        missing_fields.append("Title (at least 3 characters)")
    if not space.category:
        missing_fields.append("Space Category")
    if not space.price_hourly or space.price_hourly <= 0:
        missing_fields.append("Valid Hourly Rate (> 0)")
    if not space.address and not space.city and not space.location:
        missing_fields.append("Physical Location / Address")
    if not space.photos or len(space.photos) == 0:
        missing_fields.append("At least 1 premise photograph")

    if missing_fields:
        return jsonify({
            "success": False,
            "error": "Listing incomplete. Please configure required fields before publishing.",
            "missing_fields": missing_fields
        }), 400

    space.is_active = True
    space.draft = False
    audit = AuditLog(
        user_id=current_user.id,
        action="space_published",
        details=f"Space #{space.id} '{space.title}' published by host {current_user.name}"
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Space '{space.title}' is now published and accepting bookings!",
        "space": space.to_dict()
    }), 200


@api_v1_spaces.route("/api/host/spaces/<int:space_id>/unpublish", methods=["POST"])
@login_required
def unpublish_host_space(space_id):
    space = Space.query.get_or_404(space_id)
    if space.owner_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Unauthorized: You do not own this space."}), 403

    space.is_active = False
    audit = AuditLog(
        user_id=current_user.id,
        action="space_unpublished",
        details=f"Space #{space.id} '{space.title}' unpublished/paused by host {current_user.name}"
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Space '{space.title}' has been paused and hidden from search.",
        "space": space.to_dict()
    }), 200


@api_v1_spaces.route("/api/host/spaces/<int:space_id>/access-logs", methods=["GET"])
@login_required
def get_space_access_logs(space_id):
    space = Space.query.get_or_404(space_id)
    if space.owner_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Unauthorized: You do not own this space."}), 403

    logs = AccessLog.query.filter_by(space_id=space.id).order_by(AccessLog.created_at.desc()).limit(100).all()
    return jsonify({
        "success": True,
        "space_id": space.id,
        "access_logs": [log.to_dict() for log in logs],
        "count": len(logs)
    }), 200


# =========================================================================
# SPACE INQUIRIES ENDPOINT (Seeker Questions -> Host Dashboard)
# =========================================================================
@api_v1_spaces.route("/api/inquiries", methods=["GET", "POST"])
def api_inquiries():
    """Handles inquiry submissions from space detail page and queries for seeker/host views."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Authentication required to submit or view inquiries."}), 401

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        raw_space_id = data.get("space_id")
        question = sanitize_string(data.get("question", ""), max_length=500).strip()
        if not question:
            return jsonify({"success": False, "error": "Please provide your inquiry question."}), 400

        space = None
        if raw_space_id:
            try:
                space = Space.query.get(int(raw_space_id))
            except Exception:
                space = None

        # Build context-aware automated pre-answer
        ai_ans = ""
        if space:
            q_lower = question.lower()
            if "parking" in q_lower:
                ai_ans = f"Host notes for {space.title}: On-site/street parking available according to building rules."
            elif "wifi" in q_lower or "speed" in q_lower:
                ai_ans = f"{space.title} offers verified high-speed Wi-Fi included in hourly reservation."
            elif "power" in q_lower or "backup" in q_lower or "outlet" in q_lower:
                ai_ans = f"Premise has verified power outlets ({space.ai_power_access or 'standard'})."
            else:
                ai_ans = f"Inquiry forwarded directly to Host ({space.owner.name if space.owner else 'Host Partner'}). They usually respond within 15 minutes."

        inquiry = SpaceInquiry(
            space_id=space.id if space else None,
            user_id=current_user.id,
            question=question,
            ai_answer=ai_ans or "Inquiry dispatched to property host."
        )
        db.session.add(inquiry)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Inquiry sent directly to host!",
            "inquiry": inquiry.to_dict()
        }), 201

    # GET inquiries: inquiries for spaces owned by current host + inquiries asked by current seeker
    owned_spaces = Space.query.filter_by(owner_id=current_user.id).all()
    owned_ids = [s.id for s in owned_spaces]

    query_filter = SpaceInquiry.user_id == current_user.id
    if owned_ids:
        query_filter = db.or_(query_filter, SpaceInquiry.space_id.in_(owned_ids))

    inquiries = SpaceInquiry.query.filter(query_filter).order_by(SpaceInquiry.created_at.desc()).all()
    return jsonify({
        "success": True,
        "inquiries": [i.to_dict() for i in inquiries]
    }), 200


@api_v1_spaces.route("/api/inquiries/<int:inquiry_id>/reply", methods=["POST"])
def api_reply_inquiry(inquiry_id):
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Authentication required."}), 401
    
    inquiry = SpaceInquiry.query.get_or_404(inquiry_id)
    space = Space.query.get(inquiry.space_id)
    if not space or space.owner_id != current_user.id:
        return jsonify({"success": False, "error": "Only the property owner can reply to this inquiry."}), 403

    data = request.get_json(silent=True) or {}
    reply_text = sanitize_string(data.get("reply", ""), max_length=1000)
    if not reply_text:
        return jsonify({"success": False, "error": "Reply text cannot be empty."}), 400

    inquiry.response = reply_text
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Reply saved successfully.",
        "inquiry": inquiry.to_dict()
    }), 200


@api_v1_spaces.route("/api/spaces/search", methods=["GET", "POST"])
@rate_limit_ai
def api_search_spaces_hybrid():
    """
    Lightweight Hybrid Semantic AI Search endpoint.
    Combines:
    - Query understanding (intent & constraint extraction)
    - Deterministic hard filtering (capacity, max price, category, location proximity)
    - Real booking availability validation (checks Booking database records)
    - Vector cosine similarity on dense embeddings
    - Keyword relevance scoring
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form or {}
    else:
        data = request.args.to_dict()

    raw_query = sanitize_string(data.get("query") or data.get("q") or "", max_length=300)
    loc = sanitize_string(data.get("location") or data.get("loc") or data.get("city") or "", max_length=100)
    cat = sanitize_string(data.get("category") or data.get("space_type") or "", max_length=50)
    
    raw_cap = data.get("capacity") or data.get("min_capacity")
    cap = None
    if raw_cap:
        try:
            cap = int(raw_cap)
        except (ValueError, TypeError):
            cap = None

    raw_price = data.get("max_price") or data.get("price")
    price = None
    if raw_price:
        try:
            price = float(raw_price)
        except (ValueError, TypeError):
            price = None

    raw_lat = data.get("lat")
    lat_val = None
    if raw_lat:
        try:
            lat_val = float(raw_lat)
        except (ValueError, TypeError):
            lat_val = None

    raw_lng = data.get("lng")
    lng_val = None
    if raw_lng:
        try:
            lng_val = float(raw_lng)
        except (ValueError, TypeError):
            lng_val = None

    raw_radius = data.get("radius") or data.get("radius_km")
    rad_val = None
    if raw_radius and str(raw_radius).lower() not in ("all", "any", ""):
        try:
            rad_val = float(raw_radius)
        except (ValueError, TypeError):
            rad_val = None

    date_str = sanitize_string(data.get("date") or "", max_length=40) or None
    start_time = sanitize_string(data.get("start_time") or "", max_length=40) or None
    end_time = sanitize_string(data.get("end_time") or "", max_length=40) or None
    
    amenities = data.get("amenities")
    if isinstance(amenities, str):
        amenities = [a.strip() for a in amenities.split(",") if a.strip()]
    elif not isinstance(amenities, list):
        amenities = None

    from backend.modules.search.hybrid_search import hybrid_search_spaces
    result = hybrid_search_spaces(
        raw_query=raw_query,
        location=loc or None,
        category=cat or None,
        min_capacity=cap,
        max_price=price,
        lat=lat_val,
        lng=lng_val,
        radius_km=rad_val,
        date=date_str,
        start_time=start_time,
        end_time=end_time,
        amenities=amenities,
        current_user_id=current_user.id if current_user.is_authenticated else None,
        limit=30
    )
    return jsonify(result), 200


@api_v1_spaces.route("/api/spaces/ai-match", methods=["POST"])
@rate_limit_ai
def ai_match_spaces():
    """
    Natural Language AI matchmaking endpoint.
    Powered by the SpaceLoop Hybrid Semantic Search Engine.
    Preserves 100% backward compatibility for all SpaceLoop clients and test suites.
    """
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

    lat_val = None
    if raw_lat:
        try:
            lat_val = float(raw_lat)
        except (ValueError, TypeError):
            lat_val = None

    lng_val = None
    if raw_lng:
        try:
            lng_val = float(raw_lng)
        except (ValueError, TypeError):
            lng_val = None

    from backend.modules.search.hybrid_search import hybrid_search_spaces
    search_res = hybrid_search_spaces(
        raw_query=query_text,
        location=loc or None,
        lat=lat_val,
        lng=lng_val,
        radius_km=radius_km,
        current_user_id=current_user.id if current_user.is_authenticated else None,
        limit=30
    )

    for r in search_res.get("results", []):
        if "match_score" not in r:
            r["match_score"] = round(r.get("composite_score", 0.95) * 100)

    return jsonify(search_res), 200


# =========================================================================
# REVIEWS ENDPOINTS (Verified Stay Reviews + Trust & Safety Protection)
# =========================================================================
@api_v1_spaces.route("/api/spaces/<int:space_id>/reviews", methods=["GET"])
def get_space_reviews(space_id):
    """Returns verified reviews for a specific physical space."""
    etag = space_cache.generate_etag(f"reviews_{space_id}")
    conditional_resp = space_cache.check_etag_and_respond(etag)
    if conditional_resp:
        return conditional_resp

    cache_key = f"space_reviews:{space_id}"
    cached_resp = space_cache.get_cached_response(cache_key, etag)
    if cached_resp:
        return cached_resp

    space = Space.query.get_or_404(space_id)
    reviews = Review.query.filter_by(space_id=space.id).order_by(Review.created_at.desc()).all()
    payload = {
        "success": True,
        "space_id": space.id,
        "reviews": [r.to_dict() for r in reviews],
        "count": len(reviews),
        "average_rating": space.average_rating()
    }
    return space_cache.cache_and_respond(cache_key, etag, payload)


@api_v1_spaces.route("/api/spaces/<int:space_id>/reviews", methods=["POST"])
@login_required
def create_space_review(space_id):
    """
    Submits a review for a physical space.
    Strictly gated by Trust & Safety (requires verified completed stay, blocks duplication and collusion).
    """
    space = Space.query.get_or_404(space_id)
    data = request.get_json(silent=True) or {}

    rating = int(validate_numeric(data.get("rating"), min_val=1, max_val=5, default=5))
    comment = sanitize_string(data.get("comment", ""), max_length=1500)
    if not comment or len(comment.strip()) < 3:
        return jsonify({"error": "Review comment must be at least 3 characters long."}), 400

    booking_id = validate_numeric(data.get("booking_id"), min_val=1, default=None)
    booking = None
    if booking_id:
        booking = Booking.query.get(int(booking_id))
    else:
        # Auto-lookup latest completed stay for current_user at this space
        booking = Booking.query.filter(
            Booking.space_id == space.id,
            Booking.renter_id == current_user.id,
            Booking.session_state == "checked_out"
        ).order_by(Booking.departure_time.desc()).first()

    # Evaluate review with Trust & Safety Engine
    from backend.modules.trust_safety import TrustSafetyEngine
    assessment = TrustSafetyEngine.evaluate_review(
        reviewer=current_user,
        space=space,
        booking=booking,
        rating=rating,
        comment=comment
    )

    if assessment.recommended_action == "restrict_action":
        return jsonify({
            "error": "Review Restricted",
            "message": f"Trust & Safety alert: {assessment.evidence_text}",
            "risk_level": assessment.risk_level,
            "risk_score": assessment.risk_score,
            "assessment_id": assessment.id,
            "recommended_action": assessment.recommended_action
        }), 403

    new_review = Review(
        space_id=space.id,
        user_id=current_user.id,
        booking_id=booking.id if booking else None,
        user_name=current_user.name or "Verified Guest",
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()
    space_cache.bump_catalog_version(space.id)

    return jsonify({
        "success": True,
        "message": "Review submitted successfully!",
        "review": new_review.to_dict(),
        "trust_safety": {
            "risk_level": assessment.risk_level,
            "confidence": assessment.confidence
        }
    }), 201

