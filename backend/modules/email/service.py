"""
SpaceLoop Central Email Service
Provides reliable, idempotent, and fault-tolerant transactional email notifications via Resend.
Strictly decoupled: email sending errors will never crash or roll back core business transactions.
"""
import os
import logging
from datetime import datetime
from models import db, EmailLog
from config import Config
from backend.modules.email.adapter import (
    BaseEmailAdapter,
    ResendEmailAdapter,
    DevelopmentEmailAdapter,
    SMTPEmailAdapter,
    BrevoEmailAdapter,
)
from backend.modules.email.templates import (
    render_welcome_email,
    render_email_verification,
    render_security_alert,
    render_booking_request_to_host,
    render_booking_approved_to_customer,
    render_booking_rejected_to_customer,
    render_booking_confirmed,
    render_upcoming_reminder,
    render_booking_cancelled,
    render_escrow_deposit_held,
    render_escrow_refund,
    render_payment_failed,
)

logger = logging.getLogger("spaceloop.email")


class EmailService:
    _adapter: BaseEmailAdapter = None

    @classmethod
    def get_adapter(cls) -> BaseEmailAdapter:
        provider = (os.environ.get("EMAIL_PROVIDER") or getattr(Config, "EMAIL_PROVIDER", "")).strip().lower()
        brevo_key = (os.environ.get("BREVO_API_KEY") or getattr(Config, "BREVO_API_KEY", "")).strip()
        resend_key = (os.environ.get("RESEND_API_KEY") or getattr(Config, "RESEND_API_KEY", "")).strip()
        smtp_host = (os.environ.get("SMTP_HOST") or getattr(Config, "SMTP_HOST", "")).strip()
        smtp_port = int(os.environ.get("SMTP_PORT") or getattr(Config, "SMTP_PORT", 587))
        smtp_user = (os.environ.get("SMTP_USER") or getattr(Config, "SMTP_USER", "")).strip()
        smtp_password = (os.environ.get("SMTP_PASSWORD") or getattr(Config, "SMTP_PASSWORD", "")).strip()
        from_email = (os.environ.get("EMAIL_FROM") or os.environ.get("RESEND_FROM_EMAIL") or getattr(Config, "EMAIL_FROM", "")).strip()

        # Determine desired adapter type: Brevo takes top priority because it works over HTTPS port 443
        if provider == "brevo" or brevo_key:
            target_class = BrevoEmailAdapter
        elif provider == "resend" or (resend_key and provider != "smtp"):
            target_class = ResendEmailAdapter
        elif provider == "smtp" or (smtp_host and smtp_user):
            target_class = SMTPEmailAdapter
        else:
            target_class = DevelopmentEmailAdapter

        # Reinitialize if not initialized or if adapter type has changed
        if cls._adapter is None or not isinstance(cls._adapter, target_class):
            if target_class is BrevoEmailAdapter:
                effective_from = from_email or "SpaceLoop <notifications@spaceloop.in>"
                logger.info("[EMAIL_SERVICE] Initializing BrevoEmailAdapter with configured API key")
                cls._adapter = BrevoEmailAdapter(api_key=brevo_key, from_email=effective_from)
            elif target_class is SMTPEmailAdapter:
                effective_from = from_email or (f"SpaceLoop <{smtp_user}>" if smtp_user else "SpaceLoop <noreply@spaceloop.in>")
                logger.info(f"[EMAIL_SERVICE] Initializing SMTPEmailAdapter (host: {smtp_host}:{smtp_port}, user: {smtp_user})")
                cls._adapter = SMTPEmailAdapter(
                    host=smtp_host,
                    port=smtp_port,
                    user=smtp_user,
                    password=smtp_password,
                    from_email=effective_from,
                )
            elif target_class is ResendEmailAdapter:
                effective_from = from_email or "SpaceLoop <onboarding@resend.dev>"
                logger.info("[EMAIL_SERVICE] Initializing ResendEmailAdapter with configured API key")
                cls._adapter = ResendEmailAdapter(api_key=resend_key, from_email=effective_from)
            else:
                logger.info("[EMAIL_SERVICE] Initializing DevelopmentEmailAdapter (in-memory mode)")
                cls._adapter = DevelopmentEmailAdapter()

        return cls._adapter

    @classmethod
    def set_adapter(cls, adapter: BaseEmailAdapter):
        """Allows test suites to inject mock adapters."""
        cls._adapter = adapter

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        event_type: str = "general",
        user_id: int = None,
        booking_id: int = None,
        idempotency_key: str = None
    ) -> bool:
        """
        Dispatches transactional email with deduplication, logging, and fault isolation.
        Guarantees that errors never bubble up to corrupt caller database operations.
        """
        if not to_email or "@" not in to_email:
            logger.warning(f"[EMAIL_SERVICE] Invalid recipient email '{to_email}' - skipping send.")
            return False

        # 1. Idempotency Check: Prevent duplicate sends
        if idempotency_key:
            try:
                existing_sent = EmailLog.query.filter_by(
                    idempotency_key=idempotency_key,
                    status="sent"
                ).first()
                if existing_sent:
                    logger.info(f"[EMAIL_SERVICE] Idempotent duplicate intercepted: '{idempotency_key}' already sent. Skipping.")
                    return True
            except Exception as db_err:
                logger.warning(f"[EMAIL_SERVICE] Idempotency query error: {db_err}")

        # 2. Dispatch via active adapter
        adapter = cls.get_adapter()
        success = False
        provider_id = None
        error_msg = None

        try:
            success, provider_id, error_msg = adapter.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                idempotency_key=idempotency_key
            )
        except Exception as send_exc:
            success = False
            error_msg = f"Unexpected adapter exception: {str(send_exc)}"
            logger.error(f"[EMAIL_SERVICE] Unhandled send exception for {to_email}: {error_msg}")

        # 3. Observability Logging (non-sensitive)
        try:
            status_val = "sent" if success else "failed"
            safe_key = idempotency_key or f"evt_{int(datetime.utcnow().timestamp())}_{to_email}"
            
            # Avoid crashing if the same idempotency key exists as failed
            existing_record = EmailLog.query.filter_by(idempotency_key=safe_key).first()
            if existing_record:
                existing_record.status = status_val
                existing_record.resend_id = provider_id
                existing_record.error_message = error_msg
            else:
                log_entry = EmailLog(
                    idempotency_key=safe_key,
                    event_type=event_type,
                    recipient_email=to_email,
                    user_id=user_id,
                    booking_id=booking_id,
                    subject=subject[:255],
                    status=status_val,
                    resend_id=provider_id,
                    error_message=error_msg[:1000] if error_msg else None
                )
                db.session.add(log_entry)
            db.session.commit()
        except Exception as log_exc:
            db.session.rollback()
            logger.warning(f"[EMAIL_SERVICE] Failed to record EmailLog in DB: {log_exc}")

        return success

    # ==========================================================================
    # High-Level Event Notification Dispatchers
    # ==========================================================================

    @classmethod
    def notify_welcome(cls, user) -> bool:
        if not user or not getattr(user, "email", None):
            return False
        subject, html_body, text_body = render_welcome_email(user)
        key = f"welcome-user-{user.id}"
        return cls.send_email(
            to_email=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            event_type="user_welcome",
            user_id=user.id,
            idempotency_key=key
        )

    @classmethod
    def notify_email_verification(cls, to_email: str, raw_token: str, verify_url: str = None, user_id: int = None) -> bool:
        if not verify_url:
            base_url = (os.environ.get("APP_URL") or os.environ.get("BASE_URL") or os.environ.get("FRONTEND_URL") or "").rstrip("/")
            if not base_url:
                try:
                    from flask import request, has_request_context
                    if has_request_context():
                        base_url = request.host_url.rstrip("/")
                except Exception:
                    pass
            if not base_url:
                base_url = "https://spaceloop.vercel.app" if (os.environ.get("RENDER") or os.environ.get("VERCEL")) else "http://localhost:5000"
            if ("onrender.com" in base_url or os.environ.get("RENDER")) and base_url.startswith("http://"):
                base_url = "https://" + base_url[len("http://"):]
            verify_url = f"{base_url}/auth/verify-email/{raw_token}"
        link = verify_url
        subject, html_body, text_body = render_email_verification(to_email, link)
        key = f"email-verify-{to_email}-{raw_token[:12]}"
        return cls.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            event_type="email_verification",
            user_id=user_id,
            idempotency_key=key
        )

    # Backward compatibility alias
    send_email_verification = notify_email_verification
    send_verification_email = notify_email_verification

    @classmethod
    def notify_password_reset(cls, to_email: str, raw_token: str, reset_url: str = None, user_id: int = None) -> bool:
        if not reset_url:
            base_url = (os.environ.get("APP_URL") or os.environ.get("BASE_URL") or os.environ.get("FRONTEND_URL") or "").rstrip("/")
            if not base_url:
                base_url = "https://spaceloop.vercel.app" if os.environ.get("RENDER") else "http://localhost:5000"
            reset_url = f"{base_url}/auth/reset-password/{raw_token}"
        link = reset_url
        subject = "SpaceLoop — Password Reset Request"
        html_body = f"""
        <h1 style="color: #0B2545; font-size: 20px;">Password Reset Request</h1>
        <p>A password reset was requested for your SpaceLoop account.</p>
        <p><a href="{link}" style="display: inline-block; background-color: #0B3D91; color: #FFF; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Reset Password →</a></p>
        <p style="color: #64748B; font-size: 13px;">This link expires in 1 hour. If you did not request this, ignore this email.</p>
        """
        text_body = f"SpaceLoop Password Reset:\n\nVisit: {link}\n\nExpires in 1 hour."
        key = f"pwd-reset-{to_email}-{raw_token[:12]}"
        return cls.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            event_type="password_reset",
            user_id=user_id,
            idempotency_key=key
        )

    send_password_reset = notify_password_reset

    @classmethod
    def notify_security_event(cls, user, alert_title: str, alert_message: str) -> bool:
        if not user or not getattr(user, "email", None):
            return False
        subject, html_body, text_body = render_security_alert(user, alert_title, alert_message)
        key = f"sec-alert-{user.id}-{alert_title.lower().replace(' ', '-')[:20]}-{int(datetime.utcnow().timestamp()) // 60}"
        return cls.send_email(
            to_email=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            event_type="security_alert",
            user_id=user.id,
            idempotency_key=key
        )

    @classmethod
    def notify_booking_created(cls, booking) -> bool:
        """
        Dispatches initial reservation notifications:
        - To Host: Pending request or new confirmed booking
        - To Customer: Confirmation or request receipt
        """
        if not booking:
            return False

        host = booking.space.owner if booking.space else None
        renter = booking.renter
        is_pending = booking.status == "pending"

        # 1. Notify Host
        if host and host.email:
            if is_pending:
                subject, html_b, text_b = render_booking_request_to_host(booking)
                evt = "booking_request_host"
            else:
                subject, html_b, text_b = render_booking_confirmed(booking, is_host=True)
                evt = "booking_confirmed_host"

            cls.send_email(
                to_email=host.email,
                subject=subject,
                html_body=html_b,
                text_body=text_b,
                event_type=evt,
                user_id=host.id,
                booking_id=booking.id,
                idempotency_key=f"{evt}-{booking.id}-{host.id}"
            )

        # 2. Notify Customer (renter)
        if renter and renter.email:
            if not is_pending:
                subject, html_b, text_b = render_booking_confirmed(booking, is_host=False)
                evt = "booking_confirmed_seeker"
                cls.send_email(
                    to_email=renter.email,
                    subject=subject,
                    html_body=html_b,
                    text_body=text_b,
                    event_type=evt,
                    user_id=renter.id,
                    booking_id=booking.id,
                    idempotency_key=f"{evt}-{booking.id}-{renter.id}"
                )

        return True

    @classmethod
    def notify_host_approved(cls, booking) -> bool:
        """Dispatches notification to seeker that host approved their reservation."""
        if not booking or not booking.renter or not booking.renter.email:
            return False
        renter = booking.renter
        subject, html_b, text_b = render_booking_approved_to_customer(booking)
        key = f"booking-approved-{booking.id}-{renter.id}"
        return cls.send_email(
            to_email=renter.email,
            subject=subject,
            html_body=html_b,
            text_body=text_b,
            event_type="booking_approved",
            user_id=renter.id,
            booking_id=booking.id,
            idempotency_key=key
        )

    @classmethod
    def notify_host_rejected(cls, booking) -> bool:
        """Dispatches notification to seeker that host declined their reservation."""
        if not booking or not booking.renter or not booking.renter.email:
            return False
        renter = booking.renter
        subject, html_b, text_b = render_booking_rejected_to_customer(booking)
        key = f"booking-rejected-{booking.id}-{renter.id}"
        return cls.send_email(
            to_email=renter.email,
            subject=subject,
            html_body=html_b,
            text_body=text_b,
            event_type="booking_rejected",
            user_id=renter.id,
            booking_id=booking.id,
            idempotency_key=key
        )

    @classmethod
    def notify_booking_cancelled(cls, booking, cancelled_by_user=None) -> bool:
        """Dispatches cancellation notice to both host and seeker."""
        if not booking:
            return False

        host = booking.space.owner if booking.space else None
        renter = booking.renter

        if renter and renter.email:
            subject, html_b, text_b = render_booking_cancelled(booking, is_host=False)
            cls.send_email(
                to_email=renter.email,
                subject=subject,
                html_body=html_b,
                text_body=text_b,
                event_type="booking_cancelled_seeker",
                user_id=renter.id,
                booking_id=booking.id,
                idempotency_key=f"booking-cancelled-seeker-{booking.id}-{renter.id}"
            )

        if host and host.email:
            subject, html_b, text_b = render_booking_cancelled(booking, is_host=True)
            cls.send_email(
                to_email=host.email,
                subject=subject,
                html_body=html_b,
                text_body=text_b,
                event_type="booking_cancelled_host",
                user_id=host.id,
                booking_id=booking.id,
                idempotency_key=f"booking-cancelled-host-{booking.id}-{host.id}"
            )

        return True

    @classmethod
    def notify_upcoming_reminder(cls, booking) -> bool:
        """Dispatches upcoming booking reminder to seeker."""
        if not booking or not booking.renter or not booking.renter.email:
            return False
        renter = booking.renter
        subject, html_b, text_b = render_upcoming_reminder(booking)
        key = f"booking-reminder-{booking.id}-{renter.id}"
        return cls.send_email(
            to_email=renter.email,
            subject=subject,
            html_body=html_b,
            text_body=text_b,
            event_type="booking_reminder",
            user_id=renter.id,
            booking_id=booking.id,
            idempotency_key=key
        )

    @classmethod
    def notify_escrow_held(cls, booking) -> bool:
        """Dispatches receipt when security deposit is held in escrow."""
        if not booking or not booking.renter or not booking.renter.email:
            return False
        renter = booking.renter
        subject, html_b, text_b = render_escrow_deposit_held(booking)
        key = f"escrow-held-{booking.id}-{renter.id}"
        return cls.send_email(
            to_email=renter.email,
            subject=subject,
            html_body=html_b,
            text_body=text_b,
            event_type="escrow_held",
            user_id=renter.id,
            booking_id=booking.id,
            idempotency_key=key
        )

    @classmethod
    def notify_escrow_refunded(cls, booking, reason: str = "Successful Check-Out") -> bool:
        """Dispatches notification when security deposit is released/refunded."""
        if not booking or not booking.renter or not booking.renter.email:
            return False
        renter = booking.renter
        subject, html_b, text_b = render_escrow_refund(booking, reason=reason)
        key = f"escrow-refund-{booking.id}-{renter.id}"
        return cls.send_email(
            to_email=renter.email,
            subject=subject,
            html_body=html_b,
            text_body=text_b,
            event_type="escrow_refund",
            user_id=renter.id,
            booking_id=booking.id,
            idempotency_key=key
        )

    @classmethod
    def notify_payment_failed(cls, user, space_title: str, amount: float, reason: str) -> bool:
        """Dispatches notification when a payment attempt fails."""
        if not user or not getattr(user, "email", None):
            return False
        subject, html_b, text_b = render_payment_failed(user, space_title, amount, reason)
        safe_reason = reason[:20].lower().replace(" ", "-") if reason else "failed"
        key = f"payment-failed-{user.id}-{int(datetime.utcnow().timestamp()) // 300}-{safe_reason}"
        return cls.send_email(
            to_email=user.email,
            subject=subject,
            html_body=html_b,
            text_body=text_b,
            event_type="payment_failed",
            user_id=user.id,
            idempotency_key=key
        )
