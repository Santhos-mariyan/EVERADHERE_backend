#!/usr/bin/env python3
"""
Migration script to add taken_date column to medications table.

This script handles adding the missing taken_date column to the medications table
in the SQLite database.

Usage:
    python migrate_add_taken_date.py
"""

import sqlite3
import sys
from pathlib import Path

def add_taken_date_column():
    """Add taken_date column to medications table if it doesn't exist."""
    
    # Find the database file
    db_path = Path(__file__).parent / "physioclinic.db"
    
    if not db_path.exists():
        print(f"❌ Database file not found at: {db_path}")
        return False
    
    print(f"📦 Database found at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(medications)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'taken_date' in columns:
            print("✅ Column 'taken_date' already exists in medications table")
            conn.close()
            return True
        
        print("⏳ Adding 'taken_date' column to medications table...")
        
        # Add the taken_date column
        cursor.execute("""
            ALTER TABLE medications
            ADD COLUMN taken_date DATETIME NULL
        """)
        
        conn.commit()
        print("✅ Successfully added 'taken_date' column to medications table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(medications)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'taken_date' in columns:
            print("✅ Verification successful - 'taken_date' column is now present")
            conn.close()
            return True
        else:
            print("❌ Verification failed - 'taken_date' column not found after migration")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting migration to add taken_date column...\n")
    
    success = add_taken_date_column()
    
    print()
    if success:
        print("✅ Migration completed successfully!")
        print("You can now run your application normally.")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        print("Please check the errors above.")
        sys.exit(1)
