"""
SpaceLoop Transactional Email Templates
Generates high-contrast, responsive HTML and plaintext emails matching the SpaceLoop visual brand.
"""
import html

BRAND_HEADER = """
<div style="background-color: #020617; padding: 24px 32px; border-bottom: 2px solid #0B3D91; text-align: left;">
    <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
        <tr>
            <td>
                <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">
                    Space<span style="color: #3BA7F2;">Loop</span>
                </span>
                <span style="display: block; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 2px;">
                    Zero-Hardware Physical Space Network
                </span>
            </td>
        </tr>
    </table>
</div>
"""

BRAND_FOOTER = """
<div style="background-color: #F8FAFC; border-top: 1px solid #E2E8F0; padding: 24px 32px; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; color: #64748B; line-height: 1.6;">
    <p style="margin: 0 0 8px 0; font-weight: 600; color: #334155;">
        SpaceLoop Technologies Pvt Ltd
    </p>
    <p style="margin: 0 0 12px 0;">
        Secured by Zero-Hardware Telemetry, DigiLocker & UPI Micro-Escrow.
    </p>
    <p style="margin: 0; color: #94A3B8;">
        Need help? Contact our Concierge at <a href="mailto:support@spaceloop.in" style="color: #0B3D91; text-decoration: underline;">support@spaceloop.in</a>
    </p>
</div>
"""


def _wrap_email(title: str, content_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #E8F6FF; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <table cellpadding="0" cellspacing="0" border="0" style="width: 100%; background-color: #E8F6FF; padding: 32px 16px;">
        <tr>
            <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" style="max-width: 580px; width: 100%; background-color: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(11, 61, 145, 0.08); border: 1px solid #D0E6F7;">
                    <tr>
                        <td>
                            {BRAND_HEADER}
                            <div style="padding: 32px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1E293B; line-height: 1.6;">
                                {content_html}
                            </div>
                            {BRAND_FOOTER}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


# ==============================================================================
# 1. Welcome Email
# ==============================================================================
def render_welcome_email(user) -> tuple[str, str, str]:
    name = getattr(user, "name", "SpaceLoop Member") or "SpaceLoop Member"
    subject = "Welcome to SpaceLoop — Your Physical Space Marketplace"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #E0F2FE; color: #0284C7; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Account Activated
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 22px; font-weight: 800; margin: 0 0 16px 0;">
        Welcome to SpaceLoop, {html.escape(name)}!
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        You're officially part of India's zero-hardware peer-to-peer physical space marketplace. Whether you're monetizing idle real estate or reserving flexible space on-demand, SpaceLoop provides verified instant access with automated escrow security.
    </p>
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin-bottom: 24px;">
        <p style="margin: 0 0 10px 0; font-weight: 700; color: #0B3D91; font-size: 14px;">Next steps for a seamless experience:</p>
        <ul style="margin: 0; padding-left: 20px; color: #475569; font-size: 14px; line-height: 1.8;">
            <li>Complete your <strong>DigiLocker / Student KYC</strong> for instant booking approvals.</li>
            <li>Explore verified local listings equipped with smart geofencing access.</li>
            <li>Have unused square footage? List your space and start earning today.</li>
        </ul>
    </div>
    <div style="text-align: center; margin: 28px 0 16px 0;">
        <a href="https://spaceloop.in/explore" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Explore Nearby Spaces →
        </a>
    </div>
    """
    
    text_content = (
        f"Welcome to SpaceLoop, {name}!\n\n"
        f"You are officially part of India's zero-hardware physical space marketplace.\n\n"
        f"Next steps:\n"
        f"- Complete your KYC verification for instant bookings.\n"
        f"- Explore verified local spaces with smart geofence access.\n"
        f"- List your unused space to start earning.\n\n"
        f"Explore now: https://spaceloop.in/explore\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 2. Email Verification
# ==============================================================================
def render_email_verification(to_email: str, verify_url: str) -> tuple[str, str, str]:
    subject = "Verify Your SpaceLoop Email Address"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #EDE9FE; color: #6D28D9; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Action Required
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 22px; font-weight: 800; margin: 0 0 16px 0;">
        Verify your email address
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 20px 0;">
        Please confirm that <strong>{html.escape(to_email)}</strong> belongs to you to activate full account features, instant bookings, and digital door passes.
    </p>
    <div style="text-align: center; margin: 28px 0;">
        <a href="{html.escape(verify_url)}" style="background-color: #0B3D91; color: #FFFFFF; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 15px; display: inline-block;">
            Verify Email Address →
        </a>
    </div>
    <p style="color: #64748B; font-size: 13px; margin: 0 0 8px 0;">
        This verification link will expire in 24 hours. If you did not create a SpaceLoop account, no further action is required.
    </p>
    <p style="color: #94A3B8; font-size: 12px; margin: 16px 0 0 0; word-break: break-all;">
        If button doesn't work, copy this URL:<br>{html.escape(verify_url)}
    </p>
    """
    
    text_content = (
        f"Verify your SpaceLoop email address\n\n"
        f"Please verify your email address by visiting this link:\n"
        f"{verify_url}\n\n"
        f"This link expires in 24 hours. If you did not request this, please disregard.\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 3. Security / Account Alert
# ==============================================================================
def render_security_alert(user, alert_title: str, alert_message: str) -> tuple[str, str, str]:
    name = getattr(user, "name", "SpaceLoop User") or "SpaceLoop User"
    subject = f"SpaceLoop Security Alert: {alert_title}"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #FEF3C7; color: #B45309; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Security Notice
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        {html.escape(alert_title)}
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        Hello {html.escape(name)},
    </p>
    <div style="background-color: #FFFBEB; border-left: 4px solid #F59E0B; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
        <p style="color: #78350F; font-size: 14px; margin: 0; line-height: 1.6;">
            {html.escape(alert_message)}
        </p>
    </div>
    <p style="color: #475569; font-size: 14px; margin: 0 0 16px 0;">
        If you initiated this change, you can safely disregard this message. If you did not authorize this action, please reset your password immediately or contact our Trust & Safety team.
    </p>
    <div style="text-align: center; margin: 24px 0 12px 0;">
        <a href="https://spaceloop.in/dashboard" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Review Security Settings →
        </a>
    </div>
    """
    
    text_content = (
        f"SpaceLoop Security Alert: {alert_title}\n\n"
        f"Hello {name},\n\n"
        f"{alert_message}\n\n"
        f"If you did not authorize this action, please contact support@spaceloop.in immediately.\n\n"
        f"SpaceLoop Trust & Safety: https://spaceloop.in/dashboard"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 4. Booking Request (To Host)
# ==============================================================================
def render_booking_request_to_host(booking) -> tuple[str, str, str]:
    space = booking.space
    renter = booking.renter
    space_title = space.title if space else "Your Space"
    renter_name = renter.name if renter else "A verified seeker"
    start_str = booking.start_time.strftime("%b %d, %Y at %I:%M %p") if booking.start_time else "TBD"
    end_str = booking.end_time.strftime("%I:%M %p") if booking.end_time else "TBD"
    
    subject = f"New Reservation Request: {space_title} (#{booking.id})"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #FEF3C7; color: #B45309; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Pending Host Approval
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        New Booking Request for {html.escape(space_title)}
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 20px 0;">
        <strong>{html.escape(renter_name)}</strong> has requested to book your space. Please review the details below:
    </p>
    <table cellpadding="8" cellspacing="0" border="0" style="width: 100%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 24px; font-size: 14px;">
        <tr>
            <td style="color: #64748B; width: 35%;">Booking ID:</td>
            <td style="color: #0B2545; font-weight: 700;">#{booking.id}</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Date & Time:</td>
            <td style="color: #0B2545; font-weight: 600;">{start_str} – {end_str}</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Duration:</td>
            <td style="color: #0B2545;">{booking.hours_booked:.1f} hours</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Attendees:</td>
            <td style="color: #0B2545;">{booking.attendees_count} people</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Purpose:</td>
            <td style="color: #0B2545;">{html.escape(booking.intended_purpose or 'Creative work')}</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Total Payout:</td>
            <td style="color: #059669; font-weight: 700;">₹{booking.total_price:.2f}</td>
        </tr>
    </table>
    <div style="text-align: center; margin: 24px 0 16px 0;">
        <a href="https://spaceloop.in/dashboard" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Review & Accept Request →
        </a>
    </div>
    """
    
    text_content = (
        f"New Reservation Request: {space_title} (#{booking.id})\n\n"
        f"{renter_name} has requested to book your space.\n"
        f"Time: {start_str} to {end_str} ({booking.hours_booked:.1f} hours)\n"
        f"Attendees: {booking.attendees_count}\n"
        f"Purpose: {booking.intended_purpose}\n"
        f"Payout: ₹{booking.total_price:.2f}\n\n"
        f"Log in to review and accept: https://spaceloop.in/dashboard\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 5. Host Approved (To Customer)
# ==============================================================================
def render_booking_approved_to_customer(booking) -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    start_str = booking.start_time.strftime("%b %d, %Y at %I:%M %p") if booking.start_time else "TBD"
    end_str = booking.end_time.strftime("%I:%M %p") if booking.end_time else "TBD"
    
    subject = f"Booking Approved! Your Pass for {space_title} (#{booking.id})"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #DCFCE7; color: #15803D; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Host Approved & Confirmed
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        Great news! The host accepted your reservation.
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 20px 0;">
        Your booking for <strong>{html.escape(space_title)}</strong> is officially confirmed. Your digital access pass is ready.
    </p>
    <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 20px; margin-bottom: 24px; text-align: center;">
        <span style="font-size: 12px; color: #1E40AF; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Arrival / Caretaker PIN</span>
        <div style="font-size: 32px; font-weight: 800; color: #0B3D91; letter-spacing: 6px; margin: 8px 0;">
            {html.escape(booking.arrival_pin or '4821')}
        </div>
        <p style="margin: 0; color: #3B82F6; font-size: 12px;">Present this PIN or scan the door QR pass upon arrival.</p>
    </div>
    <table cellpadding="8" cellspacing="0" border="0" style="width: 100%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 24px; font-size: 14px;">
        <tr>
            <td style="color: #64748B; width: 35%;">Scheduled Time:</td>
            <td style="color: #0B2545; font-weight: 600;">{start_str} – {end_str}</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Address:</td>
            <td style="color: #0B2545;">{html.escape(space.address if space else 'Premise address available in pass')}</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Security Deposit:</td>
            <td style="color: #059669; font-weight: 600;">₹100 (UPI Micro-Escrow Held)</td>
        </tr>
    </table>
    <div style="text-align: center; margin: 24px 0 16px 0;">
        <a href="https://spaceloop.in/booking/{booking.id}/session" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Open Live Access Pass →
        </a>
    </div>
    """
    
    text_content = (
        f"Booking Approved: {space_title} (#{booking.id})\n\n"
        f"The host has approved your booking!\n"
        f"Time: {start_str} to {end_str}\n"
        f"Arrival PIN: {booking.arrival_pin or '4821'}\n"
        f"Address: {space.address if space else 'Premise verified'}\n\n"
        f"Access Pass: https://spaceloop.in/booking/{booking.id}/session\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 6. Host Rejected (To Customer)
# ==============================================================================
def render_booking_rejected_to_customer(booking) -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    start_str = booking.start_time.strftime("%b %d, %Y at %I:%M %p") if booking.start_time else "TBD"
    
    subject = f"Booking Update: Reservation Declined for {space_title} (#{booking.id})"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #FEE2E2; color: #991B1B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Booking Declined
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        Reservation Request Not Accepted
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        The host was unable to accommodate your reservation request for <strong>{html.escape(space_title)}</strong> scheduled for <strong>{start_str}</strong>.
    </p>
    <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
        <p style="color: #166534; font-size: 14px; margin: 0; font-weight: 600;">
            ✓ Your ₹100 UPI security deposit has been instantly refunded to your original payment method. No cancellation fees apply.
        </p>
    </div>
    <div style="text-align: center; margin: 24px 0 12px 0;">
        <a href="https://spaceloop.in/explore" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Explore Alternative Spaces →
        </a>
    </div>
    """
    
    text_content = (
        f"Booking Update: Reservation Declined for {space_title} (#{booking.id})\n\n"
        f"The host was unable to accommodate your reservation for {start_str}.\n"
        f"Your ₹100 security deposit has been instantly refunded.\n\n"
        f"Explore alternative spaces: https://spaceloop.in/explore\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 7. Booking Confirmed (Instant Booking)
# ==============================================================================
def render_booking_confirmed(booking, is_host: bool = False) -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    start_str = booking.start_time.strftime("%b %d, %Y at %I:%M %p") if booking.start_time else "TBD"
    end_str = booking.end_time.strftime("%I:%M %p") if booking.end_time else "TBD"
    
    if is_host:
        subject = f"Confirmed Booking on Your Space: {space_title} (#{booking.id})"
        html_content = f"""
        <div style="margin-bottom: 20px;">
            <span style="display: inline-block; background-color: #DCFCE7; color: #15803D; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
                New Confirmed Booking
            </span>
        </div>
        <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
            You have a new confirmed reservation!
        </h1>
        <p style="color: #334155; font-size: 15px; margin: 0 0 20px 0;">
            A verified seeker has booked <strong>{html.escape(space_title)}</strong>.
        </p>
        <table cellpadding="8" cellspacing="0" border="0" style="width: 100%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 24px; font-size: 14px;">
            <tr>
                <td style="color: #64748B; width: 35%;">Booking ID:</td>
                <td style="color: #0B2545; font-weight: 700;">#{booking.id}</td>
            </tr>
            <tr>
                <td style="color: #64748B;">Date & Time:</td>
                <td style="color: #0B2545; font-weight: 600;">{start_str} – {end_str}</td>
            </tr>
            <tr>
                <td style="color: #64748B;">Guest:</td>
                <td style="color: #0B2545;">{html.escape(booking.renter.name if booking.renter else 'Verified Guest')}</td>
            </tr>
            <tr>
                <td style="color: #64748B;">Total Payout:</td>
                <td style="color: #059669; font-weight: 700;">₹{booking.total_price:.2f}</td>
            </tr>
        </table>
        <div style="text-align: center; margin: 24px 0 16px 0;">
            <a href="https://spaceloop.in/dashboard" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
                View Host Dashboard →
            </a>
        </div>
        """
        text_content = (
            f"New Confirmed Booking: {space_title} (#{booking.id})\n\n"
            f"Time: {start_str} – {end_str}\n"
            f"Guest: {booking.renter.name if booking.renter else 'Guest'}\n"
            f"Payout: ₹{booking.total_price:.2f}\n\n"
            f"Host Dashboard: https://spaceloop.in/dashboard\n\n"
            f"SpaceLoop Support: support@spaceloop.in"
        )
    else:
        subject = f"Booking Confirmation: {space_title} (#{booking.id})"
        html_content = f"""
        <div style="margin-bottom: 20px;">
            <span style="display: inline-block; background-color: #DCFCE7; color: #15803D; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
                Instant Booking Confirmed
            </span>
        </div>
        <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
            Your SpaceLoop booking is confirmed!
        </h1>
        <p style="color: #334155; font-size: 15px; margin: 0 0 20px 0;">
            You have reserved <strong>{html.escape(space_title)}</strong>. Micro-lease license generated and escrow held.
        </p>
        <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 20px; margin-bottom: 24px; text-align: center;">
            <span style="font-size: 12px; color: #1E40AF; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Arrival PIN</span>
            <div style="font-size: 32px; font-weight: 800; color: #0B3D91; letter-spacing: 6px; margin: 8px 0;">
                {html.escape(booking.arrival_pin or '4821')}
            </div>
            <p style="margin: 0; color: #3B82F6; font-size: 12px;">Present this PIN or scan the door QR pass upon arrival.</p>
        </div>
        <table cellpadding="8" cellspacing="0" border="0" style="width: 100%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 24px; font-size: 14px;">
            <tr>
                <td style="color: #64748B; width: 35%;">Confirmed Time:</td>
                <td style="color: #0B2545; font-weight: 600;">{start_str} – {end_str}</td>
            </tr>
            <tr>
                <td style="color: #64748B;">Address:</td>
                <td style="color: #0B2545;">{html.escape(space.address if space else 'Premise address')}</td>
            </tr>
            <tr>
                <td style="color: #64748B;">Security Deposit:</td>
                <td style="color: #059669; font-weight: 600;">₹100 (UPI Micro-Escrow Held)</td>
            </tr>
        </table>
        <div style="text-align: center; margin: 24px 0 16px 0;">
            <a href="https://spaceloop.in/booking/{booking.id}/session" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
                Access Pass & Directions →
            </a>
        </div>
        """
        text_content = (
            f"Booking Confirmation: {space_title} (#{booking.id})\n\n"
            f"Your booking is confirmed!\n"
            f"Time: {start_str} – {end_str}\n"
            f"Arrival PIN: {booking.arrival_pin or '4821'}\n"
            f"Address: {space.address if space else 'Address in pass'}\n\n"
            f"Live Pass: https://spaceloop.in/booking/{booking.id}/session\n\n"
            f"SpaceLoop Support: support@spaceloop.in"
        )
        
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 8. Upcoming Booking Reminder
# ==============================================================================
def render_upcoming_reminder(booking) -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    start_str = booking.start_time.strftime("%b %d, %Y at %I:%M %p") if booking.start_time else "Soon"
    
    subject = f"Reminder: Your upcoming session at {space_title} starts at {start_str}"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #E0F2FE; color: #0284C7; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Session Reminder
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        Your upcoming space reservation starts soon!
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 20px 0;">
        This is a friendly reminder for your reservation at <strong>{html.escape(space_title)}</strong>.
    </p>
    <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 20px; margin-bottom: 24px; text-align: center;">
        <span style="font-size: 12px; color: #1E40AF; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Arrival PIN</span>
        <div style="font-size: 32px; font-weight: 800; color: #0B3D91; letter-spacing: 6px; margin: 8px 0;">
            {html.escape(booking.arrival_pin or '4821')}
        </div>
        <p style="margin: 0; color: #3B82F6; font-size: 12px;">Check-in opens 15 minutes before your scheduled slot.</p>
    </div>
    <table cellpadding="8" cellspacing="0" border="0" style="width: 100%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 24px; font-size: 14px;">
        <tr>
            <td style="color: #64748B; width: 35%;">Scheduled Time:</td>
            <td style="color: #0B2545; font-weight: 600;">{start_str}</td>
        </tr>
        <tr>
            <td style="color: #64748B;">Address:</td>
            <td style="color: #0B2545;">{html.escape(space.address if space else 'Premise address')}</td>
        </tr>
    </table>
    <div style="text-align: center; margin: 24px 0 16px 0;">
        <a href="https://spaceloop.in/booking/{booking.id}/session" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Open Live Check-In Console →
        </a>
    </div>
    """
    
    text_content = (
        f"Reminder: Upcoming SpaceLoop session at {space_title}\n\n"
        f"Starts at: {start_str}\n"
        f"Arrival PIN: {booking.arrival_pin or '4821'}\n"
        f"Address: {space.address if space else 'Premise'}\n\n"
        f"Live Console: https://spaceloop.in/booking/{booking.id}/session\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 9. Booking Cancelled
# ==============================================================================
def render_booking_cancelled(booking, is_host: bool = False) -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    start_str = booking.start_time.strftime("%b %d, %Y at %I:%M %p") if booking.start_time else "TBD"
    
    subject = f"Booking Cancelled: {space_title} (#{booking.id})"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #FEE2E2; color: #991B1B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Booking Cancelled
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        Reservation Cancelled
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        The booking for <strong>{html.escape(space_title)}</strong> scheduled for <strong>{start_str}</strong> has been cancelled.
    </p>
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
        <p style="color: #475569; font-size: 14px; margin: 0;">
            Any applicable security deposit (₹100) has been released according to SpaceLoop Escrow Refund Policy.
        </p>
    </div>
    <div style="text-align: center; margin: 24px 0 12px 0;">
        <a href="https://spaceloop.in/dashboard" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Go to Dashboard →
        </a>
    </div>
    """
    
    text_content = (
        f"Booking Cancelled: {space_title} (#{booking.id})\n\n"
        f"Scheduled: {start_str}\n"
        f"Status: Cancelled. Security deposit refunded according to policy.\n\n"
        f"Dashboard: https://spaceloop.in/dashboard\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 10. Escrow Deposit Held Confirmation
# ==============================================================================
def render_escrow_deposit_held(booking) -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    amount = getattr(booking, "escrow_deposit_amount", 100.0) or 100.0
    
    subject = f"Escrow Deposit Receipt: ₹{int(amount)} Held Safely (#{booking.id})"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #FEF3C7; color: #B45309; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            UPI Micro-Escrow Held
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        Security Deposit Held in Escrow
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        Your security deposit of <strong>₹{int(amount)}</strong> for <strong>{html.escape(space_title)}</strong> is securely held in SpaceLoop UPI Escrow.
    </p>
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
        <p style="margin: 0 0 8px 0; font-weight: 700; color: #0B3D91; font-size: 14px;">How Escrow Protection Works:</p>
        <ul style="margin: 0; padding-left: 20px; color: #475569; font-size: 14px; line-height: 1.8;">
            <li>Funds are not paid to the host directly; they remain locked in escrow.</li>
            <li>Upon on-time check-out and clean room scan, the deposit is <strong>instantly refunded</strong> via UPI.</li>
            <li>Zero friction, complete transparency.</li>
        </ul>
    </div>
    """
    
    text_content = (
        f"Escrow Deposit Receipt: ₹{int(amount)} Held Safely (#{booking.id})\n\n"
        f"Space: {space_title}\n"
        f"Deposit Amount: ₹{int(amount)}\n"
        f"Status: Safely locked in UPI Micro-Escrow.\n"
        f"Your deposit will be automatically released upon successful check-out.\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 11. Escrow Release / Refund Notification
# ==============================================================================
def render_escrow_refund(booking, reason: str = "Successful Check-Out") -> tuple[str, str, str]:
    space = booking.space
    space_title = space.title if space else "Space"
    amount = getattr(booking, "escrow_deposit_amount", 100.0) or 100.0
    
    subject = f"Refund Complete: ₹{int(amount)} UPI Escrow Released (#{booking.id})"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #DCFCE7; color: #15803D; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Refund Processed
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        ₹{int(amount)} Security Deposit Released!
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        We have processed the full refund of your security deposit for <strong>{html.escape(space_title)}</strong>.
    </p>
    <table cellpadding="8" cellspacing="0" border="0" style="width: 100%; background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; margin-bottom: 24px; font-size: 14px;">
        <tr>
            <td style="color: #166534; width: 35%;">Refund Reason:</td>
            <td style="color: #14532D; font-weight: 600;">{html.escape(reason)}</td>
        </tr>
        <tr>
            <td style="color: #166534;">Refund Amount:</td>
            <td style="color: #15803D; font-weight: 800; font-size: 16px;">₹{amount:.2f}</td>
        </tr>
        <tr>
            <td style="color: #166534;">Destination:</td>
            <td style="color: #14532D;">Original UPI VPA / Account</td>
        </tr>
    </table>
    <p style="color: #475569; font-size: 13px; margin: 0 0 16px 0;">
        Thank you for being a responsible member of the SpaceLoop community. Your Objective Trust Index (OTI) score has been updated.
    </p>
    """
    
    text_content = (
        f"Refund Complete: ₹{int(amount)} UPI Escrow Released (#{booking.id})\n\n"
        f"Space: {space_title}\n"
        f"Reason: {reason}\n"
        f"Amount: ₹{amount:.2f}\n"
        f"Status: Refund sent to original payment method.\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content


# ==============================================================================
# 12. Payment Failure Notification
# ==============================================================================
def render_payment_failed(user, space_title: str, amount: float, reason: str) -> tuple[str, str, str]:
    name = getattr(user, "name", "SpaceLoop User") or "SpaceLoop User"
    subject = f"Action Required: Payment Failed for {space_title}"
    
    html_content = f"""
    <div style="margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #FEE2E2; color: #991B1B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 9999px;">
            Payment Failed
        </span>
    </div>
    <h1 style="color: #0B2545; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
        Payment Could Not Be Processed
    </h1>
    <p style="color: #334155; font-size: 15px; margin: 0 0 16px 0;">
        Hello {html.escape(name)}, we were unable to complete payment of <strong>₹{amount:.2f}</strong> for your reservation at <strong>{html.escape(space_title)}</strong>.
    </p>
    <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
        <p style="color: #991B1B; font-size: 14px; margin: 0;">
            Reason: {html.escape(reason or 'Payment authorization declined by issuing bank/UPI PSP.')}
        </p>
    </div>
    <p style="color: #475569; font-size: 14px; margin: 0 0 20px 0;">
        Your space slot has not been reserved. Please verify your payment details and retry to secure your desired time slot.
    </p>
    <div style="text-align: center; margin: 24px 0 12px 0;">
        <a href="https://spaceloop.in/explore" style="background-color: #0B3D91; color: #FFFFFF; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; display: inline-block;">
            Retry Reservation →
        </a>
    </div>
    """
    
    text_content = (
        f"Action Required: Payment Failed for {space_title}\n\n"
        f"Hello {name},\n"
        f"We were unable to process your payment of ₹{amount:.2f} for {space_title}.\n"
        f"Reason: {reason}\n\n"
        f"Please retry at https://spaceloop.in/explore\n\n"
        f"SpaceLoop Support: support@spaceloop.in"
    )
    
    return subject, _wrap_email(subject, html_content), text_content
