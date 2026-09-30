"""
Vercel Serverless Function Entrypoint for SpaceLoop API
Transparently forwards API requests to the production SpaceLoop backend on Render.
Built using standard library urllib for zero-dependency high reliability and sub-second cold starts.
"""
import os
import json
import urllib.request
import urllib.error
from urllib.parse import parse_qs, urlencode

BACKEND_URL = os.environ.get("RENDER_BACKEND_URL", "https://spaceloop.onrender.com").rstrip("/")


def app(environ, start_response):
    # 1. Resolve target path
    path = environ.get("PATH_INFO", "")
    qs = environ.get("QUERY_STRING", "")

    # Handle rewrite query parameters (__path__, _vercel_path, slug, path)
    if "__path__=" in qs or "_vercel_path=" in qs or "slug=" in qs or "path=" in qs:
        params = parse_qs(qs, keep_blank_values=True)
        for key in ("__path__", "_vercel_path", "slug", "path"):
            if key in params:
                path = params.pop(key)[0]
                qs = urlencode(params, doseq=True)
                break

    if not path.startswith("/"):
        path = "/" + path

    # If routed directly to entrypoint without subpath, point to health
    if path in ("/api/index", "/api/index.py", "/api"):
        path = "/api/health"

    # 2. Build target URL
    target_url = f"{BACKEND_URL}{path}"
    if qs:
        target_url += f"?{qs}"

    method = environ.get("REQUEST_METHOD", "GET")

    # 3. Read request body if present
    body = None
    try:
        content_length = int(environ.get("CONTENT_LENGTH", 0))
    except (ValueError, TypeError):
        content_length = 0

    if content_length > 0 and "wsgi.input" in environ:
        body = environ["wsgi.input"].read(content_length)

    # 4. Normalize and forward headers
    headers = {}
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            header_name = k[5:].replace("_", "-").title()
            if header_name.lower() not in ("host", "content-length"):
                headers[header_name] = v
        elif k in ("CONTENT_TYPE", "CONTENT_LENGTH") and v:
            headers[k.replace("_", "-").title()] = v

    headers["X-Forwarded-Host"] = environ.get("HTTP_HOST", "spaceloop.vercel.app")
    headers["X-Forwarded-Proto"] = "https"

    req = urllib.request.Request(target_url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            status_code = resp.status
            reason = resp.reason
            resp_body = resp.read()
            resp_headers = []
            for h, val in resp.getheaders():
                if h.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                    resp_headers.append((h, val))
            resp_headers.append(("Content-Length", str(len(resp_body))))
            start_response(f"{status_code} {reason}", resp_headers)
            return [resp_body]
    except urllib.error.HTTPError as e:
        err_body = e.read()
        resp_headers = []
        for h, val in e.headers.items():
            if h.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                resp_headers.append((h, val))
        resp_headers.append(("Content-Length", str(len(err_body))))
        start_response(f"{e.code} {e.reason}", resp_headers)
        return [err_body]
    except Exception as e:
        err_json = json.dumps({
            "error": "Failed to connect to SpaceLoop backend on Render.",
            "detail": str(e),
            "backend_url": BACKEND_URL
        }).encode("utf-8")
        start_response("502 Bad Gateway", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(err_json)))
        ])
        return [err_json]
