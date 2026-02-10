#!/usr/bin/env python
"""Clear all data from database while keeping the schema"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.models import User, Medication, TestResult, Video, Notification, Reminder

def clear_database():
    """Delete all data from all tables while keeping schema"""
    db = SessionLocal()
    
    try:
        print("🗑️  Clearing database...")
        print("=" * 60)
        
        # Count records before deletion
        users_count = db.query(User).count()
        meds_count = db.query(Medication).count()
        tests_count = db.query(TestResult).count()
        videos_count = db.query(Video).count()
        notifications_count = db.query(Notification).count()
        reminders_count = db.query(Reminder).count()
        
        print(f"Records to delete:")
        print(f"  • Users: {users_count}")
        print(f"  • Medications: {meds_count}")
        print(f"  • Test Results: {tests_count}")
        print(f"  • Videos: {videos_count}")
        print(f"  • Notifications: {notifications_count}")
        print(f"  • Reminders: {reminders_count}")
        print(f"  TOTAL: {users_count + meds_count + tests_count + videos_count + notifications_count + reminders_count}")
        
        # Delete all data (order matters for foreign keys)
        print("\n🗑️  Deleting data...")
        db.query(Notification).delete()
        print("  ✓ Notifications cleared")
        
        db.query(Reminder).delete()
        print("  ✓ Reminders cleared")
        
        db.query(Medication).delete()
        print("  ✓ Medications cleared")
        
        db.query(TestResult).delete()
        print("  ✓ Test Results cleared")
        
        db.query(Video).delete()
        print("  ✓ Videos cleared")
        
        db.query(User).delete()
        print("  ✓ Users cleared")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✓✓✓ DATABASE CLEARED SUCCESSFULLY! ✓✓✓")
        print("=" * 60)
        print("\nSchema preserved:")
        print("  • Table structure intact")
        print("  • All data removed")
        print("  • Ready for new login info")
        print("\n✓ Database is ready for fresh data!")
        
    except Exception as e:
        print(f"✗ Error clearing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_database()
