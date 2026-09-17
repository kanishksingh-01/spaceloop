# SpaceLoop Authorization Matrix

> **Document Version:** 1.0.0  
> **Classification:** Security Specification & Access Control Matrix  
> **Date:** September 17, 2026  
> **Status:** SPECIFICATION COMPLETE

---

## 1. System Roles & Capabilities

SpaceLoop defines four core subject authorization tiers:

1. **ANON (Anonymous / Guest):** Unauthenticated visitors. Allowed to view public landing pages, explore listings, calculate estimated yields, and initiate registration/login.
2. **SEEKER (Student / Remote Worker / Renter):** Authenticated users looking for micro-spaces. Can create bookings, manage their own bookings, check in with GPS, check out, and submit student verification (DigiLocker).
3. **HOST (Space Owner / Property Manager):** Authenticated users offering micro-spaces. Can create and edit their own listings, view bookings for their spaces, download physical QR access signs, view earnings, and submit host KYC (Discom/Electricity bill).
4. **ADMIN (Platform Administrator):** Privileged system operators provisioned solely via trusted server-side mechanisms (`scripts/create_admin.py`). Can inspect system status, moderate listings, and manage system operations.

*Note on Dual Capabilities:* A user registered with `role="both"` holds both SEEKER and HOST capabilities concurrently. The user may switch their UI viewing context (`session["active_context"]`) between Seeker and Host modes, without changing their authenticated identity (`current_user.id`).

---

## 2. Formal Authorization Matrix

| Action / Resource | ANON | SEEKER | HOST | ADMIN | Permission Enum | Ownership Check |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Landing Page** (`GET /`) | **Y** | **Y** | **Y** | **Y** | Public | None |
| **Explore Public Spaces** (`GET /api/spaces`) | **Y** | **Y** | **Y** | **Y** | Public | None |
| **Space Details** (`GET /space/<id>`) | **Y** | **Y** | **Y** | **Y** | Public | None |
| **Yield Calculator** (`POST /api/calculator/estimate`) | **Y** | **Y** | **Y** | **Y** | Public | None |
| **User Registration** (`POST /auth/register`) | **Y** | **N** (Authed) | **N** (Authed) | **N** | Public (Anon) | None |
| **User Login** (`POST /auth/login`) | **Y** | **N** (Authed) | **N** (Authed) | **N** | Public (Anon) | None |
| **Create Booking** (`POST /api/bookings`) | **N** | **Y** | **Y** | **Y** | `BOOKING_CREATE` | Assigns `renter_id = current_user.id` |
| **View Own Booking** (`GET /booking/<id>/session`) | **N** | **Y** | **Y** | **Y** | `BOOKING_VIEW` | `booking.renter_id == user.id` OR `booking.space.owner_id == user.id` |
| **View Others Booking** | **N** | **N** | **N** | **Y** | `BOOKING_VIEW_ALL` | Admin only |
| **Check-In Booking (GPS)** (`POST /api/booking/<id>/check-in`) | **N** | **Y** | **N** | **Y** | `BOOKING_CHECKIN` | `booking.renter_id == user.id` |
| **Check-Out Booking (Inspection)** (`POST /api/booking/<id>/check-out`) | **N** | **Y** | **N** | **Y** | `BOOKING_CHECKOUT` | `booking.renter_id == user.id` |
| **Cancel Booking** (`POST /api/booking/<id>/cancel`) | **N** | **Y** | **Y** | **Y** | `BOOKING_CANCEL` | Renter or Space Host or Admin |
| **Create Space** (`POST /api/spaces`) | **N** | **N\*** | **Y** | **Y** | `SPACE_CREATE` | Requires Host capability |
| **Edit Own Space** (`POST /api/spaces/<id>/edit`) | **N** | **N** | **Y** | **Y** | `SPACE_UPDATE` | `space.owner_id == current_user.id` |
| **Toggle Own Space Status** (`POST /api/spaces/<id>/toggle-status`) | **N** | **N** | **Y** | **Y** | `SPACE_UPDATE` | `space.owner_id == current_user.id` |
| **Edit Others Space** | **N** | **N** | **N** | **Y** | `SPACE_MODERATE` | Admin only |
| **Printable QR Sign** (`GET /space/<id>/printable-qr`) | **N** | **N** | **Y** | **Y** | `SPACE_VIEW` | `space.owner_id == current_user.id` or Admin |
| **View Own Earnings** (`GET /dashboard`) | **N** | **N** | **Y** | **Y** | `EARNINGS_VIEW` | Restricted to host context/owner |
| **Admin Dashboard** | **N** | **N** | **N** | **Y** | `ADMIN_ACCESS` | `current_user.is_admin` |
| **Manage Users** | **N** | **N** | **N** | **Y** | `USER_MANAGE` | `current_user.is_admin` |
| **Moderate Spaces** | **N** | **N** | **N** | **Y** | `SPACE_MODERATE` | `current_user.is_admin` |
| **Toggle AI Simulation** (`POST /api/dev/toggle-ai-simulation`) | **N** | **N** | **N** | **Y** | `SYSTEM_CONFIGURE` | Admin / Dev only |

*\* A seeker can transition to host capability through a proper server-authorized host onboarding flow (setting `user.role = "both"` or creating a listing once identity is verified).*

---

## 3. Centralized Permission Definitions

Implemented in `backend/modules/auth/permissions.py`:

```python
from enum import Enum, auto

class Permission(Enum):
    # Public
    PUBLIC_VIEW = auto()
    
    # Booking permissions
    BOOKING_CREATE = auto()
    BOOKING_VIEW = auto()
    BOOKING_CANCEL = auto()
    BOOKING_CHECKIN = auto()
    BOOKING_CHECKOUT = auto()
    BOOKING_VIEW_ALL = auto()
    
    # Space permissions
    SPACE_CREATE = auto()
    SPACE_VIEW = auto()
    SPACE_UPDATE = auto()
    SPACE_DELETE = auto()
    SPACE_MODERATE = auto()
    
    # Financial & Host
    EARNINGS_VIEW = auto()
    
    # Admin permissions
    ADMIN_ACCESS = auto()
    USER_MANAGE = auto()
    SYSTEM_CONFIGURE = auto()
```

---

## 4. Resource Ownership Verification Contract

The central `authorize(user, permission, resource=None)` function enforces:

1. **Authentication Gate:** If `user is None` or `user.is_anonymous`, reject all non-public permissions with HTTP 401.
2. **Admin Superuser Override:** If `user.is_admin`, allow all permissions unconditionally.
3. **Role & Capability Match:** Verify user holds required capability for the action.
4. **Ownership Verification:**
   - For `Space`:
     ```python
     if permission in (Permission.SPACE_UPDATE, Permission.SPACE_DELETE):
         if space.owner_id != user.id and not user.is_admin:
             raise ForbiddenError("You do not have permission to modify this space.")
     ```
   - For `Booking`:
     ```python
     if permission == Permission.BOOKING_VIEW:
         if booking.renter_id != user.id and booking.space.owner_id != user.id and not user.is_admin:
             raise ForbiddenError("You do not have permission to view this booking.")
     if permission in (Permission.BOOKING_CHECKIN, Permission.BOOKING_CHECKOUT):
         if booking.renter_id != user.id and not user.is_admin:
             raise ForbiddenError("Only the verified renter may check in or out.")
     if permission == Permission.BOOKING_CANCEL:
         if booking.renter_id != user.id and booking.space.owner_id != user.id and not user.is_admin:
             raise ForbiddenError("You do not have permission to cancel this booking.")
     ```

---

## 5. Automated Test Coverage Derived from Matrix

Every cell in this matrix must be directly covered by unit and integration tests:
- `test_matrix_public_access_allowed_for_anonymous()`
- `test_matrix_seeker_cannot_edit_space()`
- `test_matrix_host_cannot_edit_other_host_space()`
- `test_matrix_seeker_cannot_checkin_other_seeker_booking()`
- `test_matrix_admin_can_moderate_any_space()`
- `test_matrix_anonymous_cannot_create_booking()`
