"""
SpaceLoop System, AI Concierge, KYC & Analytics REST Blueprint
Handles platform telemetry, health checks, dashboard metrics, LoopBot chat,
India Stack KYC verification, and dynamic yield estimation.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from models import db, Booking, Space, SpaceInquiry, User
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

    seeker_bookings = Booking.query.filter_by(renter_id=active_user_id).order_by(Booking.created_at.desc()).all()
    host_spaces = Space.query.filter_by(owner_id=active_user_id).order_by(Space.created_at.desc()).all()
    host_bookings = Booking.query.join(Space).filter(Space.owner_id == active_user_id).order_by(Booking.created_at.desc()).all()

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
    category = sanitize_string(data.get("category", "Studio"), max_length=50)
    sqft = validate_numeric(data.get("sqft"), min_val=20, max_val=50000, default=300)
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
    return jsonify(estimate)


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
        return jsonify({"reply": "Hello! How can I assist you with SpaceLoop today?"}), 200

    user_context = None
    if current_user.is_authenticated:
        user_context = {
            "user_name": current_user.name,
            "role": current_user.role,
            "is_verified": current_user.is_student_verified or current_user.is_host_verified
        }

    response = concierge_chat(messages, context_data=user_context)
    return jsonify({"reply": response})


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
    user.discom_provider = discom_res["discom_provider"]
    user.discom_ca_masked = discom_res["discom_ca_masked"]
    user.upi_verified = True
    user.upi_vpa_masked = upi_res["upi_vpa_masked"]
    user.bank_beneficiary_name = upi_res["bank_beneficiary_name"]
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
        "database": db_status,
        "ai_engine": ai_status,
        "server_timestamp": datetime.utcnow().isoformat()
    }), status_code
