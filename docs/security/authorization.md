# SpaceLoop Authorization Architecture

> **Document Version:** 1.0.0  
> **Classification:** Technical Architecture & Security Specification  
> **Date:** September 17, 2026

---

## 1. Principles of SpaceLoop Authorization

1. **Principle of Least Privilege:** Users operate with the minimum permissions required for their tasks.
2. **Server-Side Authorization Authority:** The client may request actions, but the server unconditionally determines whether the action is permitted based on `current_user` capabilities and database records.
3. **Decoupled Personas:** A user possessing dual capabilities (`role="both"`) can toggle their viewing perspective between Host and Seeker dashboards (`session["active_context"]`), but their identity (`current_user.id`) never changes.
4. **Strict Object Ownership:** Verifying identity alone is insufficient; mutations to a resource (`Space`, `Booking`) must verify that `current_user` is the rightful owner or an administrator.

---

## 2. Centralized Permission System

Implemented in `backend/modules/auth/permissions.py`:

```python
def authorize(user, permission: Permission, resource=None) -> bool:
    if not user or not user.is_authenticated:
        raise UnauthorizedError("Authentication required")
        
    if user.is_admin:
        return True  # Administrators have full platform access
        
    # Space Ownership Rules
    if permission in (Permission.SPACE_UPDATE, Permission.SPACE_DELETE):
        if not resource or resource.owner_id != user.id:
            raise ForbiddenError("You do not own this space listing.")
            
    # Booking Rules
    if permission == Permission.BOOKING_VIEW:
        if not resource or (resource.renter_id != user.id and resource.space.owner_id != user.id):
            raise ForbiddenError("You do not have permission to view this booking.")
            
    if permission in (Permission.BOOKING_CHECKIN, Permission.BOOKING_CHECKOUT):
        if not resource or resource.renter_id != user.id:
            raise ForbiddenError("Only the verified renter may check in/out.")
            
    if permission == Permission.BOOKING_CANCEL:
        if not resource or (resource.renter_id != user.id and resource.space.owner_id != user.id):
            raise ForbiddenError("You do not have permission to cancel this booking.")
            
    return True
```

---

## 3. Administrative Boundary & Provisioning

Administrative capabilities are strictly guarded:
- Admins bypass ownership checks for moderation and dispute resolution.
- Admins are NEVER provisioned via web registration forms or URL parameters.
- Admin creation is restricted to explicit command-line invocation via `scripts/create_admin.py`, requiring interactive email/password entry.
