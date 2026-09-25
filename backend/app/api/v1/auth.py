import re
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect
from flask_login import current_user, login_user, logout_user, login_required
from models import db, User, MFARecoveryCode
from config import Config
from backend.app.extensions import limiter
from backend.modules.auth.service import AuthService
from backend.modules.auth.session import set_active_context
from backend.modules.auth.audit import record_audit
from backend.modules.auth.email_service import EmailService
from backend.modules.auth.email_validation import validate_email_address
from backend.modules.auth.mfa import (
    generate_totp_secret,
    encrypt_totp_secret,
    decrypt_totp_secret,
    get_totp_provisioning_uri,
    generate_qr_data_uri,
    verify_totp_code,
    generate_recovery_codes,
    hash_recovery_code,
    generate_mfa_challenge_token,
    verify_mfa_challenge_token,
    generate_mfa_setup_token,
    verify_mfa_setup_token,
)
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
        "mfa_enabled": bool(getattr(user, "mfa_enabled", False)),
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

    if not user.is_email_verified:
        record_audit("AUTH_LOGIN_BLOCKED_UNVERIFIED_EMAIL", user_id=user.id, details={"email": user.email})
        return jsonify({
            "success": False,
            "error": "Please verify your email address before logging in.",
            "email_verification_required": True,
            "email": user.email
        }), 403

    if getattr(user, "mfa_enabled", False):
        mfa_token = generate_mfa_challenge_token(user.id)
        record_audit("AUTH_MFA_CHALLENGE_ISSUED", user_id=user.id)
        return jsonify({
            "success": True,
            "mfa_required": True,
            "mfa_token": mfa_token,
            "email": user.email,
            "message": "Two-factor authentication required. Please enter your authenticator code."
        }), 200

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

    # Dispatch email verification link
    EmailService.send_email_verification(user.email, raw_token)

    # Note: User session is NOT established until email ownership is verified.
    return jsonify({
        "success": True,
        "email_verification_required": True,
        "email": user.email,
        "message": "Registration successful. Please verify your email address before logging in.",
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

    if not user.is_email_verified:
        record_audit("AUTH_LOGIN_BLOCKED_UNVERIFIED_EMAIL", user_id=user.id, details={"email": user.email, "portal": "seeker"})
        return jsonify({
            "success": False,
            "error": "Please verify your email address before logging in.",
            "email_verification_required": True,
            "email": user.email,
            "portal": "seeker"
        }), 403

    if getattr(user, "mfa_enabled", False):
        mfa_token = generate_mfa_challenge_token(user.id)
        record_audit("AUTH_MFA_CHALLENGE_ISSUED", user_id=user.id)
        return jsonify({
            "success": True,
            "mfa_required": True,
            "mfa_token": mfa_token,
            "email": user.email,
            "portal": "seeker",
            "message": "Two-factor authentication required. Please enter your authenticator code."
        }), 200

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

    # Dispatch email verification link
    EmailService.send_email_verification(user.email, raw_token)

    # Note: User session is NOT established until email ownership is verified.
    return jsonify({
        "success": True,
        "email_verification_required": True,
        "email": user.email,
        "message": "Seeker account created. Please verify your email address before logging in.",
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

    if not user.is_email_verified:
        record_audit("AUTH_LOGIN_BLOCKED_UNVERIFIED_EMAIL", user_id=user.id, details={"email": user.email, "portal": "host"})
        return jsonify({
            "success": False,
            "error": "Please verify your email address before logging in.",
            "email_verification_required": True,
            "email": user.email,
            "portal": "host"
        }), 403

    if not user.is_host:
        return jsonify({
            "success": False,
            "error": "This account is registered as a Seeker only. Please complete Host Property KYC to unlock the Host Portal."
        }), 403

    if getattr(user, "mfa_enabled", False):
        mfa_token = generate_mfa_challenge_token(user.id)
        record_audit("AUTH_MFA_CHALLENGE_ISSUED", user_id=user.id)
        return jsonify({
            "success": True,
            "mfa_required": True,
            "mfa_token": mfa_token,
            "email": user.email,
            "portal": "host",
            "message": "Two-factor authentication required. Please enter your authenticator code."
        }), 200

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

    # Dispatch email verification link
    EmailService.send_email_verification(user.email, raw_token)

    # Note: User session is NOT established until email ownership is verified.
    return jsonify({
        "success": True,
        "email_verification_required": True,
        "email": user.email,
        "message": "Host registered. Please verify your email address before logging in.",
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


# =========================================================================
# MULTI-FACTOR AUTHENTICATION (MFA / TOTP RFC 6238) ENDPOINTS
# =========================================================================

@api_v1_auth.route("/mfa/setup", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_mfa_setup():
    """
    Initiates TOTP MFA enrollment.
    Strictly enforces email verification before generating any TOTP secrets.
    """
    if not current_user.is_email_verified:
        return jsonify({
            "success": False,
            "error": "Email verification is required before enrolling in Multi-Factor Authentication. Please verify your email address first.",
            "email_verification_required": True,
            "email": current_user.email
        }), 403

    if current_user.mfa_enabled:
        return jsonify({
            "success": False,
            "error": "Multi-Factor Authentication is already enabled for this account."
        }), 400

    secret = generate_totp_secret()
    otpauth_uri = get_totp_provisioning_uri(secret, current_user.email)
    qr_code = generate_qr_data_uri(otpauth_uri)
    setup_token = generate_mfa_setup_token(current_user.id, secret)

    return jsonify({
        "success": True,
        "secret": secret,
        "qr_code": qr_code,
        "otpauth_uri": otpauth_uri,
        "setup_token": setup_token
    }), 200


@api_v1_auth.route("/mfa/verify-setup", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def api_mfa_verify_setup():
    """
    Verifies the first TOTP code to finalize MFA enrollment.
    Only enables MFA and persists encrypted secret and hashed recovery codes after confirmation.
    """
    data = request.get_json(silent=True) or {}
    setup_token = data.get("setup_token", "")
    code = data.get("code", "")

    if not setup_token or not code:
        return jsonify({"success": False, "error": "Setup token and 6-digit verification code are required."}), 400

    user_id, secret = verify_mfa_setup_token(setup_token)
    if not user_id or user_id != current_user.id or not secret:
        return jsonify({"success": False, "error": "MFA setup session has expired or is invalid. Please restart setup."}), 400

    if not verify_totp_code(secret, code):
        return jsonify({
            "success": False,
            "error": "Invalid 6-digit verification code. Please check your authenticator app and system clock, then try again."
        }), 400

    # Verification successful: store encrypted secret and activate MFA
    current_user.mfa_enabled = True
    current_user.totp_secret = encrypt_totp_secret(secret)

    # Generate 10 single-use recovery codes
    recovery_codes = generate_recovery_codes(10)
    MFARecoveryCode.query.filter_by(user_id=current_user.id).delete()
    for rc in recovery_codes:
        db.session.add(MFARecoveryCode(
            user_id=current_user.id,
            code_hash=hash_recovery_code(rc),
            used=False
        ))

    db.session.commit()
    record_audit("AUTH_MFA_ENROLLED", user_id=current_user.id)

    return jsonify({
        "success": True,
        "message": "Multi-Factor Authentication enabled successfully.",
        "recovery_codes": recovery_codes,
        "user": safe_user_profile(current_user)
    }), 200


@api_v1_auth.route("/mfa/verify", methods=["POST"])
@limiter.limit("5 per minute")
def api_mfa_verify_login():
    """
    Validates MFA challenge via 6-digit TOTP code or single-use recovery code.
    Upon successful verification, establishes authenticated session.
    """
    data = request.get_json(silent=True) or {}
    mfa_token = data.get("mfa_token", "")
    code = data.get("code", "")
    recovery_code = data.get("recovery_code", "")

    if not mfa_token:
        return jsonify({"success": False, "error": "MFA session token is missing."}), 400

    user_id = verify_mfa_challenge_token(mfa_token)
    if not user_id:
        return jsonify({"success": False, "error": "MFA challenge session expired or invalid. Please log in again."}), 400

    user = User.query.get(user_id)
    if not user or not user.is_active or not user.mfa_enabled:
        return jsonify({"success": False, "error": "Account not eligible for MFA challenge."}), 400

    method_used = ""
    if code:
        raw_secret = decrypt_totp_secret(user.totp_secret)
        if not raw_secret or not verify_totp_code(raw_secret, code):
            return jsonify({"success": False, "error": "Invalid 6-digit authentication code."}), 400
        method_used = "totp"
    elif recovery_code:
        chash = hash_recovery_code(recovery_code)
        rec_entry = MFARecoveryCode.query.filter_by(user_id=user.id, code_hash=chash, used=False).first()
        if not rec_entry:
            return jsonify({"success": False, "error": "Invalid or already used backup recovery code."}), 400
        rec_entry.used = True
        rec_entry.used_at = datetime.utcnow()
        db.session.commit()
        method_used = "recovery_code"
    else:
        return jsonify({"success": False, "error": "Please provide a 6-digit TOTP code or backup recovery code."}), 400

    login_user(user, remember=bool(data.get("remember", False)))
    context = data.get("portal") or ("host" if user.is_host and not user.is_seeker else "seeker")
    set_active_context(user, context)
    record_audit(f"AUTH_MFA_LOGIN_SUCCESS_{method_used.upper()}", user_id=user.id)

    return jsonify({
        "success": True,
        "message": "Authenticated successfully with two-factor authentication.",
        "portal": context,
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/mfa/disable", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def api_mfa_disable():
    """
    Disables MFA for the authenticated user.
    Requires password confirmation PLUS either a valid TOTP code or recovery code.
    Purges secret and all recovery codes upon deactivation.
    """
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    code = data.get("code", "")
    recovery_code = data.get("recovery_code", "")

    if not current_user.mfa_enabled:
        return jsonify({"success": False, "error": "Multi-Factor Authentication is not enabled on this account."}), 400

    if not password or not current_user.check_password(password):
        return jsonify({"success": False, "error": "Incorrect account password."}), 401

    if code:
        raw_secret = decrypt_totp_secret(current_user.totp_secret)
        if not raw_secret or not verify_totp_code(raw_secret, code):
            return jsonify({"success": False, "error": "Invalid 6-digit authentication code."}), 400
    elif recovery_code:
        chash = hash_recovery_code(recovery_code)
        rec_entry = MFARecoveryCode.query.filter_by(user_id=current_user.id, code_hash=chash, used=False).first()
        if not rec_entry:
            return jsonify({"success": False, "error": "Invalid or already used backup recovery code."}), 400
        rec_entry.used = True
        rec_entry.used_at = datetime.utcnow()
    else:
        return jsonify({
            "success": False,
            "error": "A valid 6-digit TOTP code or backup recovery code is required to confirm deactivation."
        }), 400

    current_user.mfa_enabled = False
    current_user.totp_secret = None
    MFARecoveryCode.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    record_audit("AUTH_MFA_DISABLED", user_id=current_user.id)

    return jsonify({
        "success": True,
        "message": "Multi-Factor Authentication disabled successfully.",
        "user": safe_user_profile(current_user)
    }), 200


@api_v1_auth.route("/resend-verification", methods=["POST"])
@limiter.limit("3 per minute")
def api_resend_verification():
    """
    Resends email verification link.
    Supports authenticated users OR unauthenticated requests with {"email": "..."}.
    Enforces anti-enumeration defense by returning an identical generic response.
    """
    generic_msg = "If this email address is registered and unverified, a verification link has been sent. Please check your inbox."
    target_user = None

    if current_user.is_authenticated:
        if current_user.is_email_verified:
            return jsonify({"success": True, "message": "Email is already verified."}), 200
        target_user = current_user
    else:
        data = request.get_json(silent=True) or request.form or {}
        raw_email = sanitize_string(data.get("email", ""), max_length=120)
        if not raw_email:
            return jsonify({"success": False, "error": "Email address is required."}), 400

        is_valid, normalized_email, _ = validate_email_address(raw_email, check_disposable=False)
        if is_valid:
            target_user = User.query.filter(db.func.lower(User.email) == normalized_email).first()

    if target_user and not target_user.is_email_verified and target_user.is_active:
        raw_token, _ = AuthService.create_email_verification_token(target_user.id)
        EmailService.send_email_verification(target_user.email, raw_token)
        record_audit("AUTH_VERIFICATION_RESENT", user_id=target_user.id, details={"email": target_user.email})

    return jsonify({
        "success": True,
        "message": generic_msg
    }), 200


@api_v1_auth.route("/verify-email", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def api_verify_email():
    """
    Validates email verification token and marks account verified.
    Supports JSON POST {"token": "..."} and GET ?token=...
    """
    token = ""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        token = data.get("token") or request.form.get("token") or ""
    else:
        token = request.args.get("token", "")

    token = sanitize_string(token, max_length=100)
    if not token:
        return jsonify({"success": False, "error": "Verification token is required."}), 400

    success, message, user = AuthService.verify_email_token(token)
    if not success:
        if request.accept_mimetypes.accept_html and not request.is_json:
            return redirect(f"/auth/verify-email/{token}")
        return jsonify({"success": False, "error": message}), 400

    if request.accept_mimetypes.accept_html and not request.is_json:
        return redirect(f"/auth/verify-email/{token}")

    return jsonify({
        "success": True,
        "message": message,
        "user": safe_user_profile(user) if user else None
    }), 200


@api_v1_auth.route("/change-email", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def api_change_email():
    """
    Initiates email change for authenticated user.
    Keeps current email active and verified until the new email address confirms ownership.
    """
    data = request.get_json(silent=True) or {}
    new_email = sanitize_string(data.get("new_email", ""), max_length=120)
    password = data.get("password", "")

    if not password or not current_user.check_password(password):
        return jsonify({"success": False, "error": "Current password is required to change email."}), 401

    success, msg, raw_token = AuthService.request_email_change(current_user.id, new_email)
    if not success:
        return jsonify({"success": False, "error": msg}), 400

    EmailService.send_email_verification(new_email.strip().lower(), raw_token)
    return jsonify({
        "success": True,
        "message": f"Verification email sent to {new_email}. Please check your inbox to confirm the change."
    }), 200
