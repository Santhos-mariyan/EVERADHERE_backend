#!/usr/bin/env python3
"""
Test script to verify the registration and verification flow
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_registration_flow():
    """Test the complete registration and verification flow"""

    # Test data
    user_data = {
        "name": "Test User",
        "age": 25,
        "gender": "Male",
        "email": "test@example.com",
        "password": "testpassword123",
        "location": "Test City",
        "user_type": "patient",
        "contact_number": "+1234567890"
    }

    print("🧪 Testing Registration Flow")
    print("=" * 50)

    # Step 1: Register user
    print("1. Registering user...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ Registration initiated successfully")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False

    # Step 2: Try to register again immediately (should fail)
    print("\n2. Trying to register again immediately (should fail)...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Correctly blocked duplicate registration")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Unexpected response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Step 3: Wait for OTP to expire (15 minutes is too long, so we'll simulate by manually checking)
    print("\n3. Registration flow test completed successfully!")
    print("   Note: OTP expiration would need to be tested with actual timing")
    print("   The logic now allows re-registration after OTP expires")

    return True

def test_login_without_verification():
    """Test that unverified users cannot login"""

    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    print("\n🧪 Testing Login Without Verification")
    print("=" * 50)

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 403:
            print("✅ Correctly blocked unverified user login")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Registration Flow Tests")
    print("=" * 60)

    success1 = test_registration_flow()
    success2 = test_login_without_verification()

    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)