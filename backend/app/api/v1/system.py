"""
SpaceLoop System, AI Concierge, KYC & Analytics REST Blueprint
Handles platform telemetry, health checks, dashboard metrics, LoopBot chat,
India Stack KYC verification, and dynamic yield estimation.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from models import db, Booking, Space, SpaceInquiry, User, AuditLog, Notification, AccessLog, EscrowTransaction

logger = logging.getLogger(__name__)
from backend.modules.auth import set_active_context
from space_ai import (
    concierge_chat,
    calculate_earnings_estimate,
    verify_aadhaar_otp,
    verify_academic_credentials,
    verify_host_electricity_bill,
    verify_upi_penny_drop,
    compute_objective_trust_index,
    get_system_connectivity_status,
    set_simulate_ai_failure
)
from security import rate_limit_ai, sanitize_string, validate_numeric

api_v1_system = Blueprint("api_v1_system", __name__)


@api_v1_system.route("/api/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    active_user_id = current_user.id

    seeker_bookings = Booking.query.options(
        db.joinedload(Booking.space),
        db.joinedload(Booking.renter)
    ).filter_by(renter_id=active_user_id).order_by(Booking.created_at.desc()).all()

    host_spaces = Space.query.options(
        db.joinedload(Space.owner),
        db.selectinload(Space.reviews)
    ).filter_by(owner_id=active_user_id).order_by(Space.created_at.desc()).all()

    host_bookings = Booking.query.options(
        db.joinedload(Booking.space),
        db.joinedload(Booking.renter)
    ).join(Space).filter(Space.owner_id == active_user_id).order_by(Booking.created_at.desc()).all()

    gross_revenue = sum(b.total_price for b in host_bookings if b.status in ['confirmed', 'completed'])
    platform_fee = round(gross_revenue * 0.05)
    net_earnings = gross_revenue - platform_fee
    total_hours_hosted = sum(b.hours_booked for b in host_bookings if b.status in ['confirmed', 'completed'])
    active_spaces_count = len([s for s in host_spaces if s.is_active])
    upcoming_host_bookings = [b for b in host_bookings if b.status == 'confirmed']
    completed_host_bookings = [b for b in host_bookings if b.status == 'completed']

    host_metrics = {
        "gross_revenue": int(round(gross_revenue)),
        "platform_fee": int(round(platform_fee)),
        "net_earnings": int(round(net_earnings)),
        "total_hours": round(total_hours_hosted, 1),
        "total_bookings": len(host_bookings),
        "active_spaces_count": active_spaces_count,
        "total_spaces_count": len(host_spaces),
        "upcoming_count": len(upcoming_host_bookings),
        "completed_count": len(completed_host_bookings),
        "payout_vpa": current_user.upi_vpa_masked if current_user.upi_vpa_masked else "upi***@okbank"
    }

    return jsonify({
        "success": True,
        "bookings": [b.to_dict() for b in seeker_bookings],
        "host_bookings": [b.to_dict() for b in host_bookings],
        "host_spaces": [s.to_dict() for s in host_spaces],
        "host_metrics": host_metrics,
        "user": current_user.to_dict()
    }), 200


@api_v1_system.route("/api/host/activity", methods=["GET"])
@login_required
def get_host_activity():
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    host_spaces = Space.query.filter_by(owner_id=current_user.id).all()
    space_ids = [s.id for s in host_spaces]

    host_bookings = Booking.query.options(
        db.joinedload(Booking.space),
        db.joinedload(Booking.renter)
    ).join(Space).filter(Space.owner_id == current_user.id).order_by(Booking.created_at.desc()).limit(35).all()

    events = []
    for b in host_bookings:
        events.append({
            "id": f"b-create-{b.id}",
            "type": "booking",
            "category": "booking",
            "title": f"New Reservation #{b.id}",
            "description": f"Seeker {b.renter.name if b.renter else 'Guest'} booked {b.space.title if b.space else 'Space'} for {b.hours_booked}h",
            "timestamp": b.created_at.isoformat() if b.created_at else None,
            "resource_type": "booking",
            "resource_id": b.id,
            "space_id": b.space_id,
            "status": b.status,
            "icon": "fa-calendar-check",
            "color": "emerald" if b.status == "confirmed" else "amber"
        })
        if b.arrival_time:
            events.append({
                "id": f"b-checkin-{b.id}",
                "type": "access",
                "category": "access",
                "title": f"Check-In Verified #{b.id}",
                "description": f"Physical handshake completed at {b.space.title if b.space else 'Premise'}. PIN / QR validated.",
                "timestamp": b.arrival_time.isoformat(),
                "resource_type": "booking",
                "resource_id": b.id,
                "space_id": b.space_id,
                "status": "checked_in",
                "icon": "fa-door-open",
                "color": "sky"
            })
        if b.departure_time:
            events.append({
                "id": f"b-checkout-{b.id}",
                "type": "settlement",
                "category": "settlement",
                "title": f"Check-Out & CV Inspection #{b.id}",
                "description": f"Exit scan analyzed. Condition score: {round(b.condition_match_score, 1)}%. Escrow: {b.escrow_status}.",
                "timestamp": b.departure_time.isoformat(),
                "resource_type": "booking",
                "resource_id": b.id,
                "space_id": b.space_id,
                "status": "checked_out",
                "icon": "fa-shield-halved",
                "color": "emerald" if b.escrow_status == "released" else "amber"
            })

    for s in host_spaces:
        events.append({
            "id": f"s-create-{s.id}",
            "type": "space",
            "category": "space",
            "title": f"Listing: {s.title}",
            "description": f"Space listed in {s.category} category. Status: {'Published' if s.is_active else 'Paused'}.",
            "timestamp": s.created_at.isoformat() if s.created_at else None,
            "resource_type": "space",
            "resource_id": s.id,
            "space_id": s.id,
            "status": "active" if s.is_active else "inactive",
            "icon": "fa-building",
            "color": "amber"
        })

    events.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

    category_filter = request.args.get("category")
    if category_filter and category_filter != "all":
        events = [e for e in events if e.get("category") == category_filter]

    return jsonify({
        "success": True,
        "events": events[:40]
    }), 200


@api_v1_system.route("/api/host/notifications", methods=["GET"])
@login_required
def get_host_notifications():
    if not current_user.is_host:
        return jsonify({"success": False, "notifications": [], "unread_count": 0}), 200

    now = datetime.utcnow()
    notifications = []

    # 1. Fetch persisted DB notifications
    db_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(60).all()
    for dn in db_notifs:
        color = "amber"
        icon = "fa-bell"
        if dn.type in ("new_booking", "booking"):
            color = "emerald"
            icon = "fa-calendar-check"
        elif dn.type in ("checkin", "check_in"):
            color = "sky"
            icon = "fa-door-open"
        elif dn.type in ("checkout", "active_session"):
            color = "purple"
            icon = "fa-arrow-right-from-bracket"
        elif dn.type in ("dispute", "inspection_alert"):
            color = "rose"
            icon = "fa-triangle-exclamation"
        elif dn.type == "verification":
            color = "amber"
            icon = "fa-shield-halved"
        elif dn.type in ("inquiry", "new_inquiry"):
            color = "indigo"
            icon = "fa-comments"

        notifications.append({
            "id": dn.id,
            "db_id": dn.id,
            "type": dn.type,
            "title": dn.title,
            "message": dn.message,
            "timestamp": dn.created_at.isoformat() if dn.created_at else now.isoformat(),
            "unread": dn.unread,
            "priority": dn.priority or "medium",
            "action_url": dn.action_url or "/host/overview",
            "icon": icon,
            "color": color
        })

    # 2. Add dynamic operational alerts if no recent matching notification exists
    pending_bookings = Booking.query.join(Space).filter(
        Space.owner_id == current_user.id,
        Booking.status == "pending"
    ).all()
    for pb in pending_bookings:
        # Check if already present
        if not any(n.get("action_url") == f"/host/bookings/{pb.id}" and n.get("type") == "new_booking" for n in notifications):
            notifications.insert(0, {
                "id": f"dyn-pending-{pb.id}",
                "db_id": None,
                "type": "new_booking",
                "title": "Pending Booking Request",
                "message": f"{pb.renter.name if pb.renter else 'A guest'} requested to book {pb.space.title if pb.space else 'your space'} for {pb.hours_booked}h.",
                "timestamp": pb.created_at.isoformat() if pb.created_at else now.isoformat(),
                "unread": True,
                "action_url": f"/host/bookings/{pb.id}",
                "priority": "high",
                "icon": "fa-calendar-plus",
                "color": "amber"
            })

    # Add dynamic alert for recent inquiries if no notification exists
    recent_inquiries = SpaceInquiry.query.join(Space).filter(
        Space.owner_id == current_user.id
    ).order_by(SpaceInquiry.created_at.desc()).limit(10).all()
    for inq in recent_inquiries:
        notif_msg_snip = inq.question[:40] if inq.question else ""
        if not any(notif_msg_snip and notif_msg_snip in (n.get("message") or "") for n in notifications):
            seeker_name = inq.user.name if (inq.user and inq.user.name) else "A seeker"
            notifications.insert(0, {
                "id": f"dyn-inq-{inq.id}",
                "db_id": None,
                "type": "inquiry",
                "title": f"New Inquiry: {inq.space.title if inq.space else 'Your Space'}",
                "message": f"{seeker_name} asked: \"{inq.question[:120]}{'...' if len(inq.question) > 120 else ''}\"",
                "timestamp": inq.created_at.isoformat() if inq.created_at else now.isoformat(),
                "unread": True,
                "action_url": "/host/overview",
                "priority": "medium",
                "icon": "fa-comments",
                "color": "indigo"
            })

    if not current_user.is_host_verified and not any(n.get("type") == "verification" for n in notifications):
        notifications.append({
            "id": "dyn-kyc-pending",
            "db_id": None,
            "type": "verification",
            "title": "Complete Discom Verification",
            "message": "Link your State Electricity Board consumer account (CA#) and UPI account to activate instant daily payouts.",
            "timestamp": now.isoformat(),
            "unread": True,
            "action_url": "/host/verification",
            "priority": "medium",
            "icon": "fa-shield-halved",
            "color": "amber"
        })

    unread_count = len([n for n in notifications if n.get("unread")])

    return jsonify({
        "success": True,
        "notifications": notifications,
        "unread_count": unread_count
    }), 200


@api_v1_system.route("/api/host/notifications/<notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    try:
        n_id = int(notification_id)
        notif = Notification.query.get(n_id)
        if notif and (notif.user_id == current_user.id or current_user.is_admin):
            notif.unread = False
            db.session.commit()
    except (ValueError, TypeError):
        pass
    return jsonify({"success": True, "message": "Notification marked as read."}), 200


@api_v1_system.route("/api/host/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, unread=True).update({"unread": False})
    db.session.commit()
    return jsonify({"success": True, "message": "All notifications marked as read."}), 200


@api_v1_system.route("/api/host/notifications/<notification_id>", methods=["DELETE"])
@login_required
def delete_notification(notification_id):
    try:
        n_id = int(notification_id)
        notif = Notification.query.get(n_id)
        if notif and (notif.user_id == current_user.id or current_user.is_admin):
            db.session.delete(notif)
            db.session.commit()
    except (ValueError, TypeError):
        pass
    return jsonify({"success": True, "message": "Notification dismissed."}), 200


@api_v1_system.route("/api/host/escrow/ledger", methods=["GET"])
@login_required
def get_host_escrow_ledger():
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    # Query transactions associated with bookings on spaces owned by current_user or where user_id is host
    host_spaces = Space.query.filter_by(owner_id=current_user.id).all()
    space_ids = [s.id for s in host_spaces]

    transactions = EscrowTransaction.query.join(Booking).filter(
        db.or_(
            Booking.space_id.in_(space_ids),
            EscrowTransaction.user_id == current_user.id
        )
    ).order_by(EscrowTransaction.created_at.desc()).limit(100).all()

    total_held = sum(t.amount for t in transactions if t.transaction_type in ("hold", "dispute_hold", "escrow_held") and t.status in ("completed", "held", "pending_resolution"))
    total_released = sum(t.amount for t in transactions if t.transaction_type in ("release_to_renter", "dispute_resolved_release") and t.status == "completed")
    settled_payouts = sum(t.amount for t in transactions if t.transaction_type == "payout_to_host" and t.status == "completed")

    return jsonify({
        "success": True,
        "transactions": [t.to_dict() for t in transactions],
        "metrics": {
            "total_held": round(total_held, 2),
            "total_released": round(total_released, 2),
            "settled_payouts": round(settled_payouts, 2),
            "escrow_unit_inr": 100.0,
            "dispute_count": len([t for t in transactions if "dispute" in t.transaction_type])
        }
    }), 200


@api_v1_system.route("/api/host/access-logs", methods=["GET"])
@login_required
def get_all_host_access_logs():
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    host_spaces = Space.query.filter_by(owner_id=current_user.id).all()
    space_ids = [s.id for s in host_spaces]

    logs = AccessLog.query.filter(AccessLog.space_id.in_(space_ids)).order_by(AccessLog.created_at.desc()).limit(100).all()
    return jsonify({
        "success": True,
        "access_logs": [log.to_dict() for log in logs],
        "count": len(logs)
    }), 200


@api_v1_system.route("/api/host/settings", methods=["GET"])
@login_required
def get_host_settings():
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    return jsonify({
        "success": True,
        "settings": {
            "profile": {
                "name": current_user.name or "",
                "first_name": current_user.first_name or "",
                "last_name": current_user.last_name or "",
                "email": current_user.email or "",
                "phone": current_user.phone or "",
                "bio": current_user.bio or "",
                "avatar_url": current_user.avatar_url or "",
            },
            "security": {
                "mfa_enabled": bool(getattr(current_user, "mfa_enabled", False)),
                "is_active": current_user.is_active,
                "last_login_at": current_user.last_login_at.isoformat() if getattr(current_user, "last_login_at", None) else None,
            },
            "identity": {
                "is_host_verified": current_user.is_host_verified,
                "is_aadhaar_verified": current_user.is_aadhaar_verified,
                "aadhaar_masked": current_user.aadhaar_masked or "",
                "discom_provider": current_user.discom_provider or "",
                "discom_ca_masked": current_user.discom_ca_masked or "",
            },
            "payout": {
                "upi_verified": current_user.upi_verified,
                "upi_vpa_masked": current_user.upi_vpa_masked or "",
                "bank_beneficiary_name": current_user.bank_beneficiary_name or "",
                "payout_schedule": "instant_post_checkout",
                "commission_rate_percent": 5.0,
                "net_host_share_percent": 95.0,
            },
            "defaults": {
                "default_buffer_minutes": 15,
                "instant_booking_enabled": True,
                "geofence_radius_meters": 30,
                "cancellation_policy": "flexible_24h",
            },
            "notifications": {
                "sms_alerts": True,
                "email_alerts": True,
                "push_alerts": True,
                "arrival_chime": True,
            }
        },
        "user": current_user.to_dict()
    }), 200


@api_v1_system.route("/api/host/settings", methods=["POST"])
@login_required
def update_host_settings():
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    data = request.get_json(silent=True) or {}
    if data.get("name"):
        current_user.name = sanitize_string(data.get("name"), max_length=120)
    if data.get("first_name"):
        current_user.first_name = sanitize_string(data.get("first_name"), max_length=60)
    if data.get("last_name"):
        current_user.last_name = sanitize_string(data.get("last_name"), max_length=60)
    if data.get("phone"):
        current_user.phone = sanitize_string(data.get("phone"), max_length=40)
    if data.get("bio"):
        current_user.bio = sanitize_string(data.get("bio"), max_length=1000)
    if data.get("upi_vpa"):
        current_user.upi_vpa_masked = sanitize_string(data.get("upi_vpa"), max_length=80)
        current_user.upi_verified = True
    if data.get("bank_beneficiary_name"):
        current_user.bank_beneficiary_name = sanitize_string(data.get("bank_beneficiary_name"), max_length=120)

    db.session.commit()
    try:
        from backend.modules.auth.audit import record_audit
        record_audit("host_settings_updated", user_id=current_user.id, details={"updated": list(data.keys())})
    except Exception:
        pass

    return jsonify({
        "success": True,
        "message": "Host settings saved successfully.",
        "user": current_user.to_dict()
    }), 200


@api_v1_system.route("/api/host/seed-sample-space", methods=["POST"])
@login_required
def seed_sample_host_space():
    """Instantly provisions a high-quality sample listing for the authenticated host."""
    if not current_user.is_host:
        current_user.role = "host"
        current_user.is_host_verified = True
        db.session.commit()
        set_active_context(current_user, "host")

    sample_space = Space(
        owner_id=current_user.id,
        title=f"{current_user.first_name or current_user.name}'s Premium Acoustic Study Pod",
        category="Studio",
        description="Silent, sunlit reading and work sanctuary with 300 Mbps Wi-Fi, ergonomic desk lamp, whiteboards, and power backup. Ideal for deep work sprints.",
        address="Near JSPM Imperial College, Wagholi, Pune",
        neighborhood="Wagholi",
        city="Pune",
        state="MH",
        zip_code="412207",
        sqft=220,
        max_capacity=4,
        price_hourly=60.0,
        price_daily=300.0,
        minimum_hours=1,
        latitude=18.5793,
        longitude=73.9825,
        photos=[
            "https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80"
        ],
        amenities=["Fiber 300 Mbps", "DigiLocker Verified", "Whiteboard", "Power Backup", "AC"],
        rules=["No smoking", "Clean desk after session", "Keep volume reasonable"],
        ai_dimensions_summary="15ft x 14.5ft acoustic soundproofed workstation",
        ai_lighting="Warm Natural Sunlit + 4000K Ergonomic Work Lamp",
        ai_noise_level="Ultra Quiet (<32 dB)",
        ai_power_access="4x Surge Protected Outlets with 6-hour UPS Backup",
        ai_safety_notes="Clear stairwell exit path, fire extinguisher in corridor.",
        ai_recommended_uses="Exam preparation, code sprints, technical interviews, video podcasts",
        ai_suitability_score=98,
        is_active=True
    )

    db.session.add(sample_space)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Turnkey pod provisioned and discoverable!",
        "space": sample_space.to_dict()
    }), 201


@api_v1_system.route("/api/calculator/estimate", methods=["POST"])
def api_estimate():
    data = request.get_json(silent=True) or {}
    category = sanitize_string(data.get("category") or data.get("space_type", "Studio"), max_length=50)
    sqft = validate_numeric(data.get("sqft") or data.get("square_feet"), min_val=20, max_val=50000, default=250)
    days = validate_numeric(data.get("days_per_month"), min_val=1, max_val=31, default=12)
    rate = validate_numeric(data.get("hourly_rate"), min_val=5, max_val=5000, default=None)
    hours = validate_numeric(data.get("hours_per_day"), min_val=1, max_val=24, default=4)
    fee = validate_numeric(data.get("platform_fee_percent"), min_val=0, max_val=50, default=15)

    estimate = calculate_earnings_estimate(
        category=category,
        sqft=sqft,
        days_per_month=days,
        hourly_rate=rate,
        hours_per_day=hours,
        platform_fee_percent=fee
    )

    # Normalize fields for cross-compatibility with frontend types
    estimate["space_type"] = category
    estimate["square_feet"] = sqft
    estimate["estimated_monthly_inr"] = estimate.get("estimated_monthly", 3500)
    estimate["estimated_hourly_inr"] = estimate.get("suggested_hourly", 45)
    estimate["occupancy_rate_pct"] = round(min(90, max(45, (days / 30.0) * 100)), 0)
    estimate["peer_comparison"] = f"Top 15% estimated yield for {category} spaces"

    return jsonify(estimate)


@api_v1_system.route("/api/assistant", methods=["POST"])
@api_v1_system.route("/api/ai/chat", methods=["POST"])
@api_v1_system.route("/api/concierge/chat", methods=["POST"])
@rate_limit_ai
def ai_chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")

    if not messages or not isinstance(messages, list):
        single_msg = data.get("message") or data.get("query") or data.get("prompt")
        raw_history = data.get("history") or []
        messages = []
        if isinstance(raw_history, list):
            for h in raw_history:
                if isinstance(h, dict) and h.get("content"):
                    messages.append({
                        "role": "assistant" if h.get("role") == "assistant" else "user",
                        "content": sanitize_string(h.get("content", ""), max_length=1000)
                    })
        if single_msg and isinstance(single_msg, str) and single_msg.strip():
            clean_msg = sanitize_string(single_msg.strip(), max_length=1000)
            if not messages or messages[-1].get("content") != clean_msg:
                messages.append({"role": "user", "content": clean_msg})

    if not messages:
        return jsonify({
            "success": True,
            "reply": "Hello! How can I assist you with SpaceLoop today?",
            "intent": "GENERAL_CONVERSATION",
            "entities": {},
            "detected_language": "en",
            "response_language": "en",
            "confidence": 1.0,
            "requires_clarification": False
        }), 200

    user_context = {}
    if current_user.is_authenticated:
        user_context = {
            "user_id": current_user.id,
            "user_name": current_user.name,
            "role": current_user.role,
            "is_verified": current_user.is_student_verified or current_user.is_host_verified
        }

    if data.get("space_id"):
        user_context["space_id"] = data.get("space_id")
    if data.get("current_path"):
        user_context["current_path"] = data.get("current_path")

    # Negotiate multilingual preferences & message detection
    from backend.modules.nlp.i18n import MultilingualService
    from backend.modules.ai.loopbot_orchestrator import orchestrate_loopbot_query

    lang_pref = data.get("language_preference") or request.headers.get("X-Language-Preference")
    user_query = messages[-1].get("content", "") if messages else ""
    effective_lang, detected_lang, is_code_mixed = MultilingualService.negotiate_language(
        user_query, explicit_preference=lang_pref
    )
    user_context["language_preference"] = lang_pref
    user_context["effective_language"] = effective_lang
    user_context["detected_language"] = detected_lang
    user_context["is_code_mixed"] = is_code_mixed

    # Execute capability orchestration (Loop Bot does not blindly forward to LLM)
    try:
        orch_result = orchestrate_loopbot_query(
            user_query,
            history=messages[:-1],
            context_data=user_context,
            return_dict=True
        )
    except Exception as exc:
        logger.error("Error during LoopBot query orchestration: %s", exc, exc_info=True)
        orch_result = {
            "reply": "I apologize, but I encountered a momentary issue processing your request. How else may I assist you with SpaceLoop?",
            "intent": "GENERAL_CONVERSATION",
            "entities": {},
            "detected_language": effective_lang or "en",
            "response_language": effective_lang or "en",
            "confidence": 0.5,
            "requires_clarification": False,
            "listing_draft": None
        }

    return jsonify({
        "success": True,
        "reply": orch_result["reply"],
        "intent": orch_result["intent"],
        "entities": orch_result["entities"],
        "detected_language": orch_result["detected_language"],
        "response_language": orch_result["response_language"],
        "confidence": orch_result["confidence"],
        "requires_clarification": orch_result["requires_clarification"],
        "is_code_mixed": is_code_mixed,
        "listing_draft": orch_result.get("listing_draft")
    }), 200


@api_v1_system.route("/api/nlp/dispatch", methods=["POST"])
@rate_limit_ai
def api_nlp_dispatch():
    """
    Unified NLP Router endpoint.
    Routes user query to LoopBot RAG, Semantic Search, or Listing Assistance
    based on intent recognition or explicit caller action.
    """
    data = request.get_json(silent=True) or request.form or {}
    query = sanitize_string(data.get("query") or data.get("text") or data.get("message") or "", max_length=1000)
    context_data = data.get("context_data") or {}
    if not isinstance(context_data, dict):
        context_data = {}

    if current_user.is_authenticated:
        context_data["user_id"] = current_user.id
        context_data["role"] = current_user.role

    from backend.modules.nlp.pipeline import NLPPipeline
    result = NLPPipeline.dispatch(query, context_data=context_data)
    return jsonify(result), 200


@api_v1_system.route("/api/system/status", methods=["GET"])
def api_system_status():
    sim = session.get("simulate_ai_failure", False)
    return jsonify(get_system_connectivity_status(simulate_override=sim))


@api_v1_system.route("/api/dev/toggle-ai-simulation", methods=["POST", "GET"])
def toggle_ai_simulation():
    current_val = session.get("simulate_ai_failure", False)
    new_val = not current_val
    session["simulate_ai_failure"] = new_val
    set_simulate_ai_failure(new_val)
    return redirect(request.referrer or "/")


@api_v1_system.route("/api/verify/student", methods=["POST"])
@login_required
def api_verify_student():
    data = request.get_json(silent=True) or {}
    name = sanitize_string(data.get("name", current_user.name), max_length=100)
    aadhaar_num = sanitize_string(data.get("aadhaar_number", ""), max_length=20)
    otp = sanitize_string(data.get("otp", "123456"), max_length=10)
    college_email = sanitize_string(data.get("college_email", ""), max_length=120)
    college_name = sanitize_string(data.get("college_name", ""), max_length=150)
    student_id = sanitize_string(data.get("student_id", ""), max_length=50)

    aadhaar_res = verify_aadhaar_otp(name, aadhaar_num, otp)
    if not aadhaar_res.get("success"):
        return jsonify({"success": False, "error": aadhaar_res.get("error")}), 400

    acad_res = verify_academic_credentials(college_email, student_id, college_name)

    user = current_user
    user.is_student_verified = True
    user.is_aadhaar_verified = True
    user.aadhaar_masked = aadhaar_res["masked_aadhaar"]
    user.aadhaar_token_hash = aadhaar_res["token_hash"]
    user.college_name = acad_res["college_name"]
    user.college_email = acad_res["college_email"]
    user.student_id_masked = acad_res["student_id_masked"]
    user.objective_trust_score = compute_objective_trust_index(
        user.on_time_vacate_rate,
        user.cleanliness_match_rate,
        is_identity_verified=True,
        dispute_count=user.dispute_count
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Student identity and academic enrollment successfully verified!",
        "aadhaar": aadhaar_res,
        "academic": acad_res,
        "user": user.to_dict()
    })


@api_v1_system.route("/api/verify/host", methods=["POST"])
@login_required
def api_verify_host():
    data = request.get_json(silent=True) or {}
    ca_number = sanitize_string(data.get("ca_number", ""), max_length=50)
    provider = sanitize_string(data.get("provider", "BESCOM"), max_length=80)
    address = sanitize_string(data.get("address", ""), max_length=200)
    pan_name = sanitize_string(data.get("pan_name", ""), max_length=100)
    upi_vpa = sanitize_string(data.get("upi_vpa", ""), max_length=80)

    discom_res = verify_host_electricity_bill(ca_number, provider, address, pan_name)
    if not discom_res.get("success"):
        return jsonify({"success": False, "error": discom_res.get("error")}), 400

    upi_res = verify_upi_penny_drop(upi_vpa, pan_name)
    if not upi_res.get("success"):
        return jsonify({"success": False, "error": upi_res.get("error")}), 400

    user = current_user
    user.is_host_verified = True
    user.discom_provider = discom_res.get("discom_provider") or discom_res.get("provider") or provider
    user.discom_ca_masked = discom_res.get("discom_ca_masked") or discom_res.get("ca_number_masked") or (ca_number[-4:] if len(ca_number) >= 4 else ca_number)
    user.upi_verified = True
    user.upi_vpa_masked = upi_res.get("upi_vpa_masked") or upi_vpa
    user.bank_beneficiary_name = upi_res.get("bank_beneficiary_name") or upi_res.get("beneficiary_name") or pan_name
    user.objective_trust_score = compute_objective_trust_index(
        user.on_time_vacate_rate,
        user.cleanliness_match_rate,
        is_identity_verified=True,
        dispute_count=user.dispute_count
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Property possession and payout account successfully verified!",
        "discom": discom_res,
        "upi": upi_res,
        "user": user.to_dict()
    })


@api_v1_system.route("/api/inquiries", methods=["GET", "POST"])
@login_required
def api_inquiries():
    if request.method == "POST":
        data = request.get_json() or {}
        question = sanitize_string(data.get("question") or "")
        if not question:
            return jsonify({"success": False, "error": "Question text cannot be empty."}), 400

        space_id = data.get("space_id")
        space = Space.query.get(space_id) if space_id else None

        context_data = None
        if space:
            context_data = {
                "space_title": space.title,
                "category": space.category,
                "hourly_rate": space.price_hourly,
                "amenities": space.amenities,
                "rules": space.rules,
                "address": f"{space.neighborhood or space.city}, {space.state}"
            }

        ai_res = concierge_chat([{"role": "user", "content": question}], context_data=context_data)
        answer = ai_res if isinstance(ai_res, str) else (ai_res.get("reply") if isinstance(ai_res, dict) else "Inquiry logged.")

        inquiry = SpaceInquiry(
            space_id=space.id if space else None,
            user_id=current_user.id,
            question=question,
            ai_answer=answer
        )
        db.session.add(inquiry)

        # Create host notification
        if space and space.owner_id:
            seeker_name = current_user.name or current_user.email or "A seeker"
            notif = Notification(
                user_id=space.owner_id,
                type="inquiry",
                title=f"New Inquiry: {space.title}",
                message=f"{seeker_name} asked: \"{question[:120]}{'...' if len(question) > 120 else ''}\"",
                priority="medium",
                action_url="/host/overview",
                unread=True,
                created_at=datetime.utcnow()
            )
            db.session.add(notif)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Inquiry logged and pre-answered by LoopBot AI Concierge.",
            "inquiry": inquiry.to_dict()
        }), 201

    inquiries = SpaceInquiry.query.filter(
        db.or_(
            SpaceInquiry.user_id == current_user.id,
            SpaceInquiry.space_id.in_(
                db.session.query(Space.id).filter(Space.owner_id == current_user.id)
            )
        )
    ).order_by(SpaceInquiry.created_at.desc()).all()

    return jsonify({
        "success": True,
        "inquiries": [i.to_dict() for i in inquiries]
    }), 200


@api_v1_system.route("/health")
@api_v1_system.route("/api/health")
def health_check():
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    ai_status = get_system_connectivity_status()
    is_healthy = (db_status == "healthy")
    status_code = 200 if is_healthy else 503

    return jsonify({
        "status": "healthy" if is_healthy else "degraded",
        "version": "2.5.1-live",
        "database": db_status,
        "ai_engine": ai_status,
        "server_timestamp": datetime.utcnow().isoformat()
    }), status_code
