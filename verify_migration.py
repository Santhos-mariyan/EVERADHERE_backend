#!/usr/bin/env python3
"""
Test script to verify the migration fixed the issue.

Run this after migration to ensure medications endpoint works.
"""

import sqlite3
from pathlib import Path

def verify_migration():
    """Verify that the taken_date column was added successfully."""
    
    db_path = Path(__file__).parent / "physioclinic.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("🔍 Verifying database migration...\n")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all columns in medications table
        cursor.execute("PRAGMA table_info(medications)")
        columns = cursor.fetchall()
        
        print("📋 Medications Table Columns:")
        print("─" * 50)
        
        column_names = []
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, primary_key = col
            nullable = "✅" if not not_null else "❌"
            column_names.append(col_name)
            print(f"  {col_name:20} | {col_type:10} | Nullable: {nullable}")
        
        print("─" * 50)
        
        # Check if critical columns exist
        print("\n✅ Required Columns Check:")
        required = ['id', 'patient_id', 'doctor_id', 'medication_name', 'dosage', 
                   'frequency', 'duration', 'instructions', 'is_taken', 
                   'prescribed_date', 'taken_date']
        
        all_present = True
        for col in required:
            if col in column_names:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} MISSING")
                all_present = False
        
        if not all_present:
            print("\n❌ Migration incomplete!")
            conn.close()
            return False
        
        # Test a sample query
        print("\n🧪 Testing SQL Query...")
        try:
            cursor.execute("""
                SELECT id, medication_name, is_taken, taken_date, prescribed_date
                FROM medications
                LIMIT 1
            """)
            result = cursor.fetchone()
            print("  ✅ Query executed successfully")
            if result:
                print(f"     Sample: {result}")
        except Exception as e:
            print(f"  ❌ Query failed: {e}")
            conn.close()
            return False
        
        # Count medications
        cursor.execute("SELECT COUNT(*) FROM medications")
        count = cursor.fetchone()[0]
        print(f"\n📊 Medications Count: {count}")
        
        conn.close()
        
        print("\n✅ MIGRATION VERIFICATION SUCCESSFUL!")
        print("   Database schema matches code requirements")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE MIGRATION VERIFICATION")
    print("=" * 50 + "\n")
    
    success = verify_migration()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ STATUS: READY TO USE")
        print("=" * 50)
        exit(0)
    else:
        print("❌ STATUS: VERIFICATION FAILED")
        print("=" * 50)
        exit(1)
