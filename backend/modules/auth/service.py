from datetime import datetime, timedelta
import re
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError
from models import db, User, PasswordResetToken, EmailVerificationToken
from backend.modules.auth.password import (
    validate_password_complexity,
    hash_password,
    verify_password,
    dummy_verify_password
)
from backend.modules.auth.tokens import generate_secure_token, hash_token
from backend.modules.auth.audit import record_audit


class AuthService:

    @staticmethod
    def register_user(first_name: str, last_name: str, email: str, password: str, confirm_password: str, role: str = "seeker") -> tuple[User | None, str, str]:
        """
        Validates and registers a new SpaceLoop user.
        Returns: (user, raw_verification_token, error_message)
        """
        first_name = (first_name or "").strip()[:60]
        last_name = (last_name or "").strip()[:60]
        email = (email or "").strip().lower()

        if not first_name:
            return None, "", "First name is required."

        if len(email) > 254:
            return None, "", "Email address must not exceed 254 characters."

        # Validate email
        try:
            valid = validate_email(email, check_deliverability=False)
            email = valid.normalized
        except EmailNotValidError as e:
            return None, "", f"Invalid email format: {str(e)}"

        # Check existing user
        if User.query.filter(db.func.lower(User.email) == email).first():
            return None, "", "An account with this email already exists."

        # Validate password
        if password != confirm_password:
            return None, "", "Passwords do not match."

        is_valid, msg = validate_password_complexity(password)
        if not is_valid:
            return None, "", msg

        # Role restriction: NEVER allow registration to claim admin
        target_role = (role or "seeker").lower().strip()
        if target_role not in ("seeker", "owner", "both"):
            target_role = "seeker"

        full_name = f"{first_name} {last_name}".strip()

        user = User(
            name=full_name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=target_role,
            is_active=True,
            is_email_verified=False,
            is_admin=False
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.flush()  # assign user.id

            # Generate email verification token (24h expiry)
            raw_token, token_hash = generate_secure_token()
            verif_token = EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(days=1)
            )
            db.session.add(verif_token)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None, "", "An account with this email already exists."
        except Exception:
            db.session.rollback()
            return None, "", "Registration failed due to a database error."

        record_audit("AUTH_REGISTER_SUCCESS", user_id=user.id, details={"email": email, "role": target_role})
        return user, raw_token, ""

    @staticmethod
    def authenticate_user(email: str, password: str) -> tuple[User | None, str]:
        """
        Authenticates credentials with generic error messages and constant-time delay.
        Returns: (user, error_message)
        """
        clean_email = (email or "").strip().lower()
        generic_error = "Invalid email or password."

        if not clean_email or not password:
            dummy_verify_password()
            return None, generic_error

        # Mitigate DoS via excessively long password or email inputs
        if len(password) > 128 or len(clean_email) > 254:
            dummy_verify_password()
            record_audit("AUTH_LOGIN_FAILED", details={"email": clean_email[:50], "reason": "credential_length_exceeded"})
            return None, generic_error

        user = User.query.filter(db.func.lower(User.email) == clean_email).first()

        if not user or not user.is_active:
            dummy_verify_password()
            record_audit("AUTH_LOGIN_FAILED", details={"email": clean_email, "reason": "user_not_found_or_inactive"})
            return None, generic_error

        if not user.check_password(password):
            record_audit("AUTH_LOGIN_FAILED", user_id=user.id, details={"email": clean_email, "reason": "invalid_password"})
            return None, generic_error

        user.last_login_at = datetime.utcnow()
        db.session.commit()

        record_audit("AUTH_LOGIN_SUCCESS", user_id=user.id, details={"email": clean_email})
        return user, ""

    @staticmethod
    def request_password_reset(email: str) -> tuple[bool, str, str]:
        """
        Issues a secure reset token if user exists.
        Always returns generic message to prevent account enumeration.
        Returns: (success, generic_message, raw_token_for_dev_logging)
        """
        generic_msg = "If that email is registered, password reset instructions have been generated."
        clean_email = (email or "").strip().lower()

        if not clean_email:
            return True, generic_msg, ""

        user = User.query.filter(db.func.lower(User.email) == clean_email).first()
        if not user or not user.is_active:
            dummy_verify_password()
            record_audit("AUTH_PASSWORD_RESET_REQUESTED_UNKNOWN", details={"email": clean_email})
            return True, generic_msg, ""

        # Invalidate previous unused reset tokens for this user
        PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({"used": True})

        raw_token, token_hash = generate_secure_token()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used=False
        )
        db.session.add(reset_token)
        db.session.commit()

        record_audit("AUTH_PASSWORD_RESET_REQUESTED", user_id=user.id, details={"email": clean_email})
        return True, generic_msg, raw_token

    @staticmethod
    def reset_password(raw_token: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
        """
        Verifies token and updates password.
        Returns: (success, message)
        """
        if new_password != confirm_password:
            return False, "Passwords do not match."

        is_valid, msg = validate_password_complexity(new_password)
        if not is_valid:
            return False, msg

        token_hash = hash_token(raw_token)
        token_entry = PasswordResetToken.query.filter_by(token_hash=token_hash, used=False).first()

        if not token_entry or not token_entry.is_valid():
            return False, "This password reset link is invalid or has expired."

        user = User.query.get(token_entry.user_id)
        if not user or not user.is_active:
            return False, "Associated user account is unavailable."

        user.set_password(new_password)
        token_entry.used = True
        db.session.commit()

        record_audit("AUTH_PASSWORD_RESET_SUCCESS", user_id=user.id)
        return True, "Your password has been successfully reset. Please log in."

    @staticmethod
    def verify_email(raw_token: str) -> tuple[bool, str]:
        """
        Validates token and marks email verified.
        Returns: (success, message)
        """
        token_hash = hash_token(raw_token)
        token_entry = EmailVerificationToken.query.filter_by(token_hash=token_hash, used=False).first()

        if not token_entry or not token_entry.is_valid():
            return False, "This verification link is invalid or has expired."

        user = User.query.get(token_entry.user_id)
        if not user:
            return False, "User not found."

        user.is_email_verified = True
        token_entry.used = True
        db.session.commit()

        record_audit("AUTH_EMAIL_VERIFIED", user_id=user.id)
        return True, "Your email address has been successfully verified."
