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
    through Vercel's edge network using named route parameters.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        if "slug=" in query_string:
            params = parse_qs(query_string, keep_blank_values=True)
            if "slug" in params:
                slug = params.pop("slug")[0]
                if slug.startswith("auth/") or slug.startswith("switch-") or slug.startswith("space/"):
                    environ["PATH_INFO"] = f"/{slug}"
                elif slug.startswith("/"):
                    environ["PATH_INFO"] = slug
                else:
                    environ["PATH_INFO"] = f"/api/{slug}"
                environ["QUERY_STRING"] = urlencode(params, doseq=True)

        return self.wsgi_app(environ, start_response)


# Apply standard proxy fix headers and Vercel edge path resolver
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# Vercel WSGI entry point
# Exposed 'app' variable is automatically detected by @vercel/python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
