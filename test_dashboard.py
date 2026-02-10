#!/usr/bin/env python
"""Test dashboard endpoint"""
import requests
import json
from app.db.session import SessionLocal
from app.models.models import User, Medication
from datetime import datetime

# Get database session
db = SessionLocal()

try:
    # Check if we have users
    doctors = db.query(User).filter(User.user_type == "doctor").all()
    patients = db.query(User).filter(User.user_type == "patient").all()
    medications = db.query(Medication).all()
    
    print("=" * 60)
    print("DATABASE STATUS")
    print("=" * 60)
    print(f"Total Doctors: {len(doctors)}")
    print(f"Total Patients: {len(patients)}")
    print(f"Total Medications: {len(medications)}")
    
    if doctors:
        doctor = doctors[0]
        print(f"\nFirst Doctor: {doctor.name} (ID: {doctor.id})")
        
        # Count medications for this doctor
        doctor_meds = db.query(Medication).filter(Medication.doctor_id == doctor.id).all()
        print(f"Medications prescribed by this doctor: {len(doctor_meds)}")
        
        # Count unique patients
        from sqlalchemy import func
        distinct_patients = db.query(func.count(func.distinct(Medication.patient_id))).filter(
            Medication.doctor_id == doctor.id
        ).scalar()
        print(f"Distinct patients prescribed to: {distinct_patients or 0}")
        
        if doctor_meds:
            print("\nSample medications:")
            for med in doctor_meds[:3]:
                print(f"  - {med.medication_name} (Patient ID: {med.patient_id})")
    
    print("\n" + "=" * 60)
    print("ATTEMPTING TO GET DASHBOARD")
    print("=" * 60)
    
    # Try to get dashboard data
    if doctors:
        doctor = doctors[0]
        print(f"\nTesting with doctor: {doctor.name}")
        print(f"Auth token would be: Bearer [token]")
        print("\nNote: To test the actual endpoint, you need a valid JWT token")
        print("You can get one by logging in through the API")
        
finally:
    db.close()
