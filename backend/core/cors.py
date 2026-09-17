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
    raw_origins = app.config.get("CORS_ORIGINS", ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"])
    if isinstance(raw_origins, str):
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    elif isinstance(raw_origins, (list, set, tuple)):
        allowed_origins = list(raw_origins)
    else:
        allowed_origins = ["*"]

    # Try flask_cors if available
    try:
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
        return
    except ImportError:
        pass

    # Native robust CORS middleware fallback
    @app.before_request
    def handle_cors_preflight():
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            origin = request.headers.get("Origin", "")
            response = app.make_default_options_response()
            if "*" in allowed_origins or origin in allowed_origins or not allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin or "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Requested-With, X-CSRFToken, Accept, Origin"
                )
                response.headers["Access-Control-Max-Age"] = "86400"
            return response

    @app.after_request
    def add_cors_headers(response):
        if request.path.startswith("/api/") or request.path.startswith("/auth/"):
            origin = request.headers.get("Origin", "")
            if "*" in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
            elif origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, X-CSRFToken, Accept, Origin"
            )
        return response
