"""
Vercel Serverless Function Entrypoint for SpaceLoop API
Integrates Flask WSGI application with Vercel's Python Serverless Runtime.
"""
import os
import sys

# Ensure repository root is placed at the head of Python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app
from werkzeug.middleware.proxy_fix import ProxyFix


class VercelWSGIMiddleware:
    """
    Normalizes WSGI PATH_INFO and SCRIPT_NAME for requests routed
    through Vercel's edge network and rewrite rules.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Look for headers containing the original request path
        true_path = None
        for key in ("HTTP_X_FORWARDED_URI", "HTTP_X_ORIGINAL_URI", "RAW_URI", "REQUEST_URI"):
            val = environ.get(key)
            if val:
                p = val.split("?")[0]
                if p and p != "/api/index.py" and not p.endswith(".py"):
                    true_path = p
                    break

        if true_path:
            environ["PATH_INFO"] = true_path
        else:
            # 2. Check HTTP_X_MATCHED_PATH
            matched_path = environ.get("HTTP_X_MATCHED_PATH")
            if matched_path and not matched_path.endswith(".py"):
                environ["PATH_INFO"] = matched_path

        return self.wsgi_app(environ, start_response)


# Apply standard proxy fix headers and Vercel edge path resolver
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# Vercel WSGI entry point
# Exposed 'app' variable is automatically detected by @vercel/python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
