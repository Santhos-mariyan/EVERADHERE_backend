#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add user_timezone column to users table
Enables timezone-aware daily reset (works in IST, EST, etc.)
"""

import sqlite3
import os
import sys

# Fix for Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "physioclinic.db")

print("\n" + "="*70)
print("MIGRATION: Add user_timezone column to users table")
print("="*70)
print(f"\nDatabase path: {db_path}")

try:
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        exit(1)
    
    print(f"✅ Database found")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📋 Checking if user_timezone column exists...")
    
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"\nCurrent users table columns: {len(columns)}")
    
    if "user_timezone" in column_names:
        print("✅ Column 'user_timezone' already exists")
        conn.close()
        exit(0)
    
    print("❌ Column 'user_timezone' does not exist")
    print("➕ Adding column with default 'UTC'...")
    
    cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN user_timezone VARCHAR DEFAULT 'UTC'
    """)
    
    conn.commit()
    
    print("✅ Column added successfully")
    
    # Verify
    print("\n📋 Verifying column was added...")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print(f"\nUpdated users table columns: {len(columns)}")
    column_names = [col[1] for col in columns]
    
    if "user_timezone" in column_names:
        print("✅ Column verified in database!")
    else:
        print("❌ Column NOT found after adding")
        conn.close()
        exit(1)
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nNEXT STEPS:")
    print("1. Restart your backend server")
    print("2. Update frontend to send user's timezone on login")
    print("3. Daily reset now works with IST, EST, PST, etc.")
    print("\nSUPPORTED TIMEZONES:")
    print("  • Asia/Kolkata (IST - Indian Standard Time)")
    print("  • America/New_York (EST)")
    print("  • America/Los_Angeles (PST)")
    print("  • Europe/London (GMT)")
    print("  • UTC (default)")
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
