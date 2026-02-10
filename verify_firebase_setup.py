#!/usr/bin/env python
"""
Quick Firebase Setup Verification Script
Run this to verify everything is configured correctly
"""

import os
import sys
from pathlib import Path
import json

def check_firebase_key():
    """Check if Firebase serviceAccountKey.json exists"""
    print("\n" + "="*60)
    print("🔍 CHECKING FIREBASE SERVICE ACCOUNT KEY")
    print("="*60)
    
    possible_paths = [
        Path("app/firebase/serviceAccountKey.json"),
        Path("app") / "firebase" / "serviceAccountKey.json",
        Path(__file__).parent / "app" / "firebase" / "serviceAccountKey.json",
    ]
    
    found_path = None
    for path in possible_paths:
        if path.exists():
            found_path = path
            break
    
    if found_path:
        print(f"✅ Found: {found_path}")
        try:
            with open(found_path, 'r') as f:
                data = json.load(f)
            print(f"✅ Valid JSON format")
            print(f"✅ Project ID: {data.get('project_id', 'NOT SET')}")
            print(f"✅ Service Account Email: {data.get('client_email', 'NOT SET')}")
            return True
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON format - file is corrupted")
            return False
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return False
    else:
        print(f"❌ NOT FOUND")
        print(f"   Expected at: app/firebase/serviceAccountKey.json")
        print(f"   ")
        print(f"   📥 How to get Firebase Key:")
        print(f"   1. Go to Firebase Console: https://console.firebase.google.com/")
        print(f"   2. Select your PhysiotherapistClinic project")
        print(f"   3. Go to Project Settings → Service Accounts tab")
        print(f"   4. Click 'Generate New Private Key'")
        print(f"   5. JSON file will download")
        print(f"   6. Move file to: app/firebase/serviceAccountKey.json")
        return False


def check_database():
    """Check if User model has fcm_token field"""
    print("\n" + "="*60)
    print("🔍 CHECKING DATABASE SCHEMA")
    print("="*60)
    
    try:
        from app.models.models import User
        from sqlalchemy import inspect
        
        # Get columns
        mapper = inspect(User)
        columns = {c.name for c in mapper.columns}
        
        if 'fcm_token' in columns:
            print(f"✅ User.fcm_token field exists")
            return True
        else:
            print(f"❌ User.fcm_token field NOT FOUND")
            print(f"   Please add: fcm_token = Column(String, nullable=True)")
            return False
    except Exception as e:
        print(f"⚠️  Could not check database: {str(e)}")
        return False


def check_firebase_service():
    """Check if firebase_service module exists and has required functions"""
    print("\n" + "="*60)
    print("🔍 CHECKING FIREBASE SERVICE MODULE")
    print("="*60)
    
    try:
        from app.services import firebase_service
        
        # Check functions exist
        required_functions = [
            'init_firebase',
            'send_push_notification',
            'send_medication_prescribed_notification',
            'get_firebase_status',
            'is_firebase_initialized'
        ]
        
        all_exist = True
        for func_name in required_functions:
            if hasattr(firebase_service, func_name):
                print(f"✅ {func_name}() exists")
            else:
                print(f"❌ {func_name}() NOT FOUND")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Could not import firebase_service: {str(e)}")
        return False


def check_dependencies():
    """Check if firebase-admin is installed"""
    print("\n" + "="*60)
    print("🔍 CHECKING PYTHON DEPENDENCIES")
    print("="*60)
    
    try:
        import firebase_admin
        print(f"✅ firebase-admin is installed")
        print(f"   Version: {firebase_admin.__version__ if hasattr(firebase_admin, '__version__') else 'unknown'}")
        return True
    except ImportError:
        print(f"❌ firebase-admin is NOT installed")
        print(f"   Install with: pip install firebase-admin==6.5.0")
        return False


def check_api_endpoints():
    """Check if API endpoints exist"""
    print("\n" + "="*60)
    print("🔍 CHECKING API ENDPOINTS")
    print("="*60)
    
    try:
        from app.api.endpoints import users, medications
        
        checks = [
            ('users.save_fcm_token', hasattr(users, 'save_fcm_token')),
            ('users.get_fcm_status', hasattr(users, 'get_fcm_status')),
            ('users.test_notification', hasattr(users, 'test_notification')),
            ('medications.prescribe_medications', hasattr(medications, 'prescribe_medications')),
        ]
        
        all_exist = True
        for name, exists in checks:
            if exists:
                print(f"✅ {name} exists")
            else:
                print(f"❌ {name} NOT FOUND")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Could not check endpoints: {str(e)}")
        return False


def main():
    """Run all checks"""
    print("\n")
    print("  ███████╗██╗██████╗ ███████╗██████╗  █████╗ ███████╗███████╗")
    print("  ██╔════╝██║██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝")
    print("  █████╗  ██║██████╔╝█████╗  ██████╔╝███████║███████╗█████╗  ")
    print("  ██╔══╝  ██║██╔══██╗██╔══╝  ██╔══██╗██╔══██║╚════██║██╔══╝  ")
    print("  ██║     ██║██║  ██║███████╗██████╔╝██║  ██║███████║███████╗")
    print("  ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝")
    print("\n  Push Notification Setup Verification")
    print("\n")
    
    results = {
        "Firebase Key": check_firebase_key(),
        "Database Schema": check_database(),
        "Firebase Service": check_firebase_service(),
        "Dependencies": check_dependencies(),
        "API Endpoints": check_api_endpoints(),
    }
    
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\n🚀 You're ready to use push notifications!")
        print("\n📱 Next Steps:")
        print("   1. Start backend: python main.py")
        print("   2. Patient logs in on Android device")
        print("   3. Check backend logs for 'FCM token saved'")
        print("   4. Doctor prescribes medication")
        print("   5. Patient receives pop-up notification!")
        print("\n💡 For debugging:")
        print("   - Use endpoint: GET /api/v1/users/fcm-status")
        print("   - Test notification: POST /api/v1/users/test-notification")
        print("\n")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("="*60)
        print("\n⚠️  Please fix the issues above before using push notifications")
        print("\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
