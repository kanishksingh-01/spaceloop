import json
import logging
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, render_template

from config import Config
from models import (db, User, CycleLog, DailyLog, CareAction, SymptomEntry,
                    PCODAssessment, JournalEntry, Notification, ChatMessage)
from cycle_logic import (calculate_phase, get_hormone_curves, check_symptom,
                         score_pcod_risk, analyze_mood)
from chatbot import chat_reply, get_partner_tip, generate_partner_chat_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_demo_accounts_if_empty()

    # ---------- Template Routes ----------
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
        return render_template("partner_dashboard.html", active_tab="partner")

    @app.route("/chat")
    def chat_page():
        return render_template("chat.html", active_tab="chat")

    @app.route("/insights")
    def insights_page():
        return render_template("insights.html", active_tab="insights")

    @app.route("/settings")
    def settings_page():
        return render_template("settings.html", active_tab="settings")

    # ---------- Authentication APIs ----------
    @app.route("/api/register", methods=["POST"])
    def register():
        data = request.get_json(force=True)
        required = ["name", "email", "password", "role"]
        if not all(k in data for k in required):
            return jsonify({"error": f"Missing required fields: {required}"}), 400

        if User.query.filter_by(email=data["email"].strip().lower()).first():
            return jsonify({"error": "An account with this email already exists"}), 409

        user = User(
            name=data["name"].strip(),
            email=data["email"].strip().lower(),
            role=data["role"]
        )
        user.set_password(data["password"])

        if user.role == "self":
            user.generate_connect_code()

        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json(force=True)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401

        return jsonify(user.to_dict())

    @app.route("/api/demo-login/<string:role>", methods=["POST"])
    def demo_login(role):
        """Quick 1-click login for demo purposes during hackathon judging."""
        email = "maya@cyclecare.dev" if role == "self" else "alex@cyclecare.dev"
        user = User.query.filter_by(email=email).first()
        if not user:
            _seed_demo_accounts_if_empty(force=True)
            user = User.query.filter_by(email=email).first()
        return jsonify(user.to_dict())

    # ---------- Partner Linking APIs ----------
    @app.route("/api/partner/link", methods=["POST"])
    def link_partner():
        data = request.get_json(force=True)
        partner_user_id = data.get("partner_user_id")
        connect_code = data.get("connect_code", "").strip().upper()

        self_user = User.query.filter_by(connect_code=connect_code, role="self").first()
        partner_user = db.session.get(User, partner_user_id)

        if not self_user or not partner_user:
            return jsonify({"error": "Invalid connect code or user ID"}), 404

        if partner_user.role != "partner":
            return jsonify({"error": "Only partner accounts can link with a code"}), 400

        self_user.partner_id = partner_user.id
        partner_user.partner_id = self_user.id

        # Notify self user
        note = Notification(
            recipient_id=self_user.id,
            message=f"{partner_user.name} linked their account with yours! They will now receive privacy-safe phase tips."
        )
        db.session.add(note)
        db.session.commit()

        return jsonify({
            "status": "linked",
            "linked_with": self_user.name,
            "self_user_id": self_user.id
        })

    @app.route("/api/partner/status/<int:user_id>")
    def partner_status(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        partner_name = None
        if user.partner_id:
            partner = db.session.get(User, user.partner_id)
            if partner:
                partner_name = partner.name

        return jsonify({
            "is_linked": bool(user.partner_id),
            "partner_name": partner_name,
            "connect_code": user.connect_code
        })

    @app.route("/api/partner/unlink", methods=["POST"])
    def unlink_partner():
        data = request.get_json(force=True)
        user = db.session.get(User, data.get("user_id"))
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.partner_id:
            partner = db.session.get(User, user.partner_id)
            if partner:
                partner.partner_id = None
            user.partner_id = None
            db.session.commit()

        return jsonify({"status": "unlinked"})

    # ---------- Cycle Tracking APIs ----------
    @app.route("/api/cycle/log", methods=["POST"])
    def log_cycle():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        period_start_str = data.get("period_start")
        cycle_length = int(data.get("cycle_length", 28))
        period_duration = int(data.get("period_duration", 5))

        if not user_id or not period_start_str:
            return jsonify({"error": "Missing user_id or period_start"}), 400

        period_start = datetime.strptime(period_start_str, "%Y-%m-%d").date()

        # Deduplication & Idempotency:
        # Check if an entry for this user and period_start already exists.
        existing = CycleLog.query.filter_by(user_id=user_id, period_start=period_start).first()
        if existing:
            existing.cycle_length = cycle_length
            existing.period_duration = period_duration
            existing.created_at = datetime.utcnow()
            entry = existing
            logger.info("Updated existing cycle log %s for user %s", entry.id, user_id)
        else:
            entry = CycleLog(
                user_id=user_id,
                period_start=period_start,
                cycle_length=cycle_length,
                period_duration=period_duration
            )
            db.session.add(entry)
            logger.info("Created new cycle log for user %s", user_id)

        db.session.commit()

        # Notify partner if linked
        user = db.session.get(User, user_id)
        if user and user.partner_id:
            phase_info = calculate_phase(period_start, cycle_length)
            note = Notification(
                recipient_id=user.partner_id,
                message=f"{user.name}'s cycle updated — currently in the {phase_info['phase']} phase. {phase_info['partner_tip']}"
            )
            db.session.add(note)
            db.session.commit()

        return jsonify({"status": "logged", "id": entry.id})

    @app.route("/api/cycle/phase/<int:user_id>")
    def get_phase(user_id):
        latest = (CycleLog.query.filter_by(user_id=user_id)
                  .order_by(CycleLog.created_at.desc()).first())
        if not latest:
            return jsonify({"error": "No cycle data logged yet"}), 404

        result = calculate_phase(latest.period_start, latest.cycle_length)
        result["period_start"] = latest.period_start.isoformat()
        result["period_duration"] = latest.period_duration
        return jsonify(result)

    @app.route("/api/cycle/history/<int:user_id>")
    def cycle_history(user_id):
        logs = (CycleLog.query.filter_by(user_id=user_id)
                .order_by(CycleLog.created_at.desc()).all())
        return jsonify([l.to_dict() for l in logs])

    @app.route("/api/cycle/hormones/<int:user_id>")
    def get_hormones(user_id):
        latest = (CycleLog.query.filter_by(user_id=user_id)
                  .order_by(CycleLog.created_at.desc()).first())
        if not latest:
            return jsonify({"error": "No cycle data logged yet"}), 404

        phase_info = calculate_phase(latest.period_start, latest.cycle_length)
        curves = get_hormone_curves(phase_info["day_in_cycle"], latest.cycle_length)
        return jsonify(curves)

    # ---------- Daily Check-in APIs ----------
    @app.route("/api/daily/log", methods=["POST"])
    def log_daily():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        log_date_str = data.get("log_date", date.today().isoformat())
        log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()

        # Upsert daily log for today
        existing = DailyLog.query.filter_by(user_id=user_id, log_date=log_date).first()
        symptoms_str = json.dumps(data.get("symptoms", []))

        if existing:
            existing.mood = data.get("mood")
            existing.energy_level = data.get("energy_level", 3)
            existing.flow_intensity = data.get("flow_intensity", "none")
            existing.symptoms_json = symptoms_str
            existing.note = data.get("note")
            entry = existing
        else:
            entry = DailyLog(
                user_id=user_id,
                log_date=log_date,
                mood=data.get("mood"),
                energy_level=data.get("energy_level", 3),
                flow_intensity=data.get("flow_intensity", "none"),
                symptoms_json=symptoms_str,
                note=data.get("note")
            )
            db.session.add(entry)

        db.session.commit()
        return jsonify({"status": "saved", "entry": entry.to_dict()})

    @app.route("/api/daily/history/<int:user_id>")
    def daily_history(user_id):
        days = (DailyLog.query.filter_by(user_id=user_id)
                .order_by(DailyLog.log_date.desc()).limit(30).all())
        return jsonify([d.to_dict() for d in reversed(days)])

    # ---------- Partner Empathy Bridge & Micro-Care APIs ----------
    @app.route("/api/partner/care-action", methods=["POST"])
    def send_care_action():
        """Partner sends a tangible micro-action (virtual heat pack, sweet treat, etc.)."""
        data = request.get_json(force=True)
        sender_id = data.get("sender_id")
        recipient_id = data.get("recipient_id")
        action_type = data.get("action_type")
        custom_message = data.get("custom_message", "")

        action = CareAction(
            sender_id=sender_id,
            recipient_id=recipient_id,
            action_type=action_type,
            custom_message=custom_message
        )
        db.session.add(action)

        # Also add a notification
        titles = {
            "heat_pack": "sent you a soothing Virtual Heat Pack",
            "sweet_treat": "sent you a Sweet Treat voucher & love",
            "warm_tea": "brewed a cup of calming Herbal Tea for you",
            "dinner_taken_care": "promised: 'Dinner is on me tonight!'",
            "gentle_hug": "sent a warm, gentle squeeze & reassurance"
        }
        sender = db.session.get(User, sender_id)
        sender_name = sender.name if sender else "Your partner"
        desc = titles.get(action_type, "sent you a token of care")

        note = Notification(
            recipient_id=recipient_id,
            message=f"{sender_name} {desc}! {custom_message}"
        )
        db.session.add(note)
        db.session.commit()

        return jsonify({"status": "sent", "action": action.to_dict()})

    @app.route("/api/partner/care-actions/<int:user_id>")
    def get_care_actions(user_id):
        actions = (CareAction.query.filter_by(recipient_id=user_id)
                   .order_by(CareAction.created_at.desc()).limit(10).all())
        return jsonify([a.to_dict() for a in actions])

    @app.route("/api/partner/care-action/<int:action_id>/ack", methods=["POST"])
    def ack_care_action(action_id):
        action = db.session.get(CareAction, action_id)
        if action:
            action.is_viewed = True
            db.session.commit()
        return jsonify({"status": "acknowledged"})

    @app.route("/api/partner/view/<int:partner_user_id>")
    def partner_view(partner_user_id):
        """
        Returns derived, privacy-safe empathy view for the partner.
        Never reveals raw journal entries or chat logs.
        """
        partner_user = db.session.get(User, partner_user_id)
        if not partner_user or not partner_user.partner_id:
            return jsonify({"error": "No linked partner found"}), 404

        self_user = db.session.get(User, partner_user.partner_id)
        if not self_user:
            return jsonify({"error": "Linked user not found"}), 404

        latest_cycle = (CycleLog.query.filter_by(user_id=self_user.id)
                        .order_by(CycleLog.created_at.desc()).first())

        phase_data = None
        if latest_cycle:
            phase_data = calculate_phase(latest_cycle.period_start, latest_cycle.cycle_length)

        # Get latest daily log for mood tone without raw notes
        latest_daily = (DailyLog.query.filter_by(user_id=self_user.id)
                        .order_by(DailyLog.log_date.desc()).first())

        # Recent chats with AI companion for privacy-safe empathy briefing
        recent_chats = (ChatMessage.query.filter_by(user_id=self_user.id)
                        .order_by(ChatMessage.created_at.desc()).limit(12).all())
        chat_list = [m.to_dict() for m in reversed(recent_chats)]

        chat_summary = generate_partner_chat_summary(
            messages=chat_list,
            phase_info=phase_data,
            user_name=self_user.name,
            api_key=app.config.get("GROQ_API_KEY")
        )

        phase_name = phase_data["phase"] if phase_data else "Not yet logged"

        # Plain-English human guidance for partner ("thoda easy to understand")
        easy_phase_guide = {
            "Menstrual": {
                "simple_title": "Rest & Comfort Time",
                "season_label": "Inner Winter (Period Days)",
                "simple_meaning": f"Her period is active right now. Her body is working hard, dealing with cramps or fatigue, and needs extra warmth, rest, and low stress.",
                "her_vibe_summary": "Lower energy, quiet mood, craving coziness and comfort.",
                "primary_action": "Bring a hot water bottle, keep a soft blanket nearby, and take care of dinner without waiting to be asked.",
                "vibe_icon": "🛏️"
            },
            "Follicular": {
                "simple_title": "Fresh Energy & Bright Mood",
                "season_label": "Inner Spring (Post-Period Renewal)",
                "simple_meaning": f"Her period is over and fresh energy is kicking in! Her mental clarity, endurance, and cheerful optimism are rising every day.",
                "her_vibe_summary": "High stamina, motivated, chatty, and excited to start new things.",
                "primary_action": "Plan a fun outing or dinner, go on a walk together, and celebrate her ideas.",
                "vibe_icon": "⚡"
            },
            "Ovulation": {
                "simple_title": "Peak Energy & Glowing Days",
                "season_label": "Inner Summer (Monthly Energy Peak)",
                "simple_meaning": f"This is her monthly high point for energy, confidence, and social mood. She feels radiant, expressive, and connected.",
                "her_vibe_summary": "Magnetic, confident, affectionate, and loves deep conversations.",
                "primary_action": "Give genuine compliments, be attentive and present, and plan special quality time together.",
                "vibe_icon": "✨"
            },
            "Luteal": {
                "simple_title": "Winding Down & Emotional Care",
                "season_label": "Inner Autumn (Pre-Period Wind-down)",
                "simple_meaning": f"Her body is naturally slowing down before the next cycle. Shifting hormones can bring fatigue, bloating, or emotional sensitivity.",
                "her_vibe_summary": "More sensitive, lower social battery, craving comfort snacks and quiet time.",
                "primary_action": "Be extra patient and understanding. Never say 'are you just PMSing?'. Offer comfort treats and gentle hugs.",
                "vibe_icon": "🧸"
            }
        }

        phase_guide = easy_phase_guide.get(phase_name, {
            "simple_title": "Daily Wellness Check",
            "season_label": "Cycle Tracking Active",
            "simple_meaning": "Cycle details are updating. Stay attentive and supportive.",
            "her_vibe_summary": "Check in gently with her today.",
            "primary_action": "Ask how her day was and offer a warm gesture.",
            "vibe_icon": "🌸"
        })

        vibe = {
            "partner_name": self_user.name,
            "self_user_id": self_user.id,
            "phase": phase_name,
            "phase_desc": phase_data["phase_desc"] if phase_data else "Awaiting cycle start date",
            "day_in_cycle": phase_data["day_in_cycle"] if phase_data else None,
            "days_until_next": phase_data["days_until_next"] if phase_data else None,
            "partner_tip": phase_data["partner_tip"] if phase_data else "Check in gently today.",
            "energy_forecast": phase_data["energy_forecast"] if phase_data else "Normal",
            "recent_mood": latest_daily.mood if latest_daily else "Balanced",
            "recent_energy": latest_daily.energy_level if latest_daily else 3,
            # Human-friendly fields
            "simple_title": phase_guide["simple_title"],
            "season_label": phase_guide["season_label"],
            "simple_meaning": phase_guide["simple_meaning"],
            "her_vibe_summary": phase_guide["her_vibe_summary"],
            "primary_action": phase_guide["primary_action"],
            "vibe_icon": phase_guide["vibe_icon"],
            # Companion Chat Summary
            "chat_summary": chat_summary
        }
        return jsonify(vibe)

    # ---------- Symptom Checker APIs ----------
    @app.route("/api/symptom/check", methods=["POST"])
    def symptom_check():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        symptom_text = data.get("symptom_text", "").strip()

        if not symptom_text:
            return jsonify({"error": "Symptom description is required"}), 400

        result = check_symptom(symptom_text)
        entry = SymptomEntry(
            user_id=user_id,
            symptom_text=symptom_text,
            flagged_normal=result["flagged_normal"],
            severity=result.get("severity", "normal"),
            note=result["note"]
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify(result)

    # ---------- PCOD/PCOS Screener APIs ----------
    @app.route("/api/pcod/assess", methods=["POST"])
    def pcod_assess():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        answers = data.get("answers", {})

        result = score_pcod_risk(answers)
        entry = PCODAssessment(
            user_id=user_id,
            answers_json=json.dumps(answers),
            risk_score=result["risk_score"],
            risk_level=result["risk_level"]
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify(result)

    # ---------- Private Journal APIs ----------
    @app.route("/api/journal/add", methods=["POST"])
    def add_journal():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Journal text cannot be empty"}), 400

        mood_result = analyze_mood(text)
        entry = JournalEntry(
            user_id=user_id,
            text=text,
            mood_label=mood_result["mood_label"],
            reason_note=mood_result["reason_note"]
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify({
            "status": "saved",
            "id": entry.id,
            "mood_label": entry.mood_label,
            "reason_note": entry.reason_note
        })

    @app.route("/api/journal/history/<int:user_id>")
    def journal_history(user_id):
        entries = (JournalEntry.query.filter_by(user_id=user_id)
                   .order_by(JournalEntry.created_at.desc()).limit(15).all())
        return jsonify([
            {"text": e.text, "mood_label": e.mood_label, "reason_note": e.reason_note,
             "created_at": e.created_at.strftime("%b %d, %I:%M %p")}
            for e in reversed(entries)
        ])

    # ---------- Notifications APIs ----------
    @app.route("/api/notifications/<int:user_id>")
    def get_notifications(user_id):
        notes = (Notification.query.filter_by(recipient_id=user_id)
                 .order_by(Notification.created_at.desc()).limit(20).all())
        return jsonify([
            {"id": n.id, "message": n.message, "is_read": n.is_read,
             "created_at": n.created_at.strftime("%b %d, %I:%M %p")}
            for n in notes
        ])

    @app.route("/api/notifications/mark-read", methods=["POST"])
    def mark_notifications_read():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        Notification.query.filter_by(recipient_id=user_id, is_read=False).update({"is_read": True})
        db.session.commit()
        return jsonify({"status": "marked_read"})

    # ---------- User Settings & Security APIs ----------
    @app.route("/api/user/regenerate_code", methods=["POST"])
    def regenerate_code():
        data = request.get_json(force=True)
        user = db.session.get(User, data.get("user_id"))
        if not user or user.role != "self":
            return jsonify({"error": "Only self users can generate connect codes"}), 400

        user.generate_connect_code()
        db.session.commit()
        return jsonify({"connect_code": user.connect_code})

    @app.route("/api/user/wipe-data", methods=["POST"])
    def wipe_data():
        """Privacy-first guarantee: Full purge of user's private cycle and journal records."""
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        CycleLog.query.filter_by(user_id=user_id).delete()
        DailyLog.query.filter_by(user_id=user_id).delete()
        JournalEntry.query.filter_by(user_id=user_id).delete()
        SymptomEntry.query.filter_by(user_id=user_id).delete()
        PCODAssessment.query.filter_by(user_id=user_id).delete()
        ChatMessage.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        return jsonify({"status": "purged", "message": "All private health records have been permanently erased."})

    # ---------- AI Companion Chatbot APIs ----------
    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json(force=True)
        user_id = data.get("user_id")
        user_text = data.get("message", "").strip()
        requested_mode = data.get("mode")
        companion_name = data.get("companion_name", "Aura")

        if not user_text:
            return jsonify({"error": "Message text is required"}), 400

        # Save user's message
        db.session.add(ChatMessage(user_id=user_id, sender="user", text=user_text, mode=requested_mode or "comfort"))

        # Pull latest cycle phase context - ORDERED BY created_at.desc() (FIXED!)
        phase_info = None
        latest = (CycleLog.query.filter_by(user_id=user_id)
                  .order_by(CycleLog.created_at.desc()).first())
        if latest:
            phase_info = calculate_phase(latest.period_start, latest.cycle_length)

        result = chat_reply(
            user_text,
            phase_info=phase_info,
            api_key=app.config.get("GROQ_API_KEY"),
            requested_mode=requested_mode,
            companion_name=companion_name
        )

        db.session.add(ChatMessage(
            user_id=user_id,
            sender="bot",
            text=result["reply"],
            mode=result["mode"]
        ))

        # Strict privacy invariant: Send only derived care tips to partner, never the raw text
        user = db.session.get(User, user_id)
        if user and user.partner_id:
            tip = get_partner_tip(user_text, result["mode"])
            if tip:
                db.session.add(Notification(
                    recipient_id=user.partner_id,
                    message=f"Care Tip for {user.name}: {tip}"
                ))

        db.session.commit()
        return jsonify(result)

    @app.route("/api/chat/history/<int:user_id>")
    def chat_history(user_id):
        msgs = (ChatMessage.query.filter_by(user_id=user_id)
                .order_by(ChatMessage.created_at.asc()).all())
        return jsonify([
            {"sender": m.sender, "text": m.text, "mode": m.mode,
             "created_at": m.created_at.strftime("%I:%M %p")}
            for m in msgs
        ])

    @app.route("/api/chat/clear/<int:user_id>", methods=["POST"])
    def clear_chat(user_id):
        ChatMessage.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"status": "cleared"})

    # ---------- Insights Analytics API ----------
    @app.route("/api/insights/data/<int:user_id>")
    def insights_data(user_id):
        logs = (CycleLog.query.filter_by(user_id=user_id)
                .order_by(CycleLog.created_at.desc()).all())
        dailies = (DailyLog.query.filter_by(user_id=user_id)
                   .order_by(DailyLog.log_date.desc()).limit(30).all())

        lengths = [l.cycle_length for l in logs]
        avg_length = round(sum(lengths) / len(lengths), 1) if lengths else 28
        variation = (max(lengths) - min(lengths)) if len(lengths) > 1 else 0

        # Mood distribution
        moods = {}
        for d in dailies:
            if d.mood:
                moods[d.mood] = moods.get(d.mood, 0) + 1

        return jsonify({
            "total_cycles_logged": len(logs),
            "average_cycle_length": avg_length,
            "cycle_variation_days": variation,
            "is_regular": variation <= 4,
            "mood_breakdown": moods,
            "recent_cycles": [l.to_dict() for l in logs[:6]]
        })

    return app


def _seed_demo_accounts_if_empty(force=False):
    """Pre-seeds demonstration accounts to make live judging effortless."""
    try:
        maya = User.query.filter_by(email="maya@cyclecare.dev").first()
        if not maya or force:
            if not maya:
                maya = User(name="Maya", email="maya@cyclecare.dev", role="self")
                maya.set_password("demo1234")
                maya.connect_code = "CARE-2026"
                db.session.add(maya)
                db.session.flush()

            alex = User.query.filter_by(email="alex@cyclecare.dev").first()
            if not alex:
                alex = User(name="Alex", email="alex@cyclecare.dev", role="partner")
                alex.set_password("demo1234")
                alex.partner_id = maya.id
                db.session.add(alex)
                db.session.flush()
                maya.partner_id = alex.id

            # Seed a cycle log for Maya
            if CycleLog.query.filter_by(user_id=maya.id).count() == 0:
                recent_period = date.today() - timedelta(days=12)
                db.session.add(CycleLog(
                    user_id=maya.id,
                    period_start=recent_period,
                    cycle_length=28,
                    period_duration=5,
                    notes="Baseline normal cycle"
                ))

            # Seed a sample daily log
            if DailyLog.query.filter_by(user_id=maya.id).count() == 0:
                db.session.add(DailyLog(
                    user_id=maya.id,
                    log_date=date.today(),
                    mood="peaceful",
                    energy_level=4,
                    flow_intensity="none",
                    symptoms_json='["mild energy boost"]',
                    note="Feeling productive and clear-headed today."
                ))

            db.session.commit()
    except Exception as e:
        logger.warning("Could not auto-seed demo accounts: %s", e)
        db.session.rollback()


app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print(f"\n🚀 Cycle Care is running at: http://localhost:{port}\n")
    app.run(debug=True, port=port, host="0.0.0.0")

