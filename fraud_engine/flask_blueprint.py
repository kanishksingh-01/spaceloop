"""
SpaceLoop Fraud Engine Flask Blueprint Adapter
Provides zero-overhead in-process routing for /fraud endpoints on the primary Flask application.
Delegates directly to the unified FraudService pipeline.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db
from fraud_engine.schemas import FraudEventInput, ScoreRequest, FraudEventType
from fraud_engine.service import FraudService

api_fraud_flask = Blueprint("api_fraud_flask", __name__, url_prefix="/fraud")


@api_fraud_flask.route("/health", methods=["GET"])
def flask_fraud_health():
    return jsonify({
        "status": "healthy",
        "service": "SpaceLoop Fraud & Trust Engine",
        "version": "1.0.0",
        "framework": "FastAPI + Flask Adapter + Pandas + NumPy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@api_fraud_flask.route("/events", methods=["POST"])
def flask_ingest_event():
    data = request.get_json(silent=True) or {}
    try:
        event_input = FraudEventInput(**data)
        res = FraudService.ingest_event(event_input, db.session)
        return jsonify(res.model_dump()), 201
    except Exception as e:
        return jsonify({"error": f"Failed to ingest event: {str(e)}"}), 400


@api_fraud_flask.route("/score", methods=["POST"])
def flask_score_event():
    data = request.get_json(silent=True) or {}
    try:
        score_req = ScoreRequest(**data)
        res = FraudService.score_event(score_req, db.session)
        return jsonify(res.model_dump()), 200
    except Exception as e:
        return jsonify({"error": f"Failed to score event: {str(e)}"}), 400


@api_fraud_flask.route("/alerts", methods=["GET"])
def flask_list_alerts():
    status = request.args.get("status")
    severity = request.args.get("severity")
    limit = int(request.args.get("limit", 50))
    alerts = FraudService.get_alerts(db.session, status=status, severity=severity, limit=limit)
    return jsonify([a.model_dump() for a in alerts]), 200


@api_fraud_flask.route("/alerts/<alert_id>", methods=["GET"])
def flask_get_alert_detail(alert_id):
    alert = FraudService.get_alert_by_id(db.session, alert_id)
    if not alert:
        return jsonify({"error": f"Fraud alert '{alert_id}' not found."}), 404
    return jsonify(alert.model_dump()), 200
