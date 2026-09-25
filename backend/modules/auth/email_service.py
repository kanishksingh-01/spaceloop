"""
SpaceLoop Email Notification Service
Follows Rule 6: Clean service interface with replaceable adapters.
Provides DevelopmentEmailAdapter (logging/testing) and SMTPEmailAdapter (when configured).
"""
import os
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("spaceloop.email")


class BaseEmailAdapter(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        pass


class DevelopmentEmailAdapter(BaseEmailAdapter):
    """
    Local development and testing adapter.
    Logs email dispatch securely without sending network packets.
    """
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        logger.info(f"[DEV EMAIL ADAPTER] To: {to_email} | Subject: {subject}\n{body}")
        # Retain last dispatched email in memory for test assertions
        DevelopmentEmailAdapter.last_sent = {
            "to": to_email,
            "subject": subject,
            "body": body
        }
        return True


DevelopmentEmailAdapter.last_sent = None


class SMTPEmailAdapter(BaseEmailAdapter):
    """
    Production SMTP adapter using standard library smtplib.
    """
    def __init__(self, host: str, port: int, user: str, password: str, from_email: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.user and self.password:
                    server.starttls()
                    server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
            return False


class EmailService:
    _adapter: BaseEmailAdapter = None

    @classmethod
    def get_adapter(cls) -> BaseEmailAdapter:
        if cls._adapter is None:
            smtp_host = os.environ.get("SMTP_HOST")
            if smtp_host:
                cls._adapter = SMTPEmailAdapter(
                    host=smtp_host,
                    port=int(os.environ.get("SMTP_PORT", 587)),
                    user=os.environ.get("SMTP_USER", ""),
                    password=os.environ.get("SMTP_PASSWORD", ""),
                    from_email=os.environ.get("SMTP_FROM", "noreply@spaceloop.in")
                )
            else:
                cls._adapter = DevelopmentEmailAdapter()
        return cls._adapter

    @classmethod
    def set_adapter(cls, adapter: BaseEmailAdapter):
        cls._adapter = adapter

    @classmethod
    def send_password_reset(cls, to_email: str, raw_token: str, reset_url: str = None) -> bool:
        link = reset_url or f"/auth/reset-password/{raw_token}"
        subject = "SpaceLoop — Password Reset Request"
        body = (
            f"Hello,\n\n"
            f"A password reset was requested for your SpaceLoop account.\n"
            f"To reset your password, visit the link below:\n\n"
            f"{link}\n\n"
            f"If you did not request this, please disregard this message.\n"
            f"This link expires in 1 hour."
        )
        return cls.get_adapter().send_email(to_email, subject, body)

    @classmethod
    def send_email_verification(cls, to_email: str, raw_token: str, verify_url: str = None) -> bool:
        link = verify_url or f"/auth/verify-email/{raw_token}"
        subject = "SpaceLoop — Verify Your Email Address"
        body = (
            f"Hello,\n\n"
            f"Thank you for registering on SpaceLoop.\n"
            f"Please verify your email address by visiting:\n\n"
            f"{link}\n\n"
            f"This link expires in 24 hours."
        )
        return cls.get_adapter().send_email(to_email, subject, body)
