"""
SpaceLoop Application Hardening, Privacy & Security Defenses
Compliance: DPDP Act 2023 / UIDAI / OWASP Top 10
"""

import hashlib
import html
import re
import time
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, make_response, session, redirect, url_for, abort


# --- DPDP Act 2023 & UIDAI Salted Hash Tokens ---
DPDP_GLOBAL_SALT = "spaceloop_dpdp_salt_v2_2026"


def mask_aadhaar(aadhaar_num: str) -> str:
    """Zero raw Aadhaar storage compliance (DPDP Act 2023 Section 8).
    Returns masked representation preserving only the last 4 digits: XXXX-XXXX-4821.
    """
    if not aadhaar_num:
        return "XXXX-XXXX-0000"
    cleaned = re.sub(r'[^0-9]', '', str(aadhaar_num))
    if len(cleaned) < 4:
        return "XXXX-XXXX-XXXX"
    last4 = cleaned[-4:]
    return f"XXXX-XXXX-{last4}"


def hash_aadhaar(aadhaar_num: str, salt: str = DPDP_GLOBAL_SALT) -> str:
    """One-way salted SHA-256 tokenization for collision detection.
    Irreversible under DPDP directives.
    """
    cleaned = re.sub(r'[^0-9]', '', str(aadhaar_num))
    token_material = f"{cleaned}:{salt}".encode('utf-8')
    return hashlib.sha256(token_material).hexdigest()


def mask_student_id(student_id: str) -> str:
    """Masks student ID to protect student privacy: STU-***-1044."""
    if not student_id:
        return "STU-***-0000"
    cleaned = student_id.strip()
    if len(cleaned) <= 4:
        return f"STU-***-{cleaned}"
    last4 = cleaned[-4:]
    return f"STU-***-{last4}"


def mask_discom_ca(ca_number: str) -> str:
    """Masks Discom Consumer Account number."""
    if not ca_number:
        return "CA-***-0000"
    cleaned = str(ca_number).strip()
    last4 = cleaned[-4:] if len(cleaned) >= 4 else cleaned
    return f"CA-***-{last4}"


def mask_upi_vpa(upi_vpa: str) -> str:
    """Masks UPI Virtual Payment Address (e.g. host***@okhdfcbank)."""
    if not upi_vpa or '@' not in upi_vpa:
        return "user***@upi"
    handle, provider = upi_vpa.split('@', 1)
    prefix = handle[:3] if len(handle) >= 3 else handle
    return f"{prefix}***@{provider}"


# --- Sliding-Window AI Rate Limiter (20 calls / min per IP) ---
class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter per client IP."""
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        # Purge stale timestamps
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True

    def reset_for_ip(self, client_ip: str):
        self.requests.pop(client_ip, None)


# Global AI rate limiter instance
ai_rate_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=60)


def rate_limit_ai(max_requests=20, window_seconds=60):
    """Decorator to enforce sliding-window rate limit on AI endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            if not ai_rate_limiter.is_allowed(client_ip):
                return jsonify({
                    'error': 'Rate Limit Exceeded',
                    'message': 'Sliding-window AI rate limit reached (20 calls/min). Please wait before making more AI requests.'
                }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- Input Sanitization & HTML Escaping ---
def sanitize_input(text: str, max_length: int = 500) -> str:
    """Strips control characters, caps length, and escapes HTML entities."""
    if text is None:
        return ""
    s = str(text).strip()
    # Strip null bytes and non-printable control characters
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    s = s[:max_length]
    return html.escape(s)


def wrap_untrusted_notes(notes: str) -> str:
    """Isolates untrusted user-submitted notes within XML tags to prevent prompt injection."""
    sanitized = sanitize_input(notes, max_length=1500)
    return f"<user_untrusted_notes>\n{sanitized}\n</user_untrusted_notes>"


# --- Server-Side Financial Recomputation & Clamping ---
def clamp_financial_bounds(hours: float, price_hourly: float, escrow: float = 100.0) -> dict:
    """Guarantees server-side recomputation of booking financial figures.
    Client-passed costs or negative rates are rejected or clamped.
    """
    clamped_hours = max(1.0, min(24.0, float(hours)))
    valid_rate = max(10.0, min(10000.0, float(price_hourly)))
    calculated_rental = round(clamped_hours * valid_rate, 2)
    guaranteed_escrow = 100.0  # strictly Rs. 100 micro-escrow
    platform_fee = round(calculated_rental * 0.15, 2)  # 15% platform take rate
    host_earnings = round(calculated_rental - platform_fee, 2)
    
    return {
        'hours': clamped_hours,
        'hourly_rate': valid_rate,
        'rental_fee': calculated_rental,
        'escrow_amount': guaranteed_escrow,
        'platform_fee': platform_fee,
        'host_earnings': host_earnings,
        'total_payable': round(calculated_rental + guaranteed_escrow, 2)
    }


# --- Defensive Security Headers Injection ---
def add_security_headers(response):
    """Injects defensive HTTP security headers into every outgoing Flask response."""
    # Content-Security-Policy
    csp = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "https://cdn.tailwindcss.com https://cdnjs.cloudflare.com "
        "https://fonts.googleapis.com https://fonts.gstatic.com "
        "https://images.unsplash.com https://api.qrserver.com data: blob:; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' https:;"
    )
    response.headers['Content-Security-Policy'] = csp
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# --- Authentication & Authorization (RBAC) Defenses ---
def get_current_user():
    """Retrieves authenticated User record from current session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    from models import User
    return User.query.get(user_id)


def login_required(f):
    """Guarantees caller is authenticated.
    Redirects web clients to login page with `next` query parameter.
    Returns HTTP 401 JSON envelope for API requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if (
                request.path.startswith('/api/') or
                request.is_json or
                request.headers.get('Accept', '').startswith('application/json')
            ):
                return jsonify({
                    'error': 'Authentication Required',
                    'message': 'You must be logged in to perform this action.'
                }), 401
            next_url = request.full_path if request.query_string else request.path
            return redirect(url_for('login_page', next=next_url))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*roles):
    """Enforces Role-Based Access Control (RBAC). Platform admins always pass."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if (
                    request.path.startswith('/api/') or
                    request.is_json or
                    request.headers.get('Accept', '').startswith('application/json')
                ):
                    return jsonify({
                        'error': 'Authentication Required',
                        'message': 'Please log in to continue.'
                    }), 401
                next_url = request.full_path if request.query_string else request.path
                return redirect(url_for('login_page', next=next_url))

            if user.role not in roles and user.role != 'admin':
                if (
                    request.path.startswith('/api/') or
                    request.is_json or
                    request.headers.get('Accept', '').startswith('application/json')
                ):
                    return jsonify({
                        'error': 'Forbidden',
                        'message': f'Access restricted to roles: {", ".join(roles)}.'
                    }), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def seeker_required(f):
    return roles_required('seeker')(f)


def host_required(f):
    return roles_required('owner')(f)


def admin_required(f):
    return roles_required('admin')(f)


# --- Object-Level Access Control (Ownership Checks) ---
def ensure_booking_access(booking, user) -> bool:
    """Verifies that user is the renter, the space host, or an admin."""
    if not user:
        return False
    if user.role == 'admin':
        return True
    if booking.renter_id == user.id:
        return True
    if booking.space and booking.space.owner_id == user.id:
        return True
    return False


def ensure_space_access(space, user) -> bool:
    """Verifies that user is the owner of the space or an admin."""
    if not user:
        return False
    if user.role == 'admin':
        return True
    return space.owner_id == user.id

