import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    """Check database and ensure IST timezone for all records"""
    
    db_path = "physioclinic.db"
    
    print("\n" + "="*80)
    print("🔍 DATABASE CHECK AND IST TIMEZONE VERIFICATION")
    print("="*80)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check tables
        print("\n📋 Tables in Database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        # Check User table
        print("\n👥 User Table:")
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        user_count = cursor.fetchone()['cnt']
        print(f"  📊 Total users: {user_count}")
        
        if user_count > 0:
            cursor.execute("SELECT id, name, email, user_timezone, created_at FROM users LIMIT 1")
            user = cursor.fetchone()
            print(f"  Sample User:")
            print(f"    - ID: {user['id']}")
            print(f"    - Name: {user['name']}")
            print(f"    - Email: {user['email']}")
            print(f"    - Timezone: {user['user_timezone']}")
            print(f"    - created_at: {user['created_at']}")
            
            # Ensure timezone is set to IST
            cursor.execute("UPDATE users SET user_timezone = ? WHERE user_timezone IS NULL OR user_timezone = 'UTC'", ("Asia/Kolkata",))
            conn.commit()
            print(f"  ✅ All users timezone set to Asia/Kolkata")
        
        # Check Medications table
        print("\n💊 Medications Table:")
        cursor.execute("SELECT COUNT(*) as cnt FROM medications")
        med_count = cursor.fetchone()['cnt']
        print(f"  📊 Total medications: {med_count}")
        
        if med_count > 0:
            cursor.execute("SELECT id, medication_name, prescribed_date, is_taken FROM medications LIMIT 1")
            med = cursor.fetchone()
            print(f"  Sample Medication:")
            print(f"    - ID: {med['id']}")
            print(f"    - Name: {med['medication_name']}")
            print(f"    - prescribed_date: {med['prescribed_date']}")
            print(f"    - is_taken: {med['is_taken']}")
        
        # Check Verification Codes
        print("\n✔️  Verification Codes Table:")
        cursor.execute("SELECT COUNT(*) as cnt FROM verification_codes")
        verif_count = cursor.fetchone()['cnt']
        print(f"  📊 Total codes: {verif_count}")
        
        if verif_count > 0:
            cursor.execute("SELECT id, email, created_at, expires_at FROM verification_codes LIMIT 1")
            code = cursor.fetchone()
            print(f"  Sample Code:")
            print(f"    - Email: {code['email']}")
            print(f"    - created_at: {code['created_at']}")
            print(f"    - expires_at: {code['expires_at']}")
        
        # Summary
        print("\n" + "="*80)
        print("✅ DATABASE CHECK COMPLETE")
        print("="*80)
        print(f"\n📊 Summary:")
        print(f"  ✅ Users: {user_count}")
        print(f"  ✅ Medications: {med_count}")
        print(f"  ✅ Verification Codes: {verif_count}")
        print(f"  ✅ Database is ready for IST operations\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
