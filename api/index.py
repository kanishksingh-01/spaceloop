"""
Vercel Serverless Function Entrypoint for SpaceLoop API
Integrates Flask WSGI application with Vercel's Python Serverless Runtime.
"""
import os
import sys
from urllib.parse import parse_qs, urlencode

# Ensure repository root is placed at the head of Python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app
from werkzeug.middleware.proxy_fix import ProxyFix


class VercelWSGIMiddleware:
    """
    Normalizes WSGI PATH_INFO and SCRIPT_NAME for requests routed
    through Vercel's edge network using rewrites or proxies.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Check if route was forwarded via rewrite query parameters
        qs = environ.get("QUERY_STRING", "")
        extracted_path = None
        for key in ("__path__", "_vercel_path", "slug", "path"):
            if f"{key}=" in qs:
                params = parse_qs(qs, keep_blank_values=True)
                if key in params:
                    extracted_path = params.pop(key)[0]
                    environ["QUERY_STRING"] = urlencode(params, doseq=True)
                    break

        if extracted_path:
            if not extracted_path.startswith("/"):
                extracted_path = "/" + extracted_path
            environ["PATH_INFO"] = extracted_path
        else:
            # 2. Check if PATH_INFO was rewritten to the entrypoint filename
            current_path = environ.get("PATH_INFO", "")
            if current_path in ("/api/index", "/api/index.py", "/api"):
                # Check Vercel routing headers
                matched = environ.get("HTTP_X_MATCHED_PATH")
                if matched and not matched.startswith("/api/index") and matched != "/":
                    environ["PATH_INFO"] = matched
                else:
                    raw_uri = environ.get("RAW_URI") or environ.get("REQUEST_URI", "")
                    if raw_uri:
                        path_part = raw_uri.split("?")[0]
                        if path_part and not path_part.startswith("/api/index") and path_part != "/":
                            environ["PATH_INFO"] = path_part

        return self.wsgi_app(environ, start_response)


# Apply standard reverse proxy header normalization and Vercel path resolver
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
