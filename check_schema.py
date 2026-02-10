#!/usr/bin/env python3
"""
Check database schema for contact_number column
"""

import sqlite3

DB_PATH = 'physioclinic.db'

def check_schema():
    """Check the exact column definition"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("DATABASE SCHEMA CHECK")
        print("="*70)
        
        # Get full table schema
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\nAll columns in users table:")
        for col in columns:
            col_id, name, type_val, not_null, default, pk = col
            print(f"  {name:20} | Type: {type_val:15} | NOT NULL: {not_null} | Default: {default}")
        
        # Check contact_number specifically
        print("\n" + "-"*70)
        print("CONTACT_NUMBER column details:")
        for col in columns:
            if col[1] == 'contact_number':
                col_id, name, type_val, not_null, default, pk = col
                print(f"  Name: {name}")
                print(f"  Type: {type_val}")
                print(f"  NOT NULL: {not_null}")
                print(f"  Default: {default}")
                print(f"  Primary Key: {pk}")
                
                # Check if it's CHAR or VARCHAR
                if 'CHAR(1)' in type_val.upper():
                    print("\n  ❌ PROBLEM: Column is CHAR(1) - stores only 1 character!")
                    print("     This explains why only 'N' is saved!")
                    return False
                elif 'VARCHAR' in type_val.upper():
                    print(f"\n  ✅ Column type is {type_val}")
                else:
                    print(f"\n  Column type: {type_val}")
        
        # Check actual data
        print("\n" + "-"*70)
        print("SAMPLE DATA:")
        cursor.execute("SELECT id, name, contact_number FROM users LIMIT 5")
        rows = cursor.fetchall()
        
        for row in rows:
            user_id, name, contact = row
            print(f"  ID: {user_id}, Name: {name}, Contact: '{contact}'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_schema()
