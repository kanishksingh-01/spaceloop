import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="both")  # 'owner', 'seeker', 'both'
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

    # Relationships
    spaces = db.relationship("Space", backref="owner", lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="renter", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="user", lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship("SpaceInquiry", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
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
            "objective_trust_score": round(self.objective_trust_score, 1),
            "on_time_vacate_rate": round(self.on_time_vacate_rate, 1),
            "cleanliness_match_rate": round(self.cleanliness_match_rate, 1),
            "total_completed_hours": round(self.total_completed_hours, 1),
            "dispute_count": self.dispute_count,
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
    
    # JSON-encoded fields
    amenities_json = db.Column(db.Text, default="[]")  # e.g. ["Wi-Fi", "EV Charger", "Ground Floor Access"]
    rules_json = db.Column(db.Text, default="[]")      # e.g. ["No smoking", "Quiet hours after 10 PM"]
    photos_json = db.Column(db.Text, default="[]")     # URLs or file paths
    
    # AI-Extracted Attributes
    ai_tags_json = db.Column(db.Text, default="[]")
    ai_dimensions_summary = db.Column(db.String(255), default="")
    ai_lighting = db.Column(db.String(100), default="Natural & Ambient")
    ai_noise_level = db.Column(db.String(100), default="Quiet (<45 dB)")
    ai_power_access = db.Column(db.String(100), default="Standard 120V Outlets")
    ai_safety_notes = db.Column(db.Text, default="")
    ai_recommended_uses = db.Column(db.String(255), default="")
    ai_suitability_score = db.Column(db.Integer, default=95)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship("Booking", backref="space", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="space", lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship("SpaceInquiry", backref="space", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("idx_space_active_cat", "is_active", "category"),
        db.Index("idx_space_coords", "latitude", "longitude"),
        db.Index("idx_space_city", "city"),
    )

    @property
    def amenities(self):
        try:
            return json.loads(self.amenities_json) if self.amenities_json else []
        except Exception:
            return []

    @amenities.setter
    def amenities(self, val):
        self.amenities_json = json.dumps(val or [])

    @property
    def rules(self):
        try:
            return json.loads(self.rules_json) if self.rules_json else []
        except Exception:
            return []

    @rules.setter
    def rules(self, val):
        self.rules_json = json.dumps(val or [])

    @property
    def photos(self):
        try:
            return json.loads(self.photos_json) if self.photos_json else []
        except Exception:
            return []

    @photos.setter
    def photos(self, val):
        self.photos_json = json.dumps(val or [])

    @property
    def ai_tags(self):
        try:
            return json.loads(self.ai_tags_json) if self.ai_tags_json else []
        except Exception:
            return []

    @ai_tags.setter
    def ai_tags(self, val):
        self.ai_tags_json = json.dumps(val or [])

    def average_rating(self):
        if not self.reviews:
            return 4.9  # Default new space rating
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "owner_name": self.owner.name if self.owner else "Verified Host",
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "address": self.address,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "sqft": self.sqft,
            "max_capacity": self.max_capacity,
            "price_hourly": self.price_hourly,
            "price_daily": self.price_daily,
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
            "owner_trust_score": round(self.owner.objective_trust_score, 1) if self.owner else 98.5,
            "owner_on_time_vacate_rate": round(self.owner.on_time_vacate_rate, 1) if self.owner else 100.0,
            "owner_cleanliness_match_rate": round(self.owner.cleanliness_match_rate, 1) if self.owner else 99.0,
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
    entry_scan_photo = db.Column(db.String(500), default="")
    exit_scan_photo = db.Column(db.String(500), default="")
    condition_match_score = db.Column(db.Float, default=100.0)
    fans_lights_cleared = db.Column(db.Boolean, default=True)
    escrow_deposit_amount = db.Column(db.Float, default=100.0)  # In INR (Rs. 100 UPI hold)
    escrow_status = db.Column(db.String(30), default="held")  # 'held', 'released', 'claimed'
    objective_punctuality_score = db.Column(db.Float, default=100.0)

    __table_args__ = (
        db.Index("idx_booking_space_time", "space_id", "start_time", "end_time"),
        db.Index("idx_booking_renter_status", "renter_id", "status"),
        db.Index("idx_booking_session_state", "session_state"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_title": self.space.title if self.space else "Space",
            "space_category": self.space.category if self.space else "",
            "space_photo": self.space.photos[0] if self.space and self.space.photos else "",
            "renter_id": self.renter_id,
            "renter_name": self.renter.name if self.renter else "Guest",
            "start_time": self.start_time.strftime("%b %d, %Y at %I:%M %p") if self.start_time else "",
            "end_time": self.end_time.strftime("%b %d, %Y at %I:%M %p") if self.end_time else "",
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
            "escrow_status": self.escrow_status,
            "objective_punctuality_score": round(self.objective_punctuality_score, 1),
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_name = db.Column(db.String(120), default="Verified Guest")
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("idx_review_space", "space_id"),
        db.Index("idx_review_user", "user_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
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
            "created_at": self.created_at.strftime("%b %d, %Y at %I:%M %p") if self.created_at else "",
        }
