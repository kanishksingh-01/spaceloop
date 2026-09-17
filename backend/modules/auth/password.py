import re
from werkzeug.security import generate_password_hash, check_password_hash

# Pre-computed dummy hash to mitigate user enumeration timing attacks
DUMMY_HASH = generate_password_hash("SpaceLoopTimingAttackMitigationSalt2026")


def validate_password_complexity(password: str) -> tuple[bool, str]:
    """
    Enforces minimum password security standards:
    - At least 8 characters
    - Contains at least one letter
    - Contains at least one number
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters in length."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, ""


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or not password:
        return False
    return check_password_hash(password_hash, password)


def dummy_verify_password():
    """Simulate password verification duration when user email is not found."""
    check_password_hash(DUMMY_HASH, "dummy_password_timing_mitigation")
