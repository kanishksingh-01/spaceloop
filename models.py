"""
SpaceLoop Relational Database Architecture & Schema Specification
Compliance: DPDP Act 2023, Section 52 Indian Easements Act 1882
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Platform participant (Seeker / Owner).
    DPDP Act 2023 Compliant: Zero raw Aadhaar storage.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False, default="sha256_mock_hash")
    role = db.Column(db.String(20), nullable=False, default='seeker')  # 'seeker' or 'owner'

    # Student Verification (India Stack)
    is_student_verified = db.Column(db.Boolean, default=False)
    college_name = db.Column(db.String(150), nullable=True)
    college_email = db.Column(db.String(120), nullable=True)
    student_id_masked = db.Column(db.String(50), nullable=True)  # e.g. STU-***-4821

    # DigiLocker / Aadhaar Verification (DPDP Act 2023 Section 8 Compliant)
    is_aadhaar_verified = db.Column(db.Boolean, default=False)
    aadhaar_masked = db.Column(db.String(20), nullable=True)      # e.g. XXXX-XXXX-4821
    aadhaar_token_hash = db.Column(db.String(128), nullable=True)  # sha256(aadhaar + salt)

    # Host & Premise Verification
    is_host_verified = db.Column(db.Boolean, default=False)
    discom_provider = db.Column(db.String(80), nullable=True)     # BESCOM, TPDDL, MSEDCL, etc.
    discom_ca_masked = db.Column(db.String(30), nullable=True)    # e.g. CA-***-9921
    upi_vpa_masked = db.Column(db.String(100), nullable=True)     # e.g. host***@okaxis

    # Objective Telemetry Index (OTI) & Reputation
    objective_trust_score = db.Column(db.Float, default=85.0)     # 0 - 100 score
    on_time_vacate_rate = db.Column(db.Float, default=98.0)       # % on-time departures
    total_disputes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    owned_spaces = db.relationship('Space', backref='owner', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='renter', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_student_verified': self.is_student_verified,
            'college_name': self.college_name,
            'college_email': self.college_email,
            'student_id_masked': self.student_id_masked,
            'is_aadhaar_verified': self.is_aadhaar_verified,
            'aadhaar_masked': self.aadhaar_masked,
            'is_host_verified': self.is_host_verified,
            'discom_provider': self.discom_provider,
            'discom_ca_masked': self.discom_ca_masked,
            'upi_vpa_masked': self.upi_vpa_masked,
            'objective_trust_score': round(self.objective_trust_score, 1),
            'on_time_vacate_rate': round(self.on_time_vacate_rate, 1)
        }


class Space(db.Model):
    """Represents a micro-space listing.
    Zero-Hardware Access: Printable Door QR + GPS Geofencing + Dynamic PIN.
    """
    __tablename__ = 'spaces'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Workspace')  # Workspace, Studio, Storage, Event, Pop-up, Parking
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80), nullable=False, default='Delhi')

    # GPS Coordinates & Geofencing (<50m radar)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    geofence_radius_meters = db.Column(db.Float, default=50.0)

    # Zero-Hardware Physical Access
    room_qr_token = db.Column(db.String(64), nullable=False, unique=True)  # 64-char SHA256 hex
    physical_access_type = db.Column(db.String(30), default='caretaker')   # 'caretaker' or 'keybox'
    keybox_code = db.Column(db.String(10), default='4821')

    # Dimensions & Capacity
    sqft = db.Column(db.Integer, nullable=False, default=150)
    max_capacity = db.Column(db.Integer, nullable=False, default=2)

    # Dynamic Micro-Pricing in INR
    price_hourly = db.Column(db.Float, nullable=False, default=45.0)
    price_daily = db.Column(db.Float, nullable=False, default=320.0)

    # Multimodal Spatial AI Diagnostics
    ai_suitability_score = db.Column(db.Integer, default=94)               # 0-100%
    ai_lighting = db.Column(db.String(100), default='Natural Sunlit + Warm LED')
    ai_noise_level = db.Column(db.String(50), default='Quiet (<34 dB)')
    circuit_load = db.Column(db.String(100), default='4x Grounded 20A Circuits')
    discom_ca_number = db.Column(db.String(50), nullable=True)

    # Amenities & Media
    amenities = db.Column(db.Text, default='High-speed Wi-Fi,Air Conditioning,Ergonomic Desks,Power Backup,Drinking Water')
    image_url = db.Column(db.String(300), default='https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='space', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='space', lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship('SpaceInquiry', backref='space', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'address': self.address,
            'city': self.city,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'geofence_radius_meters': self.geofence_radius_meters,
            'room_qr_token': self.room_qr_token,
            'physical_access_type': self.physical_access_type,
            'keybox_code': self.keybox_code,
            'sqft': self.sqft,
            'max_capacity': self.max_capacity,
            'price_hourly': self.price_hourly,
            'price_daily': self.price_daily,
            'ai_suitability_score': self.ai_suitability_score,
            'ai_lighting': self.ai_lighting,
            'ai_noise_level': self.ai_noise_level,
            'circuit_load': self.circuit_load,
            'discom_ca_number': self.discom_ca_number,
            'amenities': [a.strip() for a in self.amenities.split(',') if a.strip()] if self.amenities else [],
            'image_url': self.image_url,
            'is_active': self.is_active
        }


class Booking(db.Model):
    """Tracks full lifecycle of a micro-space reservation session.
    States: confirmed -> checked_in -> checked_out -> completed
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    hours_booked = db.Column(db.Float, nullable=False, default=2.0)
    purpose = db.Column(db.String(180), default='Academic study and project development')
    attendees_count = db.Column(db.Integer, default=1)

    # Server-Side Financial Recomputation
    total_price = db.Column(db.Float, nullable=False)
    escrow_deposit_amount = db.Column(db.Float, default=100.0)             # Rs. 100 micro-escrow
    escrow_status = db.Column(db.String(30), default='held')              # 'held', 'refunded', 'disputed'
    refund_tx_hash = db.Column(db.String(100), nullable=True)

    # Access Handshake & Telemetry
    session_state = db.Column(db.String(30), default='confirmed')          # 'confirmed', 'checked_in', 'checked_out'
    arrival_pin = db.Column(db.String(10), default='4821')                 # Dynamic 4-digit PIN
    arrival_time = db.Column(db.DateTime, nullable=True)
    departure_time = db.Column(db.DateTime, nullable=True)
    checkin_gps_lat = db.Column(db.Float, nullable=True)
    checkin_gps_lng = db.Column(db.Float, nullable=True)
    checkin_distance_meters = db.Column(db.Float, nullable=True)

    # Computer Vision Delta & Objective Telemetry
    entry_photo_url = db.Column(db.String(300), nullable=True)
    exit_photo_url = db.Column(db.String(300), nullable=True)
    condition_match_score = db.Column(db.Float, nullable=True)            # 0 - 100%
    appliances_shut_off = db.Column(db.Boolean, default=True)
    punctuality_score = db.Column(db.Float, default=100.0)

    # Legal Micro-Lease (Indian Easements Act 1882, Section 52)
    micro_lease_agreement = db.Column(db.Text, nullable=True)
    lease_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Telemetry Logs
    telemetry_logs = db.relationship('TelemetryLog', backref='booking', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'space_id': self.space_id,
            'renter_id': self.renter_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'hours_booked': self.hours_booked,
            'purpose': self.purpose,
            'attendees_count': self.attendees_count,
            'total_price': self.total_price,
            'escrow_deposit_amount': self.escrow_deposit_amount,
            'escrow_status': self.escrow_status,
            'refund_tx_hash': self.refund_tx_hash,
            'session_state': self.session_state,
            'arrival_pin': self.arrival_pin,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'checkin_distance_meters': self.checkin_distance_meters,
            'condition_match_score': self.condition_match_score,
            'appliances_shut_off': self.appliances_shut_off,
            'punctuality_score': self.punctuality_score,
            'lease_hash': self.lease_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Review(db.Model):
    """Legacy qualitative feedback records, supplemented by OTI."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_name = db.Column(db.String(120), nullable=False, default='Verified Student')
    rating = db.Column(db.Integer, nullable=False, default=5)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'space_id': self.space_id,
            'user_name': self.user_name,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.strftime('%d %b %Y')
        }


class SpaceInquiry(db.Model):
    """Host-guest inquiry logs with automated AI pre-answers."""
    __tablename__ = 'space_inquiries'

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    ai_answer = db.Column(db.Text, nullable=True)
    is_resolved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'space_id': self.space_id,
            'user_id': self.user_id,
            'question': self.question,
            'ai_answer': self.ai_answer,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat()
        }


class TelemetryLog(db.Model):
    """Tamper-proof audit logs for access verification and telemetry."""
    __tablename__ = 'telemetry_logs'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'GPS_CHECKIN', 'QR_SCAN', 'DIFF_EVAL', 'ESCROW_RELEASE'
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
