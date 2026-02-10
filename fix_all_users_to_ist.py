#!/usr/bin/env python3
"""
FIX ALL USERS TO IST
Changes all users' timezone to Asia/Kolkata (IST)
Converts all last_reset_date from UTC to proper IST datetime
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey

# Database setup
DATABASE_URL = "sqlite:///physioclinic.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    user_timezone = Column(String, default="Asia/Kolkata")
    last_reset_date = Column(DateTime, nullable=True)
    user_type = Column(String)

def fix_all_users():
    """Fix all users: Set timezone to IST and convert reset dates"""
    
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("🇮🇳 FIXING ALL USERS TO IST TIMEZONE")
        print("=" * 70)
        
        # Get all users
        users = db.query(User).all()
        print(f"\nFound {len(users)} users in database")
        
        tz_ist = ZoneInfo("Asia/Kolkata")
        tz_utc = ZoneInfo("UTC")
        
        updated_count = 0
        
        for user in users:
            print(f"\n{'─'*70}")
            print(f"User: {user.name} ({user.email})")
            print(f"  Type: {user.user_type}")
            print(f"  Current Timezone: {user.user_timezone}")
            print(f"  Current last_reset_date: {user.last_reset_date}")
            
            # Fix timezone
            if user.user_timezone != "Asia/Kolkata":
                user.user_timezone = "Asia/Kolkata"
                print(f"  ✅ Changed timezone to: Asia/Kolkata")
            else:
                print(f"  ✓ Already in IST timezone")
            
            # Fix last_reset_date if it exists
            if user.last_reset_date:
                stored_reset = user.last_reset_date
                
                # If it's naive (no tzinfo), assume it was stored as UTC
                if stored_reset.tzinfo is None:
                    # Treat as UTC and convert to IST
                    stored_reset_utc = stored_reset.replace(tzinfo=tz_utc)
                    reset_in_ist = stored_reset_utc.astimezone(tz_ist)
                    user.last_reset_date = reset_in_ist
                    print(f"  ✅ Converted naive datetime to IST:")
                    print(f"     Old (naive UTC): {stored_reset}")
                    print(f"     New (IST): {reset_in_ist}")
                else:
                    # Already has timezone, ensure it's IST
                    if str(stored_reset.tzinfo) != "Asia/Kolkata":
                        reset_in_ist = stored_reset.astimezone(tz_ist)
                        user.last_reset_date = reset_in_ist
                        print(f"  ✅ Converted {stored_reset.tzinfo} to IST:")
                        print(f"     Old: {stored_reset}")
                        print(f"     New: {reset_in_ist}")
                    else:
                        print(f"  ✓ Already in IST: {stored_reset}")
            else:
                print(f"  - No last_reset_date set")
            
            updated_count += 1
        
        # Commit all changes
        print(f"\n{'='*70}")
        print(f"Saving changes to database...")
        db.commit()
        print(f"✅ Successfully updated {updated_count} users!")
        
        # Verification
        print(f"\n{'='*70}")
        print("VERIFICATION")
        print(f"{'='*70}")
        
        for user in db.query(User).all():
            print(f"\n✓ {user.name} ({user.email})")
            print(f"  Timezone: {user.user_timezone}")
            if user.last_reset_date:
                reset_display = user.last_reset_date.strftime("%Y-%m-%d %I:%M %p %Z")
                print(f"  Last Reset: {reset_display}")
            else:
                print(f"  Last Reset: Not set")
        
        print(f"\n{'='*70}")
        print(f"✅ ALL USERS SUCCESSFULLY FIXED TO IST!")
        print(f"{'='*70}\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_users()
