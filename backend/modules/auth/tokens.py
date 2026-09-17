import hashlib
import secrets


def generate_secure_token() -> tuple[str, str]:
    """
    Generates a cryptographically secure URL-safe token.
    Returns:
        (raw_token, token_hash)
    The raw_token is sent to the user (via link); the token_hash is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hex digest of a token string."""
    return hashlib.sha256((raw_token or "").encode("utf-8")).hexdigest()
