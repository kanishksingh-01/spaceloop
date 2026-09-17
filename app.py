import os
import re
from datetime import datetime, timedelta, timezone
import math
import sqlite3
import uuid
import secrets
import hashlib

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf

from config import Config
from models import db, User, Space, Booking, Review, SpaceInquiry, AuditLog
from backend.app.extensions import login_manager, csrf, limiter
from backend.app.api.v1.auth import api_v1_auth
from backend.modules.auth import (
    Permission,
    authorize,
    UnauthorizedError,
    ForbiddenError,
    permission_required,
    admin_required,
    AuthService,
    get_active_context,
    set_active_context,
    record_audit
)
from security import (
    apply_security_headers,
    rate_limit_ai,
    sanitize_string,
    sanitize_input,
    wrap_untrusted_notes,
    clamp_financial_bounds,
    validate_numeric,
    validate_image_url
)
from pricing import (
    calculate_dynamic_rate,
    calculate_host_monthly_yield,
    calculate_student_savings
)
from space_ai import (
    analyze_space_features,
    match_spaces_with_ai,
    generate_micro_lease,
    calculate_earnings_estimate,
    concierge_chat,
    verify_aadhaar_otp,
    verify_academic_credentials,
    verify_host_electricity_bill,
    verify_upi_penny_drop,
    evaluate_room_condition_delta,
    calculate_session_punctuality,
    compute_objective_trust_index,
    set_simulate_ai_failure,
    is_simulate_ai_failure,
    get_system_connectivity_status
)
from seed_data import seed_database


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between two GPS coordinates in meters using the Haversine formula."""
    try:
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 1)
    except Exception:
        return 999999.0


KNOWN_HUBS = {
    "wagholi, pune": (18.5793, 73.9822),
    "wagholi pune": (18.5793, 73.9822),
    "jspm wagholi": (18.5793, 73.9822),
    "jspm campus": (18.5793, 73.9822),
    "jspm": (18.5793, 73.9822),
    "wagholi": (18.5793, 73.9822),
    "shivajinagar, pune": (18.5204, 73.8567),
    "shivajinagar": (18.5204, 73.8567),
    "fc road": (18.5204, 73.8567),
    "fergusson college": (18.5204, 73.8567),
    "pune university": (18.5529, 73.8260),
    "pune": (18.5204, 73.8567),
    "hauz khas, new delhi": (28.5450, 77.1926),
    "hauz khas, delhi": (28.5450, 77.1926),
    "hauz khas": (28.5450, 77.1926),
    "iit delhi": (28.5450, 77.1926),
    "north campus, new delhi": (28.6900, 77.2100),
    "north campus": (28.6900, 77.2100),
    "delhi university": (28.6900, 77.2100),
    "connaught place": (28.6315, 77.2167),
    "delhi": (28.5450, 77.1926),
    "new delhi": (28.5450, 77.1926),
    "sector 62, noida": (28.6270, 77.3725),
    "sector 62": (28.6270, 77.3725),
    "noida": (28.6270, 77.3725),
    "koramangala, bangalore": (12.9352, 77.6245),
    "koramangala, bengaluru": (12.9352, 77.6245),
    "koramangala": (12.9352, 77.6245),
    "indiranagar": (12.9784, 77.6408),
    "bangalore": (12.9352, 77.6245),
    "bengaluru": (12.9352, 77.6245),
    "powai, mumbai": (19.1334, 72.9133),
    "powai": (19.1334, 72.9133),
    "iit bombay": (19.1334, 72.9133),
    "mumbai": (19.1334, 72.9133)
}


def resolve_location_coordinates(loc_name="", lat=None, lng=None):
    """
    Resolves human location name or GPS coordinates into (lat, lng, display_name).
    Prioritizes specific locality names (e.g. Wagholi, Hauz Khas) over generic metro names.
    """
    if lat is not None and lng is not None:
        try:
            fl_lat = float(lat)
            fl_lng = float(lng)
            if -90.0 <= fl_lat <= 90.0 and -180.0 <= fl_lng <= 180.0:
                name = loc_name or "Current GPS Location"
                return fl_lat, fl_lng, name
        except (ValueError, TypeError):
            pass

    if loc_name:
        clean = loc_name.strip()
        if "," in clean:
            parts = clean.split(",")
            if len(parts) == 2:
                try:
                    fl_lat = float(parts[0].strip())
                    fl_lng = float(parts[1].strip())
                    if -90.0 <= fl_lat <= 90.0 and -180.0 <= fl_lng <= 180.0:
                        return fl_lat, fl_lng, f"{round(fl_lat, 3)}, {round(fl_lng, 3)}"
                except (ValueError, TypeError):
                    pass

        clean_lower = clean.lower()
        # Sort keys descending by length so specific localities match before broad city names
        for hub_key, coords in sorted(KNOWN_HUBS.items(), key=lambda x: len(x[0]), reverse=True):
            if hub_key in clean_lower:
                display_name = clean
                if "wagholi" in hub_key:
                    display_name = "Wagholi, Pune"
                elif "shivajinagar" in hub_key or "fc road" in hub_key:
                    display_name = "Shivajinagar, Pune"
                elif "hauz khas" in hub_key or "iit delhi" in hub_key:
                    display_name = "Hauz Khas, New Delhi"
                elif "koramangala" in hub_key:
                    display_name = "Koramangala, Bengaluru"
                elif "powai" in hub_key or "iit bombay" in hub_key:
                    display_name = "Powai, Mumbai"
                elif "north campus" in hub_key:
                    display_name = "North Campus, New Delhi"
                elif "sector 62" in hub_key:
                    display_name = "Sector 62, Noida"
                else:
                    display_name = hub_key.title()
                return coords[0], coords[1], display_name

    return None, None, ""


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Ensure upload directory exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/uploads"), exist_ok=True)

    # Database Initialization & Schema Auto-Migration
    db.init_app(app)

    try:
        raw_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite" in raw_url:
            db_path = raw_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(users)")
                cols = {r[1]: r for r in cur.fetchall()}
                new_cols = [
                    ("public_id", "VARCHAR(36)"),
                    ("first_name", "VARCHAR(60) DEFAULT ''"),
                    ("last_name", "VARCHAR(60) DEFAULT ''"),
                    ("is_active", "BOOLEAN DEFAULT 1"),
                    ("is_email_verified", "BOOLEAN DEFAULT 0"),
                    ("is_admin", "BOOLEAN DEFAULT 0"),
                    ("last_login_at", "DATETIME")
                ]
                for col, col_type in new_cols:
                    if col not in cols:
                        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                cur.execute("SELECT id, name, public_id FROM users")
                for uid, name, pub_id in cur.fetchall():
                    if not pub_id:
                        parts = (name or "").strip().split(" ", 1)
                        cur.execute("UPDATE users SET public_id = ?, first_name = ?, last_name = ? WHERE id = ?",
                                    (str(uuid.uuid4()), parts[0], parts[1] if len(parts) > 1 else "", uid))
                conn.commit()
                conn.close()
    except Exception as e:
        print(f"[DB_MIGRATION_NOTICE] {e}")

    with app.app_context():
        db.create_all()
        seed_database()

    # Flask-Login Configuration
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required", "authenticated": False}), 401
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("auth_login", next=request.url))

    # Flask-WTF CSRF Protection
    csrf.init_app(app)
    # Exempt REST API endpoints from web CSRF check (secured via session/tokens)
    csrf.exempt(api_v1_auth)

    # Flask-Limiter Rate Limiting
    limiter.init_app(app)

    # Register Blueprints
    app.register_blueprint(api_v1_auth)

    @app.after_request
    def security_headers(response):
        return apply_security_headers(response)

    # Context processor injecting session context and CSRF token
    @app.context_processor
    def inject_context():
        sim = session.get("simulate_ai_failure", False)
        sys_status = get_system_connectivity_status(simulate_override=sim)
        ctx = get_active_context(current_user)
        return {
            "system_status": sys_status,
            "active_context": ctx,
            "is_host_context": ctx == "host",
            "csrf_token": generate_csrf
        }

    # ==========================================
    # HTML View Routes
    # ==========================================

    @app.route("/")
    def index():
        """
        Public landing page. Accessible without authentication.
        If user explicitly searches with parameters or query, renders exploration catalog.
        """
        if (
            request.args.get("explore")
            or request.args.get("q")
            or request.args.get("category")
            or request.args.get("loc")
            or request.args.get("lat")
            or request.args.get("lng")
            or request.args.get("radius")
            or request.args.get("max_price")
        ):
            return explore_page()

        # Represent diverse cities across India (Pune, Delhi NCR, Bengaluru, Mumbai)
        all_active = Space.query.filter_by(is_active=True).all()
        pune_spaces = [s for s in all_active if (s.city and "pune" in s.city.lower()) or (s.neighborhood and "wagholi" in s.neighborhood.lower())]
        delhi_spaces = [s for s in all_active if (s.city and "delhi" in s.city.lower())]
        blr_spaces = [s for s in all_active if (s.city and ("bangalore" in s.city.lower() or "bengaluru" in s.city.lower()))]
        mumbai_spaces = [s for s in all_active if (s.city and "mumbai" in s.city.lower())]

        featured = []
        if pune_spaces:
            featured.extend(pune_spaces[:2])
        if delhi_spaces:
            featured.extend(delhi_spaces[:2])
        if blr_spaces:
            featured.extend(blr_spaces[:1])
        if mumbai_spaces:
            featured.extend(mumbai_spaces[:1])

        for s in all_active:
            if len(featured) >= 6:
                break
            if s not in featured:
                featured.append(s)

        return render_template("landing.html", spaces=[s.to_dict() for s in featured])

    @app.route("/explore")
    def explore_page():
        """
        Full marketplace exploration view with category and AI search.
        """
        category = sanitize_string(request.args.get("category", ""), max_length=50)
        q = sanitize_string(request.args.get("q", ""), max_length=150)
        loc = sanitize_string(request.args.get("loc", ""), max_length=100)
        raw_lat = request.args.get("lat")
        raw_lng = request.args.get("lng")
        raw_radius = request.args.get("radius")
        raw_max_price = request.args.get("max_price")

        radius_km = None
        if raw_radius and raw_radius != "All":
            try:
                radius_km = float(raw_radius)
            except (ValueError, TypeError):
                radius_km = None

        max_price = None
        if raw_max_price:
            try:
                max_price = float(raw_max_price)
            except (ValueError, TypeError):
                max_price = None

        lat, lng, resolved_loc_name = resolve_location_coordinates(loc, raw_lat, raw_lng)
        if (lat is None or lng is None) and q:
            q_lat, q_lng, q_loc_name = resolve_location_coordinates(q)
            if q_lat is not None and q_lng is not None:
                lat, lng = q_lat, q_lng
                if not active_location:
                    active_location = q_loc_name

        query = Space.query.filter_by(is_active=True)
        if category and category != "All":
            query = query.filter(Space.category == category)
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
            elif loc:
                # Text fallback when coordinates are not available
                clean_l = loc.strip().lower()
                text_blob = f"{s.neighborhood or ''} {s.city or ''} {s.state or ''} {s.address or ''} {s.title or ''}".lower()
                tokens = [t for t in clean_l.replace(",", " ").split() if len(t) > 2]
                if tokens and not any(t in text_blob for t in tokens):
                    continue
            spaces_data.append(s_dict)

        if lat is not None and lng is not None:
            spaces_data.sort(key=lambda x: x.get("distance_km", 999999))
        elif loc:
            clean_l = loc.strip().lower()
            def text_priority(item):
                blob = f"{item.get('neighborhood', '')} {item.get('city', '')}".lower()
                return 0 if any(t in blob for t in clean_l.split()) else 1
            spaces_data.sort(key=text_priority)

        categories = ["All", "Studio", "Storage", "Parking", "Pop-up/Retail", "Event/Workshop"]
        return render_template(
            "explore.html",
            spaces=spaces_data,
            categories=categories,
            active_category=category or "All",
            search_query=q,
            active_location=resolved_loc_name or loc,
            active_lat=lat,
            active_lng=lng,
            active_radius=radius_km,
            active_max_price=max_price
        )

    @app.route("/space/<int:space_id>")
    def space_detail(space_id):
        space = Space.query.get_or_404(space_id)
        reviews = [r.to_dict() for r in space.reviews]
        return render_template("space_detail.html", space=space.to_dict(), reviews=reviews)

    @app.route("/list-space")
    @login_required
    def list_space_page():
        edit_id = request.args.get("edit")
        edit_space = None
        if edit_id:
            try:
                sp = Space.query.get(int(edit_id))
                if sp:
                    authorize(current_user, Permission.SPACE_UPDATE, resource=sp)
                    edit_space = sp.to_dict()
            except (ForbiddenError, UnauthorizedError) as e:
                flash(str(e), "danger")
                return redirect(url_for("dashboard_page"))
            except Exception:
                edit_space = None
        return render_template("list_space.html", edit_space=edit_space)

    @app.route("/calculator")
    def calculator_page():
        category = sanitize_string(request.args.get("category", "Studio"), max_length=50)
        rate = request.args.get("rate")
        days = request.args.get("days", 12)
        hours = request.args.get("hours", 4)
        fee = request.args.get("fee", 15)

        try:
            rate_val = float(rate) if rate else None
        except (ValueError, TypeError):
            rate_val = None

        default_calc = calculate_earnings_estimate(
            category=category,
            sqft=300,
            days_per_month=days,
            hourly_rate=rate_val,
            hours_per_day=hours,
            platform_fee_percent=fee
        )

        user_spaces = []
        if current_user.is_authenticated:
            user_spaces = [s.to_dict() for s in Space.query.filter_by(owner_id=current_user.id).all()]
        if not user_spaces:
            user_spaces = [s.to_dict() for s in Space.query.limit(4).all()]

        return render_template("calculator.html", initial_data=default_calc, host_spaces=user_spaces)

    @app.route("/dashboard")
    @login_required
    def dashboard_page():
        active_user_id = current_user.id

        seeker_bookings = Booking.query.filter_by(renter_id=active_user_id).order_by(Booking.created_at.desc()).all()
        host_spaces = Space.query.filter_by(owner_id=active_user_id).order_by(Space.created_at.desc()).all()
        host_bookings = Booking.query.join(Space).filter(Space.owner_id == active_user_id).order_by(Booking.created_at.desc()).all()
        
        gross_revenue = sum(b.total_price for b in host_bookings if b.status in ['confirmed', 'completed'])
        platform_fee = round(gross_revenue * 0.15)
        net_earnings = gross_revenue - platform_fee
        total_hours_hosted = sum(b.hours_booked for b in host_bookings if b.status in ['confirmed', 'completed'])
        active_spaces_count = len([s for s in host_spaces if s.is_active])
        upcoming_host_bookings = [b for b in host_bookings if b.status == 'confirmed']
        completed_host_bookings = [b for b in host_bookings if b.status == 'completed']

        host_metrics = {
            "gross_revenue": int(round(gross_revenue)),
            "platform_fee": int(round(platform_fee)),
            "net_earnings": int(round(net_earnings)),
            "total_hours": round(total_hours_hosted, 1),
            "total_bookings": len(host_bookings),
            "active_spaces_count": active_spaces_count,
            "total_spaces_count": len(host_spaces),
            "upcoming_count": len(upcoming_host_bookings),
            "completed_count": len(completed_host_bookings),
            "payout_vpa": current_user.upi_vpa_masked if current_user.upi_vpa_masked else "upi***@okbank"
        }

        all_owner_spaces = Space.query.order_by(Space.created_at.desc()).limit(3).all()

        return render_template(
            "dashboard.html",
            bookings=[b.to_dict() for b in seeker_bookings],
            host_bookings=[b.to_dict() for b in host_bookings],
            my_spaces=[s.to_dict() for s in host_spaces],
            demo_spaces=[s.to_dict() for s in all_owner_spaces],
            host_metrics=host_metrics,
            user=current_user.to_dict()
        )

    @app.route("/how-it-works")
    def how_it_works():
        return render_template("how_it_works.html")

    # ==========================================
    # Authentication & Session Routes
    # ==========================================

    def is_safe_redirect_url(target: str) -> bool:
        if not target or not isinstance(target, str):
            return False
        if target.startswith("//") or target.startswith("/\\") or target.startswith("\\"):
            return False
        from urllib.parse import urlparse
        parsed = urlparse(target)
        return not parsed.scheme and not parsed.netloc and target.startswith("/")

    @app.route("/login")
    def login_redirect():
        return redirect(url_for("auth_login"))

    @app.route("/auth/login", methods=["GET", "POST"])
    @limiter.limit(Config.AUTH_LOGIN_RATE_LIMIT)
    def auth_login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard_page"))

        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            remember = bool(request.form.get("remember_me"))

            user, error = AuthService.authenticate_user(email, password)
            if not user:
                flash(error, "danger")
                return render_template("auth/login.html"), 401

            session.clear()
            login_user(user, remember=remember)
            set_active_context(user, "host" if user.role == "owner" else "seeker")
            flash(f"Welcome back, {user.first_name or user.name}!", "success")

            next_url = request.args.get("next")
            if next_url and is_safe_redirect_url(next_url):
                return redirect(next_url)
            return redirect(url_for("dashboard_page"))

        return render_template("auth/login.html")

    @app.route("/auth/register", methods=["GET", "POST"])
    @limiter.limit(Config.AUTH_REGISTER_RATE_LIMIT)
    def auth_register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard_page"))

        if request.method == "POST":
            first_name = request.form.get("first_name", "")
            last_name = request.form.get("last_name", "")
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            role = request.form.get("role", "seeker")
            terms = request.form.get("terms")

            if not terms:
                flash("You must accept the Terms of Service to register.", "warning")
                return render_template("auth/register.html"), 400

            user, raw_token, error = AuthService.register_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                confirm_password=confirm_password,
                role=role
            )
            if not user:
                flash(error, "danger")
                return render_template("auth/register.html"), 400

            session.clear()
            login_user(user)
            set_active_context(user, "host" if user.role == "owner" else "seeker")
            flash("Account created successfully! Welcome to SpaceLoop.", "success")

            next_url = request.args.get("next")
            if next_url and is_safe_redirect_url(next_url):
                return redirect(next_url)
            return redirect(url_for("dashboard_page"))

        return render_template("auth/register.html")

    @app.route("/auth/logout", methods=["GET", "POST"])
    def auth_logout():
        if current_user.is_authenticated:
            uid = current_user.id
            logout_user()
            session.clear()
            record_audit("AUTH_LOGOUT", user_id=uid)
        flash("You have been signed out successfully.", "success")
        return redirect(url_for("index"))

    @app.route("/auth/demo-switch/<role>")
    def auth_demo_switch(role):
        role_clean = (role or "").strip().lower()
        target_email = None
        persona_name = ""

        if role_clean in ["seeker", "student", "aarav"]:
            target_email = "aarav@iitd.ac.in"
            persona_name = "Student Seeker (Aarav Sharma)"
        elif role_clean in ["host", "sunita"]:
            target_email = "sunita@spaceloop.in"
            persona_name = "Verified Host (Sunita Deshmukh)"
        elif role_clean in ["admin"]:
            target_email = "admin@spaceloop.in"
            persona_name = "Platform Administrator"
        elif role_clean in ["logout", "guest"]:
            if current_user.is_authenticated:
                uid = current_user.id
                logout_user()
                session.clear()
                record_audit("AUTH_LOGOUT", user_id=uid)
            flash("Switched to Guest Mode (signed out).", "info")
            return redirect(request.referrer or url_for("index"))
        else:
            flash(f"Unknown demo persona '{role}'.", "warning")
            return redirect(request.referrer or url_for("index"))

        user = User.query.filter_by(email=target_email).first()
        if not user:
            flash(f"Demo user '{target_email}' not found in database.", "danger")
            return redirect(request.referrer or url_for("index"))

        session.clear()
        login_user(user, remember=True)
        session.permanent = True
        record_audit("DEMO_SWITCH_LOGIN", user_id=user.id, details=f"Switched to {persona_name}")
        flash(f"⚡ Testing as {persona_name}! Active session enabled.", "success")

        referrer = request.referrer or ""
        if "/auth/" in referrer or not referrer:
            if role_clean == "host":
                return redirect(url_for("dashboard_page"))
            return redirect(url_for("explore_page"))
        return redirect(referrer)

    @app.route("/auth/forgot-password", methods=["GET", "POST"])
    @limiter.limit(Config.AUTH_PASSWORD_RESET_RATE_LIMIT)
    def auth_forgot_password():
        if request.method == "POST":
            email = request.form.get("email", "")
            _, msg, _ = AuthService.request_password_reset(email)
            flash(msg, "info")
            return redirect(url_for("auth_login"))
        return render_template("auth/forgot_password.html")

    @app.route("/auth/reset-password/<token>", methods=["GET", "POST"])
    def auth_reset_password(token):
        if request.method == "POST":
            new_pw = request.form.get("password", "")
            confirm_pw = request.form.get("confirm_password", "")
            success, msg = AuthService.reset_password(token, new_pw, confirm_pw)
            if not success:
                flash(msg, "danger")
                return render_template("auth/reset_password.html", token=token), 400
            flash(msg, "success")
            return redirect(url_for("auth_login"))
        return render_template("auth/reset_password.html", token=token)

    @app.route("/auth/verify-email/<token>")
    def auth_verify_email(token):
        success, msg = AuthService.verify_email(token)
        return render_template("auth/verify_email.html", success=success, message=msg)

    @app.route("/auth/access-denied")
    def auth_access_denied():
        return render_template("auth/access_denied.html"), 403

    @app.route("/verify")
    @login_required
    def verify_page():
        return render_template("verify.html", user=current_user.to_dict())

    @app.route("/booking/<int:booking_id>/session")
    @app.route("/session/<int:booking_id>")
    @login_required
    def session_page(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        try:
            authorize(current_user, Permission.BOOKING_VIEW, resource=booking)
        except ForbiddenError as e:
            flash(str(e), "danger")
            return redirect(url_for("auth_access_denied"))

        space = booking.space
        return render_template("session.html", booking=booking.to_dict(), space=space.to_dict())

    @app.route("/space/<int:space_id>/printable-qr")
    @login_required
    def printable_qr(space_id):
        space = Space.query.get_or_404(space_id)
        has_booking = Booking.query.filter(
            Booking.space_id == space.id,
            Booking.renter_id == current_user.id,
            Booking.status != "cancelled"
        ).first()
        is_owner = (current_user.id == space.owner_id)
        is_admin = getattr(current_user, "is_admin", False)
        if not is_owner and not has_booking and not is_admin:
            flash("You do not have permission to view this printable door pass.", "danger")
            return redirect(url_for("auth_access_denied"))
        return render_template("printable_qr.html", space=space.to_dict())

    @app.route("/profile")
    @login_required
    def profile_page():
        return render_template("profile.html", user=current_user.to_dict())

    @app.route("/inquiries")
    @login_required
    def inquiries_page():
        inquiries = SpaceInquiry.query.filter(
            db.or_(
                SpaceInquiry.user_id == current_user.id,
                SpaceInquiry.space_id.in_(
                    db.session.query(Space.id).filter(Space.owner_id == current_user.id)
                )
            )
        ).order_by(SpaceInquiry.created_at.desc()).all()

        if not inquiries:
            demo_space = Space.query.first()
            if demo_space:
                q1 = SpaceInquiry(
                    space_id=demo_space.id,
                    user_id=current_user.id,
                    question="Is high-speed WiFi available for video conferencing?",
                    ai_answer="Yes! This space features 300 Mbps fiber optical internet, 6 power sockets, and quiet acoustic dampening."
                )
                db.session.add(q1)
                db.session.commit()
                inquiries = [q1]

        spaces = Space.query.filter_by(is_active=True).all()
        return render_template("inquiries.html", inquiries=inquiries, spaces=spaces, user=current_user.to_dict())

    @app.route("/session")
    @login_required
    def active_session_redirect():
        latest_booking = Booking.query.filter_by(renter_id=current_user.id).order_by(Booking.created_at.desc()).first()
        if latest_booking:
            return redirect(url_for("session_page", booking_id=latest_booking.id))
        flash("You do not have any active or previous sessions.", "info")
        return redirect(url_for("dashboard_page"))

    @app.route("/switch-role", methods=["GET", "POST"])
    @login_required
    def switch_role():
        """
        Toggles UI viewing context between Host and Seeker modes.
        Identity (current_user.id) remains unchanged.
        """
        target_role = request.args.get("role") or request.form.get("role")
        if not target_role:
            target_role = "seeker" if get_active_context(current_user) == "host" else "host"

        set_active_context(current_user, target_role)
        flash(f"Switched to {target_role.title()} mode.", "info")
        return redirect(request.referrer or url_for("dashboard_page"))

    # ==========================================
    # REST API Endpoints
    # ==========================================

    @app.route("/api/spaces", methods=["GET"])
    def get_spaces():
        category = sanitize_string(request.args.get("category"), max_length=50)
        q = sanitize_string(request.args.get("q", ""), max_length=200)
        loc = sanitize_string(request.args.get("loc", ""), max_length=100)
        raw_lat = request.args.get("lat")
        raw_lng = request.args.get("lng")
        raw_radius = request.args.get("radius")
        raw_max_price = request.args.get("max_price")

        radius_km = None
        if raw_radius and raw_radius != "All":
            try:
                radius_km = float(raw_radius)
            except (ValueError, TypeError):
                radius_km = None

        max_price = None
        if raw_max_price:
            try:
                max_price = float(raw_max_price)
            except (ValueError, TypeError):
                max_price = None

        lat, lng, resolved_loc_name = resolve_location_coordinates(loc, raw_lat, raw_lng)
        if (lat is None or lng is None) and q:
            q_lat, q_lng, q_loc_name = resolve_location_coordinates(q)
            if q_lat is not None and q_lng is not None:
                lat, lng = q_lat, q_lng

        query = Space.query.filter_by(is_active=True)
        if category and category != "All":
            query = query.filter(Space.category == category)
        if max_price is not None:
            query = query.filter(Space.price_hourly <= max_price)
        if q:
            query = query.filter(
                (Space.title.ilike(f"%{q}%")) |
                (Space.neighborhood.ilike(f"%{q}%")) |
                (Space.city.ilike(f"%{q}%")) |
                (Space.address.ilike(f"%{q}%")) |
                (Space.description.ilike(f"%{q}%"))
            )

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
            elif loc:
                clean_l = loc.strip().lower()
                text_blob = f"{s.neighborhood or ''} {s.city or ''} {s.state or ''} {s.address or ''} {s.title or ''}".lower()
                tokens = [t for t in clean_l.replace(",", " ").split() if len(t) > 2]
                if tokens and not any(t in text_blob for t in tokens):
                    continue
            spaces_data.append(s_dict)

        if lat is not None and lng is not None:
            spaces_data.sort(key=lambda x: x.get("distance_km", 999999))
        elif loc:
            clean_l = loc.strip().lower()
            def text_priority(item):
                blob = f"{item.get('neighborhood', '')} {item.get('city', '')}".lower()
                return 0 if any(t in blob for t in clean_l.split()) else 1
            spaces_data.sort(key=text_priority)

        return jsonify(spaces_data)

    @app.route("/api/spaces/<int:space_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
    def api_space_detail_or_manage(space_id):
        space = Space.query.get_or_404(space_id)

        if request.method in ["PUT", "PATCH"]:
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required", "authenticated": False}), 401
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
            return jsonify({"success": True, "message": f"Space '{space.title}' updated successfully!", "space": space.to_dict()}), 200

        if request.method == "DELETE":
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required", "authenticated": False}), 401
            try:
                authorize(current_user, Permission.SPACE_DELETE, resource=space)
            except ForbiddenError as e:
                return jsonify({"error": str(e)}), 403

            db.session.delete(space)
            db.session.commit()
            return jsonify({"success": True, "message": f"Space #{space_id} deleted successfully."}), 200

        # GET method
        if not space.is_active:
            is_authorized_viewer = current_user.is_authenticated and (current_user.id == space.owner_id or getattr(current_user, "is_admin", False))
            if not is_authorized_viewer:
                return jsonify({"error": "Space listing is unavailable or has been paused by the host."}), 404

        return jsonify(space.to_dict(include_access_secrets=False))

    @app.route("/api/spaces/ai-scan", methods=["POST"])
    @rate_limit_ai
    def ai_scan_space():
        """
        AI Space Inspector: Evaluates room photo URL and description
        to generate dimensions, lighting, noise, and recommended hourly rates.
        """
        data = request.get_json(silent=True) or {}
        image_url = sanitize_string(data.get("photo_url", ""), max_length=500)
        if image_url and not validate_image_url(image_url):
            image_url = ""

        analysis = analyze_space_features(data, image_url)
        return jsonify(analysis)

    @app.route("/api/spaces", methods=["POST"])
    @login_required
    def create_space():
        """Creates a new space listing bound to the authenticated host."""
        try:
            authorize(current_user, Permission.SPACE_CREATE)
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403

        data = request.get_json(silent=True) or {}
        
        title = sanitize_string(data.get("title"), max_length=150)
        category = sanitize_string(data.get("category", "Studio"), max_length=50)
        address = sanitize_string(data.get("address"), max_length=200)
        neighborhood = sanitize_string(data.get("neighborhood", "Downtown"), max_length=100)
        city = sanitize_string(data.get("city", "Bengaluru"), max_length=100)
        state = sanitize_string(data.get("state", "KA"), max_length=50)
        zip_code = sanitize_string(data.get("zip_code", "560034"), max_length=20)
        description = sanitize_string(data.get("description", "A verified temporary space."), max_length=3000)

        price_hourly = validate_numeric(data.get("price_hourly"), min_val=5.0, max_val=5000.0, default=None)
        price_daily = validate_numeric(data.get("price_daily"), min_val=20.0, max_val=25000.0, default=None)
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

        raw_amenities = data.get("amenities") or ["Wi-Fi", "Power Outlets", "Restroom Access"]
        new_space.amenities = [sanitize_string(a, max_length=80) for a in raw_amenities if isinstance(a, str)][:15]

        raw_rules = data.get("rules") or ["No smoking", "Clean up after use", "Respect neighbors"]
        new_space.rules = [sanitize_string(r, max_length=150) for r in raw_rules if isinstance(r, str)][:10]

        new_space.photos = clean_photos[:6]
        new_space.ai_tags = ["Verified Space", "Instant Booking"]

        db.session.add(new_space)
        db.session.commit()
        return jsonify(new_space.to_dict()), 201

    @app.route("/api/spaces/<int:space_id>/edit", methods=["POST"])
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

    @app.route("/api/spaces/<int:space_id>/toggle-status", methods=["POST"])
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

    @app.route("/api/spaces/ai-match", methods=["POST"])
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
        if (lat is None or lng is None) and query_text:
            q_lat, q_lng, q_loc_name = resolve_location_coordinates(query_text)
            if q_lat is not None and q_lng is not None:
                lat, lng = q_lat, q_lng
                if not resolved_loc_name:
                    resolved_loc_name = q_loc_name

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

        for r in ranked:
            sp = r.get("space", {})
            if "distance_km" in sp:
                r["distance_km"] = sp["distance_km"]

        return jsonify({
            "results": ranked,
            "query": query_text,
            "location": resolved_loc_name or loc,
            "radius_km": radius_km,
            "total_matches": len(ranked)
        })

    @app.route("/api/bookings/precheck", methods=["POST"])
    def precheck_booking():
        data = request.get_json(silent=True) or {}
        space_id_num = validate_numeric(data.get("space_id"), min_val=1, max_val=10000000, default=None)
        if not space_id_num:
            return jsonify({"available": False, "error": "Invalid space ID."}), 400

        space = Space.query.get(int(space_id_num))
        if not space:
            return jsonify({"available": False, "error": "Space not found."}), 404
        if not space.is_active:
            return jsonify({
                "available": False, 
                "error": "This space is currently paused by the host and not accepting bookings."
            }), 400

        hours = validate_numeric(data.get("hours"), min_val=0.5, max_val=168.0, default=2.0)
        max_cap = space.max_capacity if space.max_capacity and space.max_capacity > 0 else 50
        attendees = int(validate_numeric(data.get("attendees_count"), min_val=1, max_val=1000, default=1))
        
        if attendees > max_cap:
            return jsonify({
                "available": False, 
                "error": f"Requested attendees ({attendees}) exceeds maximum space capacity of {max_cap}."
            }), 400

        subtotal = round(float(hours) * space.price_hourly, 2)
        platform_fee = round(subtotal * 0.05, 2)
        escrow_deposit = 100.0
        total_payable = round(subtotal + platform_fee + escrow_deposit, 2)

        return jsonify({
            "available": True,
            "space_id": space.id,
            "space_title": space.title,
            "max_capacity": max_cap,
            "attendees_count": attendees,
            "hours": hours,
            "hourly_rate": space.price_hourly,
            "subtotal": subtotal,
            "platform_fee": platform_fee,
            "escrow_deposit": escrow_deposit,
            "total_payable": total_payable,
            "premise_verified": bool(space.discom_ca_number or (space.owner and space.owner.is_host_verified)),
            "discom_provider": (space.owner.discom_provider if space.owner else "") or "Electricity Discom Match",
            "host_trust_score": round(space.owner.objective_trust_score, 1) if space.owner else 98.5,
            "message": "Availability and premise conditions verified."
        }), 200

    @app.route("/api/bookings", methods=["POST"])
    def create_booking():
        """Instant booking bound to the current authenticated seeker."""
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required", "authenticated": False}), 401

        renter = current_user
        try:
            authorize(current_user, Permission.BOOKING_CREATE)
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403

        data = request.get_json(silent=True) or {}
        space_id_num = validate_numeric(data.get("space_id"), min_val=1, max_val=10000000, default=None)
        if not space_id_num:
            return jsonify({"error": "Invalid space ID."}), 400

        space = Space.query.get(int(space_id_num))
        if not space:
            return jsonify({"error": "Space not found."}), 404
        if not space.is_active:
            return jsonify({"error": "Space is currently paused by the host and not accepting new bookings."}), 400

        hours = validate_numeric(data.get("hours"), min_val=0.5, max_val=168.0, default=None)
        if hours is None:
            return jsonify({"error": "Invalid duration: hours must be between 0.5 and 168."}), 400

        max_cap = space.max_capacity if space.max_capacity and space.max_capacity > 0 else 50
        raw_attendees = data.get("attendees_count")
        attendees_count = int(validate_numeric(raw_attendees, min_val=1, max_val=1000, default=1))
        if attendees_count > max_cap:
            return jsonify({
                "error": f"Requested attendees count ({attendees_count}) exceeds maximum capacity of {max_cap} for this space."
            }), 400

        purpose = sanitize_string(data.get("purpose", "Creative work & study session"), max_length=200)
        special_requests = sanitize_string(data.get("special_requests", ""), max_length=500)

        now = datetime.utcnow()
        raw_start = data.get("start_time")
        if raw_start:
            try:
                clean_start = str(raw_start).replace("Z", "+00:00")
                parsed_start = datetime.fromisoformat(clean_start)
                if parsed_start.tzinfo is not None:
                    parsed_start = parsed_start.astimezone(timezone.utc).replace(tzinfo=None)
                start_time = parsed_start
            except Exception:
                start_time = now + timedelta(minutes=15)
        else:
            cand_start = now + timedelta(minutes=15)
            # Find next free slot if space has existing active/confirmed bookings
            while True:
                cand_end = cand_start + timedelta(hours=float(hours))
                conflict = Booking.query.filter(
                    Booking.space_id == space.id,
                    Booking.status != "cancelled",
                    Booking.start_time < cand_end,
                    Booking.end_time > cand_start
                ).order_by(Booking.end_time.desc()).first()
                if not conflict:
                    start_time = cand_start
                    break
                cand_start = conflict.end_time + timedelta(minutes=15)

        if start_time < now - timedelta(minutes=5):
            return jsonify({"error": "Cannot create a booking in the past."}), 400

        end_time = start_time + timedelta(hours=float(hours))

        # P1-4 / Task 17: Short-window idempotency de-dupe on (renter_id, space_id, start_time)
        recent_duplicate = Booking.query.filter(
            Booking.renter_id == renter.id,
            Booking.space_id == space.id,
            Booking.start_time == start_time,
            Booking.created_at >= now - timedelta(seconds=5)
        ).first()
        if recent_duplicate:
            return jsonify({
                "error": "Duplicate booking request detected. Please wait before retrying.",
                "duplicate_prevented": True,
                "booking": recent_duplicate.to_dict()
            }), 409

        # P0-1: Prevent overlapping bookings
        # Condition: existing.start_time < requested_end AND existing.end_time > requested_start
        conflicting = Booking.query.filter(
            Booking.space_id == space.id,
            Booking.status != "cancelled",
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).first()
        if conflicting:
            c_start = conflicting.start_time.strftime('%b %d, %I:%M %p')
            c_end = conflicting.end_time.strftime('%I:%M %p')
            return jsonify({
                "error": f"This space is already reserved between {c_start} and {c_end} UTC. Please choose another time slot.",
                "conflicting_booking_id": conflicting.id
            }), 409

        # Authoritative server-side financial calculation (ignores untrusted client pricing/deposits)
        financial_bounds = clamp_financial_bounds(hours=float(hours), price_hourly=space.price_hourly)
        rental_fee = financial_bounds["rental_fee"]
        escrow_deposit = 100.0
        total_price = financial_bounds["total_payable"]

        # P1-2: Cryptographically random 4-digit arrival PIN
        arrival_pin = f"{secrets.randbelow(9000) + 1000}"

        new_booking = Booking(
            space_id=space.id,
            renter_id=renter.id,
            start_time=start_time,
            end_time=end_time,
            hours_booked=float(hours),
            attendees_count=attendees_count,
            escrow_deposit_amount=escrow_deposit,
            total_price=total_price,
            status="confirmed",
            intended_purpose=purpose,
            special_requests=special_requests,
            session_state="confirmed",
            arrival_pin=arrival_pin,
            escrow_status="held_simulated",
            entry_scan_photo="",
            exit_scan_photo=""
        )

        db.session.add(new_booking)
        db.session.flush()

        # P1-5: Access and transaction audit trail
        audit = AuditLog(
            user_id=renter.id,
            action="BOOKING_CREATED",
            ip_address=request.remote_addr or "",
            user_agent=request.user_agent.string[:250] if request.user_agent else "",
            details=f"Booking #{new_booking.id} created for Space #{space.id} ({hours} hrs)"
        )
        db.session.add(audit)

        lease_agreement = generate_micro_lease(space.to_dict(), new_booking.to_dict())
        new_booking.micro_lease_agreement = lease_agreement
        db.session.commit()

        lease_hash = hashlib.sha256(lease_agreement.encode("utf-8")).hexdigest()[:16]
        return jsonify({
            "success": True,
            "message": f"Booking #{new_booking.id} confirmed! Micro-lease signed and active.",
            "booking": new_booking.to_dict(),
            "agreement": lease_agreement,
            "escrow_deposit": escrow_deposit,
            "rental_fee": rental_fee,
            "total_payable": total_price,
            "arrival_pin": arrival_pin,
            "lease_hash": lease_hash,
            "session_url": f"/session/{new_booking.id}"
        }), 201

    @app.route("/api/calculator/estimate", methods=["POST"])
    def api_estimate():
        data = request.get_json(silent=True) or {}
        category = sanitize_string(data.get("category", "Studio"), max_length=50)
        sqft = validate_numeric(data.get("sqft"), min_val=20, max_val=50000, default=300)
        days = validate_numeric(data.get("days_per_month"), min_val=1, max_val=31, default=12)
        rate = validate_numeric(data.get("hourly_rate"), min_val=5, max_val=5000, default=None)
        hours = validate_numeric(data.get("hours_per_day"), min_val=1, max_val=24, default=4)
        fee = validate_numeric(data.get("platform_fee_percent"), min_val=0, max_val=50, default=15)

        estimate = calculate_earnings_estimate(
            category=category,
            sqft=sqft,
            days_per_month=days,
            hourly_rate=rate,
            hours_per_day=hours,
            platform_fee_percent=fee
        )
        return jsonify(estimate)

    @app.route("/api/ai/chat", methods=["POST"])
    @rate_limit_ai
    def ai_chat():
        data = request.get_json(silent=True) or {}
        messages = data.get("messages", [])
        if not messages or not isinstance(messages, list):
            return jsonify({"reply": "Hello! How can I assist you with SpaceLoop today?"}), 200

        user_context = None
        if current_user.is_authenticated:
            user_context = {
                "user_name": current_user.name,
                "role": current_user.role,
                "is_verified": current_user.is_student_verified or current_user.is_host_verified
            }

        response = concierge_chat(messages, context_data=user_context)
        return jsonify({"reply": response})

    @app.route("/api/concierge", methods=["POST"])
    def api_concierge():
        data = request.get_json(silent=True) or {}
        user_msg = data.get("message") or ""
        messages = data.get("messages")
        if not messages and user_msg:
            messages = [{"role": "user", "content": user_msg}]
        elif not messages:
            messages = [{"role": "user", "content": "Hello"}]

        space_id = data.get("space_id")
        context_data = None
        if space_id:
            space = Space.query.get(space_id)
            if space:
                context_data = {
                    "space_title": space.title,
                    "category": space.category,
                    "hourly_rate": space.price_hourly,
                    "amenities": space.amenities,
                    "rules": space.rules,
                    "address": f"{space.neighborhood or space.city}, {space.state}"
                }

        reply = concierge_chat(messages, context_data=context_data)
        return jsonify({
            "success": True,
            "reply": reply
        }), 200

    @app.route("/api/calculate-yield", methods=["POST"])
    def api_calculate_yield():
        data = request.get_json(silent=True) or {}
        category = sanitize_string(data.get("category", "Workspace"), max_length=50)
        sqft = float(validate_numeric(data.get("sqft"), 20, 50000, 180))
        days = int(validate_numeric(data.get("occupancy_days", data.get("days_per_month")), 1, 31, 12))
        hours = float(validate_numeric(data.get("hours_per_day", 6.0), 1.0, 24.0, 6.0))

        rate = calculate_dynamic_rate(category, sqft)
        host_yield = calculate_host_monthly_yield(rate['calculated_hourly'], days, hours)
        savings = calculate_student_savings(hours, rate['calculated_hourly'])
        return jsonify({
            "success": True,
            "rate": rate,
            "yield": host_yield,
            "savings": savings
        }), 200

    @app.route("/api/system/status", methods=["GET"])
    def api_system_status():
        sim = session.get("simulate_ai_failure", False)
        return jsonify(get_system_connectivity_status(simulate_override=sim))

    @app.route("/api/dev/toggle-ai-simulation", methods=["POST"])
    @login_required
    def toggle_ai_simulation():
        if not current_user.is_admin:
            return jsonify({"error": "Unauthorized: Administrator privileges required to toggle simulation."}), 403
        if app.config.get("FLASK_ENV") == "production":
            return jsonify({"error": "Development simulation controls are disabled in production environment."}), 403
        current_val = session.get("simulate_ai_failure", False)
        new_val = not current_val
        session["simulate_ai_failure"] = new_val
        set_simulate_ai_failure(new_val)
        if request.is_json:
            return jsonify({"success": True, "simulate_ai_failure": new_val}), 200
        return redirect(request.referrer or url_for("index"))

    @app.route("/api/verify/student", methods=["POST"])
    @login_required
    def api_verify_student():
        data = request.get_json(silent=True) or {}
        name = sanitize_string(data.get("name", current_user.name), max_length=100)
        aadhaar_num = sanitize_string(data.get("aadhaar_number", ""), max_length=20)
        otp = sanitize_string(data.get("otp", "123456"), max_length=10)
        college_email = sanitize_string(data.get("college_email", ""), max_length=120)
        college_name = sanitize_string(data.get("college_name", ""), max_length=150)
        student_id = sanitize_string(data.get("student_id", ""), max_length=50)

        aadhaar_res = verify_aadhaar_otp(name, aadhaar_num, otp)
        if not aadhaar_res.get("success"):
            return jsonify({"success": False, "error": aadhaar_res.get("error")}), 400

        acad_res = verify_academic_credentials(college_email, student_id, college_name)
        if not acad_res.get("success"):
            return jsonify({"success": False, "error": acad_res.get("error", "Academic verification failed.")}), 400

        user = current_user
        user.is_student_verified = True
        user.is_aadhaar_verified = True
        user.aadhaar_masked = aadhaar_res["masked_aadhaar"]
        user.aadhaar_token_hash = aadhaar_res["token_hash"]
        user.college_name = acad_res["college_name"]
        user.college_email = acad_res["college_email"]
        user.student_id_masked = acad_res["student_id_masked"]
        user.objective_trust_score = compute_objective_trust_index(
            user.on_time_vacate_rate,
            user.cleanliness_match_rate,
            is_identity_verified=True,
            dispute_count=user.dispute_count
        )
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Student identity and academic enrollment successfully verified!",
            "aadhaar": aadhaar_res,
            "academic": acad_res,
            "user": user.to_dict()
        })

    @app.route("/api/verify/host", methods=["POST"])
    @login_required
    def api_verify_host():
        data = request.get_json(silent=True) or {}
        ca_number = sanitize_string(data.get("ca_number", ""), max_length=50)
        provider = sanitize_string(data.get("provider", "BESCOM"), max_length=80)
        address = sanitize_string(data.get("address", ""), max_length=200)
        pan_name = sanitize_string(data.get("pan_name", ""), max_length=100)
        upi_vpa = sanitize_string(data.get("upi_vpa", ""), max_length=80)

        # Cross-validate PAN/Bank name against registered user profile name to block identity spoofing
        if pan_name and current_user.name:
            user_tokens = set(re.findall(r'\w+', current_user.name.lower()))
            pan_tokens = set(re.findall(r'\w+', pan_name.lower()))
            is_demo_or_test = app.config.get("TESTING") or os.environ.get("FLASK_ENV") != "production" or current_user.is_admin
            if not user_tokens.intersection(pan_tokens) and not is_demo_or_test:
                return jsonify({
                    "success": False,
                    "error": f"PAN / Bank account name '{pan_name}' does not match registered profile name '{current_user.name}'."
                }), 400

        discom_res = verify_host_electricity_bill(ca_number, provider, address, pan_name)
        if not discom_res.get("success"):
            return jsonify({"success": False, "error": discom_res.get("error")}), 400

        upi_res = verify_upi_penny_drop(upi_vpa, pan_name)
        if not upi_res.get("success"):
            return jsonify({"success": False, "error": upi_res.get("error")}), 400

        user = current_user
        user.is_host_verified = True
        user.discom_provider = discom_res["discom_provider"]
        user.discom_ca_masked = discom_res["discom_ca_masked"]
        user.upi_verified = True
        user.upi_vpa_masked = upi_res["upi_vpa_masked"]
        user.bank_beneficiary_name = upi_res["bank_beneficiary_name"]
        user.objective_trust_score = compute_objective_trust_index(
            user.on_time_vacate_rate,
            user.cleanliness_match_rate,
            is_identity_verified=True,
            dispute_count=user.dispute_count
        )
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Property possession and payout account successfully verified!",
            "discom": discom_res,
            "upi": upi_res,
            "user": user.to_dict()
        })

    @app.route("/api/booking/<int:booking_id>/check-in", methods=["POST"])
    @login_required
    def api_booking_checkin(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        try:
            authorize(current_user, Permission.BOOKING_CHECKIN, resource=booking)
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403

        space = booking.space
        data = request.get_json(silent=True) or {}

        if booking.status in ["cancelled", "refunded"]:
            return jsonify({
                "success": False,
                "error": "This reservation has been cancelled. In-room access is revoked."
            }), 400

        if booking.session_state == "checked_in":
            return jsonify({
                "success": True,
                "message": "Session already active.",
                "already_checked_in": True,
                "booking": booking.to_dict()
            }), 200

        if booking.session_state == "checked_out" or booking.status == "completed":
            return jsonify({
                "success": False,
                "error": "This booking session has already completed."
            }), 400

        device_lat = data.get("lat")
        device_lng = data.get("lng")
        client_qr = sanitize_string(data.get("qr_token", ""), max_length=100)
        client_pin = sanitize_string(data.get("pin", ""), max_length=10)

        now = datetime.utcnow()

        # P1-3: Enforce check-in time window (not >30m early, not after end_time)
        if booking.start_time and now < booking.start_time - timedelta(minutes=30):
            return jsonify({
                "success": False,
                "error": f"Early check-in not permitted. Your booking window begins at {booking.start_time.strftime('%I:%M %p')} UTC (check-in opens 30 minutes prior)."
            }), 400
        if booking.end_time and now > booking.end_time:
            return jsonify({
                "success": False,
                "error": f"Booking window expired at {booking.end_time.strftime('%I:%M %p')} UTC."
            }), 400

        actual_distance = 0.0
        max_allowed_dist = 50.0

        if device_lat is not None and device_lng is not None and space.latitude and space.longitude:
            actual_distance = haversine_distance(device_lat, device_lng, space.latitude, space.longitude)

        # P0-2: Check QR against genuine space token only (no DEMO_QR_PASS universal bypass)
        qr_matches = False
        if client_qr and space.room_qr_token and client_qr == space.room_qr_token:
            qr_matches = True

        pin_matches = False
        if client_pin and booking.arrival_pin and client_pin == booking.arrival_pin:
            pin_matches = True

        access_granted = False
        handshake_method = ""

        # P0-4: GPS is corroboration, never a standalone access credential
        if qr_matches and actual_distance <= max_allowed_dist:
            access_granted = True
            handshake_method = "QR_GEOFENCE_VERIFIED"
        elif qr_matches:
            access_granted = True
            handshake_method = "QR_SCAN_STANDALONE"
        elif pin_matches:
            access_granted = True
            handshake_method = "PIN_FALLBACK_VERIFIED"

        if not access_granted:
            dist_desc = f"{int(actual_distance)}m away (max {int(max_allowed_dist)}m)" if actual_distance > 0 else "Location unavailable"
            audit_fail = AuditLog(
                user_id=current_user.id,
                action="CHECKIN_REJECTED",
                ip_address=request.remote_addr or "",
                user_agent=request.user_agent.string[:250] if request.user_agent else "",
                details=f"Booking #{booking.id} check-in rejected - distance: {int(actual_distance)}m, QR supplied: {bool(client_qr)}"
            )
            db.session.add(audit_fail)
            db.session.commit()
            return jsonify({
                "success": False,
                "error": f"Handshake failed: Physical access proof required via room QR scan or 4-digit arrival PIN. (Device is {dist_desc}).",
                "distance_meters": int(actual_distance),
                "required_distance": int(max_allowed_dist),
                "arrival_pin_hint": "Check your booking confirmation for the 4-digit door PIN."
            }), 403

        raw_entry_photo = data.get("entry_photo")
        if raw_entry_photo:
            booking.entry_scan_photo = sanitize_string(raw_entry_photo, max_length=500)

        booking.session_state = "checked_in"
        booking.arrival_time = now
        booking.checkin_gps_lat = float(device_lat) if device_lat is not None else space.latitude
        booking.checkin_gps_lng = float(device_lng) if device_lng is not None else space.longitude

        audit_ok = AuditLog(
            user_id=current_user.id,
            action="CHECKIN_SUCCESS",
            ip_address=request.remote_addr or "",
            user_agent=request.user_agent.string[:250] if request.user_agent else "",
            details=f"Booking #{booking.id} check-in success via {handshake_method}"
        )
        db.session.add(audit_ok)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Check-in verified via {handshake_method}! In-room access granted.",
            "arrival_time": now.strftime("%I:%M:%S %p IST"),
            "handshake_method": handshake_method,
            "distance_meters": int(actual_distance),
            "allowed_radius": max_allowed_dist,
            "booking": booking.to_dict()
        }), 200

    @app.route("/api/booking/<int:booking_id>/check-out", methods=["POST"])
    @login_required
    def api_booking_checkout(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        try:
            authorize(current_user, Permission.BOOKING_CHECKOUT, resource=booking)
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403

        space = booking.space
        data = request.get_json(silent=True) or {}

        # P0-3: Require check-in before checkout
        if booking.session_state != "checked_in":
            return jsonify({
                "error": "You must check in before checking out.",
                "current_session_state": booking.session_state
            }), 400

        if booking.status == "completed":
            return jsonify({
                "error": "This booking session has already completed check-out.",
                "duplicate_prevented": True,
                "booking": booking.to_dict()
            }), 400

        raw_exit_photo = data.get("exit_photo")
        exit_photo = sanitize_string(raw_exit_photo, max_length=500) if raw_exit_photo else ""
        if not exit_photo and not booking.entry_scan_photo:
            exit_photo = "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"

        lat = float(validate_numeric(data.get("lat"), min_val=-90, max_val=90, default=space.latitude))
        lng = float(validate_numeric(data.get("lng"), min_val=-180, max_val=180, default=space.longitude))
        final_photo = exit_photo or booking.entry_scan_photo

        now = datetime.utcnow()

        # P0-5: Evaluate condition delta without client-controlled failure/damage simulation flags
        inspection = evaluate_room_condition_delta(
            booking.entry_scan_photo,
            final_photo
        )

        punctuality = calculate_session_punctuality(
            booking.start_time,
            booking.end_time,
            booking.arrival_time or (now - timedelta(hours=booking.hours_booked)),
            now
        )

        booking.session_state = "checked_out"
        booking.status = "completed"
        booking.departure_time = now
        booking.checkout_gps_lat = lat
        booking.checkout_gps_lng = lng
        booking.exit_scan_photo = final_photo
        booking.condition_match_score = inspection.get("condition_match_score") or 0.0
        booking.fans_lights_cleared = bool(inspection.get("fans_lights_cleared"))
        booking.objective_punctuality_score = punctuality

        # P0-6: Honest simulated escrow ledger state
        if inspection.get("escrow_decision") == "RELEASE_FULL":
            booking.escrow_status = "refund_recorded_simulated"
            msg = "Check-out completed! Room condition cleared and ₹100 simulated escrow deposit refund recorded."
            refund_state = "Refund recorded (Simulated Ledger)"
        else:
            booking.escrow_status = "held_for_review"
            msg = "Check-out recorded. Condition discrepancy flagged; ₹100 deposit held pending host review."
            refund_state = "Review required"

        renter = booking.renter
        if renter:
            renter.total_completed_hours += booking.hours_booked
            renter.on_time_vacate_rate = round(0.8 * renter.on_time_vacate_rate + 0.2 * punctuality, 1)
            cond_score = booking.condition_match_score if booking.condition_match_score is not None else 95.0
            renter.cleanliness_match_rate = round(0.8 * renter.cleanliness_match_rate + 0.2 * cond_score, 1)
            renter.objective_trust_score = compute_objective_trust_index(
                punctuality=renter.on_time_vacate_rate,
                condition_match=renter.cleanliness_match_rate,
                is_identity_verified=renter.is_aadhaar_verified or renter.is_student_verified,
                dispute_count=renter.dispute_count
            )

        audit_co = AuditLog(
            user_id=current_user.id,
            action="CHECKOUT_COMPLETED",
            ip_address=request.remote_addr or "",
            user_agent=request.user_agent.string[:250] if request.user_agent else "",
            details=f"Booking #{booking.id} check-out completed - refund status: {booking.escrow_status}"
        )
        db.session.add(audit_co)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": msg,
            "departure_time": now.strftime("%I:%M:%S %p IST"),
            "inspection": inspection,
            "punctuality_score": punctuality,
            "escrow_refund_status": "INSTANT_RELEASE_COMPLETE" if refund_state == "Released" else refund_state,
            "status": refund_state,
            "booking": booking.to_dict()
        })

    @app.route("/api/booking/<int:booking_id>/cancel", methods=["POST"])
    @login_required
    def api_cancel_booking(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        try:
            authorize(current_user, Permission.BOOKING_CANCEL, resource=booking)
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403

        if booking.status == "cancelled":
            return jsonify({"success": False, "error": "This booking is already cancelled."}), 400
        if booking.status == "completed" or booking.session_state == "checked_out":
            return jsonify({"success": False, "error": "Cannot cancel an already completed reservation."}), 400
        if booking.session_state == "checked_in":
            return jsonify({"success": False, "error": "Active session in progress cannot be cancelled directly. Please complete checkout."}), 400

        booking.status = "cancelled"
        booking.session_state = "cancelled"
        if booking.escrow_status in ["held", "held_simulated"]:
            booking.escrow_status = "refunded_simulated"
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Booking #{booking_id} cancelled successfully. ₹{int(booking.escrow_deposit_amount)} escrow deposit refunded.",
            "booking": booking.to_dict()
        }), 200

    @app.route("/api/booking/<int:booking_id>", methods=["GET", "DELETE"])
    @app.route("/api/bookings/<int:booking_id>", methods=["GET", "DELETE"])
    @login_required
    def api_booking_detail_or_manage(booking_id):
        booking = Booking.query.get_or_404(booking_id)

        if request.method == "DELETE":
            try:
                authorize(current_user, Permission.BOOKING_CANCEL, resource=booking)
            except ForbiddenError as e:
                return jsonify({"error": str(e)}), 403

            if booking.status == "cancelled":
                return jsonify({"success": False, "error": "This booking is already cancelled."}), 400
            if booking.status == "completed" or booking.session_state == "checked_out":
                return jsonify({"success": False, "error": "Cannot cancel an already completed reservation."}), 400
            if booking.session_state == "checked_in":
                return jsonify({"success": False, "error": "Active session in progress cannot be cancelled directly. Please complete checkout."}), 400

            booking.status = "cancelled"
            booking.session_state = "cancelled"
            if booking.escrow_status in ["held", "held_simulated"]:
                booking.escrow_status = "refunded_simulated"
            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"Booking #{booking_id} cancelled successfully.",
                "booking": booking.to_dict()
            }), 200

        try:
            authorize(current_user, Permission.BOOKING_VIEW, resource=booking)
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403

        return jsonify({
            "success": True,
            "booking": booking.to_dict()
        }), 200

    @app.route("/api/space/<int:space_id>/inquire", methods=["POST"])
    def api_space_direct_inquire(space_id):
        space = Space.query.get_or_404(space_id)
        if not space.is_active:
            is_authorized = current_user.is_authenticated and (current_user.id == space.owner_id or getattr(current_user, "is_admin", False))
            if not is_authorized:
                return jsonify({"success": False, "error": "Cannot inquire on a paused or inactive space listing."}), 400
        data = request.get_json(silent=True) or {}
        question = sanitize_string(data.get("question") or "", max_length=500)
        if not question:
            return jsonify({"success": False, "error": "Question cannot be empty."}), 400

        context_data = {
            "space_title": space.title,
            "category": space.category,
            "hourly_rate": space.price_hourly,
            "amenities": space.amenities,
            "rules": space.rules,
            "address": f"{space.neighborhood or space.city}, {space.state}",
            "description": space.description
        }
        answer = concierge_chat([{"role": "user", "content": question}], context_data=context_data)

        user_id = current_user.id if current_user.is_authenticated else None
        inquiry = SpaceInquiry(
            space_id=space.id,
            user_id=user_id,
            question=question,
            ai_answer=answer
        )
        db.session.add(inquiry)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Inquiry logged and answered by LoopBot.",
            "ai_answer": answer,
            "inquiry": inquiry.to_dict()
        }), 200

    @app.route("/api/inquiries", methods=["GET", "POST"])
    @login_required
    def api_inquiries():
        if request.method == "POST":
            data = request.get_json() or {}
            question = sanitize_string(data.get("question") or "")
            if not question:
                return jsonify({"success": False, "error": "Question text cannot be empty."}), 400

            space_id = data.get("space_id")
            space = Space.query.get(space_id) if space_id else None

            context_data = None
            if space:
                context_data = {
                    "space_title": space.title,
                    "category": space.category,
                    "hourly_rate": space.price_hourly,
                    "amenities": space.amenities,
                    "rules": space.rules,
                    "address": f"{space.neighborhood or space.city}, {space.state}"
                }

            ai_res = concierge_chat([{"role": "user", "content": question}], context_data=context_data)
            answer = ai_res.get("reply") if isinstance(ai_res, dict) else "Inquiry received. The host and LoopBot concierge have recorded your question."

            inquiry = SpaceInquiry(
                space_id=space.id if space else None,
                user_id=current_user.id,
                question=question,
                ai_answer=answer
            )
            db.session.add(inquiry)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Inquiry logged and pre-answered by LoopBot AI Concierge.",
                "inquiry": inquiry.to_dict()
            }), 201

        inquiries = SpaceInquiry.query.filter(
            db.or_(
                SpaceInquiry.user_id == current_user.id,
                SpaceInquiry.space_id.in_(
                    db.session.query(Space.id).filter(Space.owner_id == current_user.id)
                )
            )
        ).order_by(SpaceInquiry.created_at.desc()).all()

        return jsonify({
            "success": True,
            "inquiries": [i.to_dict() for i in inquiries]
        }), 200

    @app.errorhandler(404)
    def handle_404_error(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "error": "Resource not found (404)"}), 404
        return render_template("404.html", user=current_user.to_dict() if current_user.is_authenticated else None), 404

    @app.errorhandler(500)
    def handle_500_error(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "error": "Internal server error (500)"}), 500
        user_data = None
        try:
            if current_user and current_user.is_authenticated:
                user_data = current_user.to_dict()
        except Exception:
            user_data = None
        return render_template("500.html", user=user_data), 500

    @app.route("/health")
    @app.route("/api/health")
    def health_check():
        try:
            db.session.execute(db.text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        ai_status = get_system_connectivity_status()
        is_healthy = (db_status == "healthy")
        status_code = 200 if is_healthy else 503

        return jsonify({
            "status": "healthy" if is_healthy else "degraded",
            "database": db_status,
            "ai_engine": ai_status,
            "server_timestamp": datetime.utcnow().isoformat()
        }), status_code

    # Automatically exempt JSON /api/ endpoints from web form CSRF checks
    for endpoint, view_func in app.view_functions.items():
        try:
            for rule in app.url_map.iter_rules(endpoint):
                if rule.rule.startswith("/api/"):
                    csrf.exempt(view_func)
                    break
        except Exception:
            pass

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    is_dev = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=is_dev)
