"""
SpaceLoop Multi-Factor Authentication (MFA) Engine
Implements TOTP (Time-based One-Time Password, RFC 6238) and Single-Use Recovery Codes.
Compatible with Google Authenticator, Microsoft Authenticator, and standard authenticator apps.
"""
import base64
import hashlib
import io
import re
import secrets
from cryptography.fernet import Fernet
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import pyotp
import qrcode
from config import Config


def _get_fernet_cipher() -> Fernet:
    """
    Derives a deterministic 32-byte URL-safe base64 key from Config.SECRET_KEY
    for encrypting TOTP secrets at rest.
    """
    raw_key = hashlib.sha256(Config.SECRET_KEY.encode("utf-8")).digest()
    urlsafe_key = base64.urlsafe_b64encode(raw_key)
    return Fernet(urlsafe_key)


def encrypt_totp_secret(secret_plaintext: str) -> str:
    """Encrypts a plaintext base32 TOTP secret for secure storage at rest."""
    if not secret_plaintext:
        return ""
    cipher = _get_fernet_cipher()
    return cipher.encrypt(secret_plaintext.encode("utf-8")).decode("utf-8")


def decrypt_totp_secret(secret_encrypted: str) -> str:
    """Decrypts an encrypted TOTP secret retrieved from the database."""
    if not secret_encrypted:
        return ""
    cipher = _get_fernet_cipher()
    return cipher.decrypt(secret_encrypted.encode("utf-8")).decode("utf-8")


def generate_totp_secret() -> str:
    """
    Generates a cryptographically secure 32-character base32 secret for TOTP.
    """
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "SpaceLoop") -> str:
    """
    Constructs the otpauth:// URI for authenticator applications.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_data_uri(otpauth_uri: str) -> str:
    """
    Generates a base64 PNG data URI for the QR code in-memory.
    No image files are saved to disk.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(otpauth_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    b64_encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_encoded}"


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verifies a 6-digit TOTP code against the secret.
    Allows valid_window intervals (+/- 30 seconds) for minor clock drift.
    """
    if not secret or not code:
        return False
    sanitized_code = re.sub(r"\s+", "", str(code))
    if not re.fullmatch(r"\d{6}", sanitized_code):
        return False
    try:
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(sanitized_code, valid_window=valid_window))
    except Exception:
        return False


def generate_recovery_codes(count: int = 10) -> list[str]:
    """
    Generates a list of single-use recovery codes in format 'XXXX-XXXX'.
    """
    codes = []
    for _ in range(count):
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        codes.append(f"{part1}-{part2}")
    return codes


def hash_recovery_code(code: str) -> str:
    """
    Computes deterministic SHA-256 hash of a normalized recovery code.
    Normalizes by stripping whitespace and dashes and converting to lower case.
    """
    normalized = re.sub(r"[\s\-]+", "", str(code or "")).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# Token serializers for MFA Challenge and MFA Enrollment Setup
_mfa_challenge_serializer = URLSafeTimedSerializer(Config.SECRET_KEY, salt="spaceloop-mfa-login-challenge")
_mfa_setup_serializer = URLSafeTimedSerializer(Config.SECRET_KEY, salt="spaceloop-mfa-setup-challenge")


def generate_mfa_challenge_token(user_id: int) -> str:
    """
    Issues a short-lived (5-minute) signed token upon successful password verification
    when the user has MFA enabled.
    """
    payload = {
        "user_id": user_id,
        "purpose": "mfa_login",
        "nonce": secrets.token_hex(8)
    }
    return _mfa_challenge_serializer.dumps(payload)


def verify_mfa_challenge_token(token: str, max_age_seconds: int = 300) -> int | None:
    """
    Verifies the MFA challenge token. Returns user_id if valid and unexpired; else None.
    """
    if not token:
        return None
    try:
        data = _mfa_challenge_serializer.loads(token, max_age=max_age_seconds)
        if data.get("purpose") == "mfa_login" and data.get("user_id"):
            return int(data["user_id"])
    except (BadSignature, SignatureExpired, Exception):
        return None
    return None


def generate_mfa_setup_token(user_id: int, secret: str) -> str:
    """
    Issues a signed 15-minute token during MFA enrollment containing the uncommitted secret.
    This prevents storing unverified secrets in the database before first code confirmation.
    """
    payload = {
        "user_id": user_id,
        "secret": secret,
        "purpose": "mfa_setup",
        "nonce": secrets.token_hex(8)
    }
    return _mfa_setup_serializer.dumps(payload)


def verify_mfa_setup_token(token: str, max_age_seconds: int = 900) -> tuple[int | None, str | None]:
    """
    Verifies the MFA enrollment setup token. Returns (user_id, secret) if valid; else (None, None).
    """
    if not token:
        return None, None
    try:
        data = _mfa_setup_serializer.loads(token, max_age=max_age_seconds)
        if data.get("purpose") == "mfa_setup" and data.get("user_id") and data.get("secret"):
            return int(data["user_id"]), str(data["secret"])
    except (BadSignature, SignatureExpired, Exception):
        return None, None
    return None, None
