#!/usr/bin/env python3
"""
Migration script to add data field to verification_codes table
Run this script after updating models.py
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'physioclinic.db')

def migrate_add_data_to_verification_codes():
    """Add data column to verification_codes table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Starting migration: Adding data field to verification_codes table...")
        
        # Check if data column already exists
        cursor.execute("PRAGMA table_info(verification_codes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'data' in columns:
            print("✓ data column already exists in verification_codes table")
            conn.close()
            return True
        
        # Add data column
        # Note: SQLite uses TEXT for strings, NULL is the default for nullable columns
        cursor.execute("""
            ALTER TABLE verification_codes 
            ADD COLUMN data TEXT
        """)
        
        conn.commit()
        print("✓ Added data column to verification_codes table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(verification_codes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'data' in columns:
            print("✓ Migration successful: data column added to verification_codes table")
            conn.close()
            return True
        else:
            print("✗ Migration failed: data column not found after migration")
            conn.close()
            return False
            
    except Exception as e:
        print(f"✗ Migration error: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Migration started at: {datetime.now().isoformat()}")
    success = migrate_add_data_to_verification_codes()
    print(f"Migration completed at: {datetime.now().isoformat()}")
    
    if success:
        print("🎉 Migration successful!")
    else:
        print("❌ Migration failed!")
        exit(1)