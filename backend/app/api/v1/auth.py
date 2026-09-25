import re
import secrets
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from models import db, User
from config import Config
from backend.app.extensions import limiter
from backend.modules.auth.service import AuthService
from backend.modules.auth.session import set_active_context
from backend.modules.auth.audit import record_audit
from backend.modules.auth.email_service import EmailService
from space_ai import (
    verify_aadhaar_otp,
    verify_academic_credentials,
    verify_host_electricity_bill,
    verify_upi_penny_drop,
    compute_objective_trust_index,
    get_oti_breakdown
)
from security import sanitize_string

api_v1_auth = Blueprint("api_v1_auth", __name__, url_prefix="/api/v1/auth")


def safe_user_profile(user):
    raw_oti = getattr(user, "objective_trust_score", 98.5) or 98.5
    oti_score = round(raw_oti if raw_oti <= 100.0 else raw_oti / 10.0, 1)
    oti_breakdown = get_oti_breakdown(
        punctuality=getattr(user, "on_time_vacate_rate", 100.0),
        condition_match=getattr(user, "cleanliness_match_rate", 99.0),
        is_identity_verified=bool(getattr(user, "is_aadhaar_verified", False) or getattr(user, "is_student_verified", False) or getattr(user, "is_host_verified", False)),
        dispute_count=getattr(user, "dispute_count", 0)
    )

    return {
        "id": user.id,
        "public_id": user.public_id,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "is_host": user.is_host,
        "is_seeker": user.is_seeker,
        "is_admin": user.is_admin,
        "college_verified": getattr(user, "is_student_verified", False),
        "host_verified": getattr(user, "is_host_verified", False),
        "is_host_verified": getattr(user, "is_host_verified", False),
        "discom_provider": getattr(user, "discom_provider", "") or "",
        "discom_ca_masked": getattr(user, "discom_ca_masked", "") or "",
        "upi_verified": bool(getattr(user, "upi_verified", False)),
        "upi_vpa_masked": getattr(user, "upi_vpa_masked", "") or "",
        "bank_beneficiary_name": getattr(user, "bank_beneficiary_name", "") or "",
        "trust_score": oti_score,
        "objective_trust_score": oti_score,
        "oti_breakdown": oti_breakdown,
        "avatar_url": user.avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={user.name}",
        "phone": getattr(user, "phone", "") or "",
        "college_name": getattr(user, "college_name", "") or "",
        "is_email_verified": user.is_email_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@api_v1_auth.route("/me", methods=["GET"])
@login_required
def get_me():
    """
    Returns safe authenticated profile. Excludes password hashes and sensitive tokens.
    """
    return jsonify({
        "success": True,
        "authenticated": True,
        "user": safe_user_profile(current_user)
    }), 200


@api_v1_auth.route("/login", methods=["POST"])
@limiter.limit(Config.AUTH_LOGIN_RATE_LIMIT)
def api_login():
    data = request.get_json(silent=True) or {}
    email = sanitize_string(data.get("email", ""), max_length=120)
    password = data.get("password", "")

    user, error = AuthService.authenticate_user(email, password)
    if not user or not user.is_active:
        return jsonify({"success": False, "error": error or "Invalid email or password."}), 401

    login_user(user, remember=bool(data.get("remember", False)))
    set_active_context(user, "host" if user.is_host and not user.is_seeker else "seeker")

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/register", methods=["POST"])
@limiter.limit(Config.AUTH_REGISTER_RATE_LIMIT)
def api_register():
    data = request.get_json(silent=True) or {}
    first_name = sanitize_string(data.get("first_name", ""), max_length=60)
    last_name = sanitize_string(data.get("last_name", ""), max_length=60)
    
    # If name is provided instead of first/last
    if not first_name and data.get("name"):
        parts = str(data.get("name")).strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    email = sanitize_string(data.get("email", ""), max_length=120)
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", password)
    role = sanitize_string(data.get("role", "seeker"), max_length=20)

    user, raw_token, error = AuthService.register_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        confirm_password=confirm_password,
        role=role
    )
    if not user:
        return jsonify({"success": False, "error": error}), 400

    login_user(user)
    set_active_context(user, "host" if user.is_host else "seeker")

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "user": safe_user_profile(user)
    }), 201


# =========================================================================
# DEDICATED SEEKER AUTHENTICATION ENDPOINTS
# =========================================================================
@api_v1_auth.route("/seeker/login", methods=["POST"])
@limiter.limit(Config.AUTH_LOGIN_RATE_LIMIT)
def api_seeker_login():
    """Dedicated Seeker Login for workspace searchers."""
    data = request.get_json(silent=True) or {}
    email = sanitize_string(data.get("email", ""), max_length=120)
    password = data.get("password", "")

    user, error = AuthService.authenticate_user(email, password)
    if not user or not user.is_active:
        return jsonify({"success": False, "error": error or "Invalid seeker credentials."}), 401

    login_user(user, remember=bool(data.get("remember", False)))
    set_active_context(user, "seeker")

    return jsonify({
        "success": True,
        "message": "Seeker authenticated successfully",
        "portal": "seeker",
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/seeker/register", methods=["POST"])
@limiter.limit(Config.AUTH_REGISTER_RATE_LIMIT)
def api_seeker_register():
    """Dedicated Seeker Registration."""
    data = request.get_json(silent=True) or {}
    first_name = sanitize_string(data.get("first_name", ""), max_length=60)
    last_name = sanitize_string(data.get("last_name", ""), max_length=60)
    if not first_name and data.get("name"):
        parts = str(data.get("name")).strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    email = sanitize_string(data.get("email", ""), max_length=120)
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", password)

    user, raw_token, error = AuthService.register_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        confirm_password=confirm_password,
        role="seeker"
    )
    if not user:
        return jsonify({"success": False, "error": error}), 400

    login_user(user)
    set_active_context(user, "seeker")

    return jsonify({
        "success": True,
        "message": "Seeker account created successfully",
        "portal": "seeker",
        "user": safe_user_profile(user)
    }), 201


# =========================================================================
# DEDICATED HOST AUTHENTICATION & VERIFICATION ENDPOINTS
# =========================================================================
@api_v1_auth.route("/host/login", methods=["POST"])
@limiter.limit(Config.AUTH_LOGIN_RATE_LIMIT)
def api_host_login():
    """Dedicated Host Login with host permission verification."""
    data = request.get_json(silent=True) or {}
    email = sanitize_string(data.get("email", ""), max_length=120)
    password = data.get("password", "")

    user, error = AuthService.authenticate_user(email, password)
    if not user or not user.is_active:
        return jsonify({"success": False, "error": error or "Invalid host credentials."}), 401

    if not user.is_host:
        return jsonify({
            "success": False,
            "error": "This account is registered as a Seeker only. Please complete Host Property KYC to unlock the Host Portal."
        }), 403

    login_user(user, remember=bool(data.get("remember", False)))
    set_active_context(user, "host")

    return jsonify({
        "success": True,
        "message": "Host authenticated successfully",
        "portal": "host",
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/host/register", methods=["POST"])
@limiter.limit(Config.AUTH_REGISTER_RATE_LIMIT)
def api_host_register():
    """Dedicated Host Registration with Discom Utility & UPI Penny Drop verification."""
    data = request.get_json(silent=True) or {}
    first_name = sanitize_string(data.get("first_name", ""), max_length=60)
    last_name = sanitize_string(data.get("last_name", ""), max_length=60)
    if not first_name and data.get("name"):
        parts = str(data.get("name")).strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    email = sanitize_string(data.get("email", ""), max_length=120)
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", password)

    # Discom & UPI verification details
    ca_number = sanitize_string(data.get("ca_number") or data.get("discom_ca") or "", max_length=50)
    provider = sanitize_string(data.get("provider") or data.get("discom_provider") or "BESCOM", max_length=80)
    address = sanitize_string(data.get("address", ""), max_length=200)
    upi_vpa = sanitize_string(data.get("upi_vpa", ""), max_length=80)
    pan_name = sanitize_string(data.get("pan_name") or data.get("bank_beneficiary_name") or f"{first_name} {last_name}".strip(), max_length=100)

    # 1. Verify property electricity bill (Discom)
    discom_res = verify_host_electricity_bill(ca_number, provider, address, pan_name)
    if not discom_res.get("success"):
        return jsonify({"success": False, "error": f"Discom KYC failed: {discom_res.get('error')}"}), 400

    # 2. Verify payout UPI account (Penny drop)
    upi_res = verify_upi_penny_drop(upi_vpa, pan_name)
    if not upi_res.get("success"):
        return jsonify({"success": False, "error": f"Payout verification failed: {upi_res.get('error')}"}), 400

    # 3. Create host user or elevate existing user
    user, raw_token, error = AuthService.register_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        confirm_password=confirm_password,
        role="host"
    )

    if not user:
        return jsonify({"success": False, "error": error}), 400

    # Persist verified infrastructure credentials
    user.is_host_verified = True
    user.discom_provider = discom_res["provider"]
    user.discom_ca_masked = discom_res["ca_number_masked"]
    user.upi_verified = True
    user.upi_vpa_masked = upi_res["upi_vpa_masked"]
    user.bank_beneficiary_name = upi_res["beneficiary_name"]
    user.objective_trust_score = 98.5
    db.session.commit()

    login_user(user)
    set_active_context(user, "host")

    return jsonify({
        "success": True,
        "message": "Host registered and verified via Discom CA & UPI Penny Drop",
        "portal": "host",
        "discom": discom_res,
        "upi": upi_res,
        "user": safe_user_profile(user)
    }), 201


@api_v1_auth.route("/host/upgrade", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def api_host_upgrade():
    """Elevates authenticated Seeker to Verified Host."""
    data = request.get_json(silent=True) or {}
    ca_number = sanitize_string(data.get("ca_number") or data.get("discom_ca") or "", max_length=50)
    provider = sanitize_string(data.get("provider") or data.get("discom_provider") or "BESCOM", max_length=80)
    address = sanitize_string(data.get("address", ""), max_length=200)
    upi_vpa = sanitize_string(data.get("upi_vpa", ""), max_length=80)
    pan_name = sanitize_string(data.get("pan_name") or data.get("bank_beneficiary_name") or current_user.name, max_length=100)

    # 1. Verify property electricity bill (Discom)
    discom_res = verify_host_electricity_bill(ca_number, provider, address, pan_name)
    if not discom_res.get("success"):
        return jsonify({"success": False, "error": f"Discom KYC failed: {discom_res.get('error')}"}), 400

    # 2. Verify payout UPI account (Penny drop)
    upi_res = verify_upi_penny_drop(upi_vpa, pan_name)
    if not upi_res.get("success"):
        return jsonify({"success": False, "error": f"Payout verification failed: {upi_res.get('error')}"}), 400

    # Elevate role
    if current_user.role == "seeker":
        current_user.role = "both"
    elif current_user.role not in ("host", "owner", "both"):
        current_user.role = "both"

    current_user.is_host_verified = True
    current_user.discom_provider = discom_res["provider"]
    current_user.discom_ca_masked = discom_res["ca_number_masked"]
    current_user.upi_verified = True
    current_user.upi_vpa_masked = upi_res["upi_vpa_masked"]
    current_user.bank_beneficiary_name = upi_res["beneficiary_name"]
    current_user.objective_trust_score = max(getattr(current_user, "objective_trust_score", 90.0) or 90.0, 98.0)
    db.session.commit()

    set_active_context(current_user, "host")

    return jsonify({
        "success": True,
        "message": "Account successfully elevated to Verified Host! You can now list and monetize spaces.",
        "portal": "host",
        "discom": discom_res,
        "upi": upi_res,
        "user": safe_user_profile(current_user)
    }), 200


@api_v1_auth.route("/digilocker", methods=["POST"])
@limiter.limit("10 per minute")
def api_digilocker_login():
    """
    DigiLocker / Aadhaar verification auth method.
    Verifies Aadhaar OTP, creates account with cryptographic random unusable password,
    or links credential to already authenticated user.
    """
    data = request.get_json(silent=True) or {}
    name = sanitize_string(data.get("name", "DigiLocker User"), max_length=100)
    aadhaar_num = sanitize_string(data.get("aadhaar_number", ""), max_length=20)
    otp = sanitize_string(data.get("otp", ""), max_length=10)
    role = sanitize_string(data.get("role", "seeker"), max_length=20)

    aadhaar_res = verify_aadhaar_otp(name, aadhaar_num, otp)
    if not aadhaar_res.get("success"):
        return jsonify({"success": False, "error": aadhaar_res.get("error")}), 400

    masked = aadhaar_res["masked_aadhaar"]

    # If user is already authenticated, link to existing profile
    if current_user.is_authenticated:
        current_user.is_aadhaar_verified = True
        current_user.aadhaar_masked = masked
        current_user.aadhaar_token_hash = aadhaar_res["token_hash"]
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "DigiLocker Aadhaar credential linked to your account",
            "user": safe_user_profile(current_user)
        }), 200

    # Look for existing user with this synthetic token email
    synthetic_email = f"aadhaar_{masked.replace('-', '')}@spaceloop.in".lower()
    user = User.query.filter_by(email=synthetic_email).first()

    if not user:
        name_parts = name.split(" ", 1)
        user = User(
            name=name,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email=synthetic_email,
            role=role if role in ("seeker", "host", "owner") else "seeker",
            is_active=True,
            is_email_verified=True,
            is_aadhaar_verified=True,
            aadhaar_masked=masked,
            aadhaar_token_hash=aadhaar_res["token_hash"],
            is_student_verified=(role == "seeker"),
            is_host_verified=(role in ("host", "owner")),
            objective_trust_score=98.0
        )
        # Cryptographically secure random unusable password: cannot be brute-forced via normal login
        user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)
        db.session.commit()
    else:
        user.is_aadhaar_verified = True
        user.aadhaar_masked = masked
        db.session.commit()

    login_user(user)
    set_active_context(user, "host" if user.is_host else "seeker")
    return jsonify({
        "success": True,
        "message": "DigiLocker authentication verified",
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/student-sso", methods=["POST"])
@limiter.limit("10 per minute")
def api_student_sso_login():
    """
    University Academic SSO authentication method.
    Verifies college domain credential and authenticates student.
    Uses cryptographically random unusable password for newly provisioned accounts.
    """
    data = request.get_json(silent=True) or {}
    college_email = sanitize_string(data.get("college_email", ""), max_length=120).lower()
    student_name = sanitize_string(data.get("name", "Student Scholar"), max_length=100)
    college_name = sanitize_string(data.get("college_name", ""), max_length=150)
    student_id = sanitize_string(data.get("student_id", ""), max_length=50)

    acad_res = verify_academic_credentials(college_email, student_id, college_name)
    if not acad_res.get("success"):
        return jsonify({"success": False, "error": acad_res.get("error")}), 400

    # If user is already authenticated, link university verification
    if current_user.is_authenticated:
        current_user.is_student_verified = True
        current_user.college_name = acad_res["college_name"]
        current_user.college_email = acad_res["college_email"]
        current_user.student_id_masked = acad_res["student_id_masked"]
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Academic credentials linked to your account",
            "user": safe_user_profile(current_user)
        }), 200

    user = User.query.filter(db.func.lower(User.email) == college_email).first()
    if not user:
        name_parts = student_name.split(" ", 1)
        user = User(
            name=student_name,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email=college_email,
            role="seeker",
            is_active=True,
            is_email_verified=True,
            is_student_verified=True,
            college_name=acad_res["college_name"],
            college_email=acad_res["college_email"],
            student_id_masked=acad_res["student_id_masked"],
            objective_trust_score=97.5
        )
        # Cryptographically secure random unusable password: cannot be brute-forced via normal login
        user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)
        db.session.commit()
    else:
        user.is_student_verified = True
        user.college_name = acad_res["college_name"]
        db.session.commit()

    login_user(user)
    set_active_context(user, "seeker")
    return jsonify({
        "success": True,
        "message": "Student SSO authentication successful",
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/forgot-password", methods=["POST"])
@limiter.limit(Config.AUTH_PASSWORD_RESET_RATE_LIMIT)
def api_forgot_password():
    """
    Requests a password reset token and dispatches it via EmailService.
    Always returns generic 200 response to prevent account enumeration.
    """
    data = request.get_json(silent=True) or {}
    email = sanitize_string(data.get("email", ""), max_length=120)
    success, msg, raw_token = AuthService.request_password_reset(email)
    if raw_token:
        EmailService.send_password_reset(email, raw_token)
    return jsonify({
        "success": True,
        "message": msg
    }), 200


@api_v1_auth.route("/reset-password", methods=["POST"])
@limiter.limit(Config.AUTH_PASSWORD_RESET_RATE_LIMIT)
def api_reset_password():
    """
    Resets user password with valid single-use token and password complexity verification.
    """
    data = request.get_json(silent=True) or {}
    token = sanitize_string(data.get("token", ""), max_length=100)
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    success, msg = AuthService.reset_password(token, password, confirm_password)
    if not success:
        return jsonify({"success": False, "error": msg}), 400

    return jsonify({
        "success": True,
        "message": msg
    }), 200


@api_v1_auth.route("/logout", methods=["POST"])
@login_required
def api_logout():
    user_id = current_user.id
    logout_user()
    record_audit("AUTH_LOGOUT", user_id=user_id)
    return jsonify({"success": True, "message": "Logged out successfully"}), 200
