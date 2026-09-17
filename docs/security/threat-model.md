# SpaceLoop Threat Model

> **Document Version:** 1.0.0  
> **Classification:** Application Security Architecture & Risk Analysis  
> **Date:** September 17, 2026  
> **Standard Reference:** OWASP Top 10 (2021), ASVS Level 2, STRIDE Model

---

## 1. Executive Summary

This Threat Model assesses the security posture of the SpaceLoop application, with special focus on the authentication, authorization, and session boundaries. Historically, demo applications often prioritize rapid prototyping over security; this threat model identifies attack vectors present in demo architectures and specifies the controls and automated tests implemented to eliminate them.

---

## 2. Comprehensive Threat Analysis

### Threat 1: Credential Theft & Plaintext Storage
- **Description:** Storing passwords in plaintext, using weak cryptographic hashes (e.g. MD5, SHA1), or logging passwords in application logs or exception traces.
- **Impact:** Compromise of user accounts across SpaceLoop and potential credential re-use on third-party services.
- **Mitigation:**
  1. Enforce salted, adaptive one-way password hashing using Werkzeug (defaulting to PBKDF2:SHA256 with >=600,000 iterations or Argon2id/scrypt).
  2. Implement strict sanitization in logging filters (`AuditLog`, application logs) ensuring passwords, tokens, and authorization credentials are never logged.
  3. Validate password complexity (minimum 8 characters, requiring mixed alphanumeric characters).
- **Test:** `test_password_hashing_complexity()` and `test_passwords_never_logged()`.

---

### Threat 2: Brute-Force Password Guessing
- **Description:** Repeated automated login attempts targeting a specific user account using common password dictionaries.
- **Impact:** Account takeover of high-value host or seeker profiles.
- **Mitigation:**
  1. Integrate `Flask-Limiter` on `/auth/login` and `/api/v1/auth/login` restricted to 5 attempts per minute per IP.
  2. Implement progressive delays or account temporary lockouts after consecutive failed attempts.
  3. Log failed authentication attempts in `AuditLog` with action `AUTH_LOGIN_FAILED`.
- **Test:** `test_login_rate_limiting()` verifying HTTP 429 Too Many Requests after threshold.

---

### Threat 3: Credential Stuffing
- **Description:** Automated spraying of breached username/password combinations across multiple accounts.
- **Impact:** Distributed compromise of user accounts without triggering per-account lockout thresholds.
- **Mitigation:**
  1. Global IP-level rate limiting on all `/auth/*` endpoints.
  2. User-Agent and client telemetry validation.
  3. Generic error responses for authentication failures to prevent distinguishing invalid users from wrong passwords.
- **Test:** `test_credential_stuffing_rate_limit()` testing multi-account requests from single origin.

---

### Threat 4: Session Fixation
- **Description:** An attacker pre-determines or forces a known session ID onto the victim prior to login, then hijacks the authenticated session once the user logs in.
- **Impact:** Unauthorized session takeover of authenticated seeker or host sessions.
- **Mitigation:**
  1. Always call `session.regenerate()` or clear and regenerate the session upon successful authentication.
  2. In Flask-Login, `login_user()` automatically clears the old session and issues a fresh session identifier.
- **Test:** `test_session_regeneration_on_login()` asserting session cookie value changes before and after login.

---

### Threat 5: Session Hijacking & Cookie Theft
- **Description:** Interception or exfiltration of session cookies via network sniffing, cross-site scripting (XSS), or insecure transport.
- **Impact:** Full impersonation of the victim without possessing their credentials.
- **Mitigation:**
  1. Enforce cookie security flags:
     - `SESSION_COOKIE_HTTPONLY = True` (prevents JavaScript access to cookies).
     - `SESSION_COOKIE_SECURE = True` in production (enforces transmission strictly over HTTPS).
     - `SESSION_COOKIE_SAMESITE = "Lax"` (prevents cross-origin leakage).
  2. Invalidate sessions server-side upon logout.
- **Test:** `test_cookie_security_flags()` inspecting `Set-Cookie` headers for `HttpOnly`, `SameSite=Lax`, and `Secure`.

---

### Threat 6: Cross-Site Request Forgery (CSRF)
- **Description:** A malicious external site induces an authenticated user to unknowingly submit state-changing requests (e.g. creating bookings, canceling spaces, updating profile).
- **Impact:** Unintended financial transactions, booking cancellations, or profile modifications executed on behalf of the victim.
- **Mitigation:**
  1. Integrate `Flask-WTF` (`CSRFProtect`) globally across all state-changing HTTP methods (`POST`, `PUT`, `DELETE`, `PATCH`).
  2. Include `csrf_token()` hidden inputs in all Jinja forms.
  3. Require `X-CSRF-Token` header for AJAX/fetch requests from the browser.
- **Test:** `test_csrf_protection_rejects_missing_token()` asserting HTTP 400 Bad Request on state-changing requests without CSRF token.

---

### Threat 7: Cross-Site Scripting (XSS)
- **Description:** Injection of malicious scripts into user inputs (space descriptions, reviews, inquiries, chat) rendered into the browser.
- **Impact:** Execution of malicious scripts in victims browsers, session token theft, DOM manipulation.
- **Mitigation:**
  1. Rely on Jinja2 auto-escaping by default.
  2. Ensure any raw HTML rendering is sanitized using bleach or equivalent sanitizers.
  3. Configure Content-Security-Policy (CSP) and security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`).
- **Test:** `test_xss_sanitization_in_space_and_chat()` verifying HTML tags are escaped or stripped.

---

### Threat 8: Insecure Direct Object Reference (IDOR)
- **Description:** A user manipulates an object identifier (e.g. `space_id`, `booking_id`) in URL paths or request payloads to access or modify resources belonging to another user.
- **Impact:**
  - Seeker A viewing or canceling Seeker B booking.
  - Host A editing, pausing, or deleting Host B space listing.
  - Seeker triggering GPS check-in or checkout condition report for another user session.
- **Mitigation:**
  1. Centralized permission verification:
     ```python
     authorize(current_user, Permission.SPACE_UPDATE, resource=space)
     authorize(current_user, Permission.BOOKING_CANCEL, resource=booking)
     ```
  2. Reject requests where `resource.owner_id != current_user.id` with HTTP 403 Forbidden (or HTTP 404 for enumeration resistance), unless `current_user.is_admin`.
- **Test:** `test_idor_space_edit_forbidden()` and `test_idor_booking_cancel_forbidden()`.

---

### Threat 9: Privilege Escalation
- **Description:** A regular user elevates their privileges to Host or Admin without authorization (e.g. submitting `role=admin` in registration or modifying profile parameters).
- **Impact:** Full compromise of platform administration, ability to modify platform fees, view all user records, or alter system settings.
- **Mitigation:**
  1. Strict schema filtering on registration: only allow `seeker` or `owner` (host) registration roles; never accept `admin` from client payload.
  2. Administrative privileges are bound to server-side `is_admin` boolean / `admin` role, provisioned exclusively via CLI (`scripts/create_admin.py`) or database administration.
- **Test:** `test_registration_cannot_grant_admin()` asserting attempts to register with `role=admin` default to standard role and set `is_admin=False`.

---

### Threat 10: Role Tampering & Persona Hijacking
- **Description:** Manipulating the persona switching mechanism (`/switch-role` or `/switch-user`) to assume another physical user account.
- **Impact:** Account takeover and identity forgery.
- **Mitigation:**
  1. Remove `/switch-user` entirely.
  2. Persona switching must never modify `session["user_id"]` or change the database user record.
  3. Persona switching only modifies `session["active_context"]` between `seeker` and `host` for users with dual capability (`role == "both"`).
- **Test:** `test_persona_switching_preserves_user_identity()`.

---

### Threat 11: Account Enumeration
- **Description:** Attacker uses differences in response messages, HTTP status codes, or response times on login or password reset endpoints to identify whether an email address exists in the system.
- **Impact:** Targeted spear phishing and user reconnaissance against platform hosts and students.
- **Mitigation:**
  1. Generic authentication error messages: *"Invalid email or password"* for both non-existent accounts and wrong passwords.
  2. Password reset requests return identical confirmation messages: *"If that email is registered, a password reset link has been sent."*
  3. Maintain constant-time processing paths for non-existent users (e.g. running dummy hash calculation).
- **Test:** `test_generic_error_on_invalid_credentials()` and `test_password_reset_constant_response()`.

---

### Threat 12: Password Reset Abuse
- **Description:** Exploitation of password reset workflows through predictable tokens, lack of token expiration, or multi-use tokens.
- **Impact:** Unauthorized account takeover through password overwrite.
- **Mitigation:**
  1. Cryptographically secure pseudo-random tokens (`secrets.token_urlsafe(32)`).
  2. Store token hashes in `PasswordResetToken` table, not plaintext tokens.
  3. Short expiration window (e.g. 1 hour / 3600 seconds).
  4. Invalidate token immediately upon single use (`used = True`).
  5. Invalidate all active sessions for that user upon successful password reset.
- **Test:** `test_password_reset_token_single_use()` and `test_expired_reset_token_rejected()`.

---

### Threat 13: Unauthorized Booking Access & Tampering
- **Description:** Unauthenticated or unauthorized third parties creating bookings, viewing lease contracts, or accessing room session QR codes.
- **Impact:** Unauthorized physical space access, breach of legal micro-lease agreements, financial fraud.
- **Mitigation:**
  1. Restrict `/api/bookings` creation strictly to authenticated users with `@login_required`.
  2. Digital micro-lease contracts, live QR access codes, and in-room sessions (`/booking/<id>/session`) are viewable ONLY by the verified renter or the space host.
- **Test:** `test_anonymous_booking_creation_rejected()` and `test_unauthorized_session_view_forbidden()`.

---

### Threat 14: Unauthorized Space Modification
- **Description:** Modifying pricing, availability, or status of listings belonging to other hosts.
- **Impact:** Host business disruption, unauthorized discount creation, malicious listing takedowns.
- **Mitigation:**
  1. Space updates (`/api/spaces/<id>/edit`, `/api/spaces/<id>/toggle-status`) require explicit ownership verification.
  2. Ownership check: `space.owner_id == current_user.id or current_user.is_admin`.
- **Test:** `test_host_cannot_modify_other_host_space()`.

---

### Threat 15: Admin Endpoint Abuse
- **Description:** Non-admin users accessing administrative actions such as simulation toggles, system status overrides, or bulk user management.
- **Impact:** Platform stability risks and system configuration tampering.
- **Mitigation:**
  1. Protect admin routes with `@permission_required(Permission.ADMIN_ACCESS)`.
  2. Restrict dangerous development endpoints (`/api/dev/toggle-ai-simulation`) to `FLASK_ENV=development` and administrative accounts.
- **Test:** `test_non_admin_cannot_access_admin_endpoints()`.

---

## 3. Threat Mitigation Summary Matrix

| Threat # | OWASP Category | Target Layer | Key Mitigation | Primary Test |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | A02: Cryptographic Failures | Password hashing | Werkzeug PBKDF2/Argon2id + log sanitization | `test_password_hashing` |
| **T2** | A07: Identification & Auth Failures | Authentication | Flask-Limiter (5/min) + AuditLog | `test_login_rate_limiting` |
| **T3** | A07: Identification & Auth Failures | Authentication | IP Rate Limiting + Generic Responses | `test_credential_stuffing` |
| **T4** | A07: Identification & Auth Failures | Session | Session regeneration on login | `test_session_fixation` |
| **T5** | A07: Identification & Auth Failures | Session | HttpOnly, SameSite=Lax, Secure flags | `test_cookie_security_flags` |
| **T6** | A01: Broken Access Control | Web Forms / API | Flask-WTF CSRFProtect + token validation | `test_csrf_protection` |
| **T7** | A03: Injection | Rendering | Jinja2 autoescaping + Bleach sanitization | `test_xss_protection` |
| **T8** | A01: Broken Access Control | Data Access | Central `authorize()` check on all models | `test_idor_protection` |
| **T9** | A01: Broken Access Control | Authorization | Server-side role assignment only | `test_privilege_escalation` |
| **T10** | A01: Broken Access Control | Session | Persona switch updates context only | `test_persona_tampering` |
| **T11** | A07: Identification & Auth Failures | User Enum | Constant-time generic error messages | `test_account_enumeration` |
| **T12** | A07: Identification & Auth Failures | Token Lifecycle | Cryptographic hash tokens, 1h TTL, 1x use | `test_reset_token_lifecycle` |
| **T13** | A01: Broken Access Control | Bookings | `@login_required` + renter/host ownership | `test_booking_authorization` |
| **T14** | A01: Broken Access Control | Spaces | `@login_required` + space owner check | `test_space_authorization` |
| **T15** | A01: Broken Access Control | Admin | `@permission_required(Permission.ADMIN_ACCESS)` | `test_admin_endpoint_abuse` |
