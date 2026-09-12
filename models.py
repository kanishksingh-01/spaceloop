import secrets
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="self")  # 'self' or 'partner'
    connect_code = db.Column(db.String(16), unique=True, nullable=True, index=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cycle_logs = db.relationship("CycleLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    daily_logs = db.relationship("DailyLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    symptoms = db.relationship("SymptomEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    assessments = db.relationship("PCODAssessment", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    journal_entries = db.relationship("JournalEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_connect_code(self) -> str:
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = "CARE-" + "".join(secrets.choice(chars) for _ in range(4))
        self.connect_code = code
        return code

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "connect_code": self.connect_code,
            "partner_id": self.partner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CycleLog(db.Model):
    __tablename__ = "cycle_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=False, index=True)
    cycle_length = db.Column(db.Integer, nullable=False, default=28)
    period_duration = db.Column(db.Integer, nullable=False, default=5)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "period_start": self.period_start.isoformat(),
            "cycle_length": self.cycle_length,
            "period_duration": self.period_duration,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class DailyLog(db.Model):
    """10-second daily check-in for holistic cycle correlation (mood, energy, flow)."""
    __tablename__ = "daily_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    log_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    mood = db.Column(db.String(30), nullable=True)  # 'radiant', 'peaceful', 'sensitive', 'exhausted', 'irritable'
    energy_level = db.Column(db.Integer, nullable=False, default=3)  # 1 to 5
    flow_intensity = db.Column(db.String(20), nullable=True, default="none")  # none, spotting, light, medium, heavy
    symptoms_json = db.Column(db.Text, nullable=True, default="[]")  # JSON list of tags e.g. ["cramps", "bloating"]
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "log_date": self.log_date.isoformat(),
            "mood": self.mood,
            "energy_level": self.energy_level,
            "flow_intensity": self.flow_intensity,
            "symptoms": self.symptoms_json,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }


class CareAction(db.Model):
    """Micro-care actions sent by partner to show real-time tangible empathy."""
    __tablename__ = "care_actions"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False)  # 'heat_pack', 'sweet_treat', 'warm_tea', 'dinner_taken_care', 'gentle_hug'
    custom_message = db.Column(db.String(255), nullable=True)
    is_viewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "action_type": self.action_type,
            "custom_message": self.custom_message,
            "is_viewed": self.is_viewed,
            "created_at": self.created_at.isoformat(),
        }


class SymptomEntry(db.Model):
    __tablename__ = "symptom_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    symptom_text = db.Column(db.Text, nullable=False)
    flagged_normal = db.Column(db.Boolean, default=True)
    severity = db.Column(db.String(20), default="normal")  # 'normal', 'monitor', 'urgent'
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symptom_text": self.symptom_text,
            "flagged_normal": self.flagged_normal,
            "severity": self.severity,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }


class PCODAssessment(db.Model):
    __tablename__ = "pcod_assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    answers_json = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # 'low', 'moderate', 'elevated'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
        }


class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    mood_label = db.Column(db.String(50), nullable=True)
    reason_note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "mood_label": self.mood_label,
            "reason_note": self.reason_note,
            "created_at": self.created_at.isoformat(),
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    text = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(30), default="comfort")  # comfort, calm, draft, qa
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sender": self.sender,
            "text": self.text,
            "mode": self.mode,
            "created_at": self.created_at.isoformat(),
        }
