import hashlib
from datetime import datetime, timedelta
from models import db, User, Space, Booking, Review, SpaceInquiry


def seed_database(force=False):
    """
    Seeds the database with realistic development and demo data for SpaceLoop India Edition.
    Idempotent and safe: avoids duplicate entries while ensuring all required demo entities exist.
    """
    # -------------------------------------------------------------
    # 1. Hosts & Renters (Users)
    # -------------------------------------------------------------
    demo_users = [
        # Hosts
        {
            "name": "Sunita Sharma",
            "email": "sunita@spaceloop.in",
            "role": "owner",
            "bio": "Retired academic and homeowner near IIT Delhi. Providing quiet, safe study spaces for serious students.",
            "phone": "+91 98112 34567",
            "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80",
            "is_host_verified": True,
            "discom_provider": "TPDDL (Tata Power Delhi)",
            "discom_ca_masked": "***4821",
            "upi_verified": True,
            "upi_vpa_masked": "sunita***@okhdfcbank",
            "bank_beneficiary_name": "Sunita Sharma",
            "objective_trust_score": 99.2,
            "on_time_vacate_rate": 100.0,
            "cleanliness_match_rate": 98.5,
            "total_completed_hours": 48.0,
            "dispute_count": 0
        },
        {
            "name": "Vikram Mehra",
            "email": "vikram@spaceloop.in",
            "role": "owner",
            "bio": "Tech mentor and cafe workspace host in Koramangala, Bangalore.",
            "phone": "+91 98450 12345",
            "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
            "is_host_verified": True,
            "discom_provider": "BESCOM (Bangalore)",
            "discom_ca_masked": "***7190",
            "upi_verified": True,
            "upi_vpa_masked": "vikram***@okaxis",
            "bank_beneficiary_name": "Vikram Mehra",
            "objective_trust_score": 98.7,
            "on_time_vacate_rate": 98.0,
            "cleanliness_match_rate": 99.0,
            "total_completed_hours": 32.0,
            "dispute_count": 0
        },
        {
            "name": "Rajesh Kulkarni",
            "email": "rajesh@spaceloop.in",
            "role": "owner",
            "bio": "Former mechanical engineer hosting study pods and student workspaces near colleges in Wagholi & Shivajinagar, Pune.",
            "phone": "+91 98220 98765",
            "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80",
            "is_host_verified": True,
            "discom_provider": "MSEDCL (Maharashtra Discom)",
            "discom_ca_masked": "***4921",
            "upi_verified": True,
            "upi_vpa_masked": "rajesh***@oksbi",
            "bank_beneficiary_name": "Rajesh Kulkarni",
            "objective_trust_score": 98.9,
            "on_time_vacate_rate": 99.0,
            "cleanliness_match_rate": 98.0,
            "total_completed_hours": 26.0,
            "dispute_count": 0
        },
        {
            "name": "Ananya Sengupta",
            "email": "ananya@spaceloop.in",
            "role": "owner",
            "bio": "Design architect and creative studio host in Powai, Mumbai. Passionate about empowering student creators.",
            "phone": "+91 98190 33445",
            "avatar_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80",
            "is_host_verified": True,
            "discom_provider": "Adani Electricity Mumbai",
            "discom_ca_masked": "***6021",
            "upi_verified": True,
            "upi_vpa_masked": "ananya***@okicici",
            "bank_beneficiary_name": "Ananya Sengupta",
            "objective_trust_score": 99.4,
            "on_time_vacate_rate": 100.0,
            "cleanliness_match_rate": 99.5,
            "total_completed_hours": 42.0,
            "dispute_count": 0
        },
        # Renters (Seekers)
        {
            "name": "Aarav Patel",
            "email": "aarav@iitd.ac.in",
            "role": "seeker",
            "bio": "3rd-year CS student at IIT Delhi. Team lead for Smart India Hackathon.",
            "phone": "+91 99201 54321",
            "avatar_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=200&q=80",
            "is_student_verified": True,
            "college_name": "Indian Institute of Technology (IIT) Delhi",
            "college_email": "aarav@iitd.ac.in",
            "student_id_masked": "STU-***-2024",
            "is_aadhaar_verified": True,
            "aadhaar_masked": "XXXX-XXXX-4821",
            "aadhaar_token_hash": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
            "objective_trust_score": 99.5,
            "on_time_vacate_rate": 100.0,
            "cleanliness_match_rate": 99.0,
            "total_completed_hours": 18.0,
            "dispute_count": 0
        },
        {
            "name": "Priya Sharma",
            "email": "priya@coep.ac.in",
            "role": "seeker",
            "bio": "Final year electronics student at COEP Tech University Pune. Building embedded IoT systems.",
            "phone": "+91 98230 45678",
            "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80",
            "is_student_verified": True,
            "college_name": "COEP Technological University, Pune",
            "college_email": "priya@coep.ac.in",
            "student_id_masked": "STU-***-8841",
            "is_aadhaar_verified": True,
            "aadhaar_masked": "XXXX-XXXX-3921",
            "aadhaar_token_hash": "b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890a1",
            "objective_trust_score": 98.8,
            "on_time_vacate_rate": 99.2,
            "cleanliness_match_rate": 98.5,
            "total_completed_hours": 14.0,
            "dispute_count": 0
        },
        {
            "name": "Rohan Verma",
            "email": "rohan@bits.ac.in",
            "role": "seeker",
            "bio": "Computer Science student at BITS Pilani. Preparing for competitive programming contests and ACM ICPC.",
            "phone": "+91 98765 43210",
            "avatar_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=200&q=80",
            "is_student_verified": True,
            "college_name": "BITS Pilani",
            "college_email": "rohan@bits.ac.in",
            "student_id_masked": "STU-***-5512",
            "is_aadhaar_verified": True,
            "aadhaar_masked": "XXXX-XXXX-6102",
            "aadhaar_token_hash": "c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890a1b2",
            "objective_trust_score": 97.9,
            "on_time_vacate_rate": 98.0,
            "cleanliness_match_rate": 97.8,
            "total_completed_hours": 22.0,
            "dispute_count": 0
        },
        {
            "name": "Sneha Iyer",
            "email": "sneha@iisc.ac.in",
            "role": "seeker",
            "bio": "Graduate researcher in AI/ML at IISc Bangalore. Regular participant in Kaggle grandmaster sprints.",
            "phone": "+91 97400 11223",
            "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
            "is_student_verified": True,
            "college_name": "Indian Institute of Science (IISc), Bangalore",
            "college_email": "sneha@iisc.ac.in",
            "student_id_masked": "STU-***-9904",
            "is_aadhaar_verified": True,
            "aadhaar_masked": "XXXX-XXXX-8820",
            "aadhaar_token_hash": "d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890a1b2c3",
            "objective_trust_score": 99.1,
            "on_time_vacate_rate": 100.0,
            "cleanliness_match_rate": 99.2,
            "total_completed_hours": 30.0,
            "dispute_count": 0
        },
        {
            "name": "Kabir Mehta",
            "first_name": "Kabir",
            "last_name": "Mehta",
            "email": "kabir@du.ac.in",
            "role": "seeker",
            "bio": "Economics student at Delhi University. Organizer for debating societies and mock parliament conferences.",
            "phone": "+91 99112 77889",
            "avatar_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=200&q=80",
            "is_student_verified": True,
            "college_name": "University of Delhi (Hansraj College)",
            "college_email": "kabir@du.ac.in",
            "student_id_masked": "STU-***-3341",
            "is_aadhaar_verified": True,
            "aadhaar_masked": "XXXX-XXXX-7714",
            "aadhaar_token_hash": "e5f67890abcdef1234567890abcdef1234567890abcdef1234567890a1b2c3d4",
            "objective_trust_score": 96.8,
            "on_time_vacate_rate": 97.0,
            "cleanliness_match_rate": 96.5,
            "total_completed_hours": 12.0,
            "dispute_count": 0
        },
        # Explicit Dev Fixtures for Testing & Local Development
        {
            "name": "Dev Host",
            "first_name": "Dev",
            "last_name": "Host",
            "email": "dev-host@spaceloop.local",
            "role": "owner",
            "bio": "Local development host test account for automated test suites and role switching.",
            "phone": "+91 98000 00001",
            "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
            "is_host_verified": True,
            "discom_provider": "TPDDL (Tata Power Delhi)",
            "discom_ca_masked": "***9999",
            "upi_verified": True,
            "upi_vpa_masked": "devhost@upi",
            "bank_beneficiary_name": "Dev Host",
            "objective_trust_score": 99.0,
            "is_admin": False
        },
        {
            "name": "Dev Seeker",
            "first_name": "Dev",
            "last_name": "Seeker",
            "email": "dev-seeker@spaceloop.local",
            "role": "seeker",
            "bio": "Local development student seeker account for automated test suites.",
            "phone": "+91 98000 00002",
            "avatar_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=200&q=80",
            "is_student_verified": True,
            "college_name": "SpaceLoop University",
            "college_email": "dev-seeker@spaceloop.local",
            "student_id_masked": "STU-DEV-001",
            "is_aadhaar_verified": True,
            "aadhaar_masked": "XXXX-XXXX-9999",
            "objective_trust_score": 99.0,
            "is_admin": False
        },
        {
            "name": "Dev Admin",
            "first_name": "Dev",
            "last_name": "Admin",
            "email": "dev-admin@spaceloop.local",
            "role": "owner",
            "bio": "Platform Super Administrator account for moderation, disputes, and governance.",
            "phone": "+91 98000 00003",
            "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
            "is_host_verified": True,
            "upi_verified": True,
            "objective_trust_score": 100.0,
            "is_admin": True
        }
    ]

    for u_data in demo_users:
        existing = User.query.filter_by(email=u_data["email"]).first()
        if not existing:
            name_parts = u_data.get("name", "").split(" ", 1)
            u_data.setdefault("first_name", name_parts[0] if name_parts else "")
            u_data.setdefault("last_name", name_parts[1] if len(name_parts) > 1 else "")
            u_data["is_active"] = True
            u_data["is_email_verified"] = True
            u = User(**u_data)
            u.set_password("password123")
            db.session.add(u)
        else:
            if not existing.password_hash:
                existing.set_password("password123")
            existing.is_active = True
            existing.is_email_verified = True
            if "is_admin" in u_data:
                existing.is_admin = u_data["is_admin"]
            if not existing.first_name and existing.name:
                parts = existing.name.split(" ", 1)
                existing.first_name = parts[0]
                existing.last_name = parts[1] if len(parts) > 1 else ""
    db.session.commit()

    # Retrieve committed user references
    host_sunita = User.query.filter_by(email="sunita@spaceloop.in").first()
    host_vikram = User.query.filter_by(email="vikram@spaceloop.in").first()
    host_rajesh = User.query.filter_by(email="rajesh@spaceloop.in").first()
    host_ananya = User.query.filter_by(email="ananya@spaceloop.in").first()

    renter_aarav = User.query.filter_by(email="aarav@iitd.ac.in").first()
    renter_priya = User.query.filter_by(email="priya@coep.ac.in").first()
    renter_rohan = User.query.filter_by(email="rohan@bits.ac.in").first()
    renter_sneha = User.query.filter_by(email="sneha@iisc.ac.in").first()
    renter_kabir = User.query.filter_by(email="kabir@du.ac.in").first()

    # -------------------------------------------------------------
    # 2. Spaces Across Strategic Indian Educational & Tech Hubs
    # -------------------------------------------------------------
    spaces_data = [
        {
            "owner_id": host_sunita.id,
            "title": "Quiet AC Study Room & Project Studio (Near IIT Gate 1)",
            "category": "Study",
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
            "price_hourly": 75.0,
            "price_daily": 450.0,
            "minimum_hours": 1,
            "amenities": ["Dual-Band Wi-Fi (600 Mbps)", "Air Conditioning", "Magnetic Whiteboard & Markers", "Power Outlets at Each Desk", "Drinking Water (RO Filtered)", "Private Washroom"],
            "rules": ["No smoking inside", "Shoes off at entrance door", "Keep conversation volume moderate", "Switch off AC and fans before checkout"],
            "photos": [
                "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80"
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
            "owner_id": host_vikram.id,
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
                "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80"
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
            "owner_id": host_rajesh.id,
            "title": "Clean Whiteboard Discussion Room (FC Road College Hub)",
            "category": "Meeting",
            "description": "Quiet discussion and collaborative room right behind Ferguson College Road. Perfect for Pune university students preparing for engineering, medical, or UPSC exams.",
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
            "discom_consumer_name": "Rajesh Kulkarni",
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
            "owner_id": host_vikram.id,
            "title": "Secure Hardware Prototyping & Soldering Bench",
            "category": "Creative",
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
            "owner_id": host_sunita.id,
            "title": "North Campus Quiet Study Pod (Delhi University)",
            "category": "Study",
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
                "https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=1200&q=80"
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
            "owner_id": host_ananya.id,
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
            "discom_consumer_name": "Ananya Sengupta",
            "room_qr_token": "SPACELOOP_QR_MUMBAI_POWAI",
            "sqft": 300,
            "max_capacity": 5,
            "price_hourly": 90.0,
            "price_daily": 580.0,
            "minimum_hours": 2,
            "amenities": ["1 Gbps JioFiber", "2x 27-inch 4K Displays", "Coffee Machine", "Air Conditioning", "Ergonomic Chairs"],
            "rules": ["Unplug monitors after use", "Lock door with keybox code on departure"],
            "photos": [
                "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Powai", "Near IIT Bombay", "Dual 4K Displays", "Lake View"],
            "ai_dimensions_summary": "16ft x 19ft (300 sqft)",
            "ai_lighting": "Dimmable daylight track lighting",
            "ai_noise_level": "Quiet professional co-working floor",
            "ai_power_access": "8x 15A outlets with uninterrupted UPS backup",
            "ai_safety_notes": "Commercial building fire safety certified.",
            "ai_recommended_uses": "Hackathon building, investor pitch practice, startup sprints",
            "ai_suitability_score": 99
        },
        {
            "owner_id": host_rajesh.id,
            "title": "Quiet Study Pod & Hackathon Workstation (Near JSPM Wagholi)",
            "category": "Study",
            "description": "Acoustically damped project studio and study suite situated 300 meters from JSPM Imperial College campus in Wagholi, Pune. Equipped with 300 Mbps fiber internet, ergonomic study desks, dual monitor setup, whiteboard, and 24/7 power backup.",
            "address": "Bakori Road, Near JSPM Campus",
            "neighborhood": "Wagholi",
            "city": "Pune",
            "state": "Maharashtra",
            "zip_code": "412207",
            "latitude": 18.5793,
            "longitude": 73.9822,
            "geofence_radius_meters": 30,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "4920194821",
            "discom_consumer_name": "Rajesh Kulkarni",
            "room_qr_token": "SPACELOOP_QR_PUNE_WAGHOLI",
            "sqft": 220,
            "max_capacity": 4,
            "price_hourly": 55.0,
            "price_daily": 320.0,
            "minimum_hours": 1,
            "amenities": ["High-Speed Wi-Fi (300 Mbps)", "Whiteboard & Markers", "Air Cooler", "Drinking Water", "Dual Display Monitor"],
            "rules": ["No loud conversation", "Switch off appliances after use", "Clean desk before leaving"],
            "photos": [
                "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Wagholi", "Near JSPM", "Study Pod", "Dual Monitor"],
            "ai_dimensions_summary": "14ft x 16ft (220 sqft)",
            "ai_lighting": "Abundant natural daylight window + warm 4000K LED task lights",
            "ai_noise_level": "Quiet study environment (<35 dB)",
            "ai_power_access": "Surge-protected multi-plug power strip at every desk",
            "ai_safety_notes": "MCB breaker, CCTV in building reception, first-aid box.",
            "ai_recommended_uses": "College group study, coding sprints, exam preparation",
            "ai_suitability_score": 97
        },
        {
            "owner_id": host_sunita.id,
            "title": "Solar-Powered EV Two-Wheeler Charging & Parking Bay",
            "category": "Parking",
            "description": "Secure, covered gated parking slot in Hauz Khas with 16A standard EV scooter plug and solar inverter backup. Safe 24/7 access with CCTV surveillance.",
            "address": "B-4/18 Hauz Khas Enclave",
            "neighborhood": "Hauz Khas",
            "city": "New Delhi",
            "state": "Delhi",
            "zip_code": "110016",
            "latitude": 28.5442,
            "longitude": 77.1935,
            "geofence_radius_meters": 25,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "1004928199",
            "discom_consumer_name": "Sunita Sharma",
            "room_qr_token": "SPACELOOP_QR_IITD_PARKING",
            "sqft": 90,
            "max_capacity": 2,
            "price_hourly": 25.0,
            "price_daily": 140.0,
            "minimum_hours": 1,
            "amenities": ["16A EV Charging Point", "Covered Shed", "CCTV Monitoring", "Gated Security Guard"],
            "rules": ["Park within designated yellow lines", "Ensure charging switch is turned off before unplugging"],
            "photos": [
                "https://images.unsplash.com/photo-1590674899484-d5640e854abe?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["EV Charging", "Covered Parking", "CCTV", "Near Metro"],
            "ai_dimensions_summary": "9ft x 10ft (90 sqft) covered bay",
            "ai_lighting": "Solar-powered motion detector floodlight",
            "ai_noise_level": "Outdoor driveway",
            "ai_power_access": "1x 16A industrial socket with surge protector",
            "ai_safety_notes": "24/7 society guard on duty, dry powder fire extinguisher.",
            "ai_recommended_uses": "Electric scooter parking, Ather/Ola EV charging while attending classes",
            "ai_suitability_score": 95
        },
        {
            "owner_id": host_ananya.id,
            "title": "Acoustic Podcast & Vocal Recording Cabin",
            "category": "Studio",
            "description": "Soundproofed audio recording suite featuring Rode PodMic microphones, Focusrite Scarlett audio interface, boom arms, and studio headphones. Perfect for creator student projects, tech interviews, and audio podcasts.",
            "address": "100 Feet Road, HAL 2nd Stage, Indiranagar",
            "neighborhood": "Indiranagar",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560038",
            "latitude": 12.9716,
            "longitude": 77.6412,
            "geofence_radius_meters": 30,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "7712",
            "discom_ca_number": "5019289944",
            "discom_consumer_name": "Ananya Sengupta",
            "room_qr_token": "SPACELOOP_QR_BLR_PODCAST",
            "sqft": 180,
            "max_capacity": 3,
            "price_hourly": 95.0,
            "price_daily": 600.0,
            "minimum_hours": 1,
            "amenities": ["2x Rode PodMic Broadcast Mics", "Focusrite Audio Interface", "Acoustic Foam Walls (<25 dB)", "High-Speed Wi-Fi", "Studio Monitor Headphones"],
            "rules": ["No food or unsealed beverages in recording booth", "Wipe down microphone pop filters upon departure"],
            "photos": [
                "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Podcast Studio", "Soundproof", "Rode Microphones", "Indiranagar"],
            "ai_dimensions_summary": "12ft x 15ft (180 sqft) acoustic booth",
            "ai_lighting": "Custom RGB dimmable mood lighting + warm studio wash",
            "ai_noise_level": "Studio broadcast grade (<22 dB noise floor)",
            "ai_power_access": "Multiple clean audio ground power lines",
            "ai_safety_notes": "Studio emergency lighting and soundproof acoustic door escape release.",
            "ai_recommended_uses": "Podcast production, voiceovers, remote mentor interview broadcasts",
            "ai_suitability_score": 99
        },
        {
            "owner_id": host_rajesh.id,
            "title": "Secure Ground Floor Dry Storage & Gear Unit",
            "category": "Storage",
            "description": "Clean, moisture-controlled ground floor storage unit located off Nagar Road, Wagholi. Includes keypad access, perimeter CCTV, dry shelving, and easy vehicle drive-in access for college project kits and luggage.",
            "address": "Gate 3, Ivy Estate Road",
            "neighborhood": "Wagholi",
            "city": "Pune",
            "state": "Maharashtra",
            "zip_code": "412207",
            "latitude": 18.5830,
            "longitude": 73.9910,
            "geofence_radius_meters": 35,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "6241",
            "discom_ca_number": "4920883190",
            "discom_consumer_name": "Rajesh Kulkarni",
            "room_qr_token": "SPACELOOP_QR_PUNE_STORAGE",
            "sqft": 160,
            "max_capacity": 2,
            "price_hourly": 40.0,
            "price_daily": 220.0,
            "minimum_hours": 2,
            "amenities": ["24/7 Keybox Access", "Moisture Protection", "Heavy Duty Steel Shelving", "CCTV Surveillance", "Drive-in Loading Bay"],
            "rules": ["No flammable materials or perishable food items", "Ensure deadbolt is engaged when leaving"],
            "photos": [
                "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Storage Unit", "Wagholi", "Ground Floor", "Luggage Storage"],
            "ai_dimensions_summary": "10ft x 16ft (160 sqft) secure dry bay",
            "ai_lighting": "Overhead LED motion-activated tubelights",
            "ai_noise_level": "Silent secure storage corridor",
            "ai_power_access": "2x 5A utility charging sockets",
            "ai_safety_notes": "Smoke detectors and dry powder fire extinguisher installed.",
            "ai_recommended_uses": "Luggage between semesters, college club equipment, prototype storage",
            "ai_suitability_score": 96
        },
        {
            "owner_id": host_rajesh.id,
            "title": "Architectural Drafting & Design Prototyping Studio",
            "category": "Creative",
            "description": "Sunlit creative studio designed for architecture and product design students in Aundh, Pune. Equipped with large tilting drafting tables, cutting mats, A1 plot review wall, and natural northern light.",
            "address": "DP Road, Harmony Heights",
            "neighborhood": "Aundh",
            "city": "Pune",
            "state": "Maharashtra",
            "zip_code": "411007",
            "latitude": 18.5601,
            "longitude": 73.8031,
            "geofence_radius_meters": 30,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "3920194451",
            "discom_consumer_name": "Rajesh Kulkarni",
            "room_qr_token": "SPACELOOP_QR_PUNE_DESIGN",
            "sqft": 280,
            "max_capacity": 5,
            "price_hourly": 70.0,
            "price_daily": 440.0,
            "minimum_hours": 1,
            "amenities": ["Tilting Drafting Tables", "A1 Pin-Up Review Wall", "High-Speed Wi-Fi", "Cutting Mats & Rulers", "Tea/Coffee Station"],
            "rules": ["Use cutting mats for all hobby knives and cutters", "Clean up drafting trimmings before checkout"],
            "photos": [
                "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Design Studio", "Architecture Drafting", "Aundh", "Natural Light"],
            "ai_dimensions_summary": "14ft x 20ft (280 sqft) studio",
            "ai_lighting": "Northern daylight glazing + 5000K daylight balanced track lamps",
            "ai_noise_level": "Serene creative work environment (<35 dB)",
            "ai_power_access": "Tabletop power towers with surge protection",
            "ai_safety_notes": "First aid box, MCB panel, corridor security cameras.",
            "ai_recommended_uses": "Architecture model making, design jury prep, UI/UX prototyping",
            "ai_suitability_score": 98
        },
        {
            "owner_id": host_sunita.id,
            "title": "Executive Glass Whiteboard & Meeting Suite",
            "category": "Meeting",
            "description": "High-end corporate meeting suite in Cyber City, Gurgaon. Features a 10-seater conference table, magnetic glass whiteboard, 65-inch 4K presentation display with HDMI/AirPlay, and conference call speakerphone.",
            "address": "DLF Cyber City, Tower B",
            "neighborhood": "Cyber City",
            "city": "New Delhi",
            "state": "Haryana",
            "zip_code": "122002",
            "latitude": 28.4900,
            "longitude": 77.0900,
            "geofence_radius_meters": 40,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "8812",
            "discom_ca_number": "1009988211",
            "discom_consumer_name": "Sunita Sharma",
            "room_qr_token": "SPACELOOP_QR_GURGAON_MEETING",
            "sqft": 320,
            "max_capacity": 10,
            "price_hourly": 110.0,
            "price_daily": 700.0,
            "minimum_hours": 1,
            "amenities": ["65-inch 4K Display", "Glass Whiteboard", "Jabra Speakerphone", "Enterprise Gigabit Wi-Fi", "Espresso Coffee Machine"],
            "rules": ["Erase whiteboard after meeting", "Turn off AV screen and AV switch box on exit"],
            "photos": [
                "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Meeting Room", "Cyber City", "Presentation Display", "Corporate Hub"],
            "ai_dimensions_summary": "16ft x 20ft (320 sqft)",
            "ai_lighting": "Dimmable conference perimeter lighting",
            "ai_noise_level": "Acoustically isolated glass conference suite (<28 dB)",
            "ai_power_access": "In-table pop-up HDMI, USB-C, and AC sockets",
            "ai_safety_notes": "Commercial building standard fire sprinklers and emergency exits.",
            "ai_recommended_uses": "Client pitch meetings, hackathon judging presentations, team sprints",
            "ai_suitability_score": 99
        },
        {
            "owner_id": host_rajesh.id,
            "title": "Private Coding & Dual-Monitor Pod (Viman Nagar)",
            "category": "Workspace",
            "description": "Quiet personal coding workstation in Viman Nagar, Pune. Includes dual 27-inch monitors, mechanical keyboard friendly desk, Herman Miller style mesh chair, and 300 Mbps low-latency fiber.",
            "address": "Near Symbiosis Campus, Viman Nagar",
            "neighborhood": "Viman Nagar",
            "city": "Pune",
            "state": "Maharashtra",
            "zip_code": "411014",
            "latitude": 18.5679,
            "longitude": 73.9143,
            "geofence_radius_meters": 30,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "4920198822",
            "discom_consumer_name": "Rajesh Kulkarni",
            "room_qr_token": "SPACELOOP_QR_PUNE_VIMANNAGAR",
            "sqft": 140,
            "max_capacity": 2,
            "price_hourly": 65.0,
            "price_daily": 390.0,
            "minimum_hours": 1,
            "amenities": ["Dual 27-inch Displays", "Ergonomic Mesh Chair", "Low Latency 300 Mbps Fiber", "Air Conditioning", "Cold Water Dispenser"],
            "rules": ["Keep monitors on native resolution", "No open beverages near keyboards"],
            "photos": [
                "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Dual Monitor", "Viman Nagar", "Near Symbiosis", "Developer Pod"],
            "ai_dimensions_summary": "10ft x 14ft (140 sqft)",
            "ai_lighting": "Backlit screen ambient bias lighting + warm LED desk lamp",
            "ai_noise_level": "Quiet residential coding nook (<32 dB)",
            "ai_power_access": "4x 5A desktop surge sockets with USB-C PD",
            "ai_safety_notes": "UPS battery backup ensures zero disconnection during power dips.",
            "ai_recommended_uses": "Competitive programming sprints, open source contributions, remote interviews",
            "ai_suitability_score": 98
        },
        {
            "owner_id": host_rajesh.id,
            "title": "Collaborative Team Sprint & Workshop Room (Kothrud)",
            "category": "Meeting",
            "description": "Flexible workshop room with movable tables and high-density seating near MIT World Peace University, Kothrud. Equipped with high-speed internet, projector, and wall-to-wall whiteboard paint.",
            "address": "Paud Road, Ideal Colony",
            "neighborhood": "Kothrud",
            "city": "Pune",
            "state": "Maharashtra",
            "zip_code": "411038",
            "latitude": 18.5074,
            "longitude": 73.8077,
            "geofence_radius_meters": 35,
            "physical_access_type": "caretaker_handshake",
            "discom_ca_number": "3920197711",
            "discom_consumer_name": "Rajesh Kulkarni",
            "room_qr_token": "SPACELOOP_QR_PUNE_KOTHRUD",
            "sqft": 260,
            "max_capacity": 6,
            "price_hourly": 80.0,
            "price_daily": 480.0,
            "minimum_hours": 2,
            "amenities": ["1080p Projector & Screen", "Wall-to-Wall Whiteboard", "Modular Desks", "Wi-Fi (300 Mbps)", "Air Conditioning"],
            "rules": ["Reset modular desks to perimeter layout when leaving", "Wipe projector lens gently"],
            "photos": [
                "https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Kothrud", "Projector", "Team Sprint", "Modular Tables"],
            "ai_dimensions_summary": "14ft x 18ft (260 sqft)",
            "ai_lighting": "Adjustable warm/cool LED dimmable panel lights",
            "ai_noise_level": "Sound-isolated meeting room (<34 dB)",
            "ai_power_access": "Multiple floor boxes with AC sockets",
            "ai_safety_notes": "Fire alarm, two emergency exits, CCTV in lobby.",
            "ai_recommended_uses": "Design sprint workshops, team standups, product demo rehearsals",
            "ai_suitability_score": 97
        },
        {
            "owner_id": host_ananya.id,
            "title": "Photography & Creator Content Studio (Bandra West)",
            "category": "Studio",
            "description": "Boutique photo and video creator studio near Carter Road, Bandra West. Includes 3-color seamless backdrop roll (white, chroma green, black), 2x Godox softbox continuous video lights, and makeup vanity mirror.",
            "address": "Pali Hill Road, Bandra West",
            "neighborhood": "Bandra",
            "city": "Mumbai",
            "state": "Maharashtra",
            "zip_code": "400050",
            "latitude": 19.0596,
            "longitude": 72.8295,
            "geofence_radius_meters": 30,
            "physical_access_type": "mechanical_keybox",
            "keybox_code": "3341",
            "discom_ca_number": "2910488812",
            "discom_consumer_name": "Ananya Sengupta",
            "room_qr_token": "SPACELOOP_QR_MUMBAI_BANDRA",
            "sqft": 250,
            "max_capacity": 4,
            "price_hourly": 120.0,
            "price_daily": 750.0,
            "minimum_hours": 2,
            "amenities": ["Godox Softbox Lighting Kit", "3-Color Seamless Paper Rolls", "Chroma Key Green Screen", "Vanity Mirror", "High-Speed Wi-Fi", "Air Conditioning"],
            "rules": ["Do not walk on backdrops with outdoor shoes", "Turn off high-output studio lights after shoot"],
            "photos": [
                "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=1200&q=80"
            ],
            "ai_tags": ["Photo Studio", "Bandra West", "Green Screen", "Creator Friendly"],
            "ai_dimensions_summary": "14ft x 18ft (250 sqft) studio with 10ft ceiling",
            "ai_lighting": "Studio flash/continuous lighting + black-out blinds",
            "ai_noise_level": "Quiet indoor creator studio (<30 dB)",
            "ai_power_access": "Dedicated 16A heavy lighting power circuits",
            "ai_safety_notes": "Sandbags on light stands, fire extinguisher on wall.",
            "ai_recommended_uses": "Product photo shoots, YouTube video recording, creator reels, headshots",
            "ai_suitability_score": 99
        }
    ]

    # 1. Clean up duplicate spaces from previous test runs
    all_current_spaces = Space.query.all()
    seen_titles = {}
    for sp in all_current_spaces:
        if sp.title in seen_titles:
            db.session.delete(sp)
        else:
            seen_titles[sp.title] = sp
    db.session.commit()

    # 2. Insert or update all verified spaces
    for s_data in spaces_data:
        existing = Space.query.filter_by(title=s_data["title"]).first()
        if existing:
            for k, v in s_data.items():
                setattr(existing, k, v)
        else:
            s = Space(**s_data)
            db.session.add(s)
    db.session.commit()

    # -------------------------------------------------------------
    # 3. Bookings Across States: Active, Upcoming, Completed, Cancelled
    # -------------------------------------------------------------
    now = datetime.utcnow()
    space1 = Space.query.filter_by(title="Quiet AC Study Room & Project Studio (Near IIT Gate 1)").first()
    space2 = Space.query.filter_by(title="High-Speed Hackathon Nook & Brainstorm Lounge").first()
    space5 = Space.query.filter_by(title="North Campus Quiet Study Pod (Delhi University)").first()
    space6 = Space.query.filter_by(title="IIT Bombay Tech Incubator Nook & Hackathon Lab").first()
    space7 = Space.query.filter_by(title="Quiet Study Pod & Hackathon Workstation (Near JSPM Wagholi)").first()

    # (a) Active / In-progress Booking for Aarav Patel
    if space1 and renter_aarav:
        existing_active = Booking.query.filter_by(space_id=space1.id, renter_id=renter_aarav.id, session_state="checked_in").first()
        if not existing_active:
            b_active = Booking(
                space_id=space1.id,
                renter_id=renter_aarav.id,
                start_time=now - timedelta(minutes=30),
                end_time=now + timedelta(hours=1, minutes=30),
                hours_booked=2.0,
                total_price=150.0,
                status="confirmed",
                session_state="checked_in",
                arrival_pin="4821",
                arrival_time=now - timedelta(minutes=28),
                checkin_gps_lat=28.5450,
                checkin_gps_lng=77.1926,
                entry_scan_photo="https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=400&q=80",
                intended_purpose="Smart India Hackathon Finals Live Sprint & Code Review",
                attendees_count=3,
                special_requests="Need extra markers for the whiteboard.",
                escrow_deposit_amount=100.0,
                escrow_status="held",
                micro_lease_agreement="SPACELOOP DIGITALLY SIGNED MICRO-LEASE (Indian Easements Act, 1882):\nPermissive revocable license granted to Aarav Patel. ₹100 held in UPI escrow. Instant refund upon checkout condition verification."
            )
            db.session.add(b_active)

    # (b) Upcoming Confirmed Booking for Priya Sharma in Wagholi
    if space7 and renter_priya:
        existing_upcoming = Booking.query.filter_by(space_id=space7.id, renter_id=renter_priya.id, status="confirmed").first()
        if not existing_upcoming:
            b_upcoming = Booking(
                space_id=space7.id,
                renter_id=renter_priya.id,
                start_time=now + timedelta(days=1, hours=2),
                end_time=now + timedelta(days=1, hours=5),
                hours_booked=3.0,
                total_price=165.0,
                status="confirmed",
                session_state="confirmed",
                arrival_pin="3921",
                intended_purpose="COEP Final Year IoT Firmware Integration Sprint",
                attendees_count=4,
                escrow_deposit_amount=100.0,
                escrow_status="held",
                micro_lease_agreement="SPACELOOP DIGITALLY SIGNED MICRO-LEASE:\nScheduled for tomorrow. Keybox and caretaker access armed."
            )
            db.session.add(b_upcoming)

    # (c) Completed Booking with CV Verified Room Condition & Escrow Released
    if space2 and renter_rohan:
        existing_comp1 = Booking.query.filter_by(space_id=space2.id, renter_id=renter_rohan.id, status="completed").first()
        if not existing_comp1:
            b_comp1 = Booking(
                space_id=space2.id,
                renter_id=renter_rohan.id,
                start_time=now - timedelta(days=2, hours=4),
                end_time=now - timedelta(days=2, hours=1),
                hours_booked=3.0,
                total_price=240.0,
                status="completed",
                session_state="checked_out",
                arrival_pin="4821",
                arrival_time=now - timedelta(days=2, hours=4),
                departure_time=now - timedelta(days=2, hours=1, minutes=2),
                checkin_gps_lat=12.9352,
                checkin_gps_lng=77.6245,
                checkout_gps_lat=12.9352,
                checkout_gps_lng=77.6245,
                condition_match_score=98.5,
                fans_lights_cleared=True,
                objective_punctuality_score=100.0,
                escrow_deposit_amount=100.0,
                escrow_status="refunded",
                intended_purpose="ACM ICPC Regional Contest Mock Simulation",
                attendees_count=3,
                micro_lease_agreement="SPACELOOP MICRO-LEASE: Completed and verified. ₹100 UPI refund disbursed."
            )
            db.session.add(b_comp1)

    # (d) Completed Booking for Sneha Iyer in Powai
    if space6 and renter_sneha:
        existing_comp2 = Booking.query.filter_by(space_id=space6.id, renter_id=renter_sneha.id, status="completed").first()
        if not existing_comp2:
            b_comp2 = Booking(
                space_id=space6.id,
                renter_id=renter_sneha.id,
                start_time=now - timedelta(days=4, hours=3),
                end_time=now - timedelta(days=4, hours=1),
                hours_booked=2.0,
                total_price=180.0,
                status="completed",
                session_state="checked_out",
                arrival_pin="5678",
                arrival_time=now - timedelta(days=4, hours=3),
                departure_time=now - timedelta(days=4, hours=1),
                condition_match_score=99.2,
                fans_lights_cleared=True,
                objective_punctuality_score=100.0,
                escrow_deposit_amount=100.0,
                escrow_status="refunded",
                intended_purpose="NeurIPS Paper Rebuttal Writing",
                attendees_count=2,
                micro_lease_agreement="SPACELOOP MICRO-LEASE: Completed and verified. Full refund processed."
            )
            db.session.add(b_comp2)

    # (e) Cancelled Booking with Escrow Refunded
    if space5 and renter_kabir:
        existing_canc = Booking.query.filter_by(space_id=space5.id, renter_id=renter_kabir.id, status="cancelled").first()
        if not existing_canc:
            b_canc = Booking(
                space_id=space5.id,
                renter_id=renter_kabir.id,
                start_time=now - timedelta(days=1),
                end_time=now - timedelta(days=1) + timedelta(hours=2),
                hours_booked=2.0,
                total_price=130.0,
                status="cancelled",
                session_state="cancelled",
                arrival_pin="4821",
                escrow_deposit_amount=100.0,
                escrow_status="refunded",
                intended_purpose="Economics Study Group (Cancelled due to class conflict)",
                attendees_count=2,
                micro_lease_agreement="SPACELOOP MICRO-LEASE: Cancelled by seeker. ₹100 deposit refunded."
            )
            db.session.add(b_canc)

    db.session.commit()

    # -------------------------------------------------------------
    # 4. Verified Reviews
    # -------------------------------------------------------------
    demo_reviews = [
        {
            "space_id": space1.id if space1 else 1,
            "user_id": renter_aarav.id if renter_aarav else 3,
            "user_name": "Aarav Patel (IIT Delhi)",
            "rating": 5,
            "comment": "Best study room near IIT campus! AC was chilled, whiteboard was spotless, and Sunita aunty was very welcoming. Scanned the door QR and checked out in 10 seconds."
        },
        {
            "space_id": space2.id if space2 else 2,
            "user_id": renter_rohan.id if renter_rohan else 3,
            "user_name": "Rohan Verma (BITS Pilani)",
            "rating": 5,
            "comment": "The 1 Gbps fiber internet was lightning fast during our mock coding contest. Dual monitor setup worked flawlessly with my MacBook."
        },
        {
            "space_id": space7.id if space7 else 3,
            "user_id": renter_priya.id if renter_priya else 3,
            "user_name": "Priya Sharma (COEP Pune)",
            "rating": 5,
            "comment": "Extremely convenient study spot right next to colleges in Wagholi. Clean desks and peaceful ambience for project discussions."
        }
    ]

    for r_data in demo_reviews:
        existing = Review.query.filter_by(space_id=r_data["space_id"], user_name=r_data["user_name"]).first()
        if not existing:
            rev = Review(**r_data)
            db.session.add(rev)

    # -------------------------------------------------------------
    # 5. Realistic Inquiries with AI Answers
    # -------------------------------------------------------------
    demo_inquiries = [
        {
            "space_id": space1.id if space1 else 1,
            "user_id": renter_aarav.id if renter_aarav else 3,
            "question": "Is the Wi-Fi connection dedicated fiber or shared? Can we stream a live presentation to mentors?",
            "ai_answer": "Yes, this space provides a dedicated 600 Mbps dual-band optical fiber connection with sub-10ms latency, ideal for video conferencing, Zoom presentations, and live code demos."
        },
        {
            "space_id": space2.id if space2 else 2,
            "user_id": renter_rohan.id if renter_rohan else 3,
            "question": "Can we book this space for late evening brainstorming sessions past 9 PM?",
            "ai_answer": "Yes, this Koramangala terrace workspace features automated mechanical keybox entry allowing quiet evening sessions until 10 PM. Quiet residential rules apply after 10 PM."
        },
        {
            "space_id": space7.id if space7 else 3,
            "user_id": renter_priya.id if renter_priya else 3,
            "question": "Is parking available for two-wheelers outside the Wagholi study pod?",
            "ai_answer": "Yes, ample safe covered two-wheeler parking is available inside the gated building compound free of charge for verified student pass holders."
        }
    ]

    for inq_data in demo_inquiries:
        existing = SpaceInquiry.query.filter_by(question=inq_data["question"]).first()
        if not existing:
            inq = SpaceInquiry(**inq_data)
            db.session.add(inq)

    db.session.commit()
    print("Database seeded with SpaceLoop India Edition demo data successfully.")
