# SpaceLoop Authentication Architecture

> **Document Version:** 1.0.0  
> **Classification:** Technical Architecture & Implementation Guide  
> **Date:** September 17, 2026

---

## 1. Architectural Overview

SpaceLoop transitions from a demo identity model (inferred IDs and client-controlled switching) to an industry-standard, session-based authentication architecture utilizing **Flask-Login**, **Werkzeug Password Hashing**, **Flask-WTF CSRF Protection**, and **Flask-Limiter**.

### Key Architectural Tenets
1. **Immutable User Identity:** An authenticated session maps strictly to a single persistent user record in the database (`current_user.id`).
2. **Separation of Concerns:** Authentication (who you are) is strictly separated from Verification (what legal credentials you have submitted, e.g. DigiLocker, electricity bills) and from Persona Context (whether you are currently viewing the seeker or host dashboard).
3. **Generic Error Responses:** All authentication failures return identical, non-revealing messages to eliminate user enumeration vectors.
4. **Defense in Depth:** IP rate limiting, CSRF tokens, secure session cookie flags, and database audit logs protect authentication endpoints.

---

## 2. Core Authentication Workflows

### 2.1 Registration (`POST /auth/register`)
1. Visitor submits `first_name`, `last_name`, `email`, `password`, `confirm_password`, and requested initial role (`seeker` or `owner`).
2. System validates input:
   - Email format & uniqueness (case-insensitive query).
   - Password complexity: minimum 8 characters, containing letters and numbers.
   - Role validation: strictly allows `"seeker"` or `"owner"`. Rejects any payload attempting `"admin"`.
3. System hashes password using Werkzeug (`generate_password_hash` with PBKDF2:SHA256).
4. Generates a unique UUID `public_id`.
5. Inserts `User` record with `is_active=True`, `is_email_verified=False`, `is_admin=False`.
6. Issues cryptographic `EmailVerificationToken` (32 bytes urlsafe token, hashed in database, 24-hour expiration).
7. Emits `AuditLog(action="AUTH_REGISTER_SUCCESS")`.
8. Automatically logs the user in via Flask-Login `login_user()`, or redirects to login with verification banner.

### 2.2 Login (`POST /auth/login`)
1. User submits `email` and `password`.
2. Flask-Limiter enforces max 5 attempts/minute per client IP.
3. System fetches user by email. If not found or `user.is_active` is False, system computes a dummy password hash (constant-time defense against timing attacks) and responds with:
   *"Invalid email or password"*.
4. System verifies password with `check_password_hash(user.password_hash, password)`.
5. Upon failure, records `AuditLog(action="AUTH_LOGIN_FAILED")` and returns generic error.
6. Upon success:
   - Calls `login_user(user, remember=remember_me)`.
   - Flask-Login cycles the session to prevent session fixation.
   - Sets `session["active_context"] = "host" if user.role == "owner" else "seeker"`.
   - Updates `user.last_login_at = datetime.utcnow()`.
   - Records `AuditLog(action="AUTH_LOGIN_SUCCESS")`.
   - Redirects to sanitized `next` URL (safe relative redirect check) or default dashboard.

### 2.3 Logout (`POST /auth/logout`)
1. Validates CSRF token.
2. Calls `logout_user()`.
3. Clears all session keys (`session.clear()`).
4. Records `AuditLog(action="AUTH_LOGOUT")`.
5. Flashes confirmation message and redirects to landing page (`GET /`).

### 2.4 Password Reset (`/auth/forgot-password` & `/auth/reset-password/<token>`)
1. User submits email on `/auth/forgot-password`.
2. Regardless of whether the email exists, system returns:
   *"If that email is registered, password reset instructions have been generated."*
3. If user exists:
   - Invalidates previous unused reset tokens for this user.
   - Generates raw token `secrets.token_urlsafe(32)`.
   - Stores SHA-256 hash of token in `PasswordResetToken` table with 1-hour expiration (`expires_at = utcnow() + 3600s`).
   - In production, sends email with reset link; in development, logs token link for testing.
4. User clicks link: `/auth/reset-password/<raw_token>`
5. Backend hashes raw token, looks up unexpired, unused token record.
6. If valid: prompts for new password, updates `user.password_hash`, marks token `used=True`, invalidates all existing sessions.

---

## 3. Library Integration & Dependencies

- `Flask-Login (>= 0.6.3)`: User session lifecycle, `current_user`, `@login_required`.
- `Flask-WTF (>= 1.2.1)`: Form validation, global `CSRFProtect`.
- `Flask-Limiter (>= 3.5.0)`: Rate limiting auth endpoints by client IP address.
- `Werkzeug (>= 3.0.0)`: Cryptographic password hashing and constant-time string comparisons.
