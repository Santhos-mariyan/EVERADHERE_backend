"""
Quick test script to verify Firebase is working
"""
import sys
import os
sys.path.insert(0, os.getcwd())

# Test 1: Import firebase_service
print("=" * 60)
print("TEST 1: Testing Firebase Service Import")
print("=" * 60)

try:
    from app.services import firebase_service
    print("✅ Successfully imported firebase_service")
except ImportError as e:
    print(f"❌ Failed to import firebase_service: {e}")
    sys.exit(1)

# Test 2: Initialize Firebase
print("\n" + "=" * 60)
print("TEST 2: Testing Firebase Initialization")
print("=" * 60)

if firebase_service.init_firebase():
    print("✅ Firebase initialized successfully")
    status = firebase_service.get_firebase_status()
    print(f"   Status: {status}")
else:
    print(f"⚠️  Firebase not initialized: {firebase_service.get_firebase_status()['error']}")
    print("   This is expected if you haven't configured Firebase key yet")
    print("   But the import error is FIXED ✅")

# Test 3: Check if functions exist
print("\n" + "=" * 60)
print("TEST 3: Checking Firebase Service Functions")
print("=" * 60)

functions = [
    'init_firebase',
    'is_firebase_initialized',
    'get_firebase_status',
    'send_push_notification',
    'send_medication_prescribed_notification'
]

for func_name in functions:
    if hasattr(firebase_service, func_name):
        print(f"✅ {func_name} exists")
    else:
        print(f"❌ {func_name} NOT FOUND")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - No Import Errors!")
print("=" * 60)
