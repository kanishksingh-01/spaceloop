# SpaceLoop Session Management & Cookie Security

> **Document Version:** 1.0.0  
> **Classification:** Security Specification  
> **Date:** September 17, 2026

---

## 1. Session Architecture

SpaceLoop utilizes Flask cryptographically signed cookies (HMAC-SHA256) enhanced with Flask-Login session controls:
- **Session Identifier:** Tied to `current_user.id`.
- **Session Regeneration:** Upon login, the old session dictionary is cleared and a fresh session identity is generated to eliminate session fixation.
- **Session Teardown:** Upon logout, `session.clear()` removes all session artifacts and deletes the session cookie.

---

## 2. Session Cookie Hardening Directives

Configured in `config.py`:

```python
# Cookie Security Flags
SESSION_COOKIE_HTTPONLY = True          # Inaccessible to document.cookie (XSS mitigation)
SESSION_COOKIE_SAMESITE = "Lax"         # Protects against cross-origin CSRF on navigation
SESSION_COOKIE_SECURE = False           # Set to True in production (HTTPS required)
PERMANENT_SESSION_LIFETIME = timedelta(days=7) # 7-day session lifetime
SESSION_REFRESH_EACH_REQUEST = True     # Rolling expiration
```

---

## 3. CSRF Protection Integration

Cross-Site Request Forgery is enforced across all browser-driven state mutations:
1. `CSRFProtect(app)` initialized in `backend/app/extensions.py` and `app.py`.
2. HTML Forms embed `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`.
3. AJAX/Fetch calls transmit `X-CSRF-Token` headers read from the meta tag:
   ```html
   <meta name="csrf-token" content="{{ csrf_token() }}">
   ```
4. API endpoints using API-token authentication bypass CSRF only when bearer token headers are present.
