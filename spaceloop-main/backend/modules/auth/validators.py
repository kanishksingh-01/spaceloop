"""
Authentication Input Validators for SpaceLoop Platform
"""

import re
from typing import Tuple, Optional


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def validate_registration_input(
    name: str,
    email: str,
    password: str,
    role: str
) -> Tuple[bool, Optional[str]]:
    """Validates registration fields.
    Returns (True, None) on success or (False, error_message) on validation failure.
    """
    if not name or len(name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."

    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please enter a valid email address."

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    valid_roles = ('seeker', 'owner')
    if not role or role.strip().lower() not in valid_roles:
        return False, f"Role must be one of: {', '.join(valid_roles)}."

    return True, None


def validate_login_input(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Validates presence of required login credentials."""
    if not email or not email.strip():
        return False, "Email address is required."
    if not password:
        return False, "Password is required."
    return True, None
