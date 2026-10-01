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
        from_email: str = "SpaceLoop <onboarding@resend.dev>",
        timeout: float = 8.0,
        max_retries: int = 2
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.from_email = from_email or "SpaceLoop <onboarding@resend.dev>"
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

                # Smart fallback: if custom domain is not verified, auto-fallback to onboarding@resend.dev
                if (resp.status_code in (403, 422) and 
                    ("not allowed by policy" in error_detail.lower() or "domain" in error_detail.lower()) and
                    payload.get("from") != "SpaceLoop <onboarding@resend.dev>"):
                    logger.info(f"[RESEND_ADAPTER] Custom domain unverified. Auto-retrying with 'SpaceLoop <onboarding@resend.dev>'")
                    payload["from"] = "SpaceLoop <onboarding@resend.dev>"
                    continue

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
    SMTP email adapter using Python standard library smtplib.
    Supports STARTTLS (port 587) and SSL (port 465).
    Automatically strips whitespace from Google App Passwords.
    """
    def __init__(
        self,
        host: str,
        port: int = 587,
        user: str = "",
        password: str = "",
        from_email: str = "",
        timeout: float = 12.0
    ):
        self.host = (host or "").strip()
        self.port = int(port or 587)
        self.user = (user or "").strip()
        # Google App Passwords are 16 letters with spaces (e.g. "abcd efgh ijkl mnop") - remove all whitespace
        self.password = re.sub(r"\s+", "", password or "")
        self.from_email = (from_email or "").strip() or (f"SpaceLoop <{self.user}>" if self.user else "SpaceLoop <noreply@spaceloop.in>")
        self.timeout = float(timeout or 12.0)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        idempotency_key: str = None
    ) -> tuple[bool, str | None, str | None]:
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not self.host or not self.user or not self.password:
            err = "SMTP configuration incomplete: SMTP_HOST, SMTP_USER, and SMTP_PASSWORD are required."
            logger.error(f"[SMTP_ADAPTER] {err}")
            return False, None, err

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            if idempotency_key:
                msg["X-Idempotency-Key"] = idempotency_key

            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))

            # Smart connection: force IPv4 resolution and auto-fallback between 587 and 465
            server = None
            last_conn_err = None
            ports_to_try = [self.port] if self.port not in (587, 465) else [self.port, 465 if self.port == 587 else 587]

            import socket
            for p in ports_to_try:
                try:
                    # Resolve to IPv4 to prevent [Errno 101] Network is unreachable on IPv6-unroutable cloud containers
                    target_host = self.host
                    try:
                        gai = socket.getaddrinfo(self.host, p, socket.AF_INET, socket.SOCK_STREAM)
                        if gai:
                            target_host = gai[0][4][0]
                    except Exception:
                        target_host = self.host

                    if p == 465:
                        context = ssl.create_default_context()
                        s = smtplib.SMTP_SSL(target_host, p, timeout=self.timeout, context=context)
                    else:
                        s = smtplib.SMTP(target_host, p, timeout=self.timeout)
                        s.ehlo(self.host)
                        context = ssl.create_default_context()
                        s.starttls(context=context)
                        s.ehlo(self.host)

                    s.login(self.user, self.password)
                    server = s
                    break
                except Exception as conn_e:
                    last_conn_err = conn_e
                    logger.warning(f"[SMTP_ADAPTER] Attempt on port {p} ({target_host}) failed: {conn_e}")
                    server = None

            if not server:
                raise last_conn_err or Exception("Failed to establish SMTP connection")

            with server:
                server.send_message(msg)

            smtp_id = f"smtp_{uuid.uuid4().hex[:12]}"
            logger.info(f"[SMTP_ADAPTER] Successfully dispatched email to {to_email} via SMTP (id: {smtp_id})")
            return True, smtp_id, None
        except Exception as e:
            err = f"Failed to send email to {to_email} via SMTP: {e}"
            logger.error(f"[SMTP_ADAPTER] {err}")
            return False, None, err


class BrevoEmailAdapter(BaseEmailAdapter):
    """
    Production transactional email adapter using Brevo (Sendinblue) REST API.
    - Uses HTTPS POST https://api.brevo.com/v3/smtp/email (Port 443, never blocked by cloud firewalls).
    - Sends to any recipient without mandatory domain DNS records.
    - Free tier: 300 emails/day.
    """
    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(
        self,
        api_key: str,
        from_email: str = "SpaceLoop <noreply@spaceloop.in>",
        timeout: float = 10.0,
        max_retries: int = 2
    ):
        self.api_key = (api_key or "").strip()
        self.from_email = (from_email or "").strip()
        self.timeout = timeout
        self.max_retries = max_retries

    def _parse_sender(self) -> dict:
        """Parses 'Name <email@domain.com>' into {'name': 'Name', 'email': 'email@domain.com'}"""
        match = re.match(r"^([^<]+)<([^>]+)>$", self.from_email)
        if match:
            return {"name": match.group(1).strip(), "email": match.group(2).strip()}
        return {"name": "SpaceLoop", "email": self.from_email or "noreply@spaceloop.in"}

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        idempotency_key: str = None
    ) -> tuple[bool, str | None, str | None]:
        import requests

        if not self.api_key:
            err = "Brevo API key is not configured."
            logger.error(f"[BREVO_ADAPTER] {err}")
            return False, None, err

        sender = self._parse_sender()
        payload = {
            "sender": sender,
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body
        }
        if text_body:
            payload["textContent"] = text_body

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(
                    self.BREVO_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                if resp.status_code in (200, 201):
                    data = resp.json() or {}
                    msg_id = data.get("messageId") or f"brevo_{uuid.uuid4().hex[:12]}"
                    logger.info(f"[BREVO_ADAPTER] Successfully dispatched email to {to_email} via Brevo (id: {msg_id})")
                    return True, msg_id, None

                error_detail = resp.text
                last_error = f"Brevo API HTTP {resp.status_code}: {error_detail}"
                logger.warning(f"[BREVO_ADAPTER] Attempt {attempt + 1} failed for {to_email}: {last_error}")

                if resp.status_code < 500:
                    break
            except Exception as req_err:
                last_error = f"Network error connecting to Brevo: {str(req_err)}"
                logger.warning(f"[BREVO_ADAPTER] Attempt {attempt + 1} network error: {last_error}")

            if attempt < self.max_retries:
                time.sleep(1.0 * (2 ** attempt))

        logger.error(f"[BREVO_ADAPTER] All attempts exhausted for {to_email}. Error: {last_error}")
        return False, None, last_error


