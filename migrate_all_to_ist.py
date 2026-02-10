"""
Migration script to convert all datetime fields from UTC to IST timezone
This script handles all datetime fields across all tables
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.models.models import (
    User, Medication, TestResult, Video, 
    Notification, Reminder, VerificationCode
)
from app.db.session import SessionLocal

def migrate_to_ist():
    """Convert all naive UTC datetimes to IST timezone-aware datetimes"""
    
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("🔄 MIGRATING ALL DATETIME FIELDS TO IST TIMEZONE")
        print("="*80)
        
        ist = ZoneInfo("Asia/Kolkata")
        
        # 1. Fix User table
        print("\n📋 Processing User table...")
        users = db.query(User).all()
        user_count = 0
        for user in users:
            if user.created_at and user.created_at.tzinfo is None:
                # Convert naive UTC to IST-aware
                user.created_at = user.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                user_count += 1
            if user.last_reset_date and user.last_reset_date.tzinfo is None:
                user.last_reset_date = user.last_reset_date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
            print(f"  ✅ Updated user: {user.name} - ID: {user.id}")
        
        db.commit()
        print(f"  ✅ {user_count} users updated")
        
        # 2. Fix Medication table
        print("\n💊 Processing Medication table...")
        medications = db.query(Medication).all()
        med_count = 0
        for med in medications:
            if med.prescribed_date and med.prescribed_date.tzinfo is None:
                med.prescribed_date = med.prescribed_date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                med_count += 1
            if med.taken_date and med.taken_date.tzinfo is None:
                med.taken_date = med.taken_date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
            print(f"  ✅ Updated medication: {med.name} - ID: {med.id}")
        
        db.commit()
        print(f"  ✅ {med_count} medications updated")
        
        # 3. Fix TestResult table
        print("\n🩺 Processing TestResult table...")
        test_results = db.query(TestResult).all()
        test_count = 0
        for test in test_results:
            if test.date and test.date.tzinfo is None:
                test.date = test.date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                test_count += 1
                print(f"  ✅ Updated test result - ID: {test.id}")
        
        db.commit()
        print(f"  ✅ {test_count} test results updated")
        
        # 4. Fix Video table
        print("\n🎥 Processing Video table...")
        videos = db.query(Video).all()
        video_count = 0
        for video in videos:
            if video.upload_date and video.upload_date.tzinfo is None:
                video.upload_date = video.upload_date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                video_count += 1
                print(f"  ✅ Updated video: {video.title} - ID: {video.id}")
        
        db.commit()
        print(f"  ✅ {video_count} videos updated")
        
        # 5. Fix Notification table
        print("\n🔔 Processing Notification table...")
        notifications = db.query(Notification).all()
        notif_count = 0
        for notif in notifications:
            if notif.date and notif.date.tzinfo is None:
                notif.date = notif.date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                notif_count += 1
                print(f"  ✅ Updated notification - ID: {notif.id}")
        
        db.commit()
        print(f"  ✅ {notif_count} notifications updated")
        
        # 6. Fix Reminder table
        print("\n⏰ Processing Reminder table...")
        reminders = db.query(Reminder).all()
        reminder_count = 0
        for reminder in reminders:
            if reminder.created_at and reminder.created_at.tzinfo is None:
                reminder.created_at = reminder.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                reminder_count += 1
                print(f"  ✅ Updated reminder - ID: {reminder.id}")
        
        db.commit()
        print(f"  ✅ {reminder_count} reminders updated")
        
        # 7. Fix VerificationCode table
        print("\n✔️  Processing VerificationCode table...")
        verification_codes = db.query(VerificationCode).all()
        verif_count = 0
        for verif in verification_codes:
            if verif.created_at and verif.created_at.tzinfo is None:
                verif.created_at = verif.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
                verif_count += 1
            if verif.expires_at and verif.expires_at.tzinfo is None:
                verif.expires_at = verif.expires_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
            print(f"  ✅ Updated verification code - Email: {verif.email}")
        
        db.commit()
        print(f"  ✅ {verif_count} verification codes updated")
        
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETE!")
        print("="*80)
        print(f"\n📊 Summary:")
        print(f"  • Users: {user_count} updated")
        print(f"  • Medications: {med_count} updated")
        print(f"  • Test Results: {test_count} updated")
        print(f"  • Videos: {video_count} updated")
        print(f"  • Notifications: {notif_count} updated")
        print(f"  • Reminders: {reminder_count} updated")
        print(f"  • Verification Codes: {verif_count} updated")
        print("\n✅ All datetime fields are now in IST timezone!\n")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_ist()
