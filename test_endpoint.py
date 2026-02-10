#!/usr/bin/env python
"""Test the dashboard endpoint with login"""
import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 70)
print("TESTING DOCTOR DASHBOARD ENDPOINT")
print("=" * 70)

# Step 1: Login with test doctor credentials
print("\n1. Logging in as doctor...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "doctor@example.com",
        "password": "password123"
    }
)

if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data.get("access_token")
    print(f"✓ Login successful!")
    print(f"  Token: {token[:20]}...")
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(f"  Response: {login_response.text}")
    exit(1)

# Step 2: Call the dashboard endpoint
print("\n2. Calling /api/dashboard/doctor endpoint...")
headers = {"Authorization": f"Bearer {token}"}
dashboard_response = requests.get(
    f"{BASE_URL}/api/dashboard/doctor",
    headers=headers
)

if dashboard_response.status_code == 200:
    dashboard_data = dashboard_response.json()
    print(f"✓ Dashboard endpoint successful!")
    print("\n3. DASHBOARD DATA:")
    print(json.dumps(dashboard_data, indent=2, default=str))
    
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"Total Patients:        {dashboard_data.get('total_patients', 'N/A')}")
    print(f"Today's Appointments:  {dashboard_data.get('today_appointments', 'N/A')}")
    print(f"Active Patients:       {dashboard_data.get('active_patients', 'N/A')}")
    print(f"Recent Patients:       {len(dashboard_data.get('recent_patients', []))} patients")
    
    if dashboard_data.get('active_patients') == 5:
        print("\n✓✓✓ SUCCESS! Active Patients count is correct! ✓✓✓")
    else:
        print(f"\n✗ ERROR: Expected active_patients=5, got {dashboard_data.get('active_patients')}")
else:
    print(f"✗ Dashboard request failed: {dashboard_response.status_code}")
    print(f"  Response: {dashboard_response.text}")
    exit(1)

print("\n" + "=" * 70)
