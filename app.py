import json
from datetime import datetime, date

from flask import Flask, request, jsonify, render_template

from config import Config
from models import (db, User, CycleLog, SymptomEntry, PCODAssessment,
                     JournalEntry, Notification, ChatMessage)
from cycle_logic import calculate_phase, check_symptom, score_pcod_risk, analyze_mood
from chatbot import chat_reply


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------- Onboarding ----------
    @app.route("/")
    def onboarding():
        return render_template("onboarding.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html", active_tab="home")

    @app.route("/partner")
    def partner_page():
        return render_template("partner_dashboard.html", active_tab="home")

    @app.route("/chat")
    def chat_page():
        return render_template("chat.html", active_tab="chat")

    @app.route("/insights")
    def insights_page():
        return render_template("insights.html", active_tab="insights")

    @app.route("/settings")
    def settings_page():
        return render_template("settings.html", active_tab="settings")

    # ---------- Auth ----------
    @app.route("/api/register", methods=["POST"])
    def register():
        data = request.get_json(force=True)
        required = ["name", "email", "password", "role"]
        if not all(k in data for k in required):
            return jsonify({"error": f"Missing fields, need: {required}"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(name=data["name"], email=data["email"], role=data["role"])
        user.set_password(data["password"])

        if user.role == "self":
            user.generate_connect_code()

        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json(force=True)
        user = User.query.filter_by(email=data.get("email")).first()
        if not user or not user.check_password(data.get("password", "")):
            return jsonify({"error": "Invalid credentials"}), 401
        return jsonify(user.to_dict())

    # ---------- Partner connect ----------
    @app.route("/api/partner/link", methods=["POST"])
    def link_partner():
        """A 'partner' user redeems a 'self' user's connect_code."""
        data = request.get_json(force=True)
        partner_user_id = data.get("partner_user_id")
        connect_code = data.get("connect_code")

        self_user = User.query.filter_by(connect_code=connect_code, role="self").first()
        partner_user = User.query.get(partner_user_id)

        if not self_user or not partner_user:
            return jsonify({"error": "Invalid code or user"}), 404

        self_user.partner_id = partner_user.id
        partner_user.partner_id = self_user.id
        db.session.commit()
        return jsonify({"linked_with": self_user.name})

    # ---------- Cycle tracking ----------
    @app.route("/api/cycle/log", methods=["POST"])
    def log_cycle():
        data = request.get_json(force=True)
        user_id = data["user_id"]
        period_start = datetime.strptime(data["period_start"], "%Y-%m-%d").date()
        cycle_length = data.get("cycle_length", 28)

        entry = CycleLog(user_id=user_id, period_start=period_start, cycle_length=cycle_length)
        db.session.add(entry)
        db.session.commit()

        # Notify partner, if linked.
        user = User.query.get(user_id)
        if user and user.partner_id:
            phase_info = calculate_phase(period_start, cycle_length)
            note = Notification(
                recipient_id=user.partner_id,
                message=f"{user.name}'s cycle updated — currently in the {phase_info['phase']} phase. {phase_info['partner_tip']}",
            )
            db.session.add(note)
            db.session.commit()

        return jsonify({"status": "logged", "id": entry.id})

    @app.route("/api/cycle/phase/<int:user_id>")
    def get_phase(user_id):
        latest = (CycleLog.query.filter_by(user_id=user_id)
                  .order_by(CycleLog.period_start.desc()).first())
        if not latest:
            return jsonify({"error": "No cycle data logged yet"}), 404

        result = calculate_phase(latest.period_start, latest.cycle_length)
        return jsonify(result)

    @app.route("/api/cycle/history/<int:user_id>")
    def cycle_history(user_id):
        logs = (CycleLog.query.filter_by(user_id=user_id)
                .order_by(CycleLog.period_start.desc()).all())
        return jsonify([
            {"period_start": l.period_start.isoformat(), "cycle_length": l.cycle_length}
            for l in logs
        ])

    # ---------- "Is this normal?" ----------
    @app.route("/api/symptom/check", methods=["POST"])
    def symptom_check():
        data = request.get_json(force=True)
        user_id = data["user_id"]
        symptom_text = data["symptom_text"]

        result = check_symptom(symptom_text)
        entry = SymptomEntry(
            user_id=user_id, symptom_text=symptom_text,
            flagged_normal=result["flagged_normal"], note=result["note"],
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify(result)

    # ---------- PCOD/PCOS risk questionnaire ----------
    @app.route("/api/pcod/assess", methods=["POST"])
    def pcod_assess():
        data = request.get_json(force=True)
        user_id = data["user_id"]
        answers = data["answers"]  # dict of question_key -> bool

        result = score_pcod_risk(answers)
        entry = PCODAssessment(
            user_id=user_id, answers_json=json.dumps(answers),
            risk_score=result["risk_score"], risk_level=result["risk_level"],
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify(result)

    # ---------- Notifications (partner side) ----------
    @app.route("/api/notifications/<int:user_id>")
    def get_notifications(user_id):
        notes = (Notification.query.filter_by(recipient_id=user_id)
                 .order_by(Notification.created_at.desc()).all())
        return jsonify([
            {"id": n.id, "message": n.message, "is_read": n.is_read,
             "created_at": n.created_at.isoformat()}
            for n in notes
        ])

    # ---------- Journal / mood (stretch feature placeholder) ----------
    @app.route("/api/journal/add", methods=["POST"])
    def add_journal():
        data = request.get_json(force=True)
        mood_result = analyze_mood(data["text"])
        entry = JournalEntry(
            user_id=data["user_id"], text=data["text"],
            mood_label=mood_result["mood_label"], reason_note=mood_result["reason_note"],
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({
            "status": "saved", "id": entry.id,
            "mood_label": entry.mood_label, "reason_note": entry.reason_note,
        })

    @app.route("/api/journal/history/<int:user_id>")
    def journal_history(user_id):
        entries = (JournalEntry.query.filter_by(user_id=user_id)
                   .order_by(JournalEntry.created_at.desc()).limit(10).all())
        return jsonify([
            {"text": e.text, "mood_label": e.mood_label, "reason_note": e.reason_note,
             "created_at": e.created_at.isoformat()}
            for e in reversed(entries)
        ])

    @app.route("/api/user/regenerate_code", methods=["POST"])
    def regenerate_code():
        data = request.get_json(force=True)
        user = User.query.get(data["user_id"])
        if not user or user.role != "self":
            return jsonify({"error": "Not allowed"}), 400
        user.generate_connect_code()
        db.session.commit()
        return jsonify({"connect_code": user.connect_code})

    # ---------- AI companion chatbot ----------
    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json(force=True)
        user_id = data["user_id"]
        user_text = data["message"]

        # Save user's message
        db.session.add(ChatMessage(user_id=user_id, sender="user", text=user_text))

        # Pull latest cycle phase for context, if available
        phase_info = None
        latest = (CycleLog.query.filter_by(user_id=user_id)
                  .order_by(CycleLog.period_start.desc()).first())
        if latest:
            phase_info = calculate_phase(latest.period_start, latest.cycle_length)

        result = chat_reply(user_text, phase_info=phase_info, api_key=app.config.get("GROQ_API_KEY"))

        db.session.add(ChatMessage(user_id=user_id, sender="bot", text=result["reply"], mode=result["mode"]))
        db.session.commit()

        return jsonify(result)

    @app.route("/api/chat/history/<int:user_id>")
    def chat_history(user_id):
        msgs = (ChatMessage.query.filter_by(user_id=user_id)
                .order_by(ChatMessage.created_at.asc()).all())
        return jsonify([
            {"sender": m.sender, "text": m.text, "mode": m.mode, "created_at": m.created_at.isoformat()}
            for m in msgs
        ])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, host="0.0.0.0")
