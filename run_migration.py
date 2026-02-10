#!/usr/bin/env python3
"""
Direct database migration without external dependencies
Adds last_reset_date column to users table
"""

import sqlite3
import os
from datetime import datetime

# Get the database path (should be in same directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "physioclinic.db")

print("\n" + "="*70)
print("MIGRATION: Add last_reset_date column to users table")
print("="*70)
print(f"\nDatabase path: {db_path}")

try:
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        exit(1)
    
    print(f"✅ Database found")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📋 Checking if last_reset_date column exists...")
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"\nCurrent users table columns: {len(columns)}")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    if "last_reset_date" in column_names:
        print("\n✅ Column 'last_reset_date' already exists")
        conn.close()
        exit(0)
    
    print("\n❌ Column 'last_reset_date' does not exist")
    print("➕ Adding column...")
    
    # Add the column
    cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN last_reset_date DATETIME DEFAULT NULL
    """)
    
    conn.commit()
    
    print("✅ Column added successfully to database")
    
    # Verify
    print("\n📋 Verifying column was added...")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print(f"\nUpdated users table columns: {len(columns)}")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check if our column is there
    column_names = [col[1] for col in columns]
    if "last_reset_date" in column_names:
        print("\n✅ Column verified in database!")
    else:
        print("\n❌ Column NOT found after adding")
        conn.close()
        exit(1)
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nNEXT STEPS:")
    print("1. Restart your backend server")
    print("2. Daily reset will now work reliably")
    print("3. Check logs for 'Daily reset' messages")
    print("="*70 + "\n")
    
    exit(0)
    
except sqlite3.Error as e:
    print(f"\n❌ Database error: {str(e)}")
    exit(1)
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
