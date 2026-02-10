#!/usr/bin/env python3
"""
Check actual database column definition for contact_number
"""
import sqlite3
import os

db_path = 'physioclinic.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("DATABASE COLUMN ANALYSIS")
    print("="*70 + "\n")
    
    # Get table info
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print("All columns in users table:")
    print("-" * 70)
    for col in columns:
        cid, name, col_type, notnull, dflt_value, pk = col
        print(f"  ID: {cid}")
        print(f"  Name: {name}")
        print(f"  Type: {col_type}")
        print(f"  NotNull: {notnull}")
        print(f"  Default: {dflt_value}")
        print(f"  PK: {pk}")
        if name == "contact_number":
            print("  ^^^ THIS IS THE CONTACT_NUMBER COLUMN ^^^")
        print()
    
    # Check actual data
    print("="*70)
    print("Sample data from database:")
    print("="*70 + "\n")
    
    cursor.execute("SELECT id, name, email, contact_number FROM users LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        user_id, name, email, contact = row
        print(f"User: {name}")
        print(f"  Email: {email}")
        print(f"  Contact raw value: {repr(contact)}")
        print(f"  Contact type: {type(contact).__name__}")
        if contact:
            print(f"  Contact length: {len(str(contact))}")
            print(f"  Contact chars: {[c for c in str(contact)]}")
        print()
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
