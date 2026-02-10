#!/usr/bin/env python3
"""
IST-ONLY RESET FIX
Resets all medications and stores dates in IST format only (12-hour)
No UTC conversions anywhere!
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

# Database setup
DATABASE_URL = "sqlite:///physioclinic.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Define models to match database structure
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_timezone = Column(String, default="Asia/Kolkata")
    last_reset_date = Column(String, nullable=True)

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    medication_name = Column(String)
    is_taken = Column(Boolean, default=False)
    taken_date = Column(DateTime, nullable=True)

def fix_reset_ist_only():
    """Fix: Reset all medications and store date in IST format"""
    
    db = SessionLocal()
    
    try:
        
        print("=" * 60)
        print("🇮🇳 IST-ONLY RESET FIX (NO UTC)")
        print("=" * 60)
        
        # STEP 1: Get patient
        print("\nSTEP 1: Get Patient Information")
        patient = db.query(User).filter(User.id == 1).first()
        if not patient:
            print("❌ Patient not found!")
            return
        
        print(f"✅ Patient: {patient.name} (ID: {patient.id})")
        print(f"✅ Timezone: {patient.user_timezone}")
        
        # STEP 2: Get current medications
        print("\nSTEP 2: Get Current Medications")
        medications = db.query(Medication).filter(
            Medication.patient_id == patient.id
        ).all()
        
        print(f"✅ Total medications: {len(medications)}")
        taken_count = sum(1 for m in medications if m.is_taken)
        print(f"✅ Currently TAKEN: {taken_count}")
        
        # STEP 3: Reset all medications
        print("\nSTEP 3: Reset All Medications")
        for med in medications:
            if med.is_taken:
                print(f"  ✅ Reset: {med.medication_name}")
                med.is_taken = False
                med.taken_date = None
        
        print(f"✅ Total reset: {len(medications)} medications")
        
        # STEP 4: Update last reset date (IST ONLY, 12-hour format)
        print("\nSTEP 4: Update Last Reset Date (IST Format)")
        tz_ist = ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(tz=tz_ist)
        
        # Store proper datetime object with IST timezone
        print(f"Setting last_reset_date to: {now_ist}")
        patient.last_reset_date = now_ist
        
        # STEP 5: Commit changes
        print("\nSTEP 5: Commit Changes")
        db.commit()
        print(f"✅ Changes saved to database!")
        
        # STEP 6: Verification
        print("\nSTEP 6: Verification")
        taken_count = sum(1 for m in medications if m.is_taken)
        print(f"✅ Medications marked as TAKEN: {taken_count}")
        
        # Display the stored datetime in readable IST format
        if patient.last_reset_date:
            reset_display = patient.last_reset_date.strftime("%Y-%m-%d %I:%M %p IST")
            print(f"✅ Last Reset Date: {reset_display}")
        
        if taken_count == 0:
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS - All medications reset to NOT TAKEN!")
            print(f"📅 Reset Date: {reset_display}")
            print(f"{'='*60}")
        else:
            print(f"\n❌ ERROR - Some medications still TAKEN!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_reset_ist_only()
