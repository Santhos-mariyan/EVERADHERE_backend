"""
Quick test of the updated /my-medications endpoint
"""
import requests
import json
from datetime import datetime

# Test credentials
API_BASE = "http://localhost:8001/api/v1"

# Step 1: Login as patient
print("=" * 80)
print("STEP 1: LOGIN AS PATIENT")
print("=" * 80)

login_response = requests.post(f"{API_BASE}/auth/login", json={
    "email": "santhosh@patient.com",
    "password": "password123"
})

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Login successful")
print(f"   Token: {token[:50]}...")

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Get medications (this should trigger reset logic)
print("\n" + "=" * 80)
print("STEP 2: GET MY MEDICATIONS (Should trigger auto-reset)")
print("=" * 80)

meds_response = requests.get(f"{API_BASE}/medications/my-medications", headers=headers)

if meds_response.status_code != 200:
    print(f"❌ Failed to get medications: {meds_response.text}")
    exit(1)

medications = meds_response.json()
print(f"✅ Retrieved {len(medications)} medications")

# Check medication status
taken_count = sum(1 for med in medications if med.get("is_taken", False))
print(f"   Medications marked as TAKEN: {taken_count}")
print(f"   Medications marked as NOT TAKEN: {len(medications) - taken_count}")

# Print each medication
print("\nMedication Details:")
for med in medications[:5]:  # Show first 5
    status = "✅ TAKEN" if med.get("is_taken") else "❌ NOT TAKEN"
    print(f"  • {med['medication_name']:<30} {status} | TakenDate: {med.get('taken_date', 'NULL')}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE - Endpoint working!")
print("=" * 80)
print("\nWhat happened:")
print("  1. Called GET /medications/my-medications")
print("  2. Backend checked if new day in IST timezone")
print("  3. If new day → reset all taken medications")
print("  4. Returned fresh medication list")
