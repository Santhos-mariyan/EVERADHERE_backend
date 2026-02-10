#!/usr/bin/env python
"""
Quick script to clear old FCM tokens from database after Firebase project switch
Run this ONCE to prepare for new FCM tokens from the new Firebase project
"""

from app.db.session import SessionLocal
from app.models.models import User
import sys

def clear_fcm_tokens():
    """Clear all FCM tokens from database"""
    db = SessionLocal()
    try:
        # Count before
        before = db.query(User).filter(User.fcm_token != None).count()
        print(f"📊 Users with FCM tokens before: {before}")
        
        # Clear tokens
        db.query(User).update({"fcm_token": None})
        db.commit()
        
        # Count after
        after = db.query(User).filter(User.fcm_token != None).count()
        print(f"📊 Users with FCM tokens after: {after}")
        
        if before > 0:
            print(f"✅ Cleared {before} old FCM tokens")
            print("\n📋 Next steps:")
            print("   1. Start backend: python main.py")
            print("   2. Patient logs in on Android (gets new token)")
            print("   3. Doctor prescribes medicine")
            print("   4. Patient receives notification ✅")
        else:
            print("⚠️  No tokens to clear (database already clean)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing tokens: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🔔 FCM TOKEN CLEANUP SCRIPT")
    print("=" * 60)
    print("\n⚠️  This will clear all old FCM tokens")
    print("   Reason: Firebase project switched from")
    print("   'physioclinicreminder' → 'everadhere'")
    print("\n✅ After this, patients will get NEW tokens")
    print("   when they log in on Android\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        if clear_fcm_tokens():
            print("\n" + "=" * 60)
            print("✅ READY TO GO!")
            print("=" * 60)
            print("\nStart backend: python main.py")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("❌ Cancelled")
        sys.exit(1)
