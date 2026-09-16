from enum import Enum

class SessionState(str, Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    COMPLETED = "completed"

class EscrowStatus(str, Enum):
    HELD = "held"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class UserRole(str, Enum):
    SEEKER = "seeker"
    OWNER = "owner"
    ADMIN = "admin"
