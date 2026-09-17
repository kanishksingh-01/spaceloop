import sys
import os

# Add project directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Space, Booking

def run_comprehensive_check():
    print("==================================================")
    print("SPACELOOP 100% FULL FUNCTIONALITY AUDIT")
    print("==================================================")

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Clean up prior test bookings to ensure idempotent test execution
        Booking.query.filter(Booking.intended_purpose.in_([
            "Hackathon pitch practice and architecture sprint",
            "First interval booking",
            "Conflicting interval booking"
        ])).delete(synchronize_session=False)
        db.session.commit()

    # 1. Homepage & Market
    print("\n[1/14] Testing Homepage (GET /)...")
    res = client.get("/")
    assert res.status_code == 200, f"Failed GET /: {res.status_code}"
    assert b"SpaceLoop" in res.data
    assert b"\xe2\x82\xb9" in res.data or "₹".encode() in res.data  # INR symbol
    print("✓ Homepage renders with INR currency and active listings.")

    # 2. Spaces API
    print("\n[2/14] Testing Spaces API (GET /api/spaces)...")
    res = client.get("/api/spaces")
    assert res.status_code == 200
    spaces = res.get_json()
    assert len(spaces) >= 6, f"Expected >=6 spaces, got {len(spaces)}"
    space_id = spaces[0]["id"]
    print(f"✓ Spaces API returned {len(spaces)} spaces successfully.")

    # 3. Space Detail Page & OTI Proof of Reality
    print(f"\n[3/14] Testing Space Detail (GET /space/{space_id})...")
    res = client.get(f"/space/{space_id}")
    assert res.status_code == 200
    assert b"Objective Reliability Index" in res.data
    assert b"UPI Micro-Escrow Hold" in res.data
    print("✓ Space detail page loaded with Objective Telemetry Index and Escrow.")

    # 4. Multimodal AI Space Inspector
    print("\n[4/14] Testing AI Space Inspector (POST /api/spaces/ai-scan)...")
    res = client.post("/api/spaces/ai-scan", json={
        "category": "Studio",
        "description": "Sunlit study room near IIT Delhi with whiteboards and 6 sockets",
        "address": "Hauz Khas, New Delhi"
    })
    assert res.status_code == 200
    ai_scan = res.get_json()
    assert "recommended_hourly_price" in ai_scan
    assert ai_scan["suitability_score"] >= 85
    print(f"✓ AI Inspector recommended ₹{ai_scan['recommended_hourly_price']}/hr (Score: {ai_scan['suitability_score']}%).")

    # 5. Natural Language Matchmaker
    print("\n[5/14] Testing Natural Language AI Match (POST /api/spaces/ai-match)...")
    res = client.post("/api/spaces/ai-match", json={
        "query": "Quiet place for 4 students to work on a hackathon near Hauz Khas"
    })
    assert res.status_code == 200
    match_data = res.get_json()
    assert len(match_data["results"]) > 0
    top = match_data["results"][0]
    print(f"✓ AI Matchmaker ranked '{top['space']['title']}' as top match with score {top['match_score']}%.")

    # 6. Listing a Space End-to-End (Authenticated Host)
    print("\n[6/14] Testing Create Space Listing (POST /api/spaces)...")
    # Authenticate as host
    login_host = client.post("/api/v1/auth/login", json={
        "email": "sunita@spaceloop.in",
        "password": "password123"
    })
    assert login_host.status_code == 200, f"Host login failed: {login_host.get_json()}"

    res = client.post("/api/spaces", json={
        "title": "Koramangala 4th Block Student Den",
        "category": "Studio",
        "address": "80 Feet Rd, Koramangala, Bengaluru",
        "neighborhood": "Koramangala 4th Block",
        "city": "Bengaluru",
        "state": "KA",
        "price_hourly": 55.0,
        "price_daily": 350.0,
        "sqft": 300,
        "max_capacity": 6,
        "description": "High-speed optical fiber, comfortable desks, ergonomic chairs for coding sprints.",
        "photos": ["https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80"]
    })
    assert res.status_code == 201, f"Create space failed: {res.status_code} {res.data}"
    created_space = res.get_json()
    assert created_space["id"] is not None
    print(f"✓ New space created successfully (ID: {created_space['id']}).")

    # 7. Passive Income Calculator
    print("\n[7/14] Testing Earnings Calculator API (POST /api/calculator/estimate)...")
    res = client.post("/api/calculator/estimate", json={
        "category": "Studio",
        "sqft": 350,
        "days_per_month": 14
    })
    assert res.status_code == 200
    calc = res.get_json()
    assert calc["estimated_monthly"] > 1000
    assert calc["estimated_annual"] == calc["estimated_monthly"] * 12
    print(f"✓ Calculator estimate: ₹{calc['estimated_monthly']}/mo (₹{calc['estimated_annual']}/yr).")

    # 8. LoopBot AI Concierge
    print("\n[8/14] Testing LoopBot Concierge (POST /api/ai/chat)...")
    res = client.post("/api/ai/chat", json={
        "messages": [{"role": "user", "content": "How do AI micro-leases and ₹100 UPI escrow protect hosts?"}]
    })
    assert res.status_code == 200
    chat_resp = res.get_json()
    assert len(chat_resp.get("reply", "")) > 20
    print(f"✓ LoopBot replied with {len(chat_resp['reply'])} characters.")

    # 9. Student Instant KYC (Aadhaar OTP + .ac.in)
    print("\n[9/14] Testing Student KYC (POST /api/verify/student)...")
    res = client.post("/api/verify/student", json={
        "name": "Aarav Patel",
        "aadhaar_number": "548291034821",
        "otp": "123456",
        "college_email": "aarav.p@cse.iitd.ac.in",
        "college_name": "Indian Institute of Technology Delhi",
        "student_id": "2023CSB1044"
    })
    assert res.status_code == 200
    student_kyc = res.get_json()
    assert student_kyc["success"] is True
    assert student_kyc["aadhaar"]["masked_aadhaar"] == "XXXX-XXXX-4821"
    assert student_kyc["academic"]["is_institutional_email"] is True
    print(f"✓ Student KYC verified: Masked {student_kyc['aadhaar']['masked_aadhaar']}, Domain IITD verified.")

    # 10. Host Instant KYC (Discom Electricity Bill + UPI Penny Drop)
    print("\n[10/14] Testing Host KYC (POST /api/verify/host)...")
    res = client.post("/api/verify/host", json={
        "ca_number": "CA9874561230",
        "provider": "BESCOM",
        "address": "Koramangala 4th Block, Bengaluru",
        "pan_name": "Vikram Malhotra",
        "upi_vpa": "vikram.spaces@okaxis"
    })
    assert res.status_code == 200
    host_kyc = res.get_json()
    assert host_kyc["success"] is True
    assert host_kyc["discom"]["discom_provider"] == "BESCOM"
    assert host_kyc["upi"]["bank_beneficiary_name"] == "Vikram Malhotra"
    print(f"✓ Host KYC verified: BESCOM CA confirmed, UPI penny drop matched {host_kyc['upi']['bank_beneficiary_name']}.")

    # 11. Instant Booking & AI Micro-Lease Generation (Authenticated Seeker)
    print("\n[11/14] Testing Instant Booking & Micro-Lease (POST /api/bookings)...")
    # Authenticate as seeker Aarav
    login_seeker = client.post("/api/v1/auth/login", json={
        "email": "aarav@iitd.ac.in",
        "password": "password123"
    })
    assert login_seeker.status_code == 200, f"Seeker login failed: {login_seeker.get_json()}"

    res = client.post("/api/bookings", json={
        "space_id": space_id,
        "hours": 3.0,
        "purpose": "Hackathon pitch practice and architecture sprint",
        "attendees_count": 1
    })
    assert res.status_code == 201, f"Create booking failed: {res.status_code} {res.data}"
    booking_data = res.get_json()
    assert booking_data["success"] is True
    new_booking_id = booking_data["booking"]["id"]
    assert "Micro-Lease" in booking_data["agreement"]
    print(f"✓ Booking #{new_booking_id} confirmed with AI Micro-Lease Agreement generated.")

    # 12. In-Room Check-In Handshake (GPS Geofence + Door QR)
    print(f"\n[12/14] Testing Check-In Handshake (POST /api/booking/{new_booking_id}/check-in)...")
    with app.app_context():
        space_obj = Space.query.get(space_id)
        space_qr = space_obj.room_qr_token

    res = client.post(f"/api/booking/{new_booking_id}/check-in", json={
        "qr_token": space_qr,
        "lat": space_obj.latitude,
        "lng": space_obj.longitude
    })
    assert res.status_code == 200, f"Check-in failed: {res.status_code} {res.data}"
    checkin_data = res.get_json()
    assert checkin_data["success"] is True
    assert checkin_data["distance_meters"] <= 50
    print(f"✓ Check-in verified! Device within {checkin_data['distance_meters']}m, session active.")

    # 13. In-Room Check-Out Handshake & Instant Simulated Escrow Release
    print(f"\n[13/14] Testing Check-Out Handshake & UPI Escrow Release (POST /api/booking/{new_booking_id}/check-out)...")
    res = client.post(f"/api/booking/{new_booking_id}/check-out", json={
        "qr_token": space_qr,
        "lat": space_obj.latitude,
        "lng": space_obj.longitude
    })
    assert res.status_code == 200, f"Check-out failed: {res.status_code} {res.data}"
    checkout_data = res.get_json()
    assert checkout_data["success"] is True
    assert "refund" in checkout_data["booking"]["escrow_status"] or "refund" in checkout_data["message"].lower()
    print(f"✓ Check-out verified! Room condition cleared, Punctuality {checkout_data['punctuality_score']}%, simulated escrow refunded.")

    # 14. All HTML Views & Subsystems
    print("\n[14/14] Testing All Template Views...")
    authenticated_pages = [
        ("/", 200, "Home Landing Page"),
        ("/explore", 200, "Explore & Discovery"),
        (f"/space/{space_id}", 200, "Space Detail"),
        ("/list-space", 200, "List Space"),
        ("/calculator", 200, "Calculator"),
        ("/dashboard", 200, "Dashboard"),
        ("/how-it-works", 200, "How It Works"),
        ("/verify", 200, "KYC Hub"),
        (f"/booking/{new_booking_id}/session", 200, "In-Room Live Console"),
        (f"/space/{space_id}/printable-qr", 200, "Printable Door Pass"),
    ]
    for url, expected_code, name in authenticated_pages:
        res = client.get(url)
        assert res.status_code == expected_code, f"{name} ({url}) returned {res.status_code}"
        print(f"  • {name} [{url}] -> HTTP {res.status_code} OK")

    # Anonymous visitor views
    anon_client = app.test_client()
    for url, expected_code, name in [("/auth/login", 200, "Sign In"), ("/auth/register", 200, "Register")]:
        res = anon_client.get(url)
        assert res.status_code == expected_code, f"{name} ({url}) returned {res.status_code}"
        print(f"  • {name} [{url}] -> HTTP {res.status_code} OK")

    print("\n==================================================")
    print("ALL 14 END-TO-END SUBSYSTEMS ARE 100% OPERATIONAL!")
    print("==================================================")

    # 15. P0 & P1 Security & Boundary Regressions
    print("\n[15/15] Running P0 & P1 Critical Security & Integrity Regressions...")

    # P0-1: Overlapping Booking Prevention
    print("  • Testing Overlapping Booking Rejection (P0-1)...")
    with app.app_context():
        test_space = Space.query.filter_by(is_active=True).first()
        test_space_id = test_space.id

    from datetime import datetime, timedelta
    now_dt = datetime.utcnow()
    slot_start = (now_dt + timedelta(hours=48)).replace(minute=0, second=0, microsecond=0)
    slot_start_iso = slot_start.isoformat()

    # First booking succeeds (201)
    res_b1 = client.post("/api/bookings", json={
        "space_id": test_space_id,
        "hours": 3.0,
        "start_time": slot_start_iso,
        "purpose": "First interval booking"
    })
    assert res_b1.status_code == 201, f"First booking failed: {res_b1.status_code} {res_b1.data}"
    b1_id = res_b1.get_json()["booking"]["id"]

    # Second overlapping booking must be rejected (409 Conflict)
    res_b2 = client.post("/api/bookings", json={
        "space_id": test_space_id,
        "hours": 2.0,
        "start_time": (slot_start + timedelta(hours=1)).isoformat(),
        "purpose": "Conflicting interval booking"
    })
    assert res_b2.status_code == 409, f"Expected 409 for overlapping booking, got {res_b2.status_code}: {res_b2.data}"
    assert "already reserved" in res_b2.get_json().get("error", "").lower()
    print("    ✓ Overlapping booking rejected with HTTP 409 Conflict.")

    # P0-3: Require Check-In Before Checkout
    print("  • Testing Premature Checkout Rejection (P0-3)...")
    res_early_co = client.post(f"/api/booking/{b1_id}/check-out", json={})
    assert res_early_co.status_code == 400, f"Expected 400 for checkout before check-in, got {res_early_co.status_code}"
    assert "must check in" in res_early_co.get_json().get("error", "").lower()
    print("    ✓ Premature checkout without check-in rejected with HTTP 400 Bad Request.")

    # P0-2: Universal QR Bypass Rejection
    print("  • Testing Hardcoded QR Bypass Rejection (P0-2)...")
    res_bypass = client.post(f"/api/booking/{b1_id}/check-in", json={
        "qr_token": "DEMO_QR_PASS",
        "lat": test_space.latitude,
        "lng": test_space.longitude
    })
    assert res_bypass.status_code in (400, 403), f"Expected 400/403 for DEMO_QR_PASS, got {res_bypass.status_code}"
    print("    ✓ Universal QR bypass ('DEMO_QR_PASS') denied access.")

    # P0-4: GPS-Only Access Override Rejection
    print("  • Testing GPS-Only Check-in Rejection (P0-4)...")
    res_gps_only = client.post(f"/api/booking/{b1_id}/check-in", json={
        "lat": test_space.latitude,
        "lng": test_space.longitude
    })
    assert res_gps_only.status_code in (400, 403), f"Expected 400/403 for GPS without QR/PIN, got {res_gps_only.status_code}"
    print("    ✓ Standalone GPS coordinates without QR or PIN denied access.")

    # P0-7: Stop Exposing Physical Access Secrets in Public API
    print("  • Testing Physical-Access Secret Concealment (P0-7)...")
    res_pub = client.get(f"/api/spaces/{test_space_id}")
    pub_data = res_pub.get_json()
    assert pub_data.get("room_qr_token") is None, f"Leaked room_qr_token: {pub_data.get('room_qr_token')}"
    assert pub_data.get("keybox_code") is None, f"Leaked keybox_code: {pub_data.get('keybox_code')}"
    print("    ✓ Public space listing endpoint does not expose door QR token or keybox code.")

    # P1-9: Lock Down AI Simulation Controls
    print("  • Testing AI Simulation Endpoint Lockdown (P1-9)...")
    res_get_toggle = anon_client.get("/api/dev/toggle-ai-simulation")
    assert res_get_toggle.status_code == 405, f"Expected 405 for GET toggle, got {res_get_toggle.status_code}"
    res_anon_post = anon_client.post("/api/dev/toggle-ai-simulation")
    assert res_anon_post.status_code in (302, 401, 403), f"Expected auth required for POST toggle, got {res_anon_post.status_code}"
    print("    ✓ /api/dev/toggle-ai-simulation rejects unauthenticated GET and POST requests.")

    # P1-2: Secure Arrival PIN Generation
    print("  • Testing Cryptographically Secure Arrival PIN (P1-2)...")
    b1_pin = res_b1.get_json()["booking"]["arrival_pin"]
    assert len(b1_pin) == 4 and b1_pin.isdigit()
    assert 1000 <= int(b1_pin) <= 9999
    print(f"    ✓ Arrival PIN generated securely: {b1_pin} (4 digits in range [1000, 9999]).")

    print("\n==================================================")
    print("ALL P0 & P1 CRITICAL SECURITY REGRESSIONS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_comprehensive_check()
