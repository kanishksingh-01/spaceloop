import json
import os
import sys

# Add root directory to python path
sys.path.insert(0, "/Users/kanishksingh/Downloads/hack2ignite")

from app import create_app
from models import db, User, Space, Booking

def run_tests():
    print("========================================")
    print("SPACELOOP FULL VERIFICATION SUITE")
    print("========================================")
    
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        # ----------------------------------------------------
        # 1. Test Demo Switching Endpoint (GET and POST)
        # ----------------------------------------------------
        print("\n[TEST 1] Testing Demo Persona Switching...")
        res = client.post("/api/v1/auth/demo-switch/host")
        assert res.status_code == 200, f"Demo switch host failed: {res.status_code} {res.data.decode()}"
        user_info = res.get_json().get("user", {})
        assert user_info.get("role") in ("host", "owner"), f"Expected host role, got {user_info.get('role')}"
        print(f"  ✓ Switched to Host persona: {user_info.get('name')} ({user_info.get('email')}), role={user_info.get('role')}")
        
        # Check current session with /api/v1/auth/me
        res_me = client.get("/api/v1/auth/me")
        assert res_me.status_code == 200, f"/api/v1/auth/me failed: {res_me.status_code}"
        print(f"  ✓ Session verified via /api/v1/auth/me: user={res_me.get_json().get('user', {}).get('name')}")
        
        # ----------------------------------------------------
        # 2. Test Host Seed Sample Space Endpoint
        # ----------------------------------------------------
        print("\n[TEST 2] Testing Host Seed Sample Space...")
        res_seed = client.post("/api/host/seed-sample-space")
        assert res_seed.status_code in (200, 201), f"Seed sample space failed: {res_seed.status_code} {res_seed.data.decode()}"
        seed_data = res_seed.get_json()
        assert seed_data.get("success"), "Expected success=True"
        print(f"  ✓ Seeded space: {seed_data.get('space', {}).get('title')} (ID: {seed_data.get('space', {}).get('id')})")
        
        # ----------------------------------------------------
        # 3. Test Host Creating Custom Space (Renting out space)
        # ----------------------------------------------------
        print("\n[TEST 3] Testing Host Custom Space Listing (Rent out spaces)...")
        space_payload = {
            "title": "Acoustic Creator & Podcast Pod",
            "category": "Studio",
            "description": "Double acoustic insulated studio with Shure MV7 mics, ring light, and 500 Mbps fiber.",
            "address": "Baner High Street, Pune",
            "city": "Pune",
            "price_hourly": 120.0,
            "price_daily": 600.0,
            "hourly_rate": 120.0,
            "latitude": 18.5590,
            "longitude": 73.7868,
            "amenities": ["Acoustic Foam", "500 Mbps Fiber", "Smart Lock", "AC"]
        }
        res_create = client.post("/api/spaces", json=space_payload)
        assert res_create.status_code in (200, 201), f"Host create space failed: {res_create.status_code} {res_create.data.decode()}"
        created_space_data = res_create.get_json() or {}
        created_space_id = created_space_data.get("id") or created_space_data.get("space_id")
        assert created_space_id is not None, f"Expected valid created space ID: {created_space_data}"
        print(f"  ✓ Host successfully listed custom space: ID={created_space_id}, title={created_space_data.get('title')}")
        
        # ----------------------------------------------------
        # 4. Test Student SSO Verification & Booking
        # ----------------------------------------------------
        print("\n[TEST 4] Testing University Student SSO & Genuine Auth...")
        student_client = app.test_client()
        sso_payload = {
            "name": "Rohan Gupta",
            "college_name": "BITS Pilani",
            "student_id": "2023A7PS012",
            "college_email": "rohan.g@pilani.bits-pilani.ac.in"
        }
        res_sso = student_client.post("/api/v1/auth/student-sso", json=sso_payload)
        assert res_sso.status_code == 200, f"Student SSO failed: {res_sso.status_code} {res_sso.data.decode()}"
        student_user = res_sso.get_json().get("user", {})
        assert student_user.get("college_verified") is True or student_user.get("trust_score", 0) > 800
        print(f"  ✓ Student SSO authenticated: {student_user.get('name')} from {student_user.get('college_name', 'BITS Pilani')}")
        
        # ----------------------------------------------------
        # 5. Test DigiLocker Aadhaar Verification
        # ----------------------------------------------------
        print("\n[TEST 5] Testing DigiLocker Aadhaar OTP Verification...")
        digi_client = app.test_client()
        digi_payload = {
            "name": "Pooja Hegde",
            "aadhaar_number": "999988884821",
            "otp": "123456",
            "role": "host"
        }
        res_digi = digi_client.post("/api/v1/auth/digilocker", json=digi_payload)
        assert res_digi.status_code == 200, f"DigiLocker failed: {res_digi.status_code} {res_digi.data.decode()}"
        digi_user = res_digi.get_json().get("user", {})
        print(f"  ✓ DigiLocker verified user created: {digi_user.get('name')} (Trust score: {digi_user.get('trust_score')})")
        
        # ----------------------------------------------------
        # 6. Test Seeker Booking Space & Host Dashboard Visibility
        # ----------------------------------------------------
        print("\n[TEST 6] Testing Seeker Booking Space & Host Incoming Reservations...")
        booking_payload = {
            "space_id": created_space_id,
            "hours": 2,
            "custom_start_time": "14:00",
            "custom_end_time": "16:00",
            "is_slot_booking": True
        }
        res_book = student_client.post("/api/bookings", json=booking_payload)
        assert res_book.status_code in (200, 201), f"Booking failed: {res_book.status_code} {res_book.data.decode()}"
        booking_data = res_book.get_json().get("booking", {})
        print(f"  ✓ Student booked space: Booking ID={booking_data.get('id')}, Total=₹{booking_data.get('total_price')}")
        
        # Now check host's dashboard for incoming reservations (ensure Sunita host session is active)
        client.post("/api/v1/auth/demo-switch/host")
        res_host_dash = client.get("/api/dashboard")
        assert res_host_dash.status_code == 200, f"Host dashboard failed: {res_host_dash.status_code} {res_host_dash.data.decode()}"
        dash_json = res_host_dash.get_json()
        print(f"DEBUG: Host user in dashboard: {dash_json.get('user', {}).get('id')} / {dash_json.get('user', {}).get('email')}")
        print(f"DEBUG: Created space ID: {created_space_id}, host spaces in dash: {[s['id'] for s in dash_json.get('host_spaces', [])]}")
        host_bookings = dash_json.get("host_bookings", [])
        print(f"DEBUG: Host bookings found: {len(host_bookings)}")
        assert len(host_bookings) > 0, "Expected at least 1 incoming host booking"
        print(f"  ✓ Host dashboard shows {len(host_bookings)} incoming reservation(s) with gross revenue metrics!")
        
        # ----------------------------------------------------
        # 7. Test LoopBot & Gemini AI Contextual Responses
        # ----------------------------------------------------
        print("\n[TEST 7] Testing LoopBot & Gemini AI Conversational Engine...")
        
        test_prompts = [
            ("Study Space Finder", "Can you find me a quiet study pod near IIT Delhi under 80 rs?"),
            ("Legal Section 52", "Is renting an unused desk legal under Section 52 Easements Act in India?"),
            ("Host Monetization", "How can I rent out my empty corner space and earn money as a host?"),
            ("Door Pass Tech", "How does the Bluetooth smart lock and geofencing pass work when I arrive?"),
            ("General Conversation", "Hi LoopBot! Who are you and how can you help me today?")
        ]
        
        for category, prompt in test_prompts:
            ai_res = client.post("/api/concierge/chat", json={
                "message": prompt,
                "conversation_id": "test_conv_101"
            })
            assert ai_res.status_code == 200, f"AI chat failed for '{prompt}': {ai_res.status_code}"
            data = ai_res.get_json()
            reply = data.get("reply", "")
            source = data.get("source", "unknown")
            assert len(reply) > 50, f"Reply too short: {reply}"
            print(f"\n  [Prompt - {category}]: '{prompt}'")
            print(f"  [Engine Source]: {source}")
            first_line = reply.strip().split("\n")[0][:120]
            print(f"  [Reply Snippet]: {first_line}...")
        
    print("\n========================================")
    print("ALL 7 CRITICAL AUDIT TESTS PASSED (100% SUCCESS)!")
    print("========================================")

if __name__ == "__main__":
    run_tests()
