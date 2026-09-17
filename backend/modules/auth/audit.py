import json
from flask import request, has_request_context
from models import db, AuditLog

SENSITIVE_KEYS = {"password", "confirm_password", "token", "raw_token", "secret", "cookie", "aadhaar", "otp"}


def sanitize_details(details) -> str:
    if isinstance(details, dict):
        sanitized = {}
        for k, v in details.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v
        return json.dumps(sanitized)
    elif isinstance(details, str):
        return details
    return ""


def record_audit(action: str, user_id=None, details=None, ip_address=None, user_agent=None):
    """
    Records a structured, sanitized security event in the audit log.
    """
    try:
        ip = ip_address
        ua = user_agent
        if has_request_context():
            if not ip:
                ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
            if not ua:
                ua = request.headers.get("User-Agent", "")[:250]

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=(ip or "")[:45],
            user_agent=(ua or "")[:250],
            details=sanitize_details(details)
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        # Fallback if DB logging fails - never crash the application on audit log write
        db.session.rollback()
        print(f"[AUDIT_LOG_ERROR] Could not write audit log: {e}")
