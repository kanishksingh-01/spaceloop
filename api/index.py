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

# Apply standard reverse proxy header normalization
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Vercel WSGI entry point
# Exposed 'app' variable is automatically detected by @vercel/python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
