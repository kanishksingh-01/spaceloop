#!/usr/bin/env python3
"""
Test Suite: Host View vs Seeker View Strict Authentication & Authorization Enforcement
Verifies:
1. Seeker Registration & Login (/api/v1/auth/seeker/register, /api/v1/auth/seeker/login)
2. Seeker Space Listing Rejection (POST /api/spaces -> 403 Forbidden)
3. Host Registration with Discom CA# + UPI Penny Drop (/api/v1/auth/host/register)
4. Host Space Listing Authorization (POST /api/spaces -> 201 Created)
5. Seeker Upgrade to Host (/api/v1/auth/host/upgrade)
6. Upgraded Seeker Space Listing Authorization
7. Non-Host Login Blocked at Host Login Endpoint (POST /api/v1/auth/host/login -> 403)
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User, Space

def test_host_seeker_separation():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        print("=" * 60)
        print("TESTING HOST VIEW & SEEKER VIEW AUTHENTICATION SEPARATION")
        print("=" * 60)

        # 1. Register a pure Seeker
        print("\n[TEST 1] Registering dedicated Seeker user...")
        seeker_email = f"seeker_test_{os.urandom(3).hex()}@university.ac.in"
        res = client.post('/api/v1/auth/seeker/register', json={
            "name": "Kavya Seeker",
            "email": seeker_email,
            "password": "Password123!",
            "college_name": "IIT Bombay",
            "student_id": "2024CS109"
        })
        assert res.status_code in [200, 201], f"Seeker register failed: {res.get_json()}"
        seeker_data = res.get_json()
        assert seeker_data["user"]["role"] == "seeker"
        assert seeker_data["user"]["is_host"] is False
        print(f"  ✓ Seeker registered: {seeker_email}, role={seeker_data['user']['role']}, is_host={seeker_data['user']['is_host']}")

        # 2. Try to list space as Seeker -> MUST FAIL with 403 Forbidden
        print("\n[TEST 2] Verifying Seeker CANNOT list space (Route Guard)...")
        res = client.post('/api/spaces', json={
            "title": "Unauthorized Seeker Pod",
            "description": "Should be rejected",
            "category": "Study",
            "hourly_rate": 50,
            "location": "Powai, Mumbai",
            "city": "Mumbai"
        })
        assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}: {res.get_json()}"
        err_json = res.get_json()
        assert "Host authentication and property verification required" in err_json["error"]
        print(f"  ✓ Route guard successfully blocked seeker: {err_json['error']}")

        # 3. Try to log in as Host with Seeker credentials -> MUST FAIL with 403 Forbidden
        print("\n[TEST 3] Verifying Seeker CANNOT log in via Host Auth endpoint...")
        res = client.post('/api/v1/auth/host/login', json={
            "email": seeker_email,
            "password": "Password123!"
        })
        assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}: {res.get_json()}"
        print(f"  ✓ Host login endpoint blocked seeker credentials with 403 Forbidden")

        # 4. Register a Property Host with Discom CA# and UPI Penny Drop KYC
        print("\n[TEST 4] Registering verified Host with Discom CA & UPI KYC...")
        host_email = f"host_test_{os.urandom(3).hex()}@spaceloop.in"
        res = client.post('/api/v1/auth/host/register', json={
            "name": "Vikram Adani Host",
            "email": host_email,
            "password": "HostPassword123!",
            "discom_provider": "BESCOM",
            "discom_ca": "CA8834920192",
            "address": "Indiranagar 100ft Rd, Bangalore",
            "upi_vpa": "vikram.adani@okhdfcbank",
            "bank_beneficiary_name": "Vikram Adani"
        })
        assert res.status_code in [200, 201], f"Host register failed: {res.get_json()}"
        host_data = res.get_json()
        assert host_data["user"]["is_host"] is True
        assert host_data["user"]["is_host_verified"] is True
        assert host_data["user"]["discom_provider"] == "BESCOM"
        assert host_data["user"]["discom_ca_masked"].endswith("0192")
        print(f"  ✓ Host registered and verified: {host_email}")
        print(f"    - Discom Masked CA: {host_data['user']['discom_ca_masked']}")
        print(f"    - UPI Payout VPA: {host_data['user']['upi_vpa_masked']}")

        # 5. List space as verified Host -> MUST SUCCEED
        print("\n[TEST 5] Listing space as authenticated Host...")
        res = client.post('/api/spaces', json={
            "title": "Indiranagar Executive Meeting Pod",
            "description": "Soundproofed pod with high-speed fiber",
            "category": "Workspace",
            "hourly_rate": 75,
            "location": "Indiranagar",
            "address": "Indiranagar 100ft Rd, Bangalore",
            "city": "Bangalore",
            "photos": ["https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80"],
            "amenities": ["Wi-Fi", "Air Conditioning", "Ergonomic Chairs"]
        })
        assert res.status_code in [200, 201], f"Host space creation failed: {res.get_json()}"
        space_data = res.get_json()
        assert space_data["title"] == "Indiranagar Executive Meeting Pod"
        print(f"  ✓ Space successfully listed by host (ID: {space_data['id']})")

        # 6. Test Seeker Upgrade Flow
        print("\n[TEST 6] Testing Seeker Account Elevation to Host (/api/v1/auth/host/upgrade)...")
        # Log back in as Seeker
        res = client.post('/api/v1/auth/seeker/login', json={
            "email": seeker_email,
            "password": "Password123!"
        })
        assert res.status_code == 200, f"Seeker login failed: {res.get_json()}"
        
        # Upgrade seeker to host
        res = client.post('/api/v1/auth/host/upgrade', json={
            "discom_provider": "TPDDL (Tata Power Delhi)",
            "discom_ca": "10048219034",
            "address": "Hauz Khas Enclave, New Delhi",
            "upi_vpa": "kavya.spaces@okaxis",
            "bank_beneficiary_name": "Kavya Seeker"
        })
        assert res.status_code == 200, f"Host upgrade failed: {res.get_json()}"
        upgraded_data = res.get_json()
        assert upgraded_data["user"]["is_host"] is True
        assert upgraded_data["user"]["is_host_verified"] is True
        print(f"  ✓ Seeker elevated to verified Host: role={upgraded_data['user']['role']}, is_host={upgraded_data['user']['is_host']}")

        # 7. List space as newly upgraded Host -> MUST SUCCEED
        print("\n[TEST 7] Listing space as newly upgraded Host...")
        res = client.post('/api/spaces', json={
            "title": "Hauz Khas Quiet Study Library",
            "description": "Quiet sunlight space for exam prep",
            "category": "Study",
            "hourly_rate": 40,
            "location": "Hauz Khas",
            "address": "Hauz Khas Enclave, New Delhi",
            "city": "Delhi"
        })
        assert res.status_code in [200, 201], f"Upgraded host space creation failed: {res.get_json()}"
        print(f"  ✓ Upgraded user successfully created space (ID: {res.get_json()['id']})")

        print("\n" + "=" * 60)
        print("ALL 7 HOST & SEEKER AUTHENTICATION TESTS PASSED (100% SUCCESS)!")
        print("=" * 60)

if __name__ == '__main__':
    test_host_seeker_separation()
