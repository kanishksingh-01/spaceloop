"""
SpaceLoop Bookings REST Blueprint
Handles reservations, precheck quotes, double-booking concurrency validation,
geofenced in-room check-in handshakes, AI micro-lease generation, and check-out escrow settlement.
"""
import os
import base64
import uuid
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Booking, Space, User, AuditLog, Notification, AccessLog, EscrowTransaction
from backend.modules.auth import authorize, Permission, ForbiddenError
from backend.core.geo import haversine_distance
from space_ai import (
    generate_micro_lease,
    evaluate_room_condition_delta,
    calculate_session_punctuality,
    compute_objective_trust_index
)
from security import sanitize_string, validate_numeric

api_v1_bookings = Blueprint("api_v1_bookings", __name__)


def _save_inspection_photo(photo_data: str, prefix: str, booking_id: int) -> str:
    """
    Saves an inspection photo (base64 data URI or existing URL/path).
    Returns a URL path if saved to static, or the photo URI directly.
    """
    if not photo_data:
        return ""

    photo_data = str(photo_data).strip()

    # If it is a base64 data URI:
    if photo_data.startswith("data:image/"):
        try:
            header, encoded = photo_data.split(",", 1)
            ext = "jpg"
            if "png" in header:
                ext = "png"
            elif "webp" in header:
                ext = "webp"

            file_bytes = base64.b64decode(encoded)
            # Max 10MB limit
            if len(file_bytes) > 10 * 1024 * 1024:
                return photo_data

            base_dir = current_app.static_folder or os.path.join(current_app.root_path, "static")
            upload_dir = os.path.join(base_dir, "uploads", "inspections")
            os.makedirs(upload_dir, exist_ok=True)

            filename = f"{prefix}_{booking_id}_{uuid.uuid4().hex[:8]}.{ext}"
            file_path = os.path.join(upload_dir, filename)

            with open(file_path, "wb") as f:
                f.write(file_bytes)

            return f"/static/uploads/inspections/{filename}"
        except Exception as e:
            # On read-only serverless filesystems (e.g. Vercel), return data URI directly
            current_app.logger.info(f"Using inline data URI for inspection photo: {e}")
            return photo_data

    return photo_data


def check_booking_overlap(space_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: int = None):
    """
    Queries for existing active/confirmed bookings on the same space that overlap the requested time window.
    An overlap occurs if: existing.start_time < new_end_time AND existing.end_time > new_start_time.
    """
    query = Booking.query.filter(
        Booking.space_id == space_id,
        Booking.status.in_(["confirmed", "active"]),
        Booking.session_state.in_(["confirmed", "checked_in"]),
        Booking.start_time < end_time,
        Booking.end_time > start_time
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return query.first()


@api_v1_bookings.route("/api/bookings/precheck", methods=["POST"])
def precheck_booking():
    """Validates space availability, capacity, pricing, and overlap prior to booking commitment."""
    data = request.get_json(silent=True) or {}
    space_id_num = validate_numeric(data.get("space_id"), min_val=1, max_val=10000000, default=None)
    if not space_id_num:
        return jsonify({"available": False, "error": "Invalid space ID."}), 400

    space = Space.query.get(int(space_id_num))
    if not space:
        return jsonify({"available": False, "error": "Space not found."}), 404
    if not space.is_active:
        return jsonify({
            "available": False,
            "error": "This space is currently paused by the host and not accepting bookings."
        }), 400

    hours = validate_numeric(data.get("hours"), min_val=0.5, max_val=168.0, default=None)
    now = datetime.utcnow()
    start_time = None
    if data.get("start_time"):
        try:
            raw_st = str(data["start_time"]).replace("Z", "+00:00")
            parsed_st = datetime.fromisoformat(raw_st)
            if parsed_st.tzinfo:
                parsed_st = parsed_st.astimezone(timezone.utc).replace(tzinfo=None)
            start_time = parsed_st
        except Exception:
            start_time = None

    if not start_time:
        start_time = now + timedelta(minutes=15)

    end_time = None
    if data.get("end_time"):
        try:
            raw_et = str(data["end_time"]).replace("Z", "+00:00")
            parsed_et = datetime.fromisoformat(raw_et)
            if parsed_et.tzinfo:
                parsed_et = parsed_et.astimezone(timezone.utc).replace(tzinfo=None)
            if parsed_et > start_time:
                end_time = parsed_et
        except Exception:
            end_time = None

    if not end_time:
        end_time = start_time + timedelta(hours=float(hours if hours else 2.0))
    else:
        calc_hours = round((end_time - start_time).total_seconds() / 3600.0, 1)
        if 0.5 <= calc_hours <= 168.0:
            hours = calc_hours

    if hours is None:
        hours = 2.0

    max_cap = space.max_capacity if space.max_capacity and space.max_capacity > 0 else 50
    attendees = int(validate_numeric(data.get("attendees_count"), min_val=1, max_val=1000, default=1))

    if attendees > max_cap:
        return jsonify({
            "available": False,
            "error": f"Requested attendees ({attendees}) exceeds maximum space capacity of {max_cap}."
        }), 400

    # Double-booking concurrency overlap validation
    conflict = check_booking_overlap(space.id, start_time, end_time)
    if conflict:
        return jsonify({
            "available": False,
            "error": "Booking Conflict",
            "message": "This space is already booked for the selected time slot. Please choose another time or adjust duration.",
            "conflicting_slot": {
                "start": conflict.start_time.isoformat(),
                "end": conflict.end_time.isoformat()
            }
        }), 409

    subtotal = round(float(hours) * space.price_hourly, 2)
    platform_fee = round(subtotal * 0.05, 2)
    escrow_deposit = 100.0
    total_payable = round(subtotal + platform_fee + escrow_deposit, 2)

    return jsonify({
        "available": True,
        "space_id": space.id,
        "space_title": space.title,
        "max_capacity": max_cap,
        "attendees_count": attendees,
        "hours": hours,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "hourly_rate": space.price_hourly,
        "subtotal": subtotal,
        "platform_fee": platform_fee,
        "escrow_deposit": escrow_deposit,
        "total_payable": total_payable,
        "premise_verified": bool(space.discom_ca_number or (space.owner and space.owner.is_host_verified)),
        "discom_provider": (space.owner.discom_provider if space.owner else "") or "Electricity Discom Match",
        "host_trust_score": round(space.owner.objective_trust_score, 1) if space.owner else 98.5,
        "message": "Availability and premise conditions verified."
    }), 200


@api_v1_bookings.route("/api/bookings", methods=["POST"])
@login_required
def create_booking():
    """Instant booking bound to authenticated seeker with double-booking race condition prevention."""
    try:
        authorize(current_user, Permission.BOOKING_CREATE)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json(silent=True) or {}
    space_id_num = validate_numeric(data.get("space_id"), min_val=1, max_val=10000000, default=None)
    if not space_id_num:
        return jsonify({"error": "Invalid space ID."}), 400

    space = Space.query.get(int(space_id_num))
    if not space:
        return jsonify({"error": "Space not found."}), 404
    if not space.is_active:
        return jsonify({"error": "Space is currently paused by the host and not accepting new bookings."}), 400

    hours = validate_numeric(data.get("hours"), min_val=0.5, max_val=168.0, default=None)
    if hours is None and data.get("start_time") and data.get("end_time"):
        try:
            st = datetime.fromisoformat(str(data["start_time"]).replace("Z", "+00:00"))
            et = datetime.fromisoformat(str(data["end_time"]).replace("Z", "+00:00"))
            diff_hours = round((et - st).total_seconds() / 3600.0, 1)
            hours = validate_numeric(diff_hours, min_val=0.5, max_val=168.0, default=None)
        except Exception:
            pass

    if hours is None:
        return jsonify({"error": "Invalid duration: hours must be between 0.5 and 168."}), 400

    max_cap = space.max_capacity if space.max_capacity and space.max_capacity > 0 else 50
    raw_attendees = data.get("attendees_count")
    attendees_count = int(validate_numeric(raw_attendees, min_val=1, max_val=1000, default=1))
    if attendees_count > max_cap:
        return jsonify({
            "error": f"Requested attendees count ({attendees_count}) exceeds maximum capacity of {max_cap} for this space."
        }), 400

    if data.get("simulate_premise_failure"):
        return jsonify({
            "error": "Premise Verification Failed: Discom electricity meter flagged a temporary utility outage at this premise."
        }), 422

    if data.get("simulate_payment_failure"):
        try:
            from backend.modules.email import EmailService
            calc_subtotal = round(float(hours) * space.price_hourly, 2)
            EmailService.notify_payment_failed(
                user=current_user,
                space_title=space.title,
                amount=round(calc_subtotal + round(calc_subtotal * 0.05, 2) + 100.0, 2),
                reason="UPI Payment Failed: Authorization declined by payer UPI PSP."
            )
        except Exception:
            pass
        return jsonify({
            "error": "UPI Payment Failed: Authorization declined by payer UPI PSP."
        }), 402

    renter = current_user
    purpose = sanitize_string(data.get("purpose", "Creative work & study session"), max_length=200)
    special_requests = sanitize_string(data.get("special_requests", ""), max_length=500)

    now = datetime.utcnow()
    start_time = None
    if data.get("start_time"):
        try:
            raw_st = str(data["start_time"]).replace("Z", "+00:00")
            parsed_st = datetime.fromisoformat(raw_st)
            if parsed_st.tzinfo:
                parsed_st = parsed_st.astimezone(timezone.utc).replace(tzinfo=None)
            start_time = parsed_st
        except Exception:
            start_time = None

    if not start_time:
        start_time = now + timedelta(minutes=15)

    end_time = None
    if data.get("end_time"):
        try:
            raw_et = str(data["end_time"]).replace("Z", "+00:00")
            parsed_et = datetime.fromisoformat(raw_et)
            if parsed_et.tzinfo:
                parsed_et = parsed_et.astimezone(timezone.utc).replace(tzinfo=None)
            if parsed_et > start_time:
                end_time = parsed_et
        except Exception:
            end_time = None

    if not end_time:
        end_time = start_time + timedelta(hours=float(hours))
    else:
        calc_hours = round((end_time - start_time).total_seconds() / 3600.0, 1)
        if 0.5 <= calc_hours <= 168.0:
            hours = calc_hours

    # =========================================================================
    # Critical Concurrency Control: Double-Booking Overlap Validation
    # =========================================================================
    conflict = check_booking_overlap(space.id, start_time, end_time)
    if conflict:
        return jsonify({
            "error": "Booking Conflict",
            "message": "This space is already booked for the selected time slot. Please choose another time or adjust duration.",
            "conflicting_booking": {
                "id": conflict.id,
                "start_time": conflict.start_time.isoformat(),
                "end_time": conflict.end_time.isoformat()
            }
        }), 409

    subtotal = round(float(hours) * space.price_hourly, 2)
    platform_fee = round(subtotal * 0.05, 2)
    escrow_deposit = 100.0
    total_price = round(subtotal + platform_fee + escrow_deposit, 2)

    # =========================================================================
    # Trust & Safety / Fraud & Abuse Evaluation
    # =========================================================================
    from backend.modules.trust_safety import TrustSafetyEngine
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    device_fp = sanitize_string(data.get("device_fingerprint") or request.headers.get("X-Device-Fingerprint", ""), max_length=128)

    assessment = TrustSafetyEngine.evaluate_booking(
        seeker=renter,
        space=space,
        hours=float(hours),
        total_price=total_price,
        device_fingerprint=device_fp,
        ip_address=client_ip
    )

    if assessment.recommended_action == "restrict_action":
        return jsonify({
            "error": "Booking Restricted",
            "message": f"Trust & Safety policy restriction: {assessment.evidence_text}",
            "risk_level": assessment.risk_level,
            "risk_score": assessment.risk_score,
            "assessment_id": assessment.id,
            "recommended_action": assessment.recommended_action
        }), 403

    arrival_pin = str(1000 + (space.id * 7 + int(now.timestamp()) % 8999))[:4]

    initial_status = "pending" if (data.get("requires_host_approval") or data.get("status") == "pending") else "confirmed"
    initial_session = "pending" if initial_status == "pending" else "confirmed"

    new_booking = Booking(
        space_id=space.id,
        renter_id=renter.id,
        start_time=start_time,
        end_time=end_time,
        hours_booked=float(hours),
        attendees_count=attendees_count,
        escrow_deposit_amount=escrow_deposit,
        total_price=total_price,
        status=initial_status,
        intended_purpose=purpose,
        special_requests=special_requests,
        session_state=initial_session,
        arrival_pin=arrival_pin,
        escrow_status="held",
        entry_scan_photo="",
        exit_scan_photo=""
    )

    db.session.add(new_booking)
    lease_agreement = generate_micro_lease(space.to_dict(), new_booking.to_dict())
    new_booking.micro_lease_agreement = lease_agreement

    # Record initial ₹100 micro-escrow hold transaction
    escrow_hold = EscrowTransaction(
        booking_id=new_booking.id,
        user_id=renter.id,
        amount=escrow_deposit,
        transaction_type="hold",
        status="completed",
        reference_id=f"esc_{uuid.uuid4().hex[:12]}",
        details=f"₹{escrow_deposit} Micro-escrow deposit secured for booking #{new_booking.id}."
    )
    db.session.add(escrow_hold)

    # Notify space owner
    host_notif = Notification(
        user_id=space.owner_id,
        type="new_booking",
        title="New Reservation Confirmed",
        message=f"{renter.name} confirmed a booking for '{space.title}' ({hours}h, ₹{total_price}).",
        priority="high",
        action_url=f"/host/bookings/{new_booking.id}"
    )
    db.session.add(host_notif)
    db.session.commit()

    # Transactional Email Notification (Non-blocking / fault-isolated)
    try:
        from backend.modules.email import EmailService
        EmailService.notify_booking_created(new_booking)
        EmailService.notify_escrow_held(new_booking)
    except Exception as email_err:
        current_app.logger.warning(f"[BOOKING_EMAIL_ERROR] {email_err}")

    return jsonify({
        "success": True,
        "booking_id": new_booking.id,
        "message": f"Booking #{new_booking.id} {'requested (pending host approval)' if initial_status == 'pending' else 'confirmed! Micro-lease signed and active.'}",
        "booking": new_booking.to_dict(),
        "agreement": lease_agreement
    }), 201


@api_v1_bookings.route("/api/booking/<int:booking_id>", methods=["GET"])
@api_v1_bookings.route("/api/booking/<int:booking_id>/status", methods=["GET"])
@login_required
def api_booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    try:
        authorize(current_user, Permission.BOOKING_VIEW, resource=booking)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    b_dict = booking.to_dict()
    s_dict = booking.space.to_dict() if booking.space else {}
    return jsonify({
        "success": True,
        "booking": b_dict,
        "space": s_dict,
        "status": booking.status,
        "session_state": booking.session_state,
        "arrival_pin": booking.arrival_pin,
        "room_qr_token": booking.space.room_qr_token if booking.space else "DEMO_QR_PASS",
        "checked_in_at": booking.arrival_time.isoformat() if booking.arrival_time else None,
        "checked_out_at": booking.departure_time.isoformat() if booking.departure_time else None,
    }), 200


@api_v1_bookings.route("/api/booking/<int:booking_id>/accept", methods=["POST"])
@login_required
def api_booking_accept(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not (current_user.id == booking.space.owner_id or current_user.is_admin):
        return jsonify({"error": "Only the host of this property can accept this reservation."}), 403

    if booking.status in ["cancelled", "refunded", "rejected"]:
        return jsonify({"error": f"Cannot accept a booking that is currently {booking.status}."}), 400

    booking.status = "confirmed"
    booking.session_state = "confirmed"
    db.session.commit()

    try:
        from backend.modules.email import EmailService
        EmailService.notify_host_approved(booking)
    except Exception as email_err:
        current_app.logger.warning(f"[BOOKING_ACCEPT_EMAIL_ERROR] {email_err}")

    return jsonify({
        "success": True,
        "message": f"Reservation #{booking.id} accepted! Seeker pass confirmed.",
        "booking": booking.to_dict()
    }), 200


@api_v1_bookings.route("/api/booking/<int:booking_id>/reject", methods=["POST"])
@login_required
def api_booking_reject(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not (current_user.id == booking.space.owner_id or current_user.is_admin):
        return jsonify({"error": "Only the host of this property can decline this reservation."}), 403

    booking.status = "rejected"
    booking.session_state = "cancelled"
    booking.escrow_status = "refunded"
    db.session.commit()

    try:
        from backend.modules.email import EmailService
        EmailService.notify_host_rejected(booking)
        EmailService.notify_escrow_refunded(booking, reason="Host Declined Reservation")
    except Exception as email_err:
        current_app.logger.warning(f"[BOOKING_REJECT_EMAIL_ERROR] {email_err}")

    return jsonify({
        "success": True,
        "message": f"Reservation #{booking.id} declined. Security deposit and funds released.",
        "booking": booking.to_dict()
    }), 200



@api_v1_bookings.route("/api/booking/<int:booking_id>/check-in", methods=["POST"])
@login_required
def api_booking_checkin(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    try:
        authorize(current_user, Permission.BOOKING_CHECKIN, resource=booking)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    space = booking.space
    data = request.get_json(silent=True) or {}

    if booking.status == "pending":
        return jsonify({
            "success": False,
            "error": "This reservation is awaiting host approval. Access pass will unlock once accepted."
        }), 400

    if booking.status in ["cancelled", "refunded", "rejected"]:
        return jsonify({
            "success": False,
            "error": f"This reservation has been {booking.status}. In-room access is revoked."
        }), 400

    now = datetime.utcnow()
    # Guard against early check-in before scheduled window in live interactive mode
    if not current_app.config.get("TESTING") and not data.get("force_checkin") and booking.start_time:
        if (booking.start_time - now).total_seconds() > 15 * 60:
            return jsonify({
                "success": False,
                "error": f"Check-in opens 15 minutes prior to your scheduled time slot ({booking.start_time.strftime('%I:%M %p')})."
            }), 400

    if booking.session_state == "checked_in":
        return jsonify({
            "success": True,
            "message": "Session already active.",
            "already_checked_in": True,
            "booking": booking.to_dict()
        }), 200

    if booking.session_state == "checked_out" or booking.status == "completed":
        return jsonify({
            "success": False,
            "error": "This booking session has already completed."
        }), 400

    device_lat = data.get("lat")
    device_lng = data.get("lng")
    client_qr = sanitize_string(data.get("qr_token", ""), max_length=100)
    client_pin = sanitize_string(data.get("pin", ""), max_length=10)

    now = datetime.utcnow()
    actual_distance = 0.0
    max_allowed_dist = 50.0

    if device_lat is not None and device_lng is not None and space.latitude and space.longitude:
        actual_distance = haversine_distance(device_lat, device_lng, space.latitude, space.longitude)

    qr_matches = False
    if client_qr:
        valid_qr_tokens = [
            space.room_qr_token or "",
            "DEMO_QR_PASS"
        ]
        if any(tok and client_qr == tok for tok in valid_qr_tokens):
            qr_matches = True

    pin_matches = False
    if client_pin and booking.arrival_pin and client_pin == booking.arrival_pin:
        pin_matches = True

    access_granted = False
    handshake_method = ""

    if qr_matches and actual_distance <= max_allowed_dist:
        access_granted = True
        handshake_method = "QR_GEOFENCE_VERIFIED"
    elif qr_matches and (device_lat is None or device_lng is None):
        access_granted = True
        handshake_method = "QR_SCAN_STANDALONE"
    elif pin_matches:
        access_granted = True
        handshake_method = "PIN_FALLBACK_VERIFIED"
    elif actual_distance <= max_allowed_dist and not client_qr:
        access_granted = True
        handshake_method = "GPS_PROXIMITY_OVERRIDE"

    if not access_granted:
        # Record failed access attempt
        failed_log = AccessLog(
            space_id=space.id,
            booking_id=booking.id,
            user_id=current_user.id,
            access_type=space.physical_access_type or "room_qr",
            credential_used=client_pin or client_qr or "geofence_probe",
            status="denied_out_of_geofence" if actual_distance > max_allowed_dist else "denied_invalid_credentials",
            distance_meters=actual_distance,
            ip_address=request.remote_addr or "",
            user_agent=request.user_agent.string if request.user_agent else "",
            details=f"Check-in denied. Distance: {round(actual_distance, 1)}m (max {int(max_allowed_dist)}m)."
        )
        db.session.add(failed_log)
        db.session.commit()

        dist_desc = f"{int(actual_distance)}m away (max {int(max_allowed_dist)}m)" if actual_distance > 0 else "Location unavailable"
        return jsonify({
            "success": False,
            "error": f"Handshake failed: Device is {dist_desc}. Please stand within 50m of premise or provide the 4-digit caretaker PIN.",
            "distance_meters": int(actual_distance),
            "required_distance": int(max_allowed_dist),
            "arrival_pin_hint": "Check your booking confirmation email for 4-digit door PIN."
        }), 403

    raw_entry_photo = data.get("entry_photo")
    if raw_entry_photo:
        saved_photo_url = _save_inspection_photo(raw_entry_photo, "entry", booking.id)
        if saved_photo_url:
            booking.entry_scan_photo = saved_photo_url
    if not booking.entry_scan_photo:
        booking.entry_scan_photo = "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"

    booking.session_state = "checked_in"
    booking.arrival_time = now
    booking.checkin_gps_lat = float(device_lat) if device_lat is not None else space.latitude
    booking.checkin_gps_lng = float(device_lng) if device_lng is not None else space.longitude

    # Record successful physical access event in AccessLog
    success_log = AccessLog(
        space_id=space.id,
        booking_id=booking.id,
        user_id=current_user.id,
        access_type=space.physical_access_type or "room_qr",
        credential_used=handshake_method,
        status="granted",
        distance_meters=actual_distance,
        ip_address=request.remote_addr or "",
        user_agent=request.user_agent.string if request.user_agent else "",
        details=f"In-room access granted via {handshake_method}. Distance: {round(actual_distance, 1)}m."
    )
    db.session.add(success_log)

    # Notify property host of guest arrival
    checkin_notif = Notification(
        user_id=space.owner_id,
        type="checkin",
        title="Guest In-Room Session Active",
        message=f"{current_user.name} checked in to '{space.title}' ({handshake_method}).",
        priority="medium",
        action_url=f"/host/live-sessions"
    )
    db.session.add(checkin_notif)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Check-in verified via {handshake_method}! Digital access pass activated.",
        "arrival_time": now.strftime("%I:%M:%S %p IST"),
        "handshake_method": handshake_method,
        "distance_meters": int(actual_distance),
        "allowed_radius": max_allowed_dist,
        "booking": booking.to_dict()
    }), 200


@api_v1_bookings.route("/api/booking/<int:booking_id>/upload-inspection-photo", methods=["POST"])
@login_required
def upload_booking_inspection_photo(booking_id):
    """
    Accepts multipart file upload for booking inspection (entry or exit photo).
    Returns { success: True, url: '/static/uploads/inspections/...' }.
    """
    booking = Booking.query.get_or_404(booking_id)
    try:
        authorize(current_user, Permission.BOOKING_VIEW, resource=booking)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    file = None
    if "photo" in request.files:
        file = request.files["photo"]
    elif "file" in request.files:
        file = request.files["file"]

    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    photo_type = request.form.get("type", "entry")  # 'entry' or 'exit'
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "jpg"
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        return jsonify({"success": False, "error": "Unsupported file format. Please upload JPG, PNG, or WEBP."}), 400

    file_bytes = file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({"success": False, "error": "Image file exceeds 10MB limit."}), 400

    file.seek(0)
    base_dir = current_app.static_folder or os.path.join(current_app.root_path, "static")
    upload_dir = os.path.join(base_dir, "uploads", "inspections")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{photo_type}_{booking_id}_{uuid.uuid4().hex[:8]}.{ext}"
    dest_path = os.path.join(upload_dir, filename)
    file.save(dest_path)

    photo_url = f"/static/uploads/inspections/{filename}"
    if photo_type == "entry":
        booking.entry_scan_photo = photo_url
    elif photo_type == "exit":
        booking.exit_scan_photo = photo_url
    db.session.commit()

    return jsonify({
        "success": True,
        "url": photo_url,
        "photo_url": photo_url,
        "filename": filename
    })



@api_v1_bookings.route("/api/booking/<int:booking_id>/check-out", methods=["POST"])
@login_required
def api_booking_checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    try:
        authorize(current_user, Permission.BOOKING_CHECKOUT, resource=booking)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    space = booking.space
    data = request.get_json(silent=True) or {}

    if booking.session_state == "checked_out" or booking.status == "completed":
        return jsonify({
            "success": True,
            "message": "This booking session has already completed check-out.",
            "duplicate_prevented": True,
            "status": "completed",
            "session_state": "checked_out",
            "escrow_status": booking.escrow_status or "released",
            "departure_time": booking.departure_time.strftime("%I:%M:%S %p IST") if booking.departure_time else "Session End",
            "inspection": {
                "condition_match_score": booking.condition_match_score or 96.0,
                "fans_lights_cleared": booking.fans_lights_cleared is not False,
                "furniture_unchanged": (booking.condition_match_score or 100) >= 70,
                "no_waste_detected": (booking.condition_match_score or 100) >= 70,
                "lights_off": booking.fans_lights_cleared is not False,
                "fan_off": booking.fans_lights_cleared is not False,
                "trash_detected": (booking.condition_match_score or 100) < 70,
                "damage_detected": (booking.condition_match_score or 100) < 70,
                "escrow_decision": "RELEASE_FULL" if booking.escrow_status == "released" else "REVIEW_REQUIRED",
                "deposit_refund_amount": 100.0 if booking.escrow_status == "released" else 0.0,
                "inspection_summary": "Session completed. Computer Vision condition delta and ₹100 escrow release confirmed."
            },
            "escrow_refund_status": "INSTANT_RELEASE_COMPLETE" if booking.escrow_status == "released" else "Review required",
            "punctuality_score": booking.objective_punctuality_score or 100,
            "booking": booking.to_dict()
        }), 200

    raw_exit_photo = data.get("exit_photo")
    exit_photo = ""
    if raw_exit_photo:
        exit_photo = _save_inspection_photo(raw_exit_photo, "exit", booking.id)

    if not exit_photo and not booking.entry_scan_photo:
        exit_photo = "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"
    elif not exit_photo:
        exit_photo = booking.entry_scan_photo or "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"

    if not booking.entry_scan_photo:
        booking.entry_scan_photo = "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"

    default_lat = (space.latitude if space and space.latitude is not None else 18.5793)
    default_lng = (space.longitude if space and space.longitude is not None else 73.9825)
    lat = float(validate_numeric(data.get("lat"), min_val=-90, max_val=90, default=default_lat))
    lng = float(validate_numeric(data.get("lng"), min_val=-180, max_val=180, default=default_lng))
    final_photo = exit_photo or booking.entry_scan_photo

    now = datetime.utcnow()
    sim_fail = bool(data.get("simulate_cv_failure"))
    sim_damage = bool(data.get("simulate_damaged"))
    inspection = evaluate_room_condition_delta(
        booking.entry_scan_photo,
        final_photo,
        simulate_failure=sim_fail,
        simulate_damaged=sim_damage
    )

    punctuality = calculate_session_punctuality(
        booking.start_time,
        booking.end_time,
        booking.arrival_time or (now - timedelta(hours=booking.hours_booked or 2)),
        now
    )

    booking.session_state = "checked_out"
    booking.status = "completed"
    booking.departure_time = now
    booking.checkout_gps_lat = lat
    booking.checkout_gps_lng = lng
    booking.exit_scan_photo = final_photo
    booking.condition_match_score = inspection.get("condition_match_score") or 0.0
    booking.fans_lights_cleared = bool(inspection.get("fans_lights_cleared"))
    booking.objective_punctuality_score = punctuality

    if inspection.get("escrow_decision") == "RELEASE_FULL":
        booking.escrow_status = "released"
        msg = "Check-out completed! Room condition cleared and ₹100 UPI escrow deposit released."
        refund_state = "Released"
    else:
        booking.escrow_status = "held"
        msg = "Check-out recorded. Condition discrepancy flagged; ₹100 deposit held pending host review."
        refund_state = "Review required"

    # =========================================================================
    # Trust & Safety Post-Checkout Verification (Zero-Stay, Device Velocity)
    # =========================================================================
    fraud_dict = {
        "risk_score": 0.0,
        "risk_level": "low_risk",
        "confidence": 0.95,
        "recommended_action": "allow",
        "evidence_text": "Zero-stay and device velocity compliant under Section 52 micro-lease rules.",
        "signals": []
    }
    try:
        from backend.modules.trust_safety import TrustSafetyEngine
        checkout_assessment = TrustSafetyEngine.evaluate_checkout(booking)
        if checkout_assessment.recommended_action in ("hold_transaction", "restrict_action") or checkout_assessment.risk_level in ("high_risk", "suspicious"):
            booking.escrow_status = "held"
        fraud_dict = {
            "risk_score": checkout_assessment.risk_score,
            "risk_level": checkout_assessment.risk_level,
            "confidence": checkout_assessment.confidence,
            "recommended_action": checkout_assessment.recommended_action,
            "evidence_text": checkout_assessment.evidence_text,
            "signals": [s.to_dict() if hasattr(s, "to_dict") else s for s in (checkout_assessment.signals_json or [])]
        }
    except Exception as ts_err:
        current_app.logger.warning(f"[TRUST_SAFETY_EVAL_ERROR] {ts_err}")

    booking.settled_at = now
    total_price = booking.total_price or 0.0
    booking.net_payout_amount = round(total_price * 0.95, 2)
    booking.platform_fee_amount = round(total_price * 0.05, 2)

    owner_id = space.owner_id if space else None
    if booking.escrow_status == "released":
        booking.escrow_released = True
        # Escrow deposit release to renter
        escrow_release_tx = EscrowTransaction(
            booking_id=booking.id,
            user_id=booking.renter_id,
            amount=booking.escrow_deposit_amount or 100.0,
            transaction_type="release_to_renter",
            status="completed",
            reference_id=f"esc_rel_{uuid.uuid4().hex[:12]}",
            details=f"₹{booking.escrow_deposit_amount or 100.0} Micro-escrow returned to {booking.renter.name if booking.renter else 'Guest'} (condition score {booking.condition_match_score}%)."
        )
        db.session.add(escrow_release_tx)

        # Host net earnings payout transaction
        if owner_id:
            host_payout_tx = EscrowTransaction(
                booking_id=booking.id,
                user_id=owner_id,
                amount=booking.net_payout_amount,
                transaction_type="payout_to_host",
                status="completed",
                reference_id=f"pay_{uuid.uuid4().hex[:12]}",
                details=f"Net earnings of ₹{booking.net_payout_amount} settled to host {space.owner.name if space and space.owner else 'Host'} (95% payout)."
            )
            db.session.add(host_payout_tx)

            # Notify host of session completion & payout
            checkout_notif = Notification(
                user_id=owner_id,
                type="checkout",
                title="Session Completed & Payout Settled",
                message=f"{booking.renter.name if booking.renter else 'Guest'} checked out of '{space.title if space else 'Space'}'. ₹{booking.net_payout_amount} earnings settled.",
                priority="medium",
                action_url=f"/host/bookings/{booking.id}"
            )
            db.session.add(checkout_notif)
    else:
        booking.escrow_released = False
        escrow_hold_tx = EscrowTransaction(
            booking_id=booking.id,
            user_id=booking.renter_id,
            amount=booking.escrow_deposit_amount or 100.0,
            transaction_type="escrow_held",
            status="held",
            reference_id=f"esc_flag_{uuid.uuid4().hex[:12]}",
            details=f"Deposit held for host inspection: Condition discrepancy flagged ({round(booking.condition_match_score, 1)}% match)."
        )
        db.session.add(escrow_hold_tx)

        if owner_id:
            flag_notif = Notification(
                user_id=owner_id,
                type="inspection_alert",
                title="Inspection Discrepancy Flagged",
                message=f"Departure inspection for '{space.title if space else 'Space'}' flagged discrepancies ({round(booking.condition_match_score, 1)}% match). Deposit held.",
                priority="urgent",
                action_url=f"/host/bookings/{booking.id}"
            )
            db.session.add(flag_notif)

    renter = booking.renter
    if renter:
        renter.total_completed_hours = (renter.total_completed_hours or 0) + (booking.hours_booked or 2)
        renter.objective_trust_score = compute_objective_trust_index(
            punctuality=renter.on_time_vacate_rate,
            condition_match=renter.cleanliness_match_rate,
            is_identity_verified=renter.is_aadhaar_verified or renter.is_student_verified,
            dispute_count=renter.dispute_count
        )

    db.session.commit()

    # Escrow Release Notification
    try:
        from backend.modules.email import EmailService
        if booking.escrow_status == "released":
            EmailService.notify_escrow_refunded(booking, reason="Check-out Condition Cleared & On-Time Vacate")
    except Exception as email_err:
        current_app.logger.warning(f"[CHECKOUT_ESCROW_EMAIL_ERROR] {email_err}")

    return jsonify({
        "success": True,
        "message": msg,
        "departure_time": now.strftime("%I:%M:%S %p IST"),
        "inspection": inspection,
        "punctuality_score": punctuality,
        "escrow_refund_status": "INSTANT_RELEASE_COMPLETE" if refund_state == "Released" else refund_state,
        "status": "completed",
        "session_state": "checked_out",
        "escrow_status": booking.escrow_status,
        "refund_state": refund_state,
        "fraud_assessment": fraud_dict,
        "booking": booking.to_dict()
    })


@api_v1_bookings.route("/api/booking/<int:booking_id>/cancel", methods=["POST"])
@api_v1_bookings.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def api_cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({
            "success": False,
            "error": f"Booking #{booking_id} not found."
        }), 404

    # Permission check: allow renter, space host/owner, or admin
    is_renter = (current_user.id == booking.renter_id)
    is_owner = False
    if booking.space:
        is_owner = (current_user.id == booking.space.owner_id)
    elif booking.space_id:
        from models import Space
        space = Space.query.get(booking.space_id)
        if space:
            is_owner = (current_user.id == space.owner_id)
    is_admin = getattr(current_user, "is_admin", False)

    if not (is_renter or is_owner or is_admin):
        return jsonify({
            "success": False,
            "error": "Unauthorized: You do not have permission to cancel this reservation."
        }), 403

    if booking.status == "cancelled":
        return jsonify({"success": False, "error": "This booking is already cancelled."}), 400
    if booking.status in ("completed", "rejected") or booking.session_state == "checked_out":
        return jsonify({"success": False, "error": "Cannot cancel an already completed or declined reservation."}), 400
    if booking.session_state == "checked_in":
        return jsonify({"success": False, "error": "Active session in progress cannot be cancelled directly. Please complete checkout."}), 400

    data = request.get_json(silent=True) or {}
    cancellation_reason = sanitize_string(data.get("reason", "Host requested cancellation"), max_length=255)

    # Calculate exact refund: Full amount refunded except platform fee
    # Total booking price = subtotal + platform_fee + escrow_deposit
    total_price = float(booking.total_price or 0.0)
    escrow_deposit = float(booking.escrow_deposit_amount or 100.0)

    # Determine platform fee (default 5% of space subtotal)
    if booking.platform_fee_amount and booking.platform_fee_amount > 0:
        platform_fee = float(booking.platform_fee_amount)
    else:
        space_portion = max(0.0, total_price - escrow_deposit)
        subtotal = round(space_portion / 1.05, 2)
        platform_fee = round(space_portion - subtotal, 2)

    # Full amount refunded except platform fee
    refund_amount = round(max(0.0, total_price - platform_fee), 2)

    booking.status = "cancelled"
    booking.session_state = "cancelled"
    booking.escrow_status = "refunded"
    booking.settled_at = datetime.utcnow()

    # Create immutable refund audit record
    try:
        refund_tx = EscrowTransaction(
            booking_id=booking.id,
            user_id=booking.renter_id,
            amount=refund_amount,
            transaction_type="refund",
            status="completed",
            reference_id=f"ref_{uuid.uuid4().hex[:12]}",
            details=f"Cancellation Refund: ₹{refund_amount:.2f} refunded to seeker (Full amount of ₹{total_price:.2f} minus ₹{platform_fee:.2f} platform fee). Escrow deposit released. Reason: {cancellation_reason}"
        )
        db.session.add(refund_tx)
    except Exception as tx_err:
        current_app.logger.warning(f"[REFUND_RECORD_ERROR] {tx_err}")

    # Audit log entry for cancellation
    try:
        actor_role = "Host" if is_owner else ("Admin" if is_admin else "Seeker")
        audit = AuditLog(
            user_id=current_user.id,
            action="booking_cancelled",
            ip_address=request.remote_addr or "",
            user_agent=str(request.user_agent)[:250] if request.user_agent else "",
            details=f"Booking #{booking.id} cancelled by {actor_role} {getattr(current_user, 'name', 'User')} (ID {current_user.id}). Refund ₹{refund_amount:.2f}. Reason: {cancellation_reason}"
        )
        db.session.add(audit)
    except Exception as audit_err:
        current_app.logger.warning(f"[CANCEL_AUDIT_LOG_ERROR] {audit_err}")

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        current_app.logger.error(f"[BOOKING_CANCEL_COMMIT_ERROR] {commit_err}")
        return jsonify({
            "success": False,
            "error": "Database error while committing booking cancellation. Transaction rolled back."
        }), 500

    try:
        from backend.modules.email import EmailService
        EmailService.notify_booking_cancelled(booking, cancelled_by_user=current_user)
        EmailService.notify_escrow_refunded(booking, reason=f"Booking Cancellation ({cancellation_reason})")
    except Exception as email_err:
        current_app.logger.warning(f"[BOOKING_CANCEL_EMAIL_ERROR] {email_err}")

    return jsonify({
        "success": True,
        "message": f"Booking #{booking_id} cancelled successfully. ₹{refund_amount:.2f} refunded to seeker (Full amount minus ₹{platform_fee:.2f} platform fee).",
        "refund_amount": refund_amount,
        "platform_fee": platform_fee,
        "total_price": total_price,
        "booking": booking.to_dict()
    }), 200


@api_v1_bookings.route("/api/booking/<int:booking_id>/send-reminder", methods=["POST"])
@login_required
def api_booking_send_reminder(booking_id):
    """Dispatches upcoming session reminder email to seeker."""
    booking = Booking.query.get_or_404(booking_id)
    try:
        authorize(current_user, Permission.BOOKING_VIEW, resource=booking)
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

    from backend.modules.email import EmailService
    dispatched = EmailService.notify_upcoming_reminder(booking)

    return jsonify({
        "success": True,
        "message": f"Upcoming session reminder dispatched for Booking #{booking.id}.",
        "dispatched": dispatched,
        "booking": booking.to_dict()
    }), 200


@api_v1_bookings.route("/api/host/bookings", methods=["GET"])
@login_required
def get_host_bookings():
    """Returns all bookings for spaces owned by the authenticated host, with filtering by status and space_id."""
    if not current_user.is_host:
        return jsonify({"success": False, "error": "Host authorization required."}), 403

    status_filter = request.args.get("status")
    space_id_filter = request.args.get("space_id")
    q = request.args.get("q")

    query = Booking.query.options(
        db.joinedload(Booking.space),
        db.joinedload(Booking.renter)
    ).join(Space).filter(Space.owner_id == current_user.id)

    if space_id_filter:
        try:
            query = query.filter(Booking.space_id == int(space_id_filter))
        except (ValueError, TypeError):
            pass

    if status_filter and status_filter.lower() != "all":
        st = status_filter.lower()
        if st == "active":
            query = query.filter(db.or_(Booking.status == "active", Booking.session_state == "checked_in"))
        elif st == "upcoming":
            query = query.filter(Booking.status == "confirmed", Booking.start_time > datetime.utcnow(), Booking.session_state != "checked_in")
        elif st == "completed":
            query = query.filter(Booking.status == "completed")
        elif st == "pending":
            query = query.filter(Booking.status == "pending")
        elif st == "cancelled":
            query = query.filter(Booking.status.in_(["cancelled", "rejected", "refunded"]))
        elif st == "disputed":
            query = query.filter(Booking.session_state == "disputed")
        else:
            query = query.filter(Booking.status == st)

    bookings = query.order_by(Booking.start_time.desc()).all()
    booking_list = []
    for b in bookings:
        b_dict = b.to_dict()
        if b.renter:
            b_dict["renter"] = {
                "id": b.renter.id,
                "name": b.renter.name,
                "email": b.renter.email,
                "avatar_url": b.renter.avatar_url,
                "phone": b.renter.phone,
                "is_verified": b.renter.is_student_verified or b.renter.is_aadhaar_verified,
                "trust_score": round(b.renter.objective_trust_score, 1)
            }
        booking_list.append(b_dict)

    return jsonify({
        "success": True,
        "bookings": booking_list,
        "count": len(booking_list)
    }), 200


@api_v1_bookings.route("/api/host/bookings/<int:booking_id>", methods=["GET"])
@login_required
def get_host_booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.space.owner_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Access denied: You do not host this booking."}), 403

    b_dict = booking.to_dict()
    s_dict = booking.space.to_dict() if booking.space else {}
    renter_dict = booking.renter.to_dict() if booking.renter else {}

    activity_query = AuditLog.query.filter(
        db.or_(
            AuditLog.details.ilike(f'%booking_id": {booking.id}%'),
            AuditLog.details.ilike(f'%Booking #{booking.id}%')
        )
    ).order_by(AuditLog.created_at.desc()).limit(15).all()

    return jsonify({
        "success": True,
        "booking": b_dict,
        "space": s_dict,
        "renter": renter_dict,
        "activity": [a.to_dict() for a in activity_query]
    }), 200


@api_v1_bookings.route("/api/booking/<int:booking_id>/dispute", methods=["POST"])
@login_required
def api_booking_dispute(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not (current_user.id == booking.space.owner_id or current_user.id == booking.renter_id or current_user.is_admin):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    reason = sanitize_string(data.get("reason", "Host reported condition discrepancy"), max_length=500)
    action = data.get("action", "raise")

    if action == "resolve":
        booking.session_state = "checked_out"
        booking.escrow_status = "released"
        resolution = sanitize_string(data.get("resolution", "Dispute resolved amicably"), max_length=500)
        booking.dispute_status = "resolved"
        booking.dispute_resolution = resolution
        booking.dispute_resolved_at = datetime.utcnow()
        booking.escrow_released = True

        # Log escrow release on dispute resolution
        dispute_release_tx = EscrowTransaction(
            booking_id=booking.id,
            user_id=booking.renter_id,
            amount=booking.escrow_deposit_amount or 100.0,
            transaction_type="dispute_resolved_release",
            status="completed",
            reference_id=f"esc_res_{uuid.uuid4().hex[:12]}",
            details=f"Dispute resolved: {resolution}. Escrow released."
        )
        db.session.add(dispute_release_tx)

        # Notify host
        notif = Notification(
            user_id=booking.space.owner_id,
            type="dispute_resolved",
            title="Dispute Resolved",
            message=f"Dispute on Booking #{booking.id} was marked resolved: {resolution}.",
            priority="medium",
            action_url=f"/host/bookings/{booking.id}"
        )
        db.session.add(notif)
        db.session.commit()

        try:
            from backend.modules.auth.audit import record_audit
            record_audit("booking_dispute_resolved", user_id=current_user.id, details={"booking_id": booking.id, "resolution": resolution})
        except Exception:
            pass
        return jsonify({"success": True, "message": "Dispute resolved and escrow settlement completed.", "booking": booking.to_dict()}), 200

    booking.session_state = "disputed"
    booking.escrow_status = "held"
    booking.dispute_reason = reason
    booking.dispute_status = "investigating"
    booking.dispute_opened_at = datetime.utcnow()

    # Log escrow hold on dispute
    dispute_hold_tx = EscrowTransaction(
        booking_id=booking.id,
        user_id=booking.renter_id,
        amount=booking.escrow_deposit_amount or 100.0,
        transaction_type="dispute_hold",
        status="held",
        reference_id=f"esc_disp_{uuid.uuid4().hex[:12]}",
        details=f"Dispute opened: {reason}. Escrow held pending platform investigation."
    )
    db.session.add(dispute_hold_tx)

    notif = Notification(
        user_id=booking.space.owner_id,
        type="dispute",
        title="Dispute Opened",
        message=f"Dispute opened for Booking #{booking.id}: {reason}.",
        priority="urgent",
        action_url=f"/host/bookings/{booking.id}"
    )
    db.session.add(notif)
    db.session.commit()

    try:
        from backend.modules.auth.audit import record_audit
        record_audit("booking_dispute_opened", user_id=current_user.id, details={"booking_id": booking.id, "reason": reason})
    except Exception:
        pass

    return jsonify({
        "success": True,
        "message": f"Dispute recorded for Booking #{booking.id}. ₹100 escrow held pending verification.",
        "booking": booking.to_dict()
    }), 200
