"""
SpaceLoop Realistic Seed Data Generator
Populates high-density urban campus micro-spaces, verified student and host profiles.
"""

from datetime import datetime, timedelta
from models import db, User, Space, Booking, Review, SpaceInquiry, TelemetryLog
from security import mask_aadhaar, hash_aadhaar, mask_discom_ca, mask_upi_vpa, mask_student_id
from telemetry import generate_room_qr_token, generate_arrival_pin
from space_ai import synthesize_micro_lease


def seed_database():
    """Populates initial database state if empty."""
    if User.query.first():
        return  # already seeded

    # 1. Create Student Users
    student_rohit = User(
        name="Rohit Verma",
        email="rohit@iitd.ac.in",
        role="seeker",
        is_student_verified=True,
        college_name="IIT Delhi (Hauz Khas)",
        college_email="rohit@iitd.ac.in",
        student_id_masked=mask_student_id("STU-IITD-2024-8812"),
        is_aadhaar_verified=True,
        aadhaar_masked=mask_aadhaar("984512344821"),
        aadhaar_token_hash=hash_aadhaar("984512344821"),
        objective_trust_score=97.5,
        on_time_vacate_rate=100.0
    )
    student_rohit.set_password("StudentPass123!")

    student_ananya = User(
        name="Ananya Sharma",
        email="ananya@iitb.ac.in",
        role="seeker",
        is_student_verified=True,
        college_name="IIT Bombay (Powai)",
        college_email="ananya@iitb.ac.in",
        student_id_masked=mask_student_id("STU-IITB-2025-1044"),
        is_aadhaar_verified=True,
        aadhaar_masked=mask_aadhaar("781290341044"),
        aadhaar_token_hash=hash_aadhaar("781290341044"),
        objective_trust_score=94.0,
        on_time_vacate_rate=96.0
    )
    student_ananya.set_password("StudentPass123!")

    # 2. Create Host Users
    host_vikram = User(
        name="Vikram Malhotra",
        email="vikram.malhotra@gmail.com",
        role="owner",
        is_host_verified=True,
        discom_provider="BSES",
        discom_ca_masked=mask_discom_ca("10029384912"),
        upi_vpa_masked=mask_upi_vpa("vikram@okhdfcbank"),
        objective_trust_score=98.0,
        on_time_vacate_rate=100.0
    )
    host_vikram.set_password("HostPass123!")

    host_sunita = User(
        name="Sunita Rao",
        email="sunita.rao@blrspaces.in",
        role="owner",
        is_host_verified=True,
        discom_provider="BESCOM",
        discom_ca_masked=mask_discom_ca("BES883920194"),
        upi_vpa_masked=mask_upi_vpa("sunita@okaxis"),
        objective_trust_score=96.0,
        on_time_vacate_rate=100.0
    )
    host_sunita.set_password("HostPass123!")

    db.session.add_all([student_rohit, student_ananya, host_vikram, host_sunita])
    db.session.commit()

    # 3. Create Micro-Spaces
    # Space 1: Hauz Khas near IIT Delhi
    qr1 = generate_room_qr_token(1)
    space_iitd = Space(
        owner_id=host_vikram.id,
        title="Quiet Acoustic Study & Project Pod (Near IIT Gate 1)",
        category="Workspace",
        description="Air-conditioned soundproof micro-study cabin 300 meters from IIT Delhi Main Gate. Dedicated Gigabit Wi-Fi, dual 27-inch monitors, whiteboards, ergonomic Herman Miller chairs, and uninterrupted solar inverter power backup.",
        address="B-4/18 Hauz Khas Enclave, New Delhi",
        city="Delhi",
        latitude=28.5450,
        longitude=77.1926,
        geofence_radius_meters=50.0,
        room_qr_token=qr1,
        physical_access_type="caretaker",
        keybox_code="4821",
        sqft=140,
        max_capacity=2,
        price_hourly=50.0,
        price_daily=360.0,
        ai_suitability_score=98,
        ai_lighting="Bright Natural Sunlit + 5000K Reading LEDs",
        ai_noise_level="Ultra-Quiet (<30 dB)",
        circuit_load="4x Grounded 20A Circuits + 5kVA Solar Inverter",
        discom_ca_number="BSES-DL-10029384912",
        amenities="Air Conditioning,Gigabit Wi-Fi,Dual Monitors,Power Backup,Drinking Water,Whiteboard",
        image_url="https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80"
    )

    # Space 2: Koramangala Startup Belt
    qr2 = generate_room_qr_token(2)
    space_blr = Space(
        owner_id=host_sunita.id,
        title="High-Speed Fiber Builder Nook (Koramangala 4th Block)",
        category="Workspace",
        description="Daytime-vacant designer study annex in Koramangala. Perfect for hackathon sprints, remote pair programming, and coding sprints with 300 Mbps dual fiber lines.",
        address="12th Main Road, 4th Block, Koramangala, Bengaluru",
        city="Bengaluru",
        latitude=12.9352,
        longitude=77.6245,
        geofence_radius_meters=50.0,
        room_qr_token=qr2,
        physical_access_type="keybox",
        keybox_code="7731",
        sqft=180,
        max_capacity=3,
        price_hourly=55.0,
        price_daily=400.0,
        ai_suitability_score=95,
        ai_lighting="Natural Daylight + Warm Ambient LEDs",
        ai_noise_level="Quiet (<34 dB)",
        circuit_load="6x Grounded 16A Sockets + Surge Strip",
        discom_ca_number="BESCOM-KA-BES883920194",
        amenities="High-speed Wi-Fi,Air Conditioning,Mechanical Keybox,Tea/Coffee,Ergonomic Desks",
        image_url="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"
    )

    # Space 3: Powai near IIT Bombay
    qr3 = generate_room_qr_token(3)
    space_powai = Space(
        owner_id=host_vikram.id,
        title="Lakeview AI Builder Den & Robotics Nook (Powai)",
        category="Workspace",
        description="Scenic micro-workspace overlooking Powai lake. Quiet environment for thesis writing, simulation runs, and AI model benchmarking with 3-phase high current outlets.",
        address="Central Avenue, Hiranandani Gardens, Powai, Mumbai",
        city="Mumbai",
        latitude=19.1176,
        longitude=72.9060,
        geofence_radius_meters=50.0,
        room_qr_token=qr3,
        physical_access_type="caretaker",
        keybox_code="1920",
        sqft=220,
        max_capacity=4,
        price_hourly=60.0,
        price_daily=440.0,
        ai_suitability_score=96,
        ai_lighting="Panoramic Lake Daylight + Calibrated Task Lights",
        ai_noise_level="Whisper Quiet (<32 dB)",
        circuit_load="3-Phase 32A Power Bay + UPS",
        discom_ca_number="MSEDCL-MH-994821039",
        amenities="Lake View,High-Speed Wi-Fi,Air Conditioning,Soldering Station,Whiteboard",
        image_url="https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80"
    )

    # Space 4: Pune FC Road
    qr4 = generate_room_qr_token(4)
    space_pune = Space(
        owner_id=host_sunita.id,
        title="Competitive Exam Focus Pod (FC Road, Shivajinagar)",
        category="Workspace",
        description="Compact single-occupancy soundproof focus capsule dedicated to UPSC, GATE, and CAT aspirants requiring absolute silence and comfortable desk setup.",
        address="FC Road, Deccan Gymkhana, Pune",
        city="Pune",
        latitude=18.5204,
        longitude=73.8415,
        geofence_radius_meters=50.0,
        room_qr_token=qr4,
        physical_access_type="keybox",
        keybox_code="3319",
        sqft=90,
        max_capacity=1,
        price_hourly=40.0,
        price_daily=280.0,
        ai_suitability_score=97,
        ai_lighting="Neutral White 4000K Anti-Glare Reading Light",
        ai_noise_level="Ultra-Quiet (<28 dB)",
        circuit_load="2x 16A Outlets + Laptop Charger USB-C 100W",
        discom_ca_number="MSEDCL-PUNE-88120481",
        amenities="Soundproof Wall Panels,Air Conditioning,Water Dispenser,USB-C 100W PD",
        image_url="https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=800&q=80"
    )

    # Space 5: Delhi Connaught Place Creator Studio
    qr5 = generate_room_qr_token(5)
    space_cp = Space(
        owner_id=host_vikram.id,
        title="Acoustic Podcast & Video Studio (Connaught Place)",
        category="Studio",
        description="Professional acoustic treated studio equipped with Shure microphones, ring lights, and colored RGB backdrops. Perfect for student podcasters and YouTube creators.",
        address="Inner Circle, Block F, Connaught Place, New Delhi",
        city="Delhi",
        latitude=28.6328,
        longitude=77.2197,
        geofence_radius_meters=50.0,
        room_qr_token=qr5,
        physical_access_type="caretaker",
        keybox_code="5502",
        sqft=260,
        max_capacity=4,
        price_hourly=75.0,
        price_daily=550.0,
        ai_suitability_score=99,
        ai_lighting="Softbox Studio Illumination + RGB Edge Fill",
        ai_noise_level="Studio Grade Soundproof (<25 dB)",
        circuit_load="8x Dedicated Studio Grade Grounded Outlets",
        discom_ca_number="TPDDL-DEL-44910283",
        amenities="Acoustic Paneling,Shure SM7B Mics,Boom Arms,Air Conditioning,Audio Interface",
        image_url="https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=800&q=80"
    )

    db.session.add_all([space_iitd, space_blr, space_powai, space_pune, space_cp])
    db.session.commit()

    # 4. Create Active Demo Booking for Live In-Room Session Console
    now = datetime.utcnow()
    lease = synthesize_micro_lease(
        space_title=space_iitd.title,
        space_address=space_iitd.address,
        host_name=host_vikram.name,
        renter_name=student_rohit.name,
        hours=3.0,
        rate_hourly=space_iitd.price_hourly,
        purpose="Hackathon prototype development and AI model fine-tuning",
        attendees_count=1
    )

    active_booking = Booking(
        space_id=space_iitd.id,
        renter_id=student_rohit.id,
        start_time=now - timedelta(minutes=45),
        end_time=now + timedelta(minutes=135),
        hours_booked=3.0,
        total_price=150.0,
        escrow_deposit_amount=100.0,
        escrow_status="held",
        session_state="checked_in",
        arrival_pin="4821",
        arrival_time=now - timedelta(minutes=42),
        checkin_gps_lat=28.5451,
        checkin_gps_lng=77.1925,
        checkin_distance_meters=14.2,
        punctuality_score=100.0,
        condition_match_score=95.0,
        appliances_shut_off=True,
        micro_lease_agreement=lease['agreement_text'],
        lease_hash=lease['lease_hash']
    )
    db.session.add(active_booking)
    db.session.commit()

    # 5. Add initial reviews and inquiries
    rev1 = Review(
        space_id=space_iitd.id,
        user_id=student_ananya.id,
        user_name="Ananya Sharma (IIT Bombay)",
        rating=5,
        comment="Incredible acoustic isolation. Was able to record my presentation and push my code sprint without any distractions. The QR check-in took 5 seconds!"
    )
    rev2 = Review(
        space_id=space_blr.id,
        user_id=student_rohit.id,
        user_name="Rohit Verma (IIT Delhi)",
        rating=5,
        comment="Fastest Wi-Fi in Koramangala. The ₹100 micro-escrow came back to my UPI within 10 seconds after my exit photo."
    )

    inq1 = SpaceInquiry(
        space_id=space_iitd.id,
        user_id=student_ananya.id,
        question="Is there power backup in case of local load shedding?",
        ai_answer="Yes! This space is equipped with 4x Grounded 20A Circuits and an automated 5kVA solar inverter backup ensuring uninterrupted power.",
        is_resolved=True
    )

    db.session.add_all([rev1, rev2, inq1])
    db.session.commit()
