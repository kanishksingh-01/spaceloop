import json
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    name = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(60), default="")
    last_name = db.Column(db.String(60), default="")
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="both")  # 'owner', 'seeker', 'both'
    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    bio = db.Column(db.Text, default="")
    phone = db.Column(db.String(40), default="")
    avatar_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Verification & KYC (India Stack)
    is_student_verified = db.Column(db.Boolean, default=False)
    college_name = db.Column(db.String(150), default="")
    college_email = db.Column(db.String(120), default="")
    student_id_masked = db.Column(db.String(50), default="")
    
    is_aadhaar_verified = db.Column(db.Boolean, default=False)
    aadhaar_masked = db.Column(db.String(30), default="")  # e.g. 'XXXX-XXXX-4821' (DPDP Compliant)
    aadhaar_token_hash = db.Column(db.String(64), default="")

    is_host_verified = db.Column(db.Boolean, default=False)
    discom_provider = db.Column(db.String(80), default="")  # e.g. 'BESCOM', 'TPDDL'
    discom_ca_masked = db.Column(db.String(40), default="")
    upi_verified = db.Column(db.Boolean, default=False)
    upi_vpa_masked = db.Column(db.String(80), default="")
    bank_beneficiary_name = db.Column(db.String(120), default="")

    # Objective Telemetry & Trust Index (OTI)
    objective_trust_score = db.Column(db.Float, default=98.5)
    on_time_vacate_rate = db.Column(db.Float, default=100.0)
    cleanliness_match_rate = db.Column(db.Float, default=99.0)
    total_completed_hours = db.Column(db.Float, default=0.0)
    dispute_count = db.Column(db.Integer, default=0)

    # Multi-Factor Authentication (MFA / TOTP RFC 6238)
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    totp_secret = db.Column(db.String(256), nullable=True)  # Fernet encrypted at rest

    # Relationships
    spaces = db.relationship("Space", backref="owner", lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="renter", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="user", lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship("SpaceInquiry", backref="user", lazy=True, cascade="all, delete-orphan")
    password_reset_tokens = db.relationship("PasswordResetToken", backref="user", lazy=True, cascade="all, delete-orphan")
    email_verification_tokens = db.relationship("EmailVerificationToken", backref="user", lazy=True, cascade="all, delete-orphan")
    mfa_recovery_codes = db.relationship("MFARecoveryCode", backref="user", lazy=True, cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True, cascade="all, delete-orphan")

    @property
    def is_host(self) -> bool:
        return self.role in ("host", "owner", "both") or self.is_admin

    @is_host.setter
    def is_host(self, value: bool):
        if value:
            self.role = "both" if self.role in ("seeker", "both") else "host"
        elif self.role == "both":
            self.role = "seeker"

    @property
    def is_seeker(self) -> bool:
        return self.role in ("seeker", "both") or self.is_admin

    @is_seeker.setter
    def is_seeker(self, value: bool):
        if value:
            self.role = "both" if self.role in ("host", "both", "owner") else "seeker"
        elif self.role == "both":
            self.role = "host"

    @property
    def full_name(self) -> str:
        combined = f"{self.first_name} {self.last_name}".strip()
        return combined if combined else self.name

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "public_id": self.public_id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "role": self.role,
            "is_host": self.is_host,
            "is_seeker": self.is_seeker,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "mfa_enabled": bool(self.mfa_enabled),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "bio": self.bio,
            "phone": self.phone,
            "avatar_url": self.avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={self.name}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "spaces_count": len(self.spaces),
            "bookings_count": len(self.bookings),
            # Verification statuses
            "is_student_verified": self.is_student_verified,
            "college_name": self.college_name,
            "college_email": self.college_email,
            "student_id_masked": self.student_id_masked,
            "is_aadhaar_verified": self.is_aadhaar_verified,
            "aadhaar_masked": self.aadhaar_masked,
            "is_host_verified": self.is_host_verified,
            "discom_provider": self.discom_provider,
            "discom_ca_masked": self.discom_ca_masked,
            "upi_verified": self.upi_verified,
            "upi_vpa_masked": self.upi_vpa_masked,
            "bank_beneficiary_name": self.bank_beneficiary_name,
            # Objective Telemetry
            "objective_trust_score": round(self.objective_trust_score if self.objective_trust_score <= 100.0 else self.objective_trust_score / 10.0, 1) if self.objective_trust_score is not None else 98.5,
            "on_time_vacate_rate": round(self.on_time_vacate_rate, 1) if self.on_time_vacate_rate is not None else 100.0,
            "cleanliness_match_rate": round(self.cleanliness_match_rate, 1) if self.cleanliness_match_rate is not None else 99.0,
            "total_completed_hours": round(self.total_completed_hours, 1) if self.total_completed_hours is not None else 0.0,
            "dispute_count": self.dispute_count or 0,
            "oti_breakdown": {
                "total_score": round(self.objective_trust_score if self.objective_trust_score <= 100.0 else self.objective_trust_score / 10.0, 1) if self.objective_trust_score is not None else 98.5,
                "punctuality": {
                    "score": round(self.on_time_vacate_rate, 1) if self.on_time_vacate_rate is not None else 100.0,
                    "weight": "35%",
                    "description": "Measures on-time departure within the booked micro-lease window."
                },
                "cleanliness": {
                    "score": round(self.cleanliness_match_rate, 1) if self.cleanliness_match_rate is not None else 99.0,
                    "weight": "35%",
                    "description": "Computer Vision delta verifying furniture unchanged, lights off, and zero trash left behind."
                },
                "identity_trust": {
                    "score": 100.0 if (self.is_aadhaar_verified or self.is_student_verified or self.is_host_verified) else 70.0,
                    "weight": "20%",
                    "description": "DigiLocker Aadhaar, student university SSO, or Discom utility meter verification."
                },
                "dispute_history": {
                    "score": max(0.0, 100.0 - min((self.dispute_count or 0) * 15.0, 50.0)),
                    "weight": "10%",
                    "description": "Clean deposit release history with zero unresolved damages or payment disputes."
                }
            }
        }


class Space(db.Model):
    __tablename__ = "spaces"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Storage, Studio, Parking, Retail, Event, Workspace
    
    # Location
    address = db.Column(db.String(255), nullable=False)
    neighborhood = db.Column(db.String(100), default="")
    city = db.Column(db.String(100), default="New Delhi")
    state = db.Column(db.String(50), default="Delhi")
    zip_code = db.Column(db.String(20), default="")
    
    # Geofencing & Physical Access (India Stack Zero-Hardware)
    latitude = db.Column(db.Float, default=28.5450)  # Defaults near IIT Delhi / Hauz Khas
    longitude = db.Column(db.Float, default=77.1926)
    geofence_radius_meters = db.Column(db.Integer, default=30)
    physical_access_type = db.Column(db.String(50), default="caretaker_handshake")  # 'caretaker_handshake', 'mechanical_keybox'
    keybox_code = db.Column(db.String(20), default="")
    discom_ca_number = db.Column(db.String(50), default="")
    discom_consumer_name = db.Column(db.String(120), default="")
    room_qr_token = db.Column(db.String(64), default="")  # Cryptographic secret for printable door QR

    # Space Metrics & Pricing
    sqft = db.Column(db.Integer, default=200)
    max_capacity = db.Column(db.Integer, default=4)
    price_hourly = db.Column(db.Float, default=25.0)
    price_daily = db.Column(db.Float, default=150.0)
    minimum_hours = db.Column(db.Integer, default=1)
    
    # JSON-encoded fields (Uses native JSONB on PostgreSQL and JSON/Text on SQLite)
    amenities_json = db.Column(db.JSON, default=list)  # e.g. ["Wi-Fi", "EV Charger", "Ground Floor Access"]
    rules_json = db.Column(db.JSON, default=list)      # e.g. ["No smoking", "Quiet hours after 10 PM"]
    photos_json = db.Column(db.JSON, default=list)     # URLs or file paths
    
    # AI-Extracted Attributes
    ai_tags_json = db.Column(db.JSON, default=list)
    ai_dimensions_summary = db.Column(db.String(255), default="")
    ai_lighting = db.Column(db.String(100), default="Natural & Ambient")
    ai_noise_level = db.Column(db.String(100), default="Quiet (<45 dB)")
    ai_power_access = db.Column(db.String(100), default="Standard 120V Outlets")
    ai_safety_notes = db.Column(db.Text, default="")
    ai_recommended_uses = db.Column(db.String(255), default="")
    ai_suitability_score = db.Column(db.Integer, default=95)

    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    draft = db.Column(db.Boolean, default=False)
    operating_hours_start = db.Column(db.String(10), default="08:00")
    operating_hours_end = db.Column(db.String(10), default="22:00")
    buffer_minutes = db.Column(db.Integer, default=15)
    instant_booking_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Semantic Vector Search (dense vector embedding stored as JSON array, pgvector compatible)
    embedding_json = db.Column(db.JSON, nullable=True)

    # Relationships
    bookings = db.relationship("Booking", backref="space", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="space", lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship("SpaceInquiry", backref="space", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("idx_space_active_cat", "is_active", "category"),
        db.Index("idx_space_owner_active", "owner_id", "is_active"),
        db.Index("idx_space_coords", "latitude", "longitude"),
        db.Index("idx_space_city", "city"),
        db.Index("idx_space_price", "price_hourly"),
    )

    @property
    def amenities(self):
        if isinstance(self.amenities_json, list):
            return self.amenities_json
        try:
            return json.loads(self.amenities_json) if self.amenities_json else []
        except Exception:
            return []

    @amenities.setter
    def amenities(self, val):
        if isinstance(val, list):
            self.amenities_json = val
        elif isinstance(val, str):
            try:
                self.amenities_json = json.loads(val)
            except Exception:
                self.amenities_json = [val] if val else []
        else:
            self.amenities_json = []

    @property
    def rules(self):
        if isinstance(self.rules_json, list):
            return self.rules_json
        try:
            return json.loads(self.rules_json) if self.rules_json else []
        except Exception:
            return []

    @rules.setter
    def rules(self, val):
        if isinstance(val, list):
            self.rules_json = val
        elif isinstance(val, str):
            try:
                self.rules_json = json.loads(val)
            except Exception:
                self.rules_json = [val] if val else []
        else:
            self.rules_json = []

    @property
    def photos(self):
        if isinstance(self.photos_json, list):
            return self.photos_json
        try:
            return json.loads(self.photos_json) if self.photos_json else []
        except Exception:
            return []

    @photos.setter
    def photos(self, val):
        if isinstance(val, list):
            self.photos_json = val
        elif isinstance(val, str):
            try:
                self.photos_json = json.loads(val)
            except Exception:
                self.photos_json = [val] if val else []
        else:
            self.photos_json = []

    @property
    def ai_tags(self):
        if isinstance(self.ai_tags_json, list):
            return self.ai_tags_json
        try:
            return json.loads(self.ai_tags_json) if self.ai_tags_json else []
        except Exception:
            return []

    @ai_tags.setter
    def ai_tags(self, val):
        if isinstance(val, list):
            self.ai_tags_json = val
        elif isinstance(val, str):
            try:
                self.ai_tags_json = json.loads(val)
            except Exception:
                self.ai_tags_json = [val] if val else []
        else:
            self.ai_tags_json = []

    @property
    def location(self):
        if self.neighborhood:
            return f"{self.neighborhood}, {self.city}"
        return self.city or "India"

    @property
    def hourly_rate(self):
        return self.price_hourly

    @property
    def daily_rate(self):
        return self.price_daily

    def average_rating(self):
        if not self.reviews:
            return 4.9  # Default new space rating
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    @property
    def embedding(self) -> list[float] | None:
        if isinstance(self.embedding_json, list):
            return self.embedding_json
        if isinstance(self.embedding_json, str):
            try:
                return json.loads(self.embedding_json)
            except Exception:
                return None
        return None

    @embedding.setter
    def embedding(self, val):
        if isinstance(val, list):
            self.embedding_json = val
        elif isinstance(val, str):
            try:
                self.embedding_json = json.loads(val)
            except Exception:
                self.embedding_json = None
        else:
            self.embedding_json = None

    def update_embedding(self, commit: bool = True):
        from backend.modules.search.embedding import build_searchable_representation, generate_embedding
        txt = build_searchable_representation(self)
        self.embedding = generate_embedding(txt)
        if commit:
            db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "owner_name": self.owner.name if self.owner else "Verified Host",
            "host_id": self.owner_id,
            "host_name": self.owner.name if self.owner else "Verified Host",
            "host_verified": self.owner.is_host_verified if self.owner else False,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "address": self.address,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "location": f"{self.neighborhood}, {self.city}" if self.neighborhood else self.city,
            "sqft": self.sqft,
            "max_capacity": self.max_capacity,
            "price_hourly": self.price_hourly,
            "price_daily": self.price_daily,
            "hourly_rate": self.price_hourly,
            "daily_rate": self.price_daily,
            "minimum_hours": self.minimum_hours,
            "amenities": self.amenities,
            "rules": self.rules,
            "photos": self.photos or ["https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"],
            "ai_tags": self.ai_tags,
            "ai_dimensions_summary": self.ai_dimensions_summary,
            "ai_lighting": self.ai_lighting,
            "ai_noise_level": self.ai_noise_level,
            "ai_power_access": self.ai_power_access,
            "ai_safety_notes": self.ai_safety_notes,
            "ai_recommended_uses": self.ai_recommended_uses,
            "ai_suitability_score": self.ai_suitability_score,
            "rating": self.average_rating(),
            "reviews_count": len(self.reviews),
            "is_active": self.is_active,
            "is_verified": bool(self.is_verified or self.discom_ca_number),
            "draft": bool(self.draft),
            "operating_hours_start": self.operating_hours_start or "08:00",
            "operating_hours_end": self.operating_hours_end or "22:00",
            "buffer_minutes": self.buffer_minutes or 15,
            "instant_booking_enabled": self.instant_booking_enabled if self.instant_booking_enabled is not None else True,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Zero-Hardware India Stack & Telemetry
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geofence_radius_meters": self.geofence_radius_meters,
            "physical_access_type": self.physical_access_type,
            "keybox_code": self.keybox_code,
            "discom_ca_number": self.discom_ca_number,
            "discom_consumer_name": self.discom_consumer_name,
            "room_qr_token": self.room_qr_token,
            "is_discom_verified": bool(self.discom_ca_number),
            # Host Trust & Verification (SpaceLoop Verified)
            "owner_verified": self.owner.is_host_verified if self.owner else False,
            "owner_aadhaar_verified": self.owner.is_aadhaar_verified if self.owner else False,
            "owner_upi_verified": self.owner.upi_verified if self.owner else False,
            "owner_trust_score": round(self.owner.objective_trust_score, 1) if (self.owner and self.owner.objective_trust_score is not None) else 98.5,
            "owner_on_time_vacate_rate": round(self.owner.on_time_vacate_rate, 1) if (self.owner and self.owner.on_time_vacate_rate is not None) else 100.0,
            "owner_cleanliness_match_rate": round(self.owner.cleanliness_match_rate, 1) if (self.owner and self.owner.cleanliness_match_rate is not None) else 99.0,
            "owner_discom_provider": self.owner.discom_provider if self.owner else "",
            "is_space_info_verified": bool(self.ai_suitability_score and self.ai_suitability_score >= 80),
        }


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    hours_booked = db.Column(db.Float, default=2.0)
    total_price = db.Column(db.Float, nullable=False)
    
    status = db.Column(db.String(30), default="confirmed")  # confirmed, completed, cancelled
    intended_purpose = db.Column(db.String(255), nullable=False)
    attendees_count = db.Column(db.Integer, default=1)
    special_requests = db.Column(db.Text, default="")
    
    # AI-Generated Micro-Lease License Agreement
    micro_lease_agreement = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # In-Room Session Telemetry (Zero Hardware India Stack)
    session_state = db.Column(db.String(30), default="confirmed")  # confirmed, checked_in, checked_out, disputed
    arrival_pin = db.Column(db.String(10), default="4821")  # 4-digit Caretaker Handshake PIN
    arrival_time = db.Column(db.DateTime, nullable=True)
    departure_time = db.Column(db.DateTime, nullable=True)
    checkin_gps_lat = db.Column(db.Float, nullable=True)
    checkin_gps_lng = db.Column(db.Float, nullable=True)
    checkout_gps_lat = db.Column(db.Float, nullable=True)
    checkout_gps_lng = db.Column(db.Float, nullable=True)
    entry_scan_photo = db.Column(db.Text, default="")
    exit_scan_photo = db.Column(db.Text, default="")
    condition_match_score = db.Column(db.Float, default=100.0)
    fans_lights_cleared = db.Column(db.Boolean, default=True)
    escrow_deposit_amount = db.Column(db.Float, default=100.0)  # In INR (Rs. 100 UPI hold)
    escrow_status = db.Column(db.String(30), default="held")  # 'held', 'released', 'claimed'
    objective_punctuality_score = db.Column(db.Float, default=100.0)

    # Disputes & Micro-Escrow Settlement
    dispute_reason = db.Column(db.Text, default="")
    dispute_status = db.Column(db.String(30), default="none")  # 'none', 'opened', 'resolved', 'forfeited'
    dispute_resolution = db.Column(db.Text, default="")
    dispute_opened_at = db.Column(db.DateTime, nullable=True)
    dispute_resolved_at = db.Column(db.DateTime, nullable=True)
    settled_at = db.Column(db.DateTime, nullable=True)
    payout_vpa = db.Column(db.String(120), default="")
    net_payout_amount = db.Column(db.Float, default=0.0)
    platform_fee_amount = db.Column(db.Float, default=0.0)

    __table_args__ = (
        db.Index("idx_booking_space_time", "space_id", "start_time", "end_time"),
        db.Index("idx_booking_renter_status", "renter_id", "status"),
        db.Index("idx_booking_space_status", "space_id", "status"),
        db.Index("idx_booking_session_state", "session_state"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_title": self.space.title if self.space else "Space",
            "space_category": self.space.category if self.space else "",
            "space_photo": self.space.photos[0] if self.space and self.space.photos else "",
            "space_address": self.space.address if (self.space and self.space.address) else (self.space.location if self.space else "Verified Premise"),
            "renter_id": self.renter_id,
            "renter_name": self.renter.name if self.renter else "Guest",
            "start_time": self.start_time.strftime("%b %d, %Y at %I:%M %p") if self.start_time else "",
            "end_time": self.end_time.strftime("%b %d, %Y at %I:%M %p") if self.end_time else "",
            "start_iso": self.start_time.isoformat() if self.start_time else None,
            "end_iso": self.end_time.isoformat() if self.end_time else None,
            "end_timestamp_ms": int(self.end_time.timestamp() * 1000) if self.end_time else None,
            "hours_booked": self.hours_booked,
            "total_price": self.total_price,
            "status": self.status,
            "intended_purpose": self.intended_purpose,
            "attendees_count": self.attendees_count,
            "micro_lease_agreement": self.micro_lease_agreement,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Session Telemetry
            "session_state": self.session_state,
            "arrival_pin": self.arrival_pin,
            "arrival_time": self.arrival_time.strftime("%I:%M %p, %b %d") if self.arrival_time else None,
            "departure_time": self.departure_time.strftime("%I:%M %p, %b %d") if self.departure_time else None,
            "entry_scan_photo": self.entry_scan_photo,
            "exit_scan_photo": self.exit_scan_photo,
            "condition_match_score": round(self.condition_match_score, 1),
            "fans_lights_cleared": self.fans_lights_cleared,
            "escrow_deposit_amount": self.escrow_deposit_amount,
            "deposit_held": self.escrow_deposit_amount,
            "escrow_status": self.escrow_status,
            "escrow_released": self.escrow_status in ("released", "refunded") or self.status == "completed",
            "objective_punctuality_score": round(self.objective_punctuality_score, 1),
            # Dispute & Payout Info
            "dispute_reason": self.dispute_reason or "",
            "dispute_status": self.dispute_status or "none",
            "dispute_resolution": self.dispute_resolution or "",
            "dispute_opened_at": self.dispute_opened_at.isoformat() if self.dispute_opened_at else None,
            "dispute_resolved_at": self.dispute_resolved_at.isoformat() if self.dispute_resolved_at else None,
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
            "payout_vpa": self.payout_vpa or (self.space.owner.upi_vpa_masked if self.space and self.space.owner else ""),
            "net_payout_amount": self.net_payout_amount or round(self.total_price * 0.95, 2),
            "platform_fee_amount": self.platform_fee_amount or round(self.total_price * 0.05, 2),
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=True)
    user_name = db.Column(db.String(120), default="Verified Guest")
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship("Booking", backref=db.backref("reviews", lazy=True), foreign_keys=[booking_id])

    __table_args__ = (
        db.Index("idx_review_space", "space_id"),
        db.Index("idx_review_user", "user_id"),
        db.Index("idx_review_booking", "booking_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "booking_id": self.booking_id,
            "user_name": self.user_name,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.strftime("%b %d, %Y") if self.created_at else "",
        }


class SpaceInquiry(db.Model):
    __tablename__ = "space_inquiries"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    question = db.Column(db.Text, nullable=False)
    ai_answer = db.Column(db.Text, default="")
    response = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("idx_inquiry_space", "space_id"),
        db.Index("idx_inquiry_user", "user_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_title": self.space.title if self.space else "General Inquiry",
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Verified Seeker",
            "question": self.question,
            "ai_answer": self.ai_answer,
            "ai_response": self.ai_answer,
            "response": self.response or "",
            "created_at": self.created_at.strftime("%b %d, %Y at %I:%M %p") if self.created_at else "",
        }


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self) -> bool:
        return not self.used and datetime.utcnow() < self.expires_at


class EmailVerificationToken(db.Model):
    __tablename__ = "email_verification_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    pending_email = db.Column(db.String(120), nullable=True)  # Used for email change verification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self) -> bool:
        return not self.used and datetime.utcnow() < self.expires_at


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    ip_address = db.Column(db.String(45), default="")
    user_agent = db.Column(db.String(255), default="")
    details = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MFARecoveryCode(db.Model):
    __tablename__ = "mfa_recovery_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False, index=True)  # SHA-256 hash of single-use recovery code
    used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def is_valid(self) -> bool:
        return not self.used


class RiskAssessment(db.Model):
    __tablename__ = "risk_assessments"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(30), nullable=False, index=True)  # 'user', 'space', 'booking', 'review', 'payout'
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    risk_level = db.Column(db.String(20), default="normal", nullable=False, index=True)  # 'normal', 'unusual', 'suspicious', 'high_risk'
    risk_score = db.Column(db.Float, default=0.0, nullable=False)  # Normalized [0.0, 1.0]
    confidence = db.Column(db.Float, default=1.0, nullable=False)  # Statistical certainty [0.0, 1.0]
    signals_json = db.Column(db.JSON, default=list)  # List of signal codes
    evidence_text = db.Column(db.Text, default="")
    recommended_action = db.Column(db.String(40), default="allow", nullable=False)  # 'allow', 'request_verification', 'require_mfa', 'hold_transaction', 'manual_review', 'restrict_action'
    action_taken = db.Column(db.String(30), default="pending", nullable=False)  # 'allowed', 'flagged', 'held', 'blocked', 'overridden'
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_notes = db.Column(db.Text, default="")
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    reviewer = db.relationship("User", foreign_keys=[reviewer_id], lazy=True)

    __table_args__ = (
        db.Index("idx_risk_entity", "entity_type", "entity_id"),
        db.Index("idx_risk_level_created", "risk_level", "created_at"),
    )

    @property
    def signals(self) -> list:
        if isinstance(self.signals_json, list):
            return self.signals_json
        if isinstance(self.signals_json, str):
            try:
                return json.loads(self.signals_json)
            except Exception:
                return []
        return []

    @signals.setter
    def signals(self, val: list):
        self.signals_json = val

    @property
    def signals_list(self) -> list:
        return self.signals

    def to_dict(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "risk_level": self.risk_level,
            "risk_score": round(self.risk_score, 4),
            "confidence": round(self.confidence, 4),
            "signals": self.signals,
            "evidence": self.evidence_text,
            "recommended_action": self.recommended_action,
            "action_taken": self.action_taken,
            "reviewer_id": self.reviewer_id,
            "reviewer_notes": self.reviewer_notes or "",
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeviceSession(db.Model):
    __tablename__ = "device_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_fingerprint = db.Column(db.String(64), nullable=False, index=True)  # Privacy-preserving SHA-256
    ip_address = db.Column(db.String(45), default="")
    ip_hash = db.Column(db.String(64), nullable=False, index=True)  # SHA-256 of IP
    user_agent = db.Column(db.String(255), default="")
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("device_sessions", lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.Index("idx_device_user", "device_fingerprint", "user_id"),
        db.Index("idx_ip_user", "ip_hash", "user_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_fingerprint": self.device_fingerprint,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmailLog(db.Model):
    """
    Transactional Email Event Log & Idempotency Store.
    Tracks outgoing emails, deduplication keys, provider IDs, and failure states without exposing secrets.
    """
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    idempotency_key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)
    recipient_email = db.Column(db.String(120), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default="sent", nullable=False, index=True)  # 'sent', 'failed', 'skipped_duplicate'
    resend_id = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("email_logs", lazy=True))
    booking = db.relationship("Booking", backref=db.backref("email_logs", lazy=True))

    __table_args__ = (
        db.Index("idx_email_event_created", "event_type", "created_at"),
        db.Index("idx_email_recipient", "recipient_email"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "idempotency_key": self.idempotency_key,
            "event_type": self.event_type,
            "recipient_email": self.recipient_email,
            "user_id": self.user_id,
            "booking_id": self.booking_id,
            "subject": self.subject,
            "status": self.status,
            "resend_id": self.resend_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FraudEventRecord(db.Model):
    """
    Normalized SpaceLoop Ingested Fraud Event Store.
    Tracks raw telemetry, normalized entity anchors, and evaluated risk scores.
    """
    __tablename__ = "fraud_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = db.Column(db.String(30), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    ip_address = db.Column(db.String(45), default="")
    device_fingerprint = db.Column(db.String(64), default="", index=True)
    user_agent = db.Column(db.String(255), default="")
    payload_json = db.Column(db.JSON, default=dict)
    risk_score = db.Column(db.Float, default=0.0)
    decision = db.Column(db.String(30), default="allow")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("fraud_events", lazy=True))

    __table_args__ = (
        db.Index("idx_fraud_event_user_type", "user_id", "event_type"),
        db.Index("idx_fraud_event_created", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "ip_address": self.ip_address,
            "device_fingerprint": self.device_fingerprint,
            "payload": self.payload_json or {},
            "risk_score": round(self.risk_score, 4),
            "decision": self.decision,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FraudAlertRecord(db.Model):
    """
    Actionable Fraud & Anomaly Triage Alert.
    Created when evaluated risk exceeds alert thresholds or critical policy gates trigger.
    """
    __tablename__ = "fraud_alerts"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    event_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = db.Column(db.String(30), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    severity = db.Column(db.String(20), default="medium", nullable=False)  # low, medium, high, critical
    risk_score = db.Column(db.Float, default=0.0, nullable=False)
    decision = db.Column(db.String(30), default="review", nullable=False)  # allow, review, challenge, hold, block
    status = db.Column(db.String(20), default="open", nullable=False)  # open, investigating, resolved, dismissed
    triggered_rules_json = db.Column(db.JSON, default=list)
    features_snapshot_json = db.Column(db.JSON, default=dict)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("fraud_alerts", lazy=True))

    __table_args__ = (
        db.Index("idx_fraud_alert_status_created", "status", "created_at"),
        db.Index("idx_fraud_alert_severity", "severity"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "severity": self.severity,
            "risk_score": round(self.risk_score, 4),
            "decision": self.decision,
            "status": self.status,
            "triggered_rules": self.triggered_rules_json or [],
            "features_snapshot": self.features_snapshot_json or {},
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="medium")
    action_url = db.Column(db.String(255), default="")
    unread = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("notifications", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "action_url": self.action_url,
            "unread": self.unread,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AccessLog(db.Model):
    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    access_type = db.Column(db.String(50), default="room_qr")
    credential_used = db.Column(db.String(100), default="")
    status = db.Column(db.String(50), default="granted")
    distance_meters = db.Column(db.Float, nullable=True)
    ip_address = db.Column(db.String(45), default="")
    user_agent = db.Column(db.String(255), default="")
    details = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    space = db.relationship("Space", backref=db.backref("access_logs", lazy=True, cascade="all, delete-orphan"))
    booking = db.relationship("Booking", backref=db.backref("access_logs", lazy=True))
    user = db.relationship("User", backref=db.backref("access_logs", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_title": self.space.title if self.space else "Space",
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Seeker",
            "access_type": self.access_type,
            "credential_used": self.credential_used,
            "status": self.status,
            "distance_meters": round(self.distance_meters, 1) if self.distance_meters is not None else None,
            "details": self.details,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EscrowTransaction(db.Model):
    __tablename__ = "escrow_transactions"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount = db.Column(db.Float, default=100.0)
    transaction_type = db.Column(db.String(30), default="hold")
    status = db.Column(db.String(30), default="completed")
    reference_id = db.Column(db.String(100), default="")
    details = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    booking = db.relationship("Booking", backref=db.backref("escrow_transactions", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("escrow_transactions", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "reference_id": self.reference_id,
            "details": self.details,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }



