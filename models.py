import secrets
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """A registered user. Role is 'self' (the person tracking) or 'partner'."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="self")

    # Connect-code system: a 'self' user generates a code, a 'partner' redeems it.
    connect_code = db.Column(db.String(10), unique=True, nullable=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    partner = db.relationship("User", remote_side=[id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_connect_code(self):
        self.connect_code = secrets.token_hex(4).upper()
        return self.connect_code

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "connect_code": self.connect_code,
            "partner_id": self.partner_id,
        }


class CycleLog(db.Model):
    """A logged period start (used to calculate the current phase)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=True)
    cycle_length = db.Column(db.Integer, default=28)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SymptomEntry(db.Model):
    """A logged symptom, checked against the 'is this normal?' rule engine."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    symptom_text = db.Column(db.Text, nullable=False)
    flagged_normal = db.Column(db.Boolean, default=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PCODAssessment(db.Model):
    """Result of the short PCOD/PCOS risk questionnaire. This is a risk
    indicator only, never a diagnosis."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    answers_json = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # low / moderate / high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JournalEntry(db.Model):
    """Stretch feature: free-text journal entry for mood detection."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    mood_label = db.Column(db.String(30), nullable=True)
    reason_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    """Notifications sent to a partner (phase updates, care tips, etc.)."""
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    """One turn of the companion chatbot conversation."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    text = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(10), nullable=True)  # 'comfort' or 'draft'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
