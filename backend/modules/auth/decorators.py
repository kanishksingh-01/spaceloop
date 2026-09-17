from functools import wraps
from flask import request, jsonify, redirect, url_for, flash, abort
from flask_login import current_user
from backend.modules.auth.permissions import Permission, authorize, UnauthorizedError, ForbiddenError


def permission_required(permission: Permission, resource_getter=None):
    """
    Decorator to enforce permission checks and resource ownership.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            resource = None
            if resource_getter:
                resource = resource_getter(*args, **kwargs)

            try:
                authorize(current_user, permission, resource=resource)
            except UnauthorizedError as e:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": str(e), "authenticated": False}), 401
                flash(str(e), "warning")
                return redirect(url_for("auth_login", next=request.url))
            except ForbiddenError as e:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": str(e)}), 403
                flash(str(e), "danger")
                return redirect(url_for("auth_access_denied"))

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """
    Convenience decorator strictly requiring administrative rights.
    """
    return permission_required(Permission.ADMIN_ACCESS)(fn)
