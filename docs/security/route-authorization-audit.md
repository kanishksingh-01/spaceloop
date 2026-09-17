# SpaceLoop Route Authorization Audit

> **Document Version:** 1.0.0  
> **Classification:** Security Architecture & Route Access Control  
> **Date:** September 17, 2026  
> **Status:** AUDIT COMPLETE — PENDING IMPLEMENTATION

---

## 1. Scope & Objective

This document audits all 36 routes currently exposed by `app.py`. For each route, we evaluate:
1. **Current Access:** What credentials or identity are currently checked.
2. **Current Vulnerabilities / Demo Assumptions:** Fallbacks, lack of ownership checks, IDOR risks.
3. **Target Authentication Requirement:** Public/Anonymous, Authenticated Session (`@login_required`), or Token.
4. **Target Authorization Requirement:** Required role (`Seeker`, `Host`, `Admin`) or fine-grained capability.
5. **Resource Ownership Check:** Whether access must be restricted to the resource creator/owner.

---

## 2. Comprehensive Route Matrix

| Route & Methods | Current Access | Required Auth | Target Role / Perm | Ownership Check Required? | Insecure Pattern / Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /` | Public / Renders index with fallback user | Public | Anonymous / Any | No | **Current:** Loads listings + user query fallback. **Target:** Clean, public landing page with CTAs. Move catalog to `/explore` (or anchor). |
| `GET /space/<int:space_id>` | Public | Public | Anonymous / Any | No | Anyone can view space details. Preserve public view. |
| `GET /list-space` | Public (fallback to host) | `@login_required` | `Host` capability | No | Redirect unauthenticated users to `/auth/login?next=/list-space`. |
| `POST /api/spaces/<int:space_id>/edit` | Public / No auth check | `@login_required` | `Host` or `Admin` | **YES:** `space.owner_id == current_user.id` or `current_user.is_admin` | **CRITICAL IDOR:** Anyone can edit any space. Fix with `authorize(current_user, Permission.SPACE_UPDATE, space)`. |
| `GET /calculator` | Public (fallback to host) | Public | Any | No | Anyone can use the yield calculator. If logged in, can prefill host context. |
| `GET /dashboard` | Insecure fallback (`seeker` or first user) | `@login_required` | Any authenticated user | Context-dependent | Render Host or Seeker dashboard based on `session["active_context"]` or role. Never fallback to stranger. |
| `POST /api/spaces/<int:space_id>/toggle-status` | Public / No auth check | `@login_required` | `Host` or `Admin` | **YES:** `space.owner_id == current_user.id` or `current_user.is_admin` | **CRITICAL IDOR:** Anyone can pause/activate any space. Check ownership. |
| `GET /how-it-works` | Public | Public | Anonymous / Any | No | Informational page. Keep public. |
| `GET /login` | Public (renders switcher pills) | Public | Anonymous (redirect if authed) | No | Replace with production login form (`/auth/login`). |
| `GET, POST /switch-user/<int:user_id>` | Public arbitrary login | **DELETE** | N/A | N/A | **CRITICAL AUTH BYPASS:** Allows logging in as any user without password. Remove completely. |
| `GET /verify` | Insecure fallback user | `@login_required` | `Seeker` or `Host` | **YES:** Verification is strictly bound to `current_user` | Decouple from auth, but require authentication to submit KYC. |
| `GET /booking/<int:booking_id>/session` | Insecure fallback user | `@login_required` | `Seeker` or `Host` | **YES:** `booking.renter_id == current_user.id` or `booking.space.owner_id == current_user.id` | **IDOR:** Only renter or space host may view live session timer/QR. |
| `GET /space/<int:space_id>/printable-qr` | Public | `@login_required` | `Host` or `Admin` | **YES:** `space.owner_id == current_user.id` or `current_user.is_admin` | Only space owner can download host physical access QR. |
| `GET /profile` | Insecure fallback user | `@login_required` | Any authenticated user | **YES:** Displays only `current_user` profile | No fallback. Must require `@login_required`. |
| `GET /inquiries` | Insecure fallback user | `@login_required` | `Host` or `Seeker` | **YES:** Only inquiries sent or received by `current_user` | Filter inquiries by `current_user.id`. |
| `GET /session` | Insecure fallback redirect | `@login_required` | Any authenticated user | **YES:** Redirects to `current_user` active booking session | Look up active booking for `current_user.id` only. |
| `GET, POST /switch-role` | Switches database user ID | `@login_required` | `both` capability | No ID switch | **CRITICAL:** Changes database user ID. Must only switch UI context (`session["active_context"]`). |
| `GET /api/spaces` | Public | Public | Anonymous / Any | No | Public discovery catalog. Keep public. |
| `GET /api/spaces/<int:space_id>` | Public | Public | Anonymous / Any | No | Public space data. |
| `POST /api/spaces/ai-scan` | Public / No auth check | `@login_required` | `Host` | No | AI vision room scanner for listing creation. Require host auth to prevent API abuse. |
| `POST /api/spaces` | Fallback to default host | `@login_required` | `Host` capability | **YES:** Assigns `space.owner_id = current_user.id` | Never fallback to host ID 1. Reject with 401 if unauthenticated. |
| `POST /api/spaces/ai-match` | Public | Public | Anonymous / Any | No | Natural language search. Rate-limited by IP/session. |
| `POST /api/bookings/precheck` | Public | Public | Anonymous / Any | No | Rate calculation pre-flight. Keep public for cost preview. |
| `POST /api/bookings` | Fallback to default seeker (ID 2) | `@login_required` | `Seeker` capability | **YES:** Sets `renter_id = current_user.id` | **CRITICAL:** Never assign booking to fallback user. Enforce login. |
| `POST /api/calculator/estimate` | Public | Public | Any | No | Financial yield calculator. Keep public. |
| `POST /api/ai/chat` | Fallback to user | Public / Opt-Auth | Any | No | AI assistant chat. Use `current_user` if authed, anonymous session if not. |
| `GET /api/system/status` | Public | Public | Any | No | System health / simulation toggle status. |
| `POST, GET /api/dev/toggle-ai-simulation`| Public | Admin / Dev only | `Admin` | No | Protect or restrict to local development environment. |
| `POST /api/verify/student` | Insecure fallback seeker | `@login_required` | `Seeker` | **YES:** Updates `current_user.student_verified` | Must update only the authenticated user. |
| `POST /api/verify/host` | Insecure fallback owner | `@login_required` | `Host` | **YES:** Updates `current_user.host_verified` | Must update only the authenticated user. |
| `POST /api/booking/<int:booking_id>/check-in` | Insecure fallback seeker | `@login_required` | `Seeker` | **YES:** `booking.renter_id == current_user.id` | **CRITICAL IDOR:** Only the registered renter can GPS check-in. |
| `POST /api/booking/<int:booking_id>/check-out` | Insecure fallback seeker | `@login_required` | `Seeker` | **YES:** `booking.renter_id == current_user.id` | **CRITICAL IDOR:** Only the registered renter can check out and submit escrow refund inspection. |
| `POST /api/booking/<int:booking_id>/cancel` | Public / No auth check | `@login_required` | `Seeker`, `Host`, `Admin`| **YES:** Must be renter, space host, or admin | **CRITICAL IDOR:** Anyone can cancel any booking. Enforce ownership check. |
| `GET, POST /api/inquiries` | Insecure fallback seeker/host | `@login_required` | Any authenticated user | **YES:** Sent as `current_user.id` or fetched for `current_user.id` | Disallow spoofing sender ID. |
| `GET /health` | Public | Public | Any | No | Health check endpoint. |
| `GET /api/health` | Public | Public | Any | No | Health check endpoint. |

---

## 3. New Auth Endpoints to Add

| Endpoint & Methods | Auth Level | Purpose |
| :--- | :--- | :--- |
| `GET, POST /auth/register` | Public (Anonymous only) | Production user registration with server-side validation & rate limiting. |
| `GET, POST /auth/login` | Public (Anonymous only) | Secure password-verified login with generic failure error alerts & rate limiting. |
| `POST /auth/logout` | `@login_required` | Secure session teardown, cookie invalidation, and session regeneration. |
| `GET, POST /auth/forgot-password` | Public | Request password reset token with constant-time generic confirmation. |
| `GET, POST /auth/reset-password/<token>`| Public | Verify cryptographic token and update password hash. |
| `GET /auth/verify-email/<token>` | Public | Verify cryptographic email token and mark account verified. |
| `GET /api/v1/auth/me` | `@login_required` | Return sanitized user profile for SPA/AJAX frontend. |
| `GET /explore` | Public | Dedicated spaces exploration page (moved from root index). |
| `GET /auth/access-denied` | Public / Authed | User-friendly 403 error page. |

---

## 4. Key Remediation Summary

1. **Delete `/switch-user`:** Eliminates arbitrary user takeover.
2. **Refactor `/switch-role`:** Eliminates account hijacking across personas.
3. **Eliminate All Fallbacks:** Remove `User.query.filter_by(role="...").first()` and `session.get("user_id", 1)` across all 16 occurrences.
4. **Enforce Strict Ownership:** Add `authorize(current_user, permission, resource)` guards to `/api/spaces/<id>/edit`, `/api/spaces/<id>/toggle-status`, `/api/booking/<id>/check-in`, `/api/booking/<id>/check-out`, and `/api/booking/<id>/cancel`.
