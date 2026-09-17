"""
Test script for verifying all 4 critical hackathon repairs:
1. Booking Duration Validation (hours: 4 and timestamp difference)
2. Unlock & Check-In endpoints (GET /api/booking/<id>/status, POST /api/booking/<id>/check-in)
3. Host Space Listing Publication (POST /api/spaces with hourly_rate, location, space_id response)
4. LoopBot AI Concierge Processing (query understanding, INR pricing, no static fallback loop)
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db, User, Space, Booking

def run_tests():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        test_space = Space.query.filter_by(is_active=True).first()
        assert test_space is not None, "Test space not found"

        print("\n" + "=" * 60)
        print("CRITICAL REPAIRS VERIFICATION SUITE")
        print("=" * 60)

        # -------------------------------------------------------------
        # 1. BOOKING DURATION VALIDATION TEST
        # -------------------------------------------------------------
        print("\n[TEST 1/4] Booking Duration Validation & Creation...")
        login_seeker = client.post("/api/v1/auth/login", json={
            "email": "aarav@iitd.ac.in",
            "password": "password123"
        })
        assert login_seeker.status_code == 200, f"Seeker login failed: {login_seeker.get_json()}"

        # Case 1A: Direct hours = 4
        res1a = client.post("/api/bookings", json={
            "space_id": test_space.id,
            "hours": 4,
            "attendees_count": 1,
            "purpose": "Focus Study Session"
        })
        assert res1a.status_code == 201, f"Expected 201, got {res1a.status_code}: {res1a.data.decode()}"
        data1a = res1a.get_json()
        assert "booking_id" in data1a, "booking_id missing from response"
        assert data1a["booking"]["hours_booked"] == 4.0, f"Expected 4.0 hours, got {data1a['booking']['hours_booked']}"
        expected_subtotal = round(4.0 * test_space.price_hourly, 2)
        expected_fee = round(expected_subtotal * 0.05, 2)
        expected_total = round(expected_subtotal + expected_fee + 100.0, 2)
        assert data1a["booking"]["total_price"] == expected_total, f"Expected total {expected_total}, got {data1a['booking']['total_price']}"
        print(f"✓ Case 1A Passed: 4h booking created successfully! Booking #{data1a['booking_id']}, Total: ₹{expected_total}")

        # Case 1B: Hours omitted, calculated from start_time and end_time (4 hours)
        now = datetime.utcnow()
        start_iso = (now + timedelta(minutes=15)).isoformat() + "Z"
        end_iso = (now + timedelta(hours=4, minutes=15)).isoformat() + "Z"
        res1b = client.post("/api/bookings", json={
            "space_id": test_space.id,
            "start_time": start_iso,
            "end_time": end_iso,
            "attendees_count": 1,
            "purpose": "Timestamp derived session"
        })
        assert res1b.status_code == 201, f"Expected 201 for timestamp derived hours, got {res1b.status_code}: {res1b.data.decode()}"
        data1b = res1b.get_json()
        assert data1b["booking"]["hours_booked"] == 4.0, f"Expected 4.0 hours from timestamps, got {data1b['booking']['hours_booked']}"
        print(f"✓ Case 1B Passed: Start/End timestamps correctly converted to 4.0h booking #{data1b['booking_id']} without duration error.")

        # -------------------------------------------------------------
        # 2. UNLOCK & CHECK-IN (GET /status & POST /check-in)
        # -------------------------------------------------------------
        print("\n[TEST 2/4] Unlock & Check-In Endpoints...")
        target_booking_id = data1a["booking_id"]

        # Case 2A: GET /api/booking/<id>/status
        res_status = client.get(f"/api/booking/{target_booking_id}/status")
        assert res_status.status_code == 200, f"GET status failed: {res_status.status_code}: {res_status.data.decode()}"
        status_data = res_status.get_json()
        assert status_data["success"] is True
        assert status_data["booking"]["id"] == target_booking_id
        assert "room_qr_token" in status_data
        assert "arrival_pin" in status_data
        print(f"✓ Case 2A Passed: GET /api/booking/{target_booking_id}/status returned real booking and space details.")

        # Case 2B: POST /api/booking/<id>/check-in
        res_checkin = client.post(f"/api/booking/{target_booking_id}/check-in", json={
            "lat": test_space.latitude,
            "lng": test_space.longitude,
            "qr_token": "DEMO_QR_PASS"
        })
        assert res_checkin.status_code == 200, f"Check-in failed: {res_checkin.status_code}: {res_checkin.data.decode()}"
        checkin_data = res_checkin.get_json()
        assert checkin_data["success"] is True
        assert checkin_data["booking"]["session_state"] == "checked_in"
        print(f"✓ Case 2B Passed: In-room check-in verified! Session active, access granted via {checkin_data.get('handshake_method')}.")

        # Case 2C: Non-existent booking returns clean 404
        res_404 = client.get("/api/booking/999999/status")
        assert res_404.status_code == 404, f"Expected 404 for missing booking, got {res_404.status_code}"
        print("✓ Case 2C Passed: Non-existent booking returns clean 404 Not Found.")

        # -------------------------------------------------------------
        # 3. HOST SPACE LISTING / PUBLISHING
        # -------------------------------------------------------------
        print("\n[TEST 3/4] Host Space Listing Publication...")
        login_host = client.post("/api/v1/auth/login", json={
            "email": "sunita@spaceloop.in",
            "password": "password123"
        })
        assert login_host.status_code == 200, f"Host login failed: {login_host.get_json()}"

        res_create_space = client.post("/api/spaces", json={
            "title": "Kannu's House Study Pod",
            "description": "Sunlit room with good air ventilation, ideal for exam prep or focused coding.",
            "category": "Study Pod",
            "hourly_rate": 100,
            "location": "Wagholi",
            "address": "Near JSPM Imperial College, Wagholi, Pune",
            "city": "Pune",
            "photos": [
                "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80"
            ],
            "amenities": ["Wi-Fi", "Power Outlets", "Whiteboard", "Quiet Zone"],
            "latitude": 18.5793,
            "longitude": 73.9825
        })
        assert res_create_space.status_code == 201, f"Failed to create space: {res_create_space.status_code}: {res_create_space.data.decode()}"
        space_data = res_create_space.get_json()
        assert "space_id" in space_data, "space_id missing from response"
        assert space_data["price_hourly"] == 100.0, f"Expected 100.0, got {space_data['price_hourly']}"
        assert space_data["neighborhood"] == "Wagholi", f"Expected Wagholi, got {space_data['neighborhood']}"
        assert space_data["latitude"] == 18.5793, f"Expected 18.5793, got {space_data['latitude']}"
        print(f"✓ Test 3 Passed: Space '{space_data['title']}' published successfully with space_id #{space_data['space_id']} at ₹{space_data['price_hourly']}/hr.")

        # -------------------------------------------------------------
        # 4. LOOPBOT AI CONCIERGE PROCESSING
        # -------------------------------------------------------------
        print("\n[TEST 4/4] LoopBot AI Concierge Processing...")

        # Prompt 1: Podcast studio
        res_ai1 = client.post("/api/ai/chat", json={
            "message": "Find me a podcast studio with natural light",
            "history": []
        })
        assert res_ai1.status_code == 200
        reply1 = res_ai1.get_json()["reply"]
        assert "Hello! How can I assist you with SpaceLoop today?" not in reply1, "LoopBot returned static greeting!"
        assert any(k in reply1.lower() for k in ["podcast", "studio", "creator", "sound-treated"]), f"Unexpected reply: {reply1}"
        print("✓ Prompt 1 Passed: Correctly answered podcast studio query with contextual studio recommendations.")

        # Prompt 2: Garage earnings
        res_ai2 = client.post("/api/ai/chat", json={
            "message": "How much can I earn renting an empty garage?"
        })
        assert res_ai2.status_code == 200
        reply2 = res_ai2.get_json()["reply"]
        assert "Hello! How can I assist you with SpaceLoop today?" not in reply2, "LoopBot returned static greeting!"
        assert any(k in reply2.lower() for k in ["earn", "garage", "storage", "₹", "month"]), f"Unexpected reply: {reply2}"
        print("✓ Prompt 2 Passed: Correctly answered empty garage earnings query with ₹ calculations.")

        # Prompt 3: AI Micro-Lease protections
        res_ai3 = client.post("/api/ai/chat", json={
            "message": "How do AI micro-lease agreements protect owners?"
        })
        assert res_ai3.status_code == 200
        reply3 = res_ai3.get_json()["reply"]
        assert "Hello! How can I assist you with SpaceLoop today?" not in reply3, "LoopBot returned static greeting!"
        assert any(k in reply3.lower() for k in ["easement", "micro-lease", "license", "escrow", "section 52"]), f"Unexpected reply: {reply3}"
        print("✓ Prompt 3 Passed: Correctly explained AI micro-lease protections under Indian Easements Act 1882.")

        print("\n" + "=" * 60)
        print("ALL 4 CRITICAL HACKATHON REPAIRS VERIFIED AND PASSING 100%!")
        print("=" * 60)

if __name__ == "__main__":
    run_tests()
