# SpaceLoop Authentication Migration Audit

> **Document Version:** 1.0.0  
> **Classification:** Security Architecture & Audit Report  
> **Date:** September 17, 2026  
> **Status:** AUDIT COMPLETE — PENDING IMPLEMENTATION

---

## 1. Executive Summary

An exhaustive security inspection was performed across the SpaceLoop repository (`app.py`, `models.py`, `seed_data.py`, `templates/`, `static/`, and `security.py`). The audit revealed that the current application relies on **demo-mode identity assumptions** and **client-controlled persona switching**, rather than a verified authentication and authorization boundary.

This document identifies every instance where identity or permissions are inferred, details the specific vulnerability, and defines the target production security behavior.

---

## 2. Insecure Demo Authentication Findings

### Finding 1: Arbitrary User Impersonation Endpoint (`/switch-user/<id>`)
- **Location:** `app.py` lines 354–359, `templates/login.html`, `templates/base.html` lines 152–165.
- **Current Behavior:** An unauthenticated visitor can submit a `POST /switch-user/<int:user_id>` with any integer ID. The backend immediately writes `session["user_id"] = user.id` without password verification, MFA, or session regeneration.
- **Problem:** Complete authentication bypass. Any visitor can impersonate any host, student seeker, or platform user simply by passing their numeric ID.
- **New Behavior:** Remove `/switch-user` entirely from production routes. Replace with standard password-verified login (`/auth/login` and `/api/v1/auth/login`) with Argon2id/scrypt/pbkdf2:sha256 password hash verification via Werkzeug.
- **Files Affected:** `app.py`, `templates/login.html`, `templates/base.html`, `static/app.js`.

---

### Finding 2: Identity Substitution via Persona Switcher (`/switch-role`)
- **Location:** `app.py` lines 423–434, `templates/base.html` lines 128–150, 184–190.
- **Current Behavior:** Calling `POST /switch-role` queries `target_user = User.query.filter_by(role=target_role).first()` and sets `session["user_id"] = target_user.id`.
- **Problem:** Persona switching switches the **physical user identity** in the database rather than the UI viewing context. A user logged in as Aarav (seeker) who clicks "Switch to Host" is magically transformed into Sunita (host, user ID 1)!
- **New Behavior:** A user has a single immutable identity (`current_user.id`). Persona switching only updates an active UI mode in the session (`session["active_context"] = "host" | "seeker"`), provided the authenticated user possesses the corresponding role or capability. It NEVER switches database user IDs.
- **Files Affected:** `app.py`, `backend/modules/auth/session.py`, `templates/base.html`.

---

### Finding 3: Unauthenticated Fallback Defaults Across Core Routes
- **Location:** `app.py` lines 135, 260, 294, 364, 381, 387, 413, 551–555, 740–743, 959–961, 1009–1011, 1283–1285.
- **Current Behavior:** Routes use patterns like:
  ```python
  user_id = session.get("user_id")
  user = User.query.get(user_id) if user_id else (User.query.filter_by(role="seeker").first() or User.query.first())
  ```
  And in space creation (`POST /api/spaces`):
  ```python
  owner_id = session.get("user_id")
  if not owner_id:
      default_host = User.query.filter_by(role="owner").first() or User.query.first()
      owner_id = default_host.id if default_host else 1
  ```
  And in booking creation (`POST /api/bookings`):
  ```python
  renter_id = session.get("user_id")
  if not renter_id:
      default_seeker = User.query.filter_by(role="seeker").first() or User.query.first()
      renter_id = default_seeker.id if default_seeker else 2
  ```
- **Problem:** Silent privilege attribution. Anonymous visitors can create spaces, book rooms, and trigger student/host KYC under the identity of seeded users without logging in.
- **New Behavior:** Strictly require authentication (`@login_required` or API token). Reject unauthenticated mutations with HTTP 401 Unauthorized (`{"error": "Authentication required"}`). Never assign arbitrary fallback users.
- **Files Affected:** `app.py`, `backend/modules/auth/decorators.py`, `backend/modules/spaces/`, `backend/modules/bookings/`.

---

### Finding 4: Insecure Default Password Hashing in Seed Data
- **Location:** `seed_data.py` lines 198–200.
- **Current Behavior:** Demo users are seeded with `u.set_password("password123")`. While it uses Werkzeug's `generate_password_hash`, the credentials are weak, predictable, and shared across all accounts.
- **Problem:** Predictable demo accounts could be targeted if deployed to production without re-seeding or isolation.
- **New Behavior:** 
  1. Clearly isolate seed accounts to development environments (`FLASK_ENV=development`).
  2. Provide explicit development accounts (`dev-host@spaceloop.local`, `dev-seeker@spaceloop.local`, `dev-admin@spaceloop.local`).
  3. Never automatically seed administrative accounts in production. Provide a standalone CLI script (`scripts/create_admin.py`) for explicit, interactive admin provisioning.
- **Files Affected:** `seed_data.py`, `scripts/create_admin.py`, `config.py`.

---

### Finding 5: Missing Role & Capability Verification (IDOR Vulnerabilities)
- **Location:** `app.py` lines 226–255 (`POST /api/spaces/<id>/edit`), 335–343 (`POST /api/spaces/<id>/toggle-status`), 1248–1267 (`POST /api/booking/<id>/cancel`).
- **Current Behavior:** In space editing:
  ```python
  @app.route("/api/spaces/<int:space_id>/edit", methods=["POST"])
  def api_edit_space(space_id):
      space = Space.query.get_or_404(space_id)
      # No check comparing current_user.id with space.owner_id!
  ```
  Any caller can edit any host's space, toggle its active status, or cancel bookings.
- **Problem:** Insecure Direct Object Reference (IDOR) and broken object-level authorization.
- **New Behavior:** Implement centralized permissions (`backend/modules/auth/permissions.py`) and object ownership verification:
  ```python
  authorize(current_user, Permission.SPACE_UPDATE, resource=space)
  ```
  Deny access with HTTP 403 Forbidden if `current_user.id != space.owner_id and not current_user.is_admin`.
- **Files Affected:** `app.py`, `backend/modules/auth/permissions.py`, `backend/modules/auth/decorators.py`.

---

### Finding 6: Missing CSRF Protection on Browser State Mutations
- **Location:** `app.py`, `templates/*.html`.
- **Current Behavior:** Forms submit `POST` requests without CSRF tokens. State-changing API endpoints accept JSON payloads without anti-forgery headers.
- **Problem:** Cross-Site Request Forgery (CSRF). Malicious sites could force an authenticated user's browser to book spaces, edit listings, or cancel reservations.
- **New Behavior:** Integrate `Flask-WTF` (`CSRFProtect`). Inject `csrf_token()` in all Jinja forms and validate `X-CSRF-Token` headers on browser AJAX requests.
- **Files Affected:** `app.py`, `templates/base.html`, `templates/auth/*.html`, `static/app.js`.

---

### Finding 7: Authentication Rate Limiting Gap
- **Location:** `security.py` lines 79–133.
- **Current Behavior:** `SimpleRateLimiter` is an in-memory sliding window applied exclusively to AI endpoints (`@rate_limit_ai`). No rate limiting exists on login, registration, or password reset routes.
- **Problem:** Vulnerability to credential stuffing, brute-force password guessing, and registration spam.
- **New Behavior:** Integrate `Flask-Limiter` with explicit configurable limits (`AUTH_LOGIN_RATE_LIMIT=5 per minute`, `AUTH_REGISTER_RATE_LIMIT=3 per hour`, `AUTH_PASSWORD_RESET_RATE_LIMIT=3 per hour`).
- **Files Affected:** `app.py`, `config.py`, `backend/modules/auth/validators.py`.

---

## 3. Summary of Files Requiring Migration

| File Path | Nature of Modification |
| :--- | :--- |
| `app.py` | Remove fallback user queries, remove `/switch-user`, integrate Flask-Login, apply `@login_required` and `@permission_required`. |
| `models.py` | Add `UserMixin`, `public_id`, `is_active`, `is_email_verified`, `last_login_at`, create `PasswordResetToken`, `EmailVerificationToken`, `AuditLog`. |
| `config.py` | Add Flask-Login, session cookie hardening, Flask-Limiter, and CSRF settings. |
| `templates/base.html` | Update navigation to reflect anonymous vs. authenticated states; remove demo persona switcher pills. |
| `templates/login.html` | Transform from demo persona switcher into production email/password login form with generic error alerts. |
| `templates/index.html` | Re-architect into a high-converting public landing page with CTAs for both guests and hosts. |
| `seed_data.py` | Ensure demo users have distinct development credentials; mark explicitly as development fixtures. |
| `security.py` | Keep AI rate limiting and data sanitization intact; delegate auth rate limiting to Flask-Limiter. |
