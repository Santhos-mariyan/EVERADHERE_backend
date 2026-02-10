#!/usr/bin/env python3
"""
Complete end-to-end test for contact_number functionality
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_registration_with_contact():
    """Test registration with contact number"""
    try:
        print("\n" + "="*70)
        print("TEST 1: REGISTRATION WITH CONTACT NUMBER")
        print("="*70)
        
        test_email = "testuser123@test.com"
        test_contact = "+91-9876543210"
        
        payload = {
            "email": test_email,
            "password": "password123",
            "name": "Test Patient",
            "age": 25,
            "gender": "Male",
            "location": "Mumbai",
            "user_type": "patient",
            "contact_number": test_contact
        }
        
        print("\n📤 Sending registration request:")
        print(json.dumps(payload, indent=2))
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            resp_data = response.json()
            print(f"✅ Registration successful!")
            print(f"   User ID: {resp_data.get('id')}")
            print(f"   Name: {resp_data.get('name')}")
            print(f"   Contact received: {resp_data.get('contact_number')}")
            
            if resp_data.get('contact_number') == test_contact:
                print(f"✅ Contact number matches!")
                return True, test_email
            else:
                print(f"❌ Contact mismatch!")
                print(f"   Sent: {test_contact}")
                print(f"   Received: {resp_data.get('contact_number')}")
                return False, test_email
        else:
            print(f"❌ Registration failed: {response.text}")
            return False, test_email
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_profile_display(email, password="password123"):
    """Test profile display with contact"""
    try:
        print("\n" + "="*70)
        print("TEST 2: LOGIN AND DISPLAY PROFILE")
        print("="*70)
        
        # Login
        login_payload = {
            "email": email,
            "password": password
        }
        
        print(f"\n🔐 Logging in...")
        response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            return False
        
        token = response.json().get('access_token')
        print(f"✅ Login successful, token received")
        
        # Get profile
        print(f"\n📋 Fetching user profile...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Profile retrieved!")
            print(f"   Name: {user_data.get('name')}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   Contact: {user_data.get('contact_number')}")
            
            if user_data.get('contact_number'):
                print(f"✅ Contact number is present in profile!")
                return True, token
            else:
                print(f"❌ Contact number is missing or empty!")
                return False, token
        else:
            print(f"❌ Failed to get profile: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_profile_update(email, token):
    """Test profile update with new contact"""
    try:
        print("\n" + "="*70)
        print("TEST 3: UPDATE PROFILE WITH NEW CONTACT")
        print("="*70)
        
        new_contact = "+91-8765432109"
        
        update_payload = {
            "name": "Test Patient Updated",
            "age": 26,
            "gender": "Male",
            "location": "Bangalore",
            "contact_number": new_contact
        }
        
        print(f"\n✏️  Updating profile:")
        print(json.dumps(update_payload, indent=2))
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{BASE_URL}/users/me", json=update_payload, headers=headers)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            updated_user = response.json()
            print(f"✅ Profile updated!")
            print(f"   Name: {updated_user.get('name')}")
            print(f"   Location: {updated_user.get('location')}")
            print(f"   Contact: {updated_user.get('contact_number')}")
            
            if updated_user.get('contact_number') == new_contact:
                print(f"✅ Contact updated correctly!")
                return True
            else:
                print(f"❌ Contact not updated!")
                print(f"   Expected: {new_contact}")
                print(f"   Got: {updated_user.get('contact_number')}")
                return False
        else:
            print(f"❌ Update failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "🚀 "*35)
    print("CONTACT NUMBER END-TO-END TEST")
    print("🚀 "*35)
    
    print("\n⚠️  Make sure backend is running at http://localhost:8001")
    print("   Command: .\\venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001")
    
    results = []
    
    # Test 1: Registration
    success, email = test_registration_with_contact()
    results.append(("Registration with Contact", success))
    
    if not success or not email:
        print("\n❌ Registration test failed, cannot continue")
        return results
    
    # Test 2: Profile Display
    success, token = test_profile_display(email)
    results.append(("Profile Display", success))
    
    if not success or not token:
        print("\n❌ Profile display test failed, cannot continue")
        return results
    
    # Test 3: Profile Update
    success = test_profile_update(email, token)
    results.append(("Profile Update", success))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Contact number fully working!")
    else:
        print("\n⚠️  Some tests failed. Check output above.")
    
    return results

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend at http://localhost:8001")
        print("   Please start the backend with:")
        print("   .\\venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
