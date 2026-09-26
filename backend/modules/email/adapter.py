"""
SpaceLoop Email Adapters
Follows Rule 6: Clean service interface with replaceable adapters.
Supports Resend API (production), DevelopmentEmailAdapter (in-memory/testing), and SMTPEmailAdapter (fallback).
"""
import os
import re
import time
import uuid
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("spaceloop.email")


class BaseEmailAdapter(ABC):
    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        idempotency_key: str = None
    ) -> tuple[bool, str | None, str | None]:
        """
        Dispatches an email.
        Returns:
            (success: bool, provider_message_id: str | None, error_message: str | None)
        """
        pass


class ResendEmailAdapter(BaseEmailAdapter):
    """
    Production transactional email adapter using Resend REST API (https://resend.com).
    - Uses Bearer token authentication with RESEND_API_KEY.
    - Sends Idempotency-Key header for duplicate prevention.
    - Implements bounded exponential backoff retries for transient 5xx/network errors.
    - Strictly prevents logging or leaking API secrets.
    """
    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(
        self,
        api_key: str,
        from_email: str = "SpaceLoop <notifications@spaceloop.in>",
        timeout: float = 8.0,
        max_retries: int = 2
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.from_email = from_email or "SpaceLoop <notifications@spaceloop.in>"
        self.timeout = timeout
        self.max_retries = max_retries

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        idempotency_key: str = None
    ) -> tuple[bool, str | None, str | None]:
        if not self.api_key:
            err = "Resend API key is not configured."
            logger.error(f"[RESEND_ADAPTER] {err}")
            return False, None, err

        import requests

        clean_text = text_body or re.sub(r"<[^>]+>", " ", html_body)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SpaceLoop-Mailer/2.5"
        }
        if idempotency_key:
            headers["Idempotency-Key"] = str(idempotency_key)

        payload = {
            "from": self.from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": clean_text
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(
                    self.RESEND_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Check status code
                if resp.status_code in (200, 201):
                    data = resp.json() if resp.text else {}
                    resend_id = data.get("id") or f"resend_{uuid.uuid4().hex[:12]}"
                    logger.info(f"[RESEND_ADAPTER] Successfully dispatched email to {to_email} (id: {resend_id})")
                    return True, resend_id, None

                # Non-transient 4xx errors should not be retried
                error_detail = ""
                try:
                    err_json = resp.json()
                    error_detail = err_json.get("message") or str(err_json)
                except Exception:
                    error_detail = resp.text[:200]

                last_error = f"Resend API HTTP {resp.status_code}: {error_detail}"
                logger.warning(f"[RESEND_ADAPTER] Attempt {attempt + 1} failed for {to_email}: {last_error}")

                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    # Client errors (e.g. invalid email or bad request) - do not retry
                    break

            except requests.exceptions.RequestException as req_err:
                last_error = f"Network error connecting to Resend: {str(req_err)}"
                logger.warning(f"[RESEND_ADAPTER] Attempt {attempt + 1} network error: {last_error}")

            # Exponential backoff before next attempt
            if attempt < self.max_retries:
                time.sleep(0.5 * (2 ** attempt))

        logger.error(f"[RESEND_ADAPTER] All attempts exhausted for {to_email}. Error: {last_error}")
        return False, None, last_error


class DevelopmentEmailAdapter(BaseEmailAdapter):
    """
    Local development and testing adapter.
    Logs email dispatch securely without sending real external network packets.
    Maintains an in-memory queue of sent messages for unit test verification.
    """
    sent_emails: list[dict] = []
    last_sent: dict | None = None

    @classmethod
    def reset(cls):
        cls.sent_emails = []
        cls.last_sent = None

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        idempotency_key: str = None
    ) -> tuple[bool, str | None, str | None]:
        is_prod = os.environ.get("FLASK_ENV") == "production" or bool(os.environ.get("RENDER"))
        mock_id = f"dev_resend_{uuid.uuid4().hex[:12]}"
        plain_body = text_body or re.sub(r"<[^>]+>", " ", html_body).strip()

        record = {
            "to": to_email,
            "subject": subject,
            "html": html_body,
            "text": plain_body,
            "body": plain_body,
            "idempotency_key": idempotency_key,
            "resend_id": mock_id,
            "timestamp": time.time()
        }

        DevelopmentEmailAdapter.sent_emails.append(record)
        DevelopmentEmailAdapter.last_sent = record

        if is_prod:
            logger.info(f"[DEV_EMAIL_ADAPTER] To: {to_email} | Subject: {subject} [body suppressed in prod]")
        else:
            logger.info(f"[DEV_EMAIL_ADAPTER] Dispatched email to {to_email} | Subject: {subject} | Key: {idempotency_key}")

        return True, mock_id, None


class SMTPEmailAdapter(BaseEmailAdapter):
    """
    SMTP fallback adapter using Python standard library smtplib.
    """
    def __init__(self, host: str, port: int, user: str, password: str, from_email: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        idempotency_key: str = None
    ) -> tuple[bool, str | None, str | None]:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            if idempotency_key:
                msg["X-Idempotency-Key"] = idempotency_key

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.user and self.password:
                    server.starttls()
                    server.login(self.user, self.password)
                server.send_message(msg)
            
            smtp_id = f"smtp_{uuid.uuid4().hex[:12]}"
            return True, smtp_id, None
        except Exception as e:
            err = f"Failed to send email to {to_email} via SMTP: {e}"
            logger.error(f"[SMTP_ADAPTER] {err}")
            return False, None, err
