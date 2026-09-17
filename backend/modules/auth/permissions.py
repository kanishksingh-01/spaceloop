from enum import Enum, auto


class Permission(Enum):
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

    # Host & Earnings
    EARNINGS_VIEW = auto()

    # Administrative
    ADMIN_ACCESS = auto()
    USER_MANAGE = auto()
    SYSTEM_CONFIGURE = auto()


class AuthError(Exception):
    def __init__(self, message: str = "Access denied", status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UnauthorizedError(AuthError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenError(AuthError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)


def authorize(user, permission: Permission, resource=None) -> bool:
    """
    Centralized server-side authorization evaluation engine.
    Enforces role capabilities, object ownership, and administrative privilege.
    """
    # 1. Public permissions require no authentication
    if permission == Permission.PUBLIC_VIEW:
        return True

    # 2. Authentication check
    if not user or not getattr(user, "is_authenticated", False):
        raise UnauthorizedError("Authentication is required to perform this action.")

    # 3. Administrator superuser bypass
    if getattr(user, "is_admin", False):
        return True

    # 4. Role & capability gates
    if permission in (Permission.ADMIN_ACCESS, Permission.USER_MANAGE, Permission.SYSTEM_CONFIGURE, Permission.SPACE_MODERATE):
        raise ForbiddenError("Administrative privileges are required for this action.")

    if permission == Permission.SPACE_CREATE:
        if not getattr(user, "is_host", False):
            raise ForbiddenError("Host capability is required to list a space.")

    if permission == Permission.EARNINGS_VIEW:
        if not getattr(user, "is_host", False):
            raise ForbiddenError("Host capability is required to view space earnings.")

    # 5. Object ownership checks
    if permission in (Permission.SPACE_UPDATE, Permission.SPACE_DELETE):
        if resource is not None:
            owner_id = getattr(resource, "owner_id", None)
            if owner_id != user.id:
                raise ForbiddenError("You do not have permission to modify or delete this space listing.")

    if permission == Permission.BOOKING_VIEW:
        if resource is not None:
            renter_id = getattr(resource, "renter_id", None)
            space = getattr(resource, "space", None)
            space_owner_id = getattr(space, "owner_id", None) if space else None
            if renter_id != user.id and space_owner_id != user.id:
                raise ForbiddenError("You do not have permission to view this booking.")

    if permission in (Permission.BOOKING_CHECKIN, Permission.BOOKING_CHECKOUT):
        if resource is not None:
            renter_id = getattr(resource, "renter_id", None)
            if renter_id != user.id:
                raise ForbiddenError("Only the verified renter of this booking may perform check-in or check-out.")

    if permission == Permission.BOOKING_CANCEL:
        if resource is not None:
            renter_id = getattr(resource, "renter_id", None)
            space = getattr(resource, "space", None)
            space_owner_id = getattr(space, "owner_id", None) if space else None
            if renter_id != user.id and space_owner_id != user.id:
                raise ForbiddenError("You do not have permission to cancel this booking.")

    return True
