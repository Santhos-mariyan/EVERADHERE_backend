#!/usr/bin/env python3
"""
Diagnostic test for contact_number field in registration
"""

import sqlite3
import json

DB_PATH = 'physioclinic.db'

def test_database_insert():
    """Test direct database insert with contact_number"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("DATABASE DIRECT INSERT TEST")
        print("="*70)
        
        # Insert test user with contact
        test_email = "contact_test@test.com"
        test_contact = "+91-9876543210"
        
        cursor.execute("""
            INSERT INTO users (name, age, gender, email, password, location, user_type, contact_number, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Test User",
            30,
            "Male",
            test_email,
            "hashed_pwd",
            "Test City",
            "patient",
            test_contact,
            False
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve and verify
        cursor.execute("SELECT id, name, email, contact_number FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        print(f"\n✅ Inserted User:")
        print(f"   ID: {user[0]}")
        print(f"   Name: {user[1]}")
        print(f"   Email: {user[2]}")
        print(f"   Contact: {user[3]}")
        
        if user[3] == test_contact:
            print(f"\n✅ Contact stored correctly: {test_contact}")
        else:
            print(f"\n❌ Contact mismatch!")
            print(f"   Expected: {test_contact}")
            print(f"   Got: {user[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_schemas():
    """Test schema definitions"""
    try:
        print("\n" + "="*70)
        print("SCHEMA VERIFICATION")
        print("="*70)
        
        # Check schemas.py
        with open('app/schemas/schemas.py', 'r') as f:
            content = f.read()
            
            if 'class UserBase' in content:
                # Find UserBase section
                start = content.find('class UserBase')
                end = content.find('class UserCreate')
                userbase_section = content[start:end]
                
                if 'contact_number' in userbase_section:
                    print("✅ UserBase has contact_number")
                else:
                    print("❌ UserBase MISSING contact_number")
                    return False
            
            if 'class UserCreate' in content:
                print("✅ UserCreate defined")
            
            if 'class UserResponse' in content:
                start = content.find('class UserResponse')
                end = content.find('class UserLogin')
                response_section = content[start:end]
                
                if 'contact_number' in response_section:
                    print("✅ UserResponse has contact_number")
                else:
                    print("❌ UserResponse MISSING contact_number")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_null_contact():
    """Test with NULL contact_number"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("NULL CONTACT TEST")
        print("="*70)
        
        # Insert user without contact
        test_email = "no_contact@test.com"
        
        cursor.execute("""
            INSERT INTO users (name, age, gender, email, password, location, user_type, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "No Contact User",
            25,
            "Female",
            test_email,
            "hashed_pwd",
            "Test City",
            "doctor",
            False
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT contact_number FROM users WHERE id = ?", (user_id,))
        contact = cursor.fetchone()[0]
        
        print(f"\n✅ Inserted user without contact:")
        print(f"   Contact value: {contact}")
        print(f"   Type: {type(contact)}")
        
        if contact is None:
            print("✅ NULL handled correctly")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "🔍 "*35)
    print("CONTACT_NUMBER DIAGNOSTIC TEST")
    print("🔍 "*35)
    
    results = []
    results.append(("Schema Check", test_schemas()))
    results.append(("Database Insert with Contact", test_database_insert()))
    results.append(("Database Insert without Contact", test_null_contact()))
    
    print("\n" + "="*70)
    print("DIAGNOSTIC RESULTS")
    print("="*70)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "="*70)
    
    if all_passed:
        print("✅ All diagnostics passed!")
    else:
        print("❌ Some diagnostics failed!")
