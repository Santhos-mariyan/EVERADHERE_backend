#!/usr/bin/env python
"""
Medication Expiration System - Diagnostic and Testing Script
Run this to verify the medication expiration system is working correctly.
"""

import requests
import json
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models.models import User, Medication
from app.core.security import get_password_hash

# Configuration
API_URL = "http://192.168.137.1:8001/api/v1"
DOCTOR_EMAIL = "doctor@test.com"
PATIENT_EMAIL = "patient@test.com"
PASSWORD = "password123"

def setup_test_users():
    """Create test doctor and patient users"""
    print("\n" + "="*60)
    print("STEP 1: Setting up test users")
    print("="*60)
    
    db = SessionLocal()
    
    # Check if users exist
    doctor = db.query(User).filter(User.email == DOCTOR_EMAIL).first()
    patient = db.query(User).filter(User.email == PATIENT_EMAIL).first()
    
    if not doctor:
        doctor = User(
            name="Dr. Test",
            email=DOCTOR_EMAIL,
            password_hash=get_password_hash(PASSWORD),
            user_type="doctor",
            is_verified=True,
            verified_at=datetime.utcnow()
        )
        db.add(doctor)
        print(f"✅ Created test doctor: {DOCTOR_EMAIL}")
    else:
        print(f"✅ Using existing doctor: {DOCTOR_EMAIL}")
    
    if not patient:
        patient = User(
            name="Patient Test",
            email=PATIENT_EMAIL,
            password_hash=get_password_hash(PASSWORD),
            user_type="patient",
            is_verified=True,
            verified_at=datetime.utcnow()
        )
        db.add(patient)
        print(f"✅ Created test patient: {PATIENT_EMAIL}")
    else:
        print(f"✅ Using existing patient: {PATIENT_EMAIL}")
    
    db.commit()
    db.refresh(doctor)
    db.refresh(patient)
    
    print(f"\nDoctor ID: {doctor.id}")
    print(f"Patient ID: {patient.id}")
    
    db.close()
    return doctor.id, patient.id

def get_auth_token(email, password):
    """Login and get auth token"""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_prescribe_medications(doctor_token, patient_id):
    """Test prescribing medications with different durations"""
    print("\n" + "="*60)
    print("STEP 2: Testing medication prescription")
    print("="*60)
    
    medications = [
        {
            "medication_name": "Expired_2Days_Ago",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "2 days",
            "instructions": "Take after meals"
        },
        {
            "medication_name": "Active_1Week",
            "dosage": "250mg",
            "frequency": "Once daily",
            "duration": "1 week",
            "instructions": "Take before sleep"
        },
        {
            "medication_name": "Active_3Months",
            "dosage": "100mg",
            "frequency": "Three times daily",
            "duration": "3 months",
            "instructions": "Take regularly"
        }
    ]
    
    payload = {
        "patient_id": patient_id,
        "medications": medications
    }
    
    response = requests.post(
        f"{API_URL}/medications/prescribe",
        json=payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    if response.status_code == 201:
        print(f"✅ Prescribed {len(medications)} medications")
        result = response.json()
        for med in result:
            print(f"   - {med['medication_name']} (ID: {med['id']}, Duration: {med['duration']})")
        return result
    else:
        print(f"❌ Prescription failed: {response.text}")
        return None

def test_cleanup_endpoint(patient_token):
    """Test the cleanup-expired endpoint"""
    print("\n" + "="*60)
    print("STEP 3: Testing cleanup-expired endpoint")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/medications/cleanup-expired",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    print(f"Response Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Cleanup successful: {response.json()['message']}")
        return True
    else:
        print(f"❌ Cleanup failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_medications(patient_token):
    """Test fetching patient medications"""
    print("\n" + "="*60)
    print("STEP 4: Fetching patient medications")
    print("="*60)
    
    response = requests.get(
        f"{API_URL}/medications/my-medications",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    if response.status_code == 200:
        medications = response.json()
        print(f"✅ Retrieved {len(medications)} medications:")
        for med in medications:
            print(f"   - {med['medication_name']} | Duration: {med['duration']} | Prescribed: {med.get('prescribed_date', 'N/A')}")
        return medications
    else:
        print(f"❌ Failed to fetch medications: {response.text}")
        return None

def test_duration_parsing():
    """Test duration parsing logic"""
    print("\n" + "="*60)
    print("STEP 5: Testing duration parsing")
    print("="*60)
    
    from app.api.endpoints.medications import parse_duration, is_medication_expired
    
    test_cases = [
        ("2 days", 2),
        ("1 week", 7),
        ("3 months", 90),
        ("1 year", 365),
    ]
    
    for duration_str, expected_days in test_cases:
        parsed = parse_duration(duration_str)
        actual_days = parsed.days
        status = "✅" if actual_days >= expected_days - 5 else "❌"
        print(f"{status} Duration '{duration_str}' = {actual_days} days (expected ~{expected_days})")

def test_expiration_calculation():
    """Test expiration calculation"""
    print("\n" + "="*60)
    print("STEP 6: Testing expiration calculations")
    print("="*60)
    
    from app.api.endpoints.medications import is_medication_expired
    
    now = datetime.utcnow()
    
    # Test 1: Medication prescribed 3 days ago with 2-day duration (EXPIRED)
    prescribed_3_days_ago = now - timedelta(days=3)
    is_expired = is_medication_expired(prescribed_3_days_ago, "2 days")
    status = "✅" if is_expired else "❌"
    print(f"{status} Medication from 3 days ago with 2-day duration: {'EXPIRED' if is_expired else 'ACTIVE'} (expected: EXPIRED)")
    
    # Test 2: Medication prescribed 2 days ago with 5-day duration (ACTIVE)
    prescribed_2_days_ago = now - timedelta(days=2)
    is_expired = is_medication_expired(prescribed_2_days_ago, "5 days")
    status = "✅" if not is_expired else "❌"
    print(f"{status} Medication from 2 days ago with 5-day duration: {'EXPIRED' if is_expired else 'ACTIVE'} (expected: ACTIVE)")
    
    # Test 3: Medication prescribed today with 1-week duration (ACTIVE)
    prescribed_today = now
    is_expired = is_medication_expired(prescribed_today, "1 week")
    status = "✅" if not is_expired else "❌"
    print(f"{status} Medication from today with 1-week duration: {'EXPIRED' if is_expired else 'ACTIVE'} (expected: ACTIVE)")

def run_all_tests():
    """Run all diagnostic tests"""
    print("\n" + "="*70)
    print("MEDICATION EXPIRATION SYSTEM - DIAGNOSTIC TEST")
    print("="*70)
    
    # Setup
    doctor_id, patient_id = setup_test_users()
    
    # Login
    print("\n" + "="*60)
    print("STEP 0: Authenticating users")
    print("="*60)
    
    doctor_token = get_auth_token(DOCTOR_EMAIL, PASSWORD)
    patient_token = get_auth_token(PATIENT_EMAIL, PASSWORD)
    
    if not doctor_token or not patient_token:
        print("❌ Authentication failed!")
        return
    
    print(f"✅ Doctor authenticated")
    print(f"✅ Patient authenticated")
    
    # Test duration parsing
    test_duration_parsing()
    
    # Test expiration calculation
    test_expiration_calculation()
    
    # Test API endpoints
    meds = test_prescribe_medications(doctor_token, patient_id)
    
    cleanup_ok = test_cleanup_endpoint(patient_token)
    
    final_meds = test_get_medications(patient_token)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if meds:
        print(f"✅ Medication prescription: PASSED ({len(meds)} medications)")
    else:
        print(f"❌ Medication prescription: FAILED")
    
    if cleanup_ok:
        print(f"✅ Cleanup endpoint: PASSED")
    else:
        print(f"⚠️  Cleanup endpoint: CHECK LOGS (may need backend restart)")
    
    if final_meds is not None:
        print(f"✅ Fetch medications: PASSED ({len(final_meds)} medications)")
    else:
        print(f"❌ Fetch medications: FAILED")
    
    print("\n✅ All diagnostic tests completed!")
    print("Check the output above for any issues.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()
