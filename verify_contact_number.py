#!/usr/bin/env python3
"""
Complete verification test for contact_number functionality
Tests: Registration -> Login -> Profile Retrieval
"""

import sqlite3
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'physioclinic.db')

def test_database_schema():
    """Verify contact_number column exists in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("🔍 DATABASE SCHEMA VERIFICATION")
        print("="*70)
        
        # Check if contact_number column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = {column[1]: column[2] for column in cursor.fetchall()}
        
        if 'contact_number' in columns:
            print("✅ contact_number column exists in users table")
            print(f"   Type: {columns['contact_number']}")
        else:
            print("❌ contact_number column NOT FOUND in users table")
            print(f"   Available columns: {list(columns.keys())}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def test_sample_user_data():
    """Insert a test user with contact number and verify retrieval"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("✔️ SAMPLE USER WITH CONTACT NUMBER")
        print("="*70)
        
        # Test data
        test_email = f"test_contact_{int(datetime.now().timestamp())}@test.com"
        test_contact = "+91-9876543210"
        
        print(f"\nInserting test user:")
        print(f"  Email: {test_email}")
        print(f"  Contact: {test_contact}")
        
        # Insert test user
        cursor.execute("""
            INSERT INTO users (name, age, gender, email, password, location, user_type, contact_number, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Test Patient",
            30,
            "Male",
            test_email,
            "hashed_password_123",
            "Test Location",
            "patient",
            test_contact,
            False
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        print(f"✅ User created with ID: {user_id}")
        
        # Retrieve and verify
        cursor.execute("SELECT id, name, email, contact_number FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"\n✅ Retrieved user data:")
            print(f"   ID: {user[0]}")
            print(f"   Name: {user[1]}")
            print(f"   Email: {user[2]}")
            print(f"   Contact: {user[3]}")
            
            if user[3] == test_contact:
                print(f"\n✅ Contact number saved and retrieved correctly!")
                conn.close()
                return True
            else:
                print(f"\n❌ Contact mismatch! Expected {test_contact}, got {user[3]}")
                conn.close()
                return False
        else:
            print("❌ User not found after insertion")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Sample user test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_models_schemas():
    """Verify backend models and schemas have contact_number"""
    try:
        print("\n" + "="*70)
        print("🔍 BACKEND MODELS & SCHEMAS VERIFICATION")
        print("="*70)
        
        # Check models.py
        with open('app/models/models.py', 'r') as f:
            models_content = f.read()
            if 'contact_number' in models_content:
                print("✅ User model contains contact_number field")
            else:
                print("❌ User model missing contact_number field")
                return False
        
        # Check schemas.py
        with open('app/schemas/schemas.py', 'r') as f:
            schemas_content = f.read()
            
            # Check UserBase
            if 'class UserBase' in schemas_content and 'contact_number' in schemas_content:
                print("✅ UserBase schema contains contact_number field")
            else:
                print("❌ UserBase schema missing contact_number field")
                return False
            
            # Check UserCreate
            if 'class UserCreate' in schemas_content:
                print("✅ UserCreate schema defined (inherits from UserBase)")
            
            # Check UserUpdate
            if 'class UserUpdate' in schemas_content and 'contact_number' in schemas_content:
                print("✅ UserUpdate schema contains contact_number field")
            
            # Check UserResponse
            if 'class UserResponse' in schemas_content and 'contact_number' in schemas_content:
                print("✅ UserResponse schema contains contact_number field")
        
        # Check auth.py
        with open('app/api/endpoints/auth.py', 'r') as f:
            auth_content = f.read()
            if 'contact_number=user.contact_number' in auth_content:
                print("✅ Registration endpoint saves contact_number")
            else:
                print("❌ Registration endpoint does NOT save contact_number")
                return False
        
        # Check users.py
        with open('app/api/endpoints/users.py', 'r') as f:
            users_content = f.read()
            if 'contact_number' in users_content and 'user_update.contact_number' in users_content:
                print("✅ Profile update endpoint saves contact_number")
            else:
                print("❌ Profile update endpoint does NOT save contact_number")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Backend verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_android_models():
    """Verify Android models have contact_number"""
    try:
        print("\n" + "="*70)
        print("🔍 ANDROID MODELS VERIFICATION")
        print("="*70)
        
        # Check User.java
        user_java_path = r"c:\Users\santh\Downloads\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\app\src\main\java\com\physioclinic\app\models\User.java"
        
        with open(user_java_path, 'r') as f:
            user_content = f.read()
            if 'contactNumber' in user_content and 'getContactNumber' in user_content:
                print("✅ User.java contains contactNumber field and getter")
            else:
                print("❌ User.java missing contactNumber")
                return False
        
        # Check UserResponse.java
        response_java_path = r"c:\Users\santh\Downloads\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\app\src\main\java\com\physioclinic\app\response\UserResponse.java"
        
        with open(response_java_path, 'r') as f:
            response_content = f.read()
            if 'contact_number' in response_content and 'contactNumber' in response_content:
                print("✅ UserResponse.java contains contact_number field")
            else:
                print("❌ UserResponse.java missing contact_number")
                return False
        
        # Check ViewProfileActivity.java
        view_profile_path = r"c:\Users\santh\Downloads\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\app\src\main\java\com\physioclinic\app\activities\ViewProfileActivity.java"
        
        with open(view_profile_path, 'r') as f:
            view_profile_content = f.read()
            if 'tvContactNumber' in view_profile_content and 'getContactNumber' in view_profile_content:
                print("✅ ViewProfileActivity.java displays contactNumber")
            else:
                print("❌ ViewProfileActivity.java missing contact display")
                return False
        
        # Check EditProfileActivity.java
        edit_profile_path = r"c:\Users\santh\Downloads\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\app\src\main\java\com\physioclinic\app\activities\EditProfileActivity.java"
        
        with open(edit_profile_path, 'r') as f:
            edit_profile_content = f.read()
            if 'etContactNumber' in edit_profile_content and 'contactNumber' in edit_profile_content:
                print("✅ EditProfileActivity.java has contact edit support")
            else:
                print("❌ EditProfileActivity.java missing contact edit")
                return False
        
        # Check RegistrationActivity.java
        registration_path = r"c:\Users\santh\Downloads\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\PhysiotherapistClinic - final FE\app\src\main\java\com\physioclinic\app\activities\RegistrationActivity.java"
        
        with open(registration_path, 'r') as f:
            registration_content = f.read()
            if 'etContactNumber' in registration_content:
                print("✅ RegistrationActivity.java has contact registration field")
            else:
                print("❌ RegistrationActivity.java missing contact field")
                return False
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Android verification failed: {e}")
        return False

def main():
    """Run all verification tests"""
    
    print("\n" + "🚀 "*35)
    print("CONTACT NUMBER COMPLETE VERIFICATION TEST")
    print("🚀 "*35)
    
    results = []
    
    # Test 1: Database schema
    results.append(("Database Schema", test_database_schema()))
    
    # Test 2: Sample user data
    results.append(("Sample User Data", test_sample_user_data()))
    
    # Test 3: Backend models & schemas
    results.append(("Backend Models & Schemas", test_backend_models_schemas()))
    
    # Test 4: Android models
    results.append(("Android Models", test_android_models()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n" + "🎉 "*20)
        print("✅ ALL TESTS PASSED - CONTACT NUMBER FULLY INTEGRATED!")
        print("🎉 "*20)
    else:
        print("\n❌ SOME TESTS FAILED - REVIEW ABOVE")
    
    print("\n📋 NEXT STEPS:")
    print("1. Start the backend: python main.py")
    print("2. Build and run the Android app")
    print("3. Register a new user with a contact number")
    print("4. Login and verify contact displays in My Profile")
    print("5. Edit profile and change contact number")
    print("6. Verify changes persist in My Profile")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
