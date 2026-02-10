#!/usr/bin/env python3
"""
COMPREHENSIVE CONTACT_NUMBER DIAGNOSTIC
Tests database, backend code, and Android requests
"""

import sqlite3
import json

def main():
    db_path = 'physioclinic.db'
    
    print("\n" + "="*80)
    print("COMPREHENSIVE CONTACT_NUMBER DIAGNOSTIC")
    print("="*80 + "\n")
    
    # ======== DATABASE CHECK ========
    print("[1] DATABASE SCHEMA CHECK")
    print("-" * 80)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        if 'contact_number' in columns:
            col_type = columns['contact_number']
            print(f"✓ contact_number column EXISTS")
            print(f"  Column Type: {col_type}")
            print(f"  Expected Type: TEXT or VARCHAR")
            if col_type in ['TEXT', 'VARCHAR', 'VARCHAR(255)', 'CHAR(1)']:
                print(f"  Status: Type is {col_type}")
                if col_type == 'CHAR(1)':
                    print(f"  ⚠️  WARNING: Column is CHAR(1) - This would truncate to 1 char!")
        else:
            print(f"✗ contact_number column NOT FOUND")
            print(f"  Available columns: {list(columns.keys())}")
        
        conn.close()
    except Exception as e:
        print(f"✗ Database error: {e}")
    
    # ======== DATA CHECK ========
    print("\n[2] ACTUAL DATA IN DATABASE")
    print("-" * 80)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, email, contact_number FROM users LIMIT 10")
        rows = cursor.fetchall()
        
        if not rows:
            print("No users in database")
        else:
            for i, row in enumerate(rows, 1):
                user_id, name, email, contact = row
                print(f"\nUser {i}:")
                print(f"  ID: {user_id}, Name: {name}")
                print(f"  Email: {email}")
                print(f"  Contact (raw): {repr(contact)}")
                print(f"  Contact (type): {type(contact).__name__}")
                if contact:
                    print(f"  Contact (len): {len(str(contact))}")
                    print(f"  Contact (chars): {list(str(contact))}")
                    # Check for common issues
                    if str(contact) == "N":
                        print(f"  ⚠️  WARNING: Contact is only 'N' (first char of 'None'?)")
                    if str(contact) == "None":
                        print(f"  ⚠️  WARNING: Contact is string 'None' not actual value")
        
        conn.close()
    except Exception as e:
        print(f"✗ Data check error: {e}")
    
    # ======== CODE ANALYSIS ========
    print("\n[3] BACKEND CODE ANALYSIS")
    print("-" * 80)
    
    try:
        with open('app/api/endpoints/auth.py', 'r') as f:
            auth_code = f.read()
        
        if 'contact_number' in auth_code:
            print("✓ auth.py contains contact_number handling")
            if 'contact == "None"' in auth_code:
                print("✓ auth.py has 'None' string conversion")
            if 'contact_number=contact' in auth_code:
                print("✓ auth.py saves contact_number to user")
        else:
            print("✗ auth.py does NOT handle contact_number")
    except Exception as e:
        print(f"✗ Code analysis error: {e}")
    
    # ======== RECOMMENDATIONS ========
    print("\n[4] TROUBLESHOOTING RECOMMENDATIONS")
    print("-" * 80)
    
    recommendations = [
        ("Check column type", "If CHAR(1), column is truncated - need to fix"),
        ("Check input validation", "Verify Android sends phone number correctly"),
        ("Check JSON serialization", "Ensure Gson serializes contactNumber as contact_number"),
        ("Check Pydantic validation", "Ensure contact_number field accepts values"),
        ("Test direct API call", "Use test_registration.py to test backend directly"),
        ("Check database transaction", "Verify commit() saves value correctly"),
    ]
    
    for i, (issue, action) in enumerate(recommendations, 1):
        print(f"{i}. {issue}")
        print(f"   Action: {action}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
