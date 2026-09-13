import time
import re
import threading
from urllib.parse import urlparse
from flask import request, jsonify

# ==========================================
# Input Validation & Sanitization
# ==========================================

SAFE_IMAGE_DATA_PREFIXES = (
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/jpg;base64,",
    "data:image/webp;base64,",
    "data:image/gif;base64,",
)


def validate_image_url(url: str) -> bool:
    """
    Validates that a URL is safe for rendering in an <img> tag.
    Allows only http, https, or safe raster image data URIs.
    Explicitly blocks javascript:, vbscript:, data:text/html, etc.
    """
    if not url or not isinstance(url, str):
        return False

    url_clean = url.strip()
    if not url_clean:
        return False

    # Block any script injection patterns in URL
    lower = url_clean.lower()
    if any(bad in lower for bad in ["javascript:", "vbscript:", "<script", "onerror=", "onload="]):
        return False

    # Allow verified base64 image data URIs
    if lower.startswith("data:image/"):
        return any(lower.startswith(prefix) for prefix in SAFE_IMAGE_DATA_PREFIXES)

    # Allow http and https schemes only
    try:
        parsed = urlparse(url_clean)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def sanitize_string(val, max_length: int = 500, default: str = "") -> str:
    """
    Sanitizes string input by stripping control characters and enforcing length bounds.
    """
    if val is None:
        return default
    text = str(val).strip()
    # Remove ASCII control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:max_length]


def validate_numeric(val, min_val: float, max_val: float, default: float = None):
    """
    Validates that a numeric input falls within an allowable range.
    """
    try:
        num = float(val)
        if min_val <= num <= max_val:
            return num
    except (ValueError, TypeError):
        pass
    return default


# ==========================================
# In-Memory Rate Limiter (Thread-safe)
# ==========================================

class SimpleRateLimiter:
    """
    Sliding-window rate limiter per client IP address.
    Protects expensive AI and booking endpoints from DoS and quota depletion.
    """

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._records = {}  # ip -> list of timestamps

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        with self._lock:
            # Clean old records
            timestamps = self._records.get(client_ip, [])
            cutoff = now - self.window_seconds
            timestamps = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= self.max_requests:
                self._records[client_ip] = timestamps
                return False

            timestamps.append(now)
            self._records[client_ip] = timestamps
            return True


# Global rate limiter instance for AI endpoints (25 requests / min per IP)
ai_rate_limiter = SimpleRateLimiter(max_requests=25, window_seconds=60)


def rate_limit_ai(func):
    """Decorator to enforce rate limiting on AI-heavy endpoints."""
    def wrapper(*args, **kwargs):
        # Determine client identifier (respecting X-Forwarded-For if behind proxy)
        client_ip = (
            request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
            .split(",")[0]
            .strip()
        )
        if not ai_rate_limiter.is_allowed(client_ip):
            return (
                jsonify({
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded for AI services. Please wait a moment before trying again."
                }),
                429
            )
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


# ==========================================
# Security Headers Middleware
# ==========================================

def apply_security_headers(response):
    """
    Applies security headers to prevent Clickjacking, MIME-sniffing, and XSS.
    """
    # Prevent browser from MIME-sniffing away from declared Content-Type
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking by denying framing by other origins
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # Enable XSS filter in older browsers
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Control referrer information leak
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Content Security Policy (allows Tailwind CDN, FontAwesome, Google Fonts, Unsplash images)
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    return response
