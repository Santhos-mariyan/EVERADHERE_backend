#!/usr/bin/env python
"""Complete working model with test data seeding"""
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.models.models import User, Medication, TestResult
from app.core.security import get_password_hash
from sqlalchemy import func

# Create all tables
Base.metadata.create_all(bind=engine)

def seed_test_data():
    """Seed database with test data"""
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Medication).delete()
        db.query(TestResult).delete()
        db.query(User).delete()
        db.commit()
        
        print("✓ Cleared existing data")
        
        # Create test doctor
        doctor = User(
            name="Dr. Smith",
            age=45,
            gender="Male",
            email="doctor@example.com",
            password=get_password_hash("password123"),
            location="Hospital A",
            user_type="doctor",
            is_verified=True
        )
        db.add(doctor)
        db.commit()
        print(f"✓ Created test doctor: {doctor.name} (ID: {doctor.id})")
        
        # Create test patients
        patients = []
        for i in range(5):
            patient = User(
                name=f"Patient {i+1}",
                age=30 + i,
                gender="Male" if i % 2 == 0 else "Female",
                email=f"patient{i+1}@example.com",
                password=get_password_hash("password123"),
                location=f"Address {i+1}",
                user_type="patient",
                is_verified=True
            )
            db.add(patient)
            db.commit()
            patients.append(patient)
            print(f"  - Created patient: {patient.name} (ID: {patient.id})")
        
        print(f"✓ Created {len(patients)} test patients")
        
        # Create medications prescribed by doctor to patients
        meds = []
        for idx, patient in enumerate(patients):
            med = Medication(
                patient_id=patient.id,
                doctor_id=doctor.id,
                medication_name=f"Medicine {idx+1}",
                dosage="1 tablet",
                frequency="Twice daily",
                duration="30 days",
                instructions=f"Take after meals",
                is_taken=False,
                prescribed_date=datetime.utcnow()
            )
            db.add(med)
            meds.append(med)
        
        db.commit()
        print(f"✓ Created {len(meds)} medications prescribed by doctor")
        
        # Verify the data
        print("\n" + "="*60)
        print("DATA VERIFICATION")
        print("="*60)
        
        total_doctors = db.query(User).filter(User.user_type == "doctor").count()
        total_patients = db.query(User).filter(User.user_type == "patient").count()
        total_meds = db.query(Medication).count()
        
        print(f"Total doctors in database: {total_doctors}")
        print(f"Total patients in database: {total_patients}")
        print(f"Total medications in database: {total_meds}")
        
        # Check medications for this doctor
        doctor_meds = db.query(Medication).filter(
            Medication.doctor_id == doctor.id
        ).all()
        print(f"\nMedications prescribed by doctor {doctor.name}: {len(doctor_meds)}")
        
        # Test the active_patients query
        active_patients = db.query(func.count(func.distinct(Medication.patient_id))).filter(
            Medication.doctor_id == doctor.id
        ).scalar()
        
        print(f"Distinct patients with medications from doctor: {active_patients or 0}")
        print(f"\nPatient IDs with medications from this doctor:")
        patient_ids = db.query(Medication.patient_id).filter(
            Medication.doctor_id == doctor.id
        ).distinct().all()
        for (pid,) in patient_ids:
            patient = db.query(User).filter(User.id == pid).first()
            print(f"  - Patient ID {pid}: {patient.name if patient else 'Unknown'}")
        
        print("\n" + "="*60)
        print("TEST DATA SEEDING COMPLETE ✓")
        print("="*60)
        print("\nYou can now test the API at: http://localhost:8001/docs")
        print(f"Login with doctor email: {doctor.email}")
        print("Password: password123")
        
        return doctor.email
        
    except Exception as e:
        print(f"✗ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_data()
