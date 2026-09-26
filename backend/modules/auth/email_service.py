"""
SpaceLoop Email Notification Service
Follows Rule 6: Clean service interface with replaceable adapters.
Re-exports the centralized EmailService and adapters from backend.modules.email
maintaining full backward compatibility.
"""
from backend.modules.email import (
    EmailService,
    BaseEmailAdapter,
    DevelopmentEmailAdapter,
    SMTPEmailAdapter,
    ResendEmailAdapter,
)

__all__ = [
    "EmailService",
    "BaseEmailAdapter",
    "DevelopmentEmailAdapter",
    "SMTPEmailAdapter",
    "ResendEmailAdapter",
]
