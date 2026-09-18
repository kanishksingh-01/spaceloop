"""
SpaceLoop Application Entry Point & Factory
Modularized architecture with:
- Dedicated REST API Blueprints (Auth, Spaces, Bookings, System)
- Unified modern React SPA serving from root / and client routes
- Production CORS middleware with configurable origins
- SQLite WAL mode concurrency and dialect-agnostic schema sync
- Zero-regression legacy HTML view support under /legacy
"""
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load local environment settings
load_dotenv()

from urllib.parse import parse_qs, urlencode
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import (
    Flask, request, jsonify, render_template, redirect, url_for, session,
    flash, send_from_directory, abort, Response
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf

from config import Config
from models import db, User, Space, Booking, Review, SpaceInquiry
from backend.app.extensions import login_manager, csrf, limiter
from backend.core.database import configure_engine_pragmas, ensure_database_schema
from backend.core.cors import configure_cors
from backend.core.geo import resolve_location_coordinates
from backend.modules.auth import AuthService, set_active_context
from security import apply_security_headers, sanitize_string

# Import Modular Blueprints
from backend.app.api.v1.auth import api_v1_auth
from backend.app.api.v1.spaces import api_v1_spaces
from backend.app.api.v1.bookings import api_v1_bookings
from backend.app.api.v1.system import api_v1_system


class VercelWSGIMiddleware:
    """
    Normalizes WSGI PATH_INFO and SCRIPT_NAME for requests routed
    through Vercel's edge network using rewrites.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        if "__path__=" in qs or "_vercel_path=" in qs or "slug=" in qs or "path=" in qs:
            params = parse_qs(qs, keep_blank_values=True)
            for key in ("__path__", "_vercel_path", "slug", "path"):
                if key in params:
                    extracted_path = params.pop(key)[0]
                    if not extracted_path.startswith("/"):
                        extracted_path = "/" + extracted_path
                    environ["PATH_INFO"] = extracted_path
                    environ["QUERY_STRING"] = urlencode(params, doseq=True)
                    break
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api"):
            matched = environ.get("HTTP_X_MATCHED_PATH")
            if matched and not matched.startswith("/api/index") and matched != "/":
                environ["PATH_INFO"] = matched
            else:
                raw_uri = environ.get("RAW_URI") or environ.get("REQUEST_URI", "")
                if raw_uri:
                    path_part = raw_uri.split("?")[0]
                    if path_part and not path_part.startswith("/api/index") and path_part != "/":
                        environ["PATH_INFO"] = path_part

        return self.wsgi_app(environ, start_response)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Wrap WSGI layer with ProxyFix and Vercel edge rewrite normalizer
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

    # 1. Database & Concurrency Configuration (SQLite WAL mode + 5000ms busy timeout)
    configure_engine_pragmas(db)
    db.init_app(app)

    # 2. Extensions & Security Initialization
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # 3. Production CORS Configuration
    configure_cors(app)

    # 4. Dialect-Agnostic Schema Sync (Cross-compatible with SQLite and PostgreSQL)
    ensure_database_schema(app, db)

    # 5. User Loader for Session Authentication
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api") or request.is_json or "application/json" in request.headers.get("Accept", ""):
            return jsonify({"error": "Authentication required", "success": False}), 401
        return redirect(url_for("auth_login", next=request.url))

    # 6. Global Security Headers Middleware
    @app.after_request
    def add_security_headers(response):
        return apply_security_headers(response)

    # 7. Jinja Template Context Processor
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.now(timezone.utc).year,
            "csrf_token": generate_csrf
        }

    # 8. Register Modular REST Blueprints
    app.register_blueprint(api_v1_auth)
    app.register_blueprint(api_v1_spaces)
    app.register_blueprint(api_v1_bookings)
    app.register_blueprint(api_v1_system)

    # 9. Automatically exempt JSON /api/ endpoints from web form CSRF checks
    for endpoint, view_func in app.view_functions.items():
        try:
            for rule in app.url_map.iter_rules(endpoint):
                if rule.rule.startswith("/api/"):
                    csrf.exempt(view_func)
                    break
        except Exception:
            pass

    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "ok", "service": "SpaceLoop API", "version": "2.5.0"})

    @app.route("/api/index")
    @app.route("/api/index.py")
    def api_index_handler():
        target_path = request.args.get("__path__") or request.args.get("_vercel_path")
        if target_path and target_path not in ("/api/index", "/api/index.py", "/"):
            with app.test_client() as client:
                query_params = {k: v for k, v in request.args.items() if k not in ("__path__", "_vercel_path")}
                resp = client.open(
                    target_path,
                    method=request.method,
                    headers=dict(request.headers),
                    query_string=query_params,
                    data=request.get_data(),
                    content_type=request.content_type
                )
                return Response(
                    resp.get_data(),
                    status=resp.status_code,
                    headers=[(k, v) for k, v in resp.headers if k.lower() not in ("content-length", "content-encoding")]
                )
        return jsonify({
            "status": "ok",
            "service": "SpaceLoop API",
            "version": "2.5.0",
            "message": "SpaceLoop Vercel Serverless Function Active"
        })

    # =========================================================================
    # UNIFIED FRONTEND ENTRY POINT (MODERN REACT SPA)
    # Serves Vite React SPA directly on root / and client routes
    # =========================================================================
    dist_dir = os.path.join(os.path.dirname(__file__), "public")
    if not os.path.exists(os.path.join(dist_dir, "index.html")):
        dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")

    @app.route("/assets/<path:filename>")
    def serve_frontend_assets(filename):
        assets_dir = os.path.join(dist_dir, "assets")
        if os.path.exists(os.path.join(assets_dir, filename)):
            return send_from_directory(assets_dir, filename)
        abort(404)

    def _serve_spa_index():
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return send_from_directory(dist_dir, "index.html")
        # Fallback to landing template if frontend has not been compiled yet
        featured = Space.query.filter_by(is_active=True).limit(6).all()
        return render_template("landing.html", spaces=[s.to_dict() for s in featured])

    @app.route("/", endpoint="index")
    @app.route("/", endpoint="root_spa")
    def index():
        """Primary Entry Point: Serves the modern React SPA on root."""
        # If legacy query param is explicitly requested, route to legacy landing or explore
        if request.args.get("legacy"):
            featured_spaces = Space.query.filter_by(is_active=True).limit(6).all()
            return render_template("landing.html", spaces=[s.to_dict() for s in featured_spaces])
        return _serve_spa_index()

    @app.route("/react")
    @app.route("/react/<path:path>")
    @app.route("/app")
    @app.route("/app/<path:path>")
    def serve_react_explicit(path=""):
        return _serve_spa_index()

    @app.route("/legacy")
    @app.route("/legacy/")
    def legacy_landing():
        featured_spaces = Space.query.filter_by(is_active=True).limit(6).all()
        return render_template("landing.html", spaces=[s.to_dict() for s in featured_spaces])

    @app.route("/explore", endpoint="explore_page")
    @app.route("/explore", endpoint="explore")
    @app.route("/legacy/explore")
    def explore():
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
        category = sanitize_string(request.args.get("category", ""), max_length=50)
        q = sanitize_string(request.args.get("q", ""), max_length=150)
        loc = sanitize_string(request.args.get("loc", ""), max_length=100)
        lat, lng, loc_name = resolve_location_coordinates(loc, request.args.get("lat"), request.args.get("lng"))
        query = Space.query.filter_by(is_active=True)
        if category and category.lower() != "all":
            query = query.filter(Space.category.ilike(f"%{category.lower()}%"))
        if q:
            query = query.filter(db.or_(Space.title.ilike(f"%{q}%"), Space.description.ilike(f"%{q}%")))
        spaces = [s.to_dict() for s in query.all()]
        return render_template("explore.html", spaces=spaces, selected_category=category, current_location=loc_name or loc)

    @app.route("/space/<int:space_id>", endpoint="space_detail")
    @app.route("/legacy/space/<int:space_id>")
    def space_detail(space_id):
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
        space = Space.query.get_or_404(space_id)
        return render_template("space_detail.html", space=space.to_dict())

    @app.route("/list-space", endpoint="list_space_page")
    @app.route("/legacy/list-space")
    @login_required
    def list_space_page():
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
        edit_id = request.args.get("edit")
        edit_space = None
        if edit_id:
            try:
                sp = Space.query.get(int(edit_id))
                if sp and (sp.owner_id == current_user.id or getattr(current_user, 'is_admin', False)):
                    edit_space = sp.to_dict()
            except Exception:
                edit_space = None
        return render_template("list_space.html", edit_space=edit_space, user=current_user.to_dict() if current_user.is_authenticated else None)

    @app.route("/calculator", endpoint="calculator_page")
    @app.route("/legacy/calculator")
    def calculator_page():
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
        from space_ai import calculate_earnings_estimate
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

        return render_template("calculator.html", initial_data=default_calc, host_spaces=user_spaces, user=current_user.to_dict() if current_user.is_authenticated else None)

    @app.route("/dashboard", endpoint="dashboard_page")
    @app.route("/legacy/dashboard")
    @login_required
    def dashboard_page():
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
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

    @app.route("/how-it-works", endpoint="how_it_works")
    @app.route("/how-it-works", endpoint="how_it_works_page")
    @app.route("/legacy/how-it-works")
    def how_it_works_page():
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
        return render_template("how_it_works.html", user=current_user.to_dict() if current_user.is_authenticated else None)

    @app.route("/verify", endpoint="verify_page")
    @app.route("/legacy/verify")
    @login_required
    def verify_page():
        if request.args.get("spa") or request.args.get("react"):
            return _serve_spa_index()
        return render_template("verify.html", user=current_user.to_dict() if current_user.is_authenticated else None)

    @app.route("/booking/<int:booking_id>/session", endpoint="session_page")
    @login_required
    def session_page(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        if current_user.id != booking.renter_id and current_user.id != booking.space.owner_id and not current_user.is_admin:
            flash("Access Denied: You do not have permission to view this booking session.", "danger")
            return redirect(url_for("auth_access_denied"))
        return render_template("session.html", booking=booking.to_dict(), space=booking.space.to_dict())

    @app.route("/session", endpoint="active_session_redirect")
    @login_required
    def active_session_redirect():
        latest_booking = Booking.query.filter_by(renter_id=current_user.id).order_by(Booking.created_at.desc()).first()
        if latest_booking:
            return redirect(url_for("session_page", booking_id=latest_booking.id))
        flash("You do not have any active or previous sessions.", "info")
        return redirect(url_for("dashboard_page"))

    @app.route("/space/<int:space_id>/printable-qr", endpoint="printable_qr")
    def printable_qr(space_id):
        space = Space.query.get_or_404(space_id)
        return render_template("printable_qr.html", space=space.to_dict())

    @app.route("/space/<int:space_id>/toggle-status", methods=["POST"], endpoint="toggle_space_status")
    @login_required
    def toggle_space_status(space_id):
        space = Space.query.get_or_404(space_id)
        if space.owner_id != current_user.id and not current_user.is_admin:
            flash("Unauthorized", "danger")
            return redirect(url_for("dashboard_page"))
        space.is_active = not space.is_active
        db.session.commit()
        flash(f"Space status changed to {'Active' if space.is_active else 'Paused'}.", "success")
        return redirect(request.referrer or url_for("dashboard_page"))

    @app.route("/profile", endpoint="profile_page")
    @login_required
    def profile_page():
        return render_template("profile.html", user=current_user.to_dict())

    @app.route("/inquiries", endpoint="inquiries_page")
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

    @app.route("/switch-user/<int:user_id>", methods=["POST", "GET"], endpoint="switch_user")
    @csrf.exempt
    def switch_user(user_id):
        user = User.query.get(user_id)
        if user:
            login_user(user)
            set_active_context(user, "host" if user.is_host and not user.is_seeker else "seeker")
            return redirect(request.referrer or url_for("index"))
        return redirect(url_for("index"))

    @app.route("/api/dev/toggle-ai-simulation", methods=["POST", "GET"], endpoint="toggle_ai_simulation")
    def toggle_ai_simulation():
        from space_ai import set_simulate_ai_failure
        current_val = session.get("simulate_ai_failure", False)
        new_val = not current_val
        session["simulate_ai_failure"] = new_val
        set_simulate_ai_failure(new_val)
        return redirect(request.referrer or url_for("index"))

    # =========================================================================
    # AUTHENTICATION & DEMO SWITCHER ROUTES
    # =========================================================================
    @app.route("/login")
    @app.route("/auth/login", methods=["GET", "POST"], endpoint="auth_login")
    def auth_login():
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form or {}
            email = sanitize_string(data.get("email", ""), max_length=120)
            password = data.get("password", "")
            user, err = AuthService.authenticate_user(email, password)
            if user:
                login_user(user)
                if request.is_json:
                    return jsonify({"success": True, "user": user.to_dict()})
                next_url = request.args.get("next")
                if not next_url or not next_url.startswith("/"):
                    next_url = url_for("dashboard_page")
                return redirect(next_url)
            if request.is_json:
                return jsonify({"success": False, "error": err}), 401
            flash(err, "danger")
            return render_template("auth/login.html"), 401
        return render_template("auth/login.html")

    @app.route("/auth/register", methods=["GET", "POST"], endpoint="auth_register")
    def auth_register():
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form or {}
            user, _, err = AuthService.register_user(
                first_name=sanitize_string(data.get("first_name", "Guest")),
                last_name=sanitize_string(data.get("last_name", "")),
                email=sanitize_string(data.get("email", "")),
                password=data.get("password", ""),
                confirm_password=data.get("confirm_password", data.get("password", "")),
                role=data.get("role", "seeker")
            )
            if user:
                login_user(user)
                if request.is_json:
                    return jsonify({"success": True, "user": user.to_dict()}), 201
                return redirect(url_for("index"))
            if request.is_json:
                return jsonify({"success": False, "error": err}), 400
            flash(err, "danger")
            return render_template("auth/register.html"), 400
        return render_template("auth/register.html")

    @app.route("/auth/logout", methods=["POST", "GET"], endpoint="auth_logout")
    def auth_logout():
        logout_user()
        if request.is_json:
            return jsonify({"success": True, "message": "Logged out."})
        return redirect(url_for("index"))

    @app.route("/auth/forgot-password", methods=["GET", "POST"], endpoint="auth_forgot_password")
    def auth_forgot_password():
        if request.method == "POST":
            email = request.form.get("email", "")
            _, msg, raw_token = AuthService.request_password_reset(email)
            flash(msg, "info")
            return redirect(url_for("auth_login"))
        return render_template("auth/forgot_password.html")

    @app.route("/auth/reset-password/<token>", methods=["GET", "POST"], endpoint="auth_reset_password")
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

    @app.route("/auth/verify-email/<token>", endpoint="auth_verify_email")
    def auth_verify_email(token):
        success, msg = AuthService.verify_email(token)
        return render_template("auth/verify_email.html", success=success, message=msg)

    @app.route("/auth/access-denied", endpoint="auth_access_denied")
    def auth_access_denied():
        return render_template("auth/access_denied.html"), 403

    @app.route("/auth/demo-switch/<role>", methods=["GET", "POST"])
    @csrf.exempt
    def demo_switch_handler(role):
        """Demo switcher for presentation and reviewer walkthroughs."""
        clean_role = role.lower().strip()
        if clean_role in ("host", "owner"):
            user = User.query.filter_by(email="sunita@spaceloop.in").first()
        elif clean_role == "admin":
            user = User.query.filter_by(email="admin@spaceloop.in").first()
        else:
            user = User.query.filter_by(email="aarav@iitd.ac.in").first()

        if not user:
            user = User.query.first()

        if user:
            login_user(user)
            set_active_context(user, "host" if user.is_host and not user.is_seeker else "seeker")
            if request.is_json or request.headers.get("Accept", "").find("application/json") != -1:
                return jsonify({"success": True, "role": clean_role, "user": user.to_dict()}), 200
            return redirect(request.referrer or url_for("root_spa"))

        return jsonify({"success": False, "error": "Demo persona not found"}), 404

    @app.route("/switch-role", methods=["GET", "POST"], endpoint="switch_role")
    @login_required
    def switch_role():
        target = request.args.get("role") or request.form.get("role") or ("host" if current_user.role != "host" else "seeker")
        set_active_context(current_user, target)
        return redirect(request.referrer or url_for("index"))

    # =========================================================================
    # ERROR HANDLERS
    # =========================================================================
    @app.errorhandler(404)
    def handle_404_error(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({
                "success": False,
                "error": "Resource not found (404)",
                "requested_path": request.path
            }), 404
        # For non-API routes, let the client-side SPA router handle navigation if dist exists
        if os.path.exists(os.path.join(dist_dir, "index.html")):
            return _serve_spa_index()
        return render_template("404.html", user=current_user.to_dict() if current_user.is_authenticated else None), 404

    @app.errorhandler(500)
    def handle_500_error(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "error": "Internal server error (500)"}), 500
        return render_template("500.html", user=current_user.to_dict() if current_user.is_authenticated else None), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
