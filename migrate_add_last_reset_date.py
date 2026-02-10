#!/usr/bin/env python3
"""
Migration script to add last_reset_date column to users table
Run this to enable the new daily reset functionality
"""

import sqlite3
from datetime import datetime

DB_PATH = "physioclinic.db"  # Database location in same directory as this script

def migrate_add_last_reset_date():
    """Add last_reset_date column to users table"""
    
    print("\n" + "="*70)
    print("MIGRATION: Add last_reset_date column to users table")
    print("="*70)
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n📋 Checking if last_reset_date column exists...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "last_reset_date" in column_names:
            print("✅ Column already exists")
            conn.close()
            return True
        
        print("❌ Column does not exist, adding it...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN last_reset_date DATETIME DEFAULT NULL
        """)
        
        conn.commit()
        
        print("✅ Column added successfully")
        
        # Verify
        print("\n📋 Verifying column was added...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\nUsers table columns:")
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            print(f"  - {col_name}: {col_type}")
        
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Restart your backend server")
        print("2. Patients will now have reliable daily reset at midnight UTC")
        print("3. Check logs for 'Daily reset' messages")
        print("="*70 + "\n")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_add_last_reset_date()
    exit(0 if success else 1)
