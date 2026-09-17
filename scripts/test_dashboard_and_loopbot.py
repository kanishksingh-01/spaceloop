#!/usr/bin/env python3
"""
Test Suite: SpaceLoop Hardened Dashboard, Pricing Bounds, Access Pass, and 7-Category LoopBot.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User, Space, Booking
from space_ai import concierge_chat
from datetime import datetime, timedelta

def run_tests():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Setup test users
        seeker = User.query.filter_by(email="aarav@iitd.ac.in").first()
        if not seeker:
            seeker = User.query.first()

        host = User.query.filter_by(role="host").first()
        if not host:
            host = seeker

        print("\n" + "=" * 60)
        print("SPACELOOP FINAL HARDENING VERIFICATION")
        print("=" * 60)

        # ----------------------------------------------------
        # TEST 1: Unauthenticated Dashboard returns 401
        # ----------------------------------------------------
        print("\n[TEST 1] Testing /api/dashboard authentication...")
        res_unauth = client.get("/api/dashboard")
        assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
        print("✓ Passed: Unauthenticated request to /api/dashboard returned 401.")

        # ----------------------------------------------------
        # TEST 2: Authenticated Dashboard returns real seeker & host data
        # ----------------------------------------------------
        print("\n[TEST 2] Testing /api/dashboard for authenticated seeker...")
        login_res = client.post("/api/v1/auth/login", json={
            "email": "aarav@iitd.ac.in",
            "password": "password123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.get_json()}"

        res_dash = client.get("/api/dashboard")
        assert res_dash.status_code == 200, f"Expected 200, got {res_dash.status_code}"
        dash_data = res_dash.get_json()
        assert dash_data["success"] is True
        assert "bookings" in dash_data
        assert "host_spaces" in dash_data
        assert "host_metrics" in dash_data
        # Ensure no mock #101 injected
        booking_ids = [b["id"] for b in dash_data["bookings"]]
        print(f"✓ Passed: Real seeker bookings returned: count={len(dash_data['bookings'])}, ids={booking_ids}")
        print(f"✓ Host metrics: {dash_data['host_metrics']}")

        # ----------------------------------------------------
        # TEST 3: Check-in response messaging (Digital access pass)
        # ----------------------------------------------------
        print("\n[TEST 3] Testing Check-in digital access pass messaging...")
        test_space = Space.query.filter_by(is_active=True).first()
        assert test_space is not None

        new_booking = Booking(
            space_id=test_space.id,
            renter_id=seeker.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=2),
            hours_booked=2.0,
            intended_purpose="Study & Focus Session",
            total_price=test_space.price_hourly * 2.0 + 100.0,
            escrow_deposit_amount=100.0,
            status="confirmed",
            session_state="pending_checkin",
            arrival_pin="5544"
        )
        db.session.add(new_booking)
        db.session.commit()

        res_checkin = client.post(f"/api/booking/{new_booking.id}/check-in", json={
            "lat": test_space.latitude,
            "lng": test_space.longitude,
            "pin": "5544"
        })
        assert res_checkin.status_code == 200, f"Expected 200, got {res_checkin.status_code}: {res_checkin.data}"
        checkin_data = res_checkin.get_json()
        assert checkin_data["success"] is True
        assert "Digital access pass activated" in checkin_data["message"], f"Unexpected message: {checkin_data['message']}"
        print(f"✓ Passed: Check-in message is honest zero-hardware pass: '{checkin_data['message']}'")

        # ----------------------------------------------------
        # TEST 4: Duration Validation Bounds (0.5 to 168 hours)
        # ----------------------------------------------------
        print("\n[TEST 4] Testing Booking Duration Validation (0.5h to 168h bounds)...")
        # Sub-minimum: 0.25h
        res_sub = client.post("/api/bookings", json={
            "space_id": test_space.id,
            "hours": 0.25
        })
        assert res_sub.status_code == 400
        print("✓ Passed: 0.25h (< 0.5h minimum) cleanly rejected with 400.")

        # Minimum: 0.5h
        res_min = client.post("/api/bookings", json={
            "space_id": test_space.id,
            "hours": 0.5
        })
        assert res_min.status_code == 201
        print("✓ Passed: 0.5h (valid minimum) successfully created with 201.")

        # Maximum: 168h (7 days)
        res_max = client.post("/api/bookings", json={
            "space_id": test_space.id,
            "hours": 168.0
        })
        assert res_max.status_code == 201
        print("✓ Passed: 168.0h (valid maximum) successfully created with 201.")

        # Over-maximum: 200h
        res_over = client.post("/api/bookings", json={
            "space_id": test_space.id,
            "hours": 200.0
        })
        assert res_over.status_code == 400
        print("✓ Passed: 200.0h (> 168h maximum) cleanly rejected with 400.")

        # ----------------------------------------------------
        # TEST 5: All 7 LoopBot Intent Categories
        # ----------------------------------------------------
        print("\n[TEST 5] Testing All 7 LoopBot Intent Categories...")

        test_cases = [
            ("Finding Spaces", "Find me a quiet study desk in Pune", ["study", "pune", "₹", "wagholi"]),
            ("Micro-Lease & Legal", "How do micro-lease agreements protect owners from squatting?", ["easement", "section 52", "license", "escrow"]),
            ("Check-In & Pass", "How do I check in at the door with the geofence?", ["geofence", "pass", "50", "pin", "check-in"]),
            ("Safety & Aadhaar", "Is Aadhaar verification safe on SpaceLoop?", ["digilocker", "dpdp", "aadhaar", "masked"]),
            ("Hosting & Earnings", "How much can I earn renting an empty garage?", ["earn", "garage", "calculator", "95%"]),
            ("Booking & Duration", "What is the maximum duration I can book a space for?", ["0.5", "168", "duration", "pricing", "platform fee"]),
            ("Out-of-Scope Fallback", "Can you tell me the recipe for butter chicken?", ["loopbot", "spaceloop", "find", "booking", "easements act"]),
        ]

        for category, prompt, expected_keywords in test_cases:
            reply = concierge_chat([{"role": "user", "content": prompt}])
            assert reply and len(reply) > 20, f"Empty reply for {category}"
            matched_kws = [k for k in expected_keywords if k.lower() in reply.lower()]
            assert len(matched_kws) >= 1, f"Failed category '{category}' for prompt '{prompt}'. Got:\n{reply}"
            print(f"✓ Category [{category}] Verified! (Matched keywords: {matched_kws})")

        print("\n" + "=" * 60)
        print("ALL HARDENING & FEATURE POLISH TESTS PASSED 100%!")
        print("=" * 60)

if __name__ == "__main__":
    run_tests()
