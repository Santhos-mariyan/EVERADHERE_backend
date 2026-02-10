#!/usr/bin/env python3
"""
Test the registration endpoint with contact_number
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_registration():
    """Test registration with contact number"""
    
    payload = {
        "email": "testuser@test.com",
        "password": "password123",
        "name": "Test User",
        "age": 30,
        "gender": "Male",
        "location": "Mumbai",
        "user_type": "patient",
        "contact_number": "+91-9876543210"
    }
    
    print("\n" + "="*70)
    print("REGISTRATION TEST")
    print("="*70)
    print("\nPayload being sent:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"\n✅ Registration successful!")
            print(f"   User ID: {user_data.get('id')}")
            print(f"   Contact received: {user_data.get('contact_number')}")
            
            if user_data.get('contact_number') == "+91-9876543210":
                print("✅ Contact matches!")
            else:
                print(f"❌ Contact mismatch!")
                print(f"   Expected: +91-9876543210")
                print(f"   Got: {user_data.get('contact_number')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Make sure backend is running on http://localhost:8001")
    test_registration()
