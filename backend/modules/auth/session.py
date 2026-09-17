from flask import session


def get_active_context(user) -> str:
    """
    Returns the active UI context (host vs seeker) for the current user.
    Defaults to "host" for pure owners, and "seeker" for seekers/both.
    """
    stored = session.get("active_context")
    if stored in ("host", "seeker"):
        return stored

    if not user or not getattr(user, "is_authenticated", False):
        return "seeker"

    if getattr(user, "role", "") == "owner":
        return "host"
    return "seeker"


def set_active_context(user, target_context: str) -> bool:
    """
    Switches UI viewing perspective between host and seeker modes.
    Ensures user identity (current_user.id) remains unchanged.
    """
    target = (target_context or "").lower().strip()
    if target not in ("host", "seeker"):
        return False

    if not user or not getattr(user, "is_authenticated", False):
        return False

    # Check if user has host capability
    if target == "host":
        if not (getattr(user, "is_host", False) or getattr(user, "is_admin", False)):
            # User wants to act as host - allow them to enter host mode to create a listing
            # (which elevates capability through onboarding)
            pass

    session["active_context"] = target
    return True
