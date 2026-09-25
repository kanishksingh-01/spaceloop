"""
SpaceLoop Production CORS Module
Provides cross-origin resource sharing support for decoupled frontend deployments (e.g. Vercel, Netlify, Vite).
"""
from flask import request


def configure_cors(app):
    """
    Configures CORS on the Flask application.
    Supports credentials, preflight OPTIONS, and custom allowed origins from configuration.
    """
    # Secure default whitelisted origins for local development and production
    default_trusted = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://spaceloop.onrender.com"
    ]
    
    raw_origins = app.config.get("CORS_ORIGINS", default_trusted)
    if isinstance(raw_origins, str):
        configured_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    elif isinstance(raw_origins, (list, set, tuple)):
        configured_origins = list(raw_origins)
    else:
        configured_origins = default_trusted

    # Build clean explicit allowed set (strip any wildcard to prevent credential leakage)
    trusted_origins = set(default_trusted + [o for o in configured_origins if o != "*"])

    def is_origin_allowed(origin_header: str) -> bool:
        if not origin_header:
            return False
        clean = origin_header.rstrip("/")
        return clean in trusted_origins or any(clean == t.rstrip("/") for t in trusted_origins)

    # Native robust CORS middleware
    @app.before_request
    def handle_cors_preflight():
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            origin = request.headers.get("Origin", "")
            response = app.make_default_options_response()
            if is_origin_allowed(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Requested-With, X-SpaceLoop-Client, X-CSRFToken, Accept, Origin"
                )
                response.headers["Access-Control-Max-Age"] = "86400"
            return response

    @app.after_request
    def add_cors_headers(response):
        if request.path.startswith("/api/") or request.path.startswith("/auth/"):
            origin = request.headers.get("Origin", "")
            if is_origin_allowed(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Requested-With, X-SpaceLoop-Client, X-CSRFToken, Accept, Origin"
                )
        return response
