"""
SpaceLoop Trust & Safety REST API Blueprint
Admin operations for risk triage, network graph inspection, and manual override controls.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, RiskAssessment, User, Space, Booking, Review, DeviceSession
from backend.modules.trust_safety import TrustSafetyEngine, build_marketplace_graph
from security import sanitize_string

api_v1_trust_safety = Blueprint("api_v1_trust_safety", __name__, url_prefix="/api/v1/trust-safety")


def require_admin():
    if not current_user.is_authenticated or not (getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"):
        return jsonify({"error": "Admin Trust & Safety authorization required."}), 403
    return None


@api_v1_trust_safety.route("/assessments", methods=["GET"])
@login_required
def get_assessments():
    admin_err = require_admin()
    if admin_err:
        return admin_err

    risk_level = request.args.get("risk_level")
    entity_type = request.args.get("entity_type")
    status = request.args.get("status")

    query = RiskAssessment.query

    if risk_level and risk_level != "all":
        query = query.filter(RiskAssessment.risk_level == risk_level)
    if entity_type and entity_type != "all":
        query = query.filter(RiskAssessment.entity_type == entity_type)
    if status == "unresolved":
        query = query.filter(RiskAssessment.action_taken.in_(["pending", "held", "flagged"]))
    elif status and status != "all":
        query = query.filter(RiskAssessment.action_taken == status)

    assessments = query.order_by(RiskAssessment.created_at.desc()).limit(100).all()
    return jsonify({
        "status": "success",
        "success": True,
        "total": len(assessments),
        "assessments": [a.to_dict() for a in assessments]
    }), 200


@api_v1_trust_safety.route("/assessments/<int:assessment_id>", methods=["GET"])
@login_required
def get_assessment_detail(assessment_id):
    admin_err = require_admin()
    if admin_err:
        return admin_err

    assessment = RiskAssessment.query.get_or_404(assessment_id)
    entity_data = None

    if assessment.entity_type == "space":
        sp = Space.query.get(assessment.entity_id)
        entity_data = sp.to_dict() if sp else None
    elif assessment.entity_type == "booking":
        bk = Booking.query.get(assessment.entity_id)
        entity_data = bk.to_dict() if bk else None
    elif assessment.entity_type == "user":
        u = User.query.get(assessment.entity_id)
        entity_data = u.to_dict() if u else None

    return jsonify({
        "status": "success",
        "assessment": assessment.to_dict(),
        "entity": entity_data
    }), 200


@api_v1_trust_safety.route("/assessments/<int:assessment_id>/action", methods=["POST"])
@login_required
def take_assessment_action(assessment_id):
    admin_err = require_admin()
    if admin_err:
        return admin_err

    assessment = RiskAssessment.query.get_or_404(assessment_id)
    data = request.get_json(silent=True) or {}

    action = sanitize_string(data.get("action", ""), max_length=40)
    notes = sanitize_string(data.get("notes", ""), max_length=500)

    valid_actions = {
        "override_allow": "overridden",
        "confirm_block": "account_restricted",
        "hold_escrow": "escrow_held",
        "request_id": "verification_requested",
        "resolve": "dismissed",
        "escrow_held": "escrow_held",
        "held": "escrow_held",
        "hold_transaction": "escrow_held",
        "dismissed": "dismissed",
        "allow": "dismissed",
        "verification_requested": "verification_requested",
        "request_verification": "verification_requested",
        "mfa_enforced": "mfa_enforced",
        "require_mfa": "mfa_enforced",
        "account_restricted": "account_restricted",
        "restrict_action": "account_restricted",
        "blocked": "account_restricted",
    }

    if action not in valid_actions:
        return jsonify({"error": f"Invalid action. Expected one of: {list(valid_actions.keys())}"}), 400

    assessment.action_taken = valid_actions[action]
    assessment.reviewer_id = current_user.id
    assessment.reviewer_notes = notes
    assessment.reviewed_at = datetime.utcnow()

    # Apply enforcement if blocking or holding
    if action == "confirm_block":
        if assessment.entity_type == "space":
            space = Space.query.get(assessment.entity_id)
            if space:
                space.is_active = False
        elif assessment.entity_type == "user":
            user = User.query.get(assessment.entity_id)
            if user:
                user.is_active = False
        elif assessment.entity_type == "booking":
            booking = Booking.query.get(assessment.entity_id)
            if booking:
                booking.status = "cancelled"
                booking.session_state = "cancelled"

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Action '{action}' successfully recorded by {current_user.name}.",
        "assessment": assessment.to_dict()
    }), 200


@api_v1_trust_safety.route("/graph/<entity_type>/<int:entity_id>", methods=["GET"])
@login_required
def get_entity_graph(entity_type, entity_id):
    admin_err = require_admin()
    if admin_err:
        return admin_err

    node_id = f"{entity_type}:{entity_id}"
    graph = build_marketplace_graph()
    subgraph = graph.extract_subgraph(node_id, hops=2)

    return jsonify({
        "status": "success",
        "success": True,
        "graph": subgraph
    }), 200


@api_v1_trust_safety.route("/stats", methods=["GET"])
@login_required
def get_trust_safety_stats():
    admin_err = require_admin()
    if admin_err:
        return admin_err

    total = RiskAssessment.query.count()
    high_risk = RiskAssessment.query.filter_by(risk_level="high_risk").count()
    suspicious = RiskAssessment.query.filter_by(risk_level="suspicious").count()
    unusual = RiskAssessment.query.filter_by(risk_level="unusual").count()
    normal = RiskAssessment.query.filter_by(risk_level="normal").count()
    pending = RiskAssessment.query.filter(RiskAssessment.action_taken.in_(["pending", "flagged", "held"])).count()

    return jsonify({
        "status": "success",
        "success": True,
        "stats": {
            "total_assessments": total,
            "high_risk_count": high_risk,
            "suspicious_count": suspicious,
            "unusual_count": unusual,
            "normal_count": normal,
            "pending_action_count": pending
        }
    }), 200


@api_v1_trust_safety.route("/evaluate", methods=["POST"])
@login_required
def on_demand_evaluate():
    """
    On-demand risk assessment trigger for any entity.
    """
    admin_err = require_admin()
    if admin_err:
        return admin_err

    data = request.get_json(silent=True) or {}
    entity_type = data.get("entity_type")
    entity_id = data.get("entity_id")

    if not entity_type or not entity_id:
        return jsonify({"error": "entity_type and entity_id required."}), 400

    assessment = None
    if entity_type == "space":
        space = Space.query.get_or_404(int(entity_id))
        assessment = TrustSafetyEngine.evaluate_listing(space, space.owner)
    elif entity_type == "booking":
        booking = Booking.query.get_or_404(int(entity_id))
        assessment = TrustSafetyEngine.evaluate_booking(
            seeker=booking.renter,
            space=booking.space,
            hours=booking.hours_booked,
            total_price=booking.total_price
        )

    if not assessment:
        return jsonify({"error": f"Evaluation for {entity_type} not supported."}), 400

    return jsonify({
        "status": "success",
        "assessment": assessment.to_dict()
    }), 200
