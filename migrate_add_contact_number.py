#!/usr/bin/env python3
"""
Migration script to add contact_number field to users table
Run this script after updating models.py and schemas.py
"""

import sqlite3
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'physioclinic.db')

def get_ist_now():
    """Returns current time in IST timezone"""
    return datetime.now(tz=ZoneInfo("Asia/Kolkata")).isoformat()

def migrate_add_contact_number():
    """Add contact_number column to users table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Starting migration: Adding contact_number field to users table...")
        
        # Check if contact_number column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'contact_number' in columns:
            print("✓ contact_number column already exists in users table")
            conn.close()
            return True
        
        # Add contact_number column
        # Note: SQLite uses TEXT for strings, NULL is the default for nullable columns
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN contact_number TEXT
        """)
        
        conn.commit()
        print("✓ Added contact_number column to users table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'contact_number' in columns:
            print("✓ Migration successful: contact_number column is now available")
            print(f"\nMigration completed at {get_ist_now()}")
            conn.close()
            return True
        else:
            print("✗ Migration failed: contact_number column not found after migration")
            conn.close()
            return False
            
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("✓ contact_number column already exists")
            return True
        else:
            print(f"✗ Database error: {e}")
            return False
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_add_contact_number()
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
