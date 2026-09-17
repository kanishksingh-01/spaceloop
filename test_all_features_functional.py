import sys
import os

# Add root directory to python path
sys.path.insert(0, "/Users/kanishksingh/Downloads/hack2ignite")

from app import create_app
from models import db, User, Space, Booking

def run_comprehensive_check():
    print("==================================================")
    print("SPACELOOP 100% FULL FUNCTIONALITY AUDIT")
    print("==================================================")

    app = create_app()
    client = app.test_client()

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

    # 6. Listing a Space End-to-End
    print("\n[6/14] Testing Create Space Listing (POST /api/spaces)...")
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
    assert res.status_code == 201
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

    # 11. Instant Booking & AI Micro-Lease Generation
    print("\n[11/14] Testing Instant Booking & Micro-Lease (POST /api/bookings)...")
    res = client.post("/api/bookings", json={
        "space_id": space_id,
        "hours": 3.0,
        "purpose": "Hackathon pitch practice and architecture sprint",
        "attendees_count": 3
    })
    assert res.status_code == 201
    booking_data = res.get_json()
    assert booking_data["success"] is True
    new_booking_id = booking_data["booking"]["id"]
    assert "Micro-Lease" in booking_data["agreement"]
    print(f"✓ Booking #{new_booking_id} confirmed with AI Micro-Lease Agreement generated.")

    # 12. In-Room Check-In Handshake (GPS Geofence + Door QR)
    print(f"\n[12/14] Testing Check-In Handshake (POST /api/booking/{new_booking_id}/check-in)...")
    target_space = client.get(f"/api/spaces/{space_id}").get_json()
    res = client.post(f"/api/booking/{new_booking_id}/check-in", json={
        "qr_token": target_space.get("room_qr_token") or "DEMO_QR_PASS",
        "lat": target_space["latitude"],
        "lng": target_space["longitude"]
    })
    assert res.status_code == 200
    checkin_data = res.get_json()
    assert checkin_data["success"] is True
    assert checkin_data["distance_meters"] <= 50
    print(f"✓ Check-in verified! Device within {checkin_data['distance_meters']}m, session active.")

    # 13. In-Room Check-Out Handshake & Instant UPI Escrow Release
    print(f"\n[13/14] Testing Check-Out Handshake & UPI Escrow Release (POST /api/booking/{new_booking_id}/check-out)...")
    res = client.post(f"/api/booking/{new_booking_id}/check-out", json={
        "qr_token": target_space.get("room_qr_token") or "DEMO_QR_PASS",
        "lat": target_space["latitude"],
        "lng": target_space["longitude"]
    })
    assert res.status_code == 200
    checkout_data = res.get_json()
    assert checkout_data["success"] is True
    assert checkout_data["escrow_refund_status"] == "INSTANT_RELEASE_COMPLETE"
    assert checkout_data["inspection"]["fans_lights_cleared"] is True
    print(f"✓ Check-out verified! Room condition cleared, Punctuality {checkout_data['punctuality_score']}%, ₹100 Escrow refunded.")

    # 14. All HTML Views & Subsystems
    print("\n[14/14] Testing All Template Views...")
    pages = [
        ("/", 200, "Home"),
        (f"/space/{space_id}", 200, "Space Detail"),
        ("/list-space", 200, "List Space"),
        ("/calculator", 200, "Calculator"),
        ("/dashboard", 200, "Dashboard"),
        ("/how-it-works", 200, "How It Works"),
        ("/verify", 200, "KYC Hub"),
        (f"/booking/{new_booking_id}/session", 200, "In-Room Live Console"),
        (f"/space/{space_id}/printable-qr", 200, "Printable Door Pass"),
        ("/login", 200, "User Switcher & Login")
    ]
    for url, expected_code, name in pages:
        res = client.get(url)
        assert res.status_code == expected_code, f"{name} ({url}) returned {res.status_code}"
        print(f"  • {name} [{url}] -> HTTP {res.status_code} OK")

    print("\n==================================================")
    print("ALL 14 END-TO-END SUBSYSTEMS ARE 100% OPERATIONAL!")
    print("==================================================")

if __name__ == "__main__":
    run_comprehensive_check()
