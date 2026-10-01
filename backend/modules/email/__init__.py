"""
SpaceLoop Email Module
Centralized, production-ready transactional email service using Resend.
"""
from backend.modules.email.adapter import (
    BaseEmailAdapter,
    ResendEmailAdapter,
    DevelopmentEmailAdapter,
    SMTPEmailAdapter,
    BrevoEmailAdapter,
)
from backend.modules.email.service import EmailService

__all__ = [
    "EmailService",
    "BaseEmailAdapter",
    "ResendEmailAdapter",
    "DevelopmentEmailAdapter",
    "SMTPEmailAdapter",
    "BrevoEmailAdapter",
]

