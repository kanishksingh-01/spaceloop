from flask import Blueprint, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from backend.modules.auth.service import AuthService
from backend.modules.auth.session import set_active_context
from backend.modules.auth.audit import record_audit

api_v1_auth = Blueprint("api_v1_auth", __name__, url_prefix="/api/v1/auth")


def safe_user_profile(user):
    return {
        "public_id": user.public_id,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "is_host": user.is_host,
        "is_seeker": user.is_seeker,
        "is_admin": user.is_admin,
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
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    user, error = AuthService.authenticate_user(email, password)
    if not user:
        return jsonify({"success": False, "error": error}), 401

    login_user(user, remember=bool(data.get("remember", False)))
    set_active_context(user, "host" if user.role == "owner" else "seeker")

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": safe_user_profile(user)
    }), 200


@api_v1_auth.route("/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    user, raw_token, error = AuthService.register_user(
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        email=data.get("email", ""),
        password=data.get("password", ""),
        confirm_password=data.get("confirm_password", ""),
        role=data.get("role", "seeker")
    )
    if not user:
        return jsonify({"success": False, "error": error}), 400

    login_user(user)
    set_active_context(user, "host" if user.role == "owner" else "seeker")

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "user": safe_user_profile(user)
    }), 201


@api_v1_auth.route("/logout", methods=["POST"])
@login_required
def api_logout():
    user_id = current_user.id
    logout_user()
    record_audit("AUTH_LOGOUT", user_id=user_id)
    return jsonify({"success": True, "message": "Logged out successfully"}), 200
