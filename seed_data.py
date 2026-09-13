import hashlib
from datetime import datetime, timedelta
from models import db, User, Space, Booking, Review


def seed_database():
    """Seeds the database with realistic demo data for SpaceLoop India Edition."""
    if Space.query.first() is not None:
        return

    print("Seeding demo users and spaces for SpaceLoop India Edition...")

    # Create Demo Users
    # 1. Verified Host (Sunita Sharma - Hauz Khas Delhi)
    host1 = User(
        name="Sunita Sharma",
        email="sunita@spaceloop.in",
        role="owner",
        bio="Retired academic and homeowner near IIT Delhi. Providing quiet, safe study spaces for serious students.",
        phone="+91 98112 34567",
        avatar_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80",
        is_host_verified=True,
        discom_provider="TPDDL (Tata Power Delhi)",
        discom_ca_masked="***4821",
        upi_verified=True,
        upi_vpa_masked="sunita***@okhdfcbank",
        bank_beneficiary_name="Sunita Sharma",
        objective_trust_score=99.2,
        on_time_vacate_rate=100.0,
        cleanliness_match_rate=98.5,
        total_completed_hours=48.0,
        dispute_count=0
    )
    host1.set_password("password123")

    # 2. Host (Vikram Mehra - Koramangala Bangalore)
    host2 = User(
        name="Vikram Mehra",
        email="vikram@spaceloop.in",
        role="owner",
        bio="Tech mentor and cafe workspace host in Koramangala, Bangalore.",
        phone="+91 98450 12345",
        avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
        is_host_verified=True,
        discom_provider="BESCOM (Bangalore)",
        discom_ca_masked="***7190",
        upi_verified=True,
        upi_vpa_masked="vikram***@okaxis",
        bank_beneficiary_name="Vikram Mehra",
        objective_trust_score=98.7,
        on_time_vacate_rate=98.0,
        cleanliness_match_rate=99.0,
        total_completed_hours=32.0,
        dispute_count=0
    )
    host2.set_password("password123")

    # 3. Verified Student Seeker (Aarav Patel - IIT Delhi)
    renter1 = User(
        name="Aarav Patel",
        email="aarav@iitd.ac.in",
        role="seeker",
        bio="3rd-year CS student at IIT Delhi. Team lead for Smart India Hackathon.",
        phone="+91 99201 54321",
        avatar_url="https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=200&q=80",
        is_student_verified=True,
        college_name="Indian Institute of Technology (IIT) Delhi",
        college_email="aarav@iitd.ac.in",
        student_id_masked="STU-***-2024",
        is_aadhaar_verified=True,
        aadhaar_masked="XXXX-XXXX-4821",
        aadhaar_token_hash="a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        objective_trust_score=99.5,
        on_time_vacate_rate=100.0,
        cleanliness_match_rate=99.0,
        total_completed_hours=18.0,
        dispute_count=0
    )
    renter1.set_password("password123")

    db.session.add_all([host1, host2, renter1])
    db.session.commit()

    # Seed Spaces
    spaces_data = [
        {
            "owner_id": host1.id,
            "title": "Quiet AC Study Room & Project Studio (Near IIT Gate 1)",
            "category": "Studio",
            "description": "Clean, air-conditioned private study suite 400 meters from IIT Delhi Gate 1. Features 4 ergonomic study desks, 600 Mbps dual-band Wi-Fi, dry-erase whiteboard, multi-port power strips, and natural daylight. Ideal for hackathon teams, code sprints, and exam preparation.",
            "address": "B-4/22 Hauz Khas Enclave",
            "neighborhood": "Hauz Khas",
            "city": "New Delhi",
            "state": "Delhi",
            "zip_code": "110016",
            "latitude": 28.5450,
            "longitude": 77.1926,
            "geofence_radius_meters": 30,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "1004928172",
            "discom_consumer_name": "Sunita Sharma",
            "room_qr_token": "SPACELOOP_QR_IITD_ROOM1",
            "sqft": 240,
            "max_capacity": 5,
            "price_hourly": 75.0,  # Rs. 75/hr (split 4 ways = Rs. 18.75/student/hr)
            "price_daily": 450.0,
            "minimum_hours": 1,
            "amenities": ["Dual-Band Wi-Fi (600 Mbps)", "Air Conditioning", "Magnetic Whiteboard & Markers", "Power Outlets at Each Desk", "Drinking Water (RO Filtered)", "Private Washroom"],
            "rules": ["No smoking inside", "Shoes off at entrance door", "Keep conversation volume moderate", "Switch off AC and fans before checkout"],
            "photos": [
                "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"
            ],
            "ai_tags": ["AC Room", "High-Speed WiFi", "Whiteboard", "Quiet Zone", "Near IIT"],
            "ai_dimensions_summary": "15ft x 16ft (240 sqft) well-ventilated room",
            "ai_lighting": "Natural daylight window + 4000K neutral-white LED study tubes",
            "ai_noise_level": "Ultra Quiet (<32 dB ambient residential)",
            "ai_power_access": "6x surge-protected 3-pin Indian sockets + USB-C fast charging",
            "ai_safety_notes": "First aid box, MCB circuit breaker, CCTV in building common corridor.",
            "ai_recommended_uses": "Group study, hackathon code sprint, gate exam prep, mock interview practice",
            "ai_suitability_score": 99
        },
        {
            "owner_id": host2.id,
            "title": "High-Speed Hackathon Nook & Brainstorm Lounge",
            "category": "Workspace",
            "description": "Quiet terrace study nook in Koramangala 4th Block. Includes cushioned seating, motorized standing desks, 1 Gbps fiber internet, and complimentary filter coffee setup. 10 minutes from St. John's and Christ University.",
            "address": "Plot 88, 4th Block, 80 Feet Road",
            "neighborhood": "Koramangala",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560034",
            "latitude": 12.9352,
            "longitude": 77.6245,
            "geofence_radius_meters": 35,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "4821",
            "discom_ca_number": "5019284711",
            "discom_consumer_name": "Vikram Mehra",
            "room_qr_token": "SPACELOOP_QR_BLR_KORAMANGALA",
            "sqft": 300,
            "max_capacity": 6,
            "price_hourly": 80.0,
            "price_daily": 500.0,
            "minimum_hours": 2,
            "amenities": ["1 Gbps ACT Fibernet", "Dual Display Monitors", "Filter Coffee Machine", "Ergonomic Chairs", "Air Conditioning", "Terrace Breakout Area"],
            "rules": ["Pack in / pack out personal trash", "Lock door with keybox code on leaving", "Quiet hours after 10 PM"],
            "photos": [
                "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80"
            ],
            "ai_tags": ["1 Gbps Fiber", "Dual Monitors", "Terrace Lounge", "Keybox Access"],
            "ai_dimensions_summary": "16ft x 18ft (300 sqft) covered rooftop lounge",
            "ai_lighting": "Ambient warm ceiling track spotlights + natural airflow",
            "ai_noise_level": "Pleasant rooftop breeze, acoustic partition (<38 dB)",
            "ai_power_access": "Spike busters on every desk with UPS power backup",
            "ai_safety_notes": "Full UPS inverter backup guarantees zero Wi-Fi drop during power cuts.",
            "ai_recommended_uses": "Hackathon building, presentation rehearsal, engineering capstone work",
            "ai_suitability_score": 98
        },
        {
            "owner_id": host1.id,
            "title": "Clean Whiteboard Discussion Room (FC Road College Hub)",
            "category": "Studio",
            "description": "Quiet study nook right behind Ferguson College Road. Perfect for Pune university students preparing for engineering, medical, or UPSC exams.",
            "address": "12 Shivajinagar, Off FC Road",
            "neighborhood": "Shivajinagar",
            "city": "Pune",
            "state": "Maharashtra",
            "zip_code": "411005",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "geofence_radius_meters": 30,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "3928174620",
            "discom_consumer_name": "Sunita Sharma",
            "room_qr_token": "SPACELOOP_QR_PUNE_FCROAD",
            "sqft": 200,
            "max_capacity": 4,
            "price_hourly": 60.0,
            "price_daily": 350.0,
            "minimum_hours": 1,
            "amenities": ["Wi-Fi (300 Mbps)", "Large 6ft Whiteboard", "Ceiling Fan + Cooler", "Drinking Water"],
            "rules": ["Erase whiteboard before checking out", "No outdoor footwear inside"],
            "photos": [
                "https://images.unsplash.com/photo-1517502884422-41eaead166d4?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["FC Road", "UPSC / GATE", "Affordable", "Whiteboard"],
            "ai_dimensions_summary": "12ft x 16ft (200 sqft)",
            "ai_lighting": "Dual LED tubelights with zero flicker",
            "ai_noise_level": "Quiet residential society",
            "ai_power_access": "4x 5A sockets",
            "ai_safety_notes": "Gated residential apartment with security guard.",
            "ai_recommended_uses": "Maths problem solving, UPSC discussions, group study",
            "ai_suitability_score": 96
        },
        {
            "owner_id": host2.id,
            "title": "Secure Hardware Prototyping & Soldering Bench",
            "category": "Workspace",
            "description": "Dedicated electronics workbench with ESD mat, soldering stations, oscilloscope, and fume extractor. Ideal for IoT and robotics student teams.",
            "address": "Industrial Area, Phase 2",
            "neighborhood": "Sector 62",
            "city": "Noida",
            "state": "Uttar Pradesh",
            "zip_code": "201309",
            "latitude": 28.6270,
            "longitude": 77.3725,
            "geofence_radius_meters": 40,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "9021",
            "discom_ca_number": "7261548291",
            "discom_consumer_name": "Vikram Mehra",
            "room_qr_token": "SPACELOOP_QR_NOIDA_ROBOTICS",
            "sqft": 350,
            "max_capacity": 4,
            "price_hourly": 85.0,
            "price_daily": 520.0,
            "minimum_hours": 2,
            "amenities": ["ESD Work Mat", "Soldering Station (Weller)", "Fume Extractor", "Digital Multimeter", "Fast Internet"],
            "rules": ["Wear safety glasses during soldering", "Turn off soldering iron power strip before exit"],
            "photos": [
                "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Hardware Lab", "Soldering Station", "Robotics Ready", "Maker Space"],
            "ai_dimensions_summary": "15ft x 23ft (350 sqft)",
            "ai_lighting": "Overhead 6500K bright task lighting",
            "ai_noise_level": "Maker workshop environment",
            "ai_power_access": "Multiple 15A heavy-duty sockets with circuit breakers",
            "ai_safety_notes": "CO2 fire extinguisher on wall, smoke detector installed.",
            "ai_recommended_uses": "PCB assembly, robotics chassis testing, 3D print prototyping",
            "ai_suitability_score": 97
        },
        {
            "owner_id": host1.id,
            "title": "North Campus Quiet Study Pod (Delhi University)",
            "category": "Studio",
            "description": "Silent reading and study suite located 2 minutes from Vishwavidyalaya Metro and Hansraj College. Ideal for semester exams, paper writing, and group discussions.",
            "address": "14 Chhatra Marg, North Campus",
            "neighborhood": "North Campus",
            "city": "New Delhi",
            "state": "Delhi",
            "zip_code": "110007",
            "latitude": 28.6900,
            "longitude": 77.2100,
            "geofence_radius_meters": 30,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "1009283741",
            "discom_consumer_name": "Sunita Sharma",
            "room_qr_token": "SPACELOOP_QR_DELHI_NORTHCAMPUS",
            "sqft": 220,
            "max_capacity": 4,
            "price_hourly": 65.0,
            "price_daily": 400.0,
            "minimum_hours": 1,
            "amenities": ["High-Speed Wi-Fi", "Silent Air Conditioning", "Bookshelf Reference Library", "RO Water Dispenser"],
            "rules": ["Strict silence in main room", "No food at study desks"],
            "photos": [
                "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["DU North Campus", "Near Metro", "Silent Zone", "Air Conditioned"],
            "ai_dimensions_summary": "14ft x 16ft (220 sqft)",
            "ai_lighting": "Soft indirect 4000K study lighting",
            "ai_noise_level": "Acoustically insulated (<30 dB)",
            "ai_power_access": "Surge-protected outlets at each study station",
            "ai_safety_notes": "CCTV outside in corridor, fire extinguisher.",
            "ai_recommended_uses": "Final exam cramming, dissertation writing, research synthesis",
            "ai_suitability_score": 98
        },
        {
            "owner_id": host2.id,
            "title": "IIT Bombay Tech Incubator Nook & Hackathon Lab",
            "category": "Workspace",
            "description": "High-tech project room overlooking Powai lake. Equipped with dual 4K monitors, high-speed fiber internet, and whiteboards.",
            "address": "Hiranandani Gardens, Powai",
            "neighborhood": "Powai",
            "city": "Mumbai",
            "state": "Maharashtra",
            "zip_code": "400076",
            "latitude": 19.1334,
            "longitude": 72.9133,
            "geofence_radius_meters": 35,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "5678",
            "discom_ca_number": "2910482710",
            "discom_consumer_name": "Vikram Mehra",
            "room_qr_token": "SPACELOOP_QR_MUMBAI_POWAI",
            "sqft": 300,
            "max_capacity": 5,
            "price_hourly": 90.0,
            "price_daily": 580.0,
            "minimum_hours": 2,
            "amenities": ["1 Gbps JioFiber", "2x 27-inch 4K Displays", "Coffee Machine", "Air Conditioning", "Ergonomic Chairs"],
            "rules": ["Unplug monitors after use", "Lock door with keybox code on departure"],
            "photos": [
                "https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Powai", "Near IIT Bombay", "Dual 4K Displays", "Lake View"],
            "ai_dimensions_summary": "16ft x 19ft (300 sqft)",
            "ai_lighting": "Dimmable daylight track lighting",
            "ai_noise_level": "Quiet professional co-working floor",
            "ai_power_access": "8x 15A outlets with uninterrupted UPS backup",
            "ai_safety_notes": "Commercial building fire safety certified.",
            "ai_recommended_uses": "Hackathon building, investor pitch practice, startup sprints",
            "ai_suitability_score": 99
        }
    ]

    for data in spaces_data:
        s = Space(**data)
        db.session.add(s)

    db.session.commit()

    # Add a sample active booking for Aarav Patel on Space 1
    # Scheduled for right now so Aarav can test the Live In-Room Session Console immediately!
    now = datetime.utcnow()
    demo_booking = Booking(
        space_id=1,
        renter_id=renter1.id,
        start_time=now - timedelta(minutes=45),
        end_time=now + timedelta(hours=2, minutes=15),
        hours_booked=3.0,
        total_price=225.0,  # 3 hours @ Rs. 75/hr
        status="confirmed",
        session_state="confirmed",
        arrival_pin="4821",
        intended_purpose="Smart India Hackathon Finals Prep & System Architecture Review",
        attendees_count=4,
        special_requests="Need extra markers for the whiteboard and quiet setting for mentor zoom call.",
        escrow_deposit_amount=100.0,
        escrow_status="held",
        micro_lease_agreement="SPACELOOP DIGITALLY SIGNED MICRO-LEASE (Indian Easements Act, 1882):\nPermissive revocable license granted to Aarav Patel for 3 hours. Deposit of Rs. 100 held in UPI micro-escrow. Full refund upon QR scan checkout and AI cleanliness verification."
    )
    db.session.add(demo_booking)

    # Add verified reviews
    rev1 = Review(
        space_id=1,
        user_id=renter1.id,
        user_name="Aarav Patel (IIT Delhi)",
        rating=5,
        comment="Best study room near campus! AC was chilled, whiteboard was spotless, and Sunita aunty was very welcoming. Scanned the QR at the door and checked out in 10 seconds."
    )
    db.session.add(rev1)
    db.session.commit()
    print("Database seeded with SpaceLoop India Edition demo data.")
