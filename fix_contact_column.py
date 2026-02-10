#!/usr/bin/env python3
"""
FIX: Recreate contact_number column with correct SQLite syntax
This removes the invalid CHAR(1) and creates a proper VARCHAR/TEXT column
"""

import sqlite3
import os

DB_PATH = 'physioclinic.db'

def fix_contact_number_column():
    """Fix the contact_number column by recreating the users table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("FIXING CONTACT_NUMBER COLUMN")
        print("="*70 + "\n")
        
        # Check current column type
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        contact_col = None
        for col in columns:
            if col[1] == 'contact_number':
                contact_col = col
                print(f"Current contact_number column type: {col[2]}")
                break
        
        if not contact_col:
            print("✗ contact_number column not found!")
            conn.close()
            return False
        
        # SQLite doesn't support direct ALTER TABLE column type changes
        # We must:
        # 1. Create backup table with renamed contact_number
        # 2. Drop original table
        # 3. Recreate with correct types
        # 4. Restore data
        
        print("\nStep 1: Renaming users table to users_backup...")
        cursor.execute("ALTER TABLE users RENAME TO users_backup")
        conn.commit()
        
        print("Step 2: Creating new users table with correct column types...")
        
        # Get list of columns from backup
        cursor.execute("PRAGMA table_info(users_backup)")
        backup_columns = cursor.fetchall()
        
        # Build CREATE TABLE statement with fixed contact_number
        create_columns = []
        for col in backup_columns:
            cid, name, col_type, notnull, dflt_value, pk = col
            
            if name == 'contact_number':
                # Fix the column definition - use TEXT which is nullable by default
                create_columns.append(f"  {name} TEXT")
                print(f"  - {name}: {col_type} → TEXT (nullable)")
            elif pk:
                create_columns.append(f"  {name} {col_type} PRIMARY KEY")
                print(f"  - {name}: {col_type} PRIMARY KEY")
            elif notnull:
                create_columns.append(f"  {name} {col_type} NOT NULL")
                print(f"  - {name}: {col_type} NOT NULL")
            else:
                create_columns.append(f"  {name} {col_type}")
                print(f"  - {name}: {col_type}")
        
        create_statement = f"CREATE TABLE users (\n" + ",\n".join(create_columns) + "\n)"
        
        print("\nStep 3: Creating new table...")
        cursor.execute(create_statement)
        conn.commit()
        
        # Get column names
        column_names = [col[1] for col in backup_columns]
        columns_str = ", ".join(column_names)
        
        print("Step 4: Copying data from backup...")
        cursor.execute(f"INSERT INTO users ({columns_str}) SELECT {columns_str} FROM users_backup")
        conn.commit()
        print(f"✓ Copied {cursor.rowcount} rows")
        
        print("Step 5: Dropping backup table...")
        cursor.execute("DROP TABLE users_backup")
        conn.commit()
        
        # Verify
        print("\nStep 6: Verifying new column...")
        cursor.execute("PRAGMA table_info(users)")
        for col in cursor.fetchall():
            if col[1] == 'contact_number':
                print(f"✓ contact_number is now type: {col[2]}")
        
        # Test with sample data
        print("\nStep 7: Testing with sample data...")
        cursor.execute("SELECT id, contact_number FROM users LIMIT 3")
        for row in cursor.fetchall():
            print(f"  User {row[0]}: contact = {repr(row[1])}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✓ FIX COMPLETE - contact_number column is now properly configured")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_contact_number_column()
    if not success:
        print("\n⚠️  Fix failed! Check error messages above.")
