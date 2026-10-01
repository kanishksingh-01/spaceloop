import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple
from flask import request, Response


class SpaceCacheManager:
    """
    In-memory read cache and HTTP ETag manager for read-heavy SpaceLoop catalog endpoints.
    Provides sub-millisecond 304 Not Modified responses and eliminates repetitive JSON/DB serialization.
    """

    def __init__(self, default_ttl_sec: int = 30):
        self._version = 1
        self._detail_versions: Dict[int, int] = {}
        self._response_cache: Dict[str, Tuple[str, float]] = {}  # key -> (json_string, expiry_timestamp)
        self.default_ttl = default_ttl_sec

    def bump_catalog_version(self, space_id: Optional[int] = None):
        """Invalidates catalog cache on mutations (create, edit, delete, toggle status, new review)."""
        self._version += 1
        if space_id is not None:
            self._detail_versions[space_id] = self._detail_versions.get(space_id, 0) + 1
        self._response_cache.clear()

    def generate_etag(self, prefix: str, user_id: Optional[int] = None, extra: str = "") -> str:
        version = self._version
        raw = f"{prefix}_v{version}_u{user_id or 'anon'}_{extra}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def check_etag_and_respond(self, etag: str) -> Optional[Response]:
        """
        If client sent matching If-None-Match header, return 304 Not Modified.
        """
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match:
            clean_inm = if_none_match.strip('"').strip("'")
            if clean_inm == etag or clean_inm == f'W/"{etag}"':
                resp = Response("", status=304)
                resp.headers["ETag"] = f'"{etag}"'
                resp.headers["Cache-Control"] = "private, no-cache"
                return resp
        return None

    def get_cached_response(self, cache_key: str, etag: str) -> Optional[Response]:
        now = time.time()
        if cache_key in self._response_cache:
            payload_str, expiry = self._response_cache[cache_key]
            if now < expiry:
                resp = Response(payload_str, status=200, mimetype="application/json")
                resp.headers["ETag"] = f'"{etag}"'
                resp.headers["Cache-Control"] = "private, no-cache"
                resp.headers["X-Cache"] = "HIT"
                return resp
            else:
                del self._response_cache[cache_key]
        return None

    def cache_and_respond(self, cache_key: str, etag: str, data: Any, ttl: Optional[int] = None) -> Response:
        payload_str = json.dumps(data)
        expiry = time.time() + (ttl or self.default_ttl)
        self._response_cache[cache_key] = (payload_str, expiry)

        resp = Response(payload_str, status=200, mimetype="application/json")
        resp.headers["ETag"] = f'"{etag}"'
        resp.headers["Cache-Control"] = "private, no-cache"
        resp.headers["X-Cache"] = "MISS"
        return resp


space_cache = SpaceCacheManager(default_ttl_sec=30)
