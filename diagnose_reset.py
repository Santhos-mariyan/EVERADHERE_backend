"""
Diagnostic script to check medication reset logic
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def diagnose_reset_logic():
    """Diagnose why medications are not resetting"""
    
    db_path = "physioclinic.db"
    
    print("\n" + "="*90)
    print("🔍 MEDICATION RESET LOGIC DIAGNOSTIC")
    print("="*90)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        tz_ist = ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(tz=tz_ist)
        today_ist = now_ist.date()
        
        print(f"\n📊 Current IST Time: {now_ist}")
        print(f"📊 Current Date (IST): {today_ist}")
        
        # Check users and their last_reset_date
        print("\n👥 USER RESET DATES:")
        print("-" * 90)
        cursor.execute("SELECT id, name, user_timezone, last_reset_date FROM users")
        users = cursor.fetchall()
        
        for user in users:
            user_id = user['id']
            name = user['name']
            tz = user['user_timezone']
            last_reset = user['last_reset_date']
            
            print(f"\n  User: {name} (ID: {user_id})")
            print(f"    Timezone: {tz}")
            print(f"    last_reset_date: {last_reset}")
            
            if last_reset:
                try:
                    # Parse the stored datetime
                    stored_dt = datetime.fromisoformat(last_reset.replace('Z', '+00:00')) if 'T' in last_reset else datetime.fromisoformat(last_reset)
                    
                    # Convert to IST
                    if stored_dt.tzinfo is None:
                        stored_dt_utc = stored_dt.replace(tzinfo=ZoneInfo("UTC"))
                        stored_ist = stored_dt_utc.astimezone(tz_ist)
                    else:
                        stored_ist = stored_dt.astimezone(tz_ist)
                    
                    last_reset_date = stored_ist.date()
                    
                    print(f"    Last reset (IST): {stored_ist}")
                    print(f"    Last reset date: {last_reset_date}")
                    print(f"    Today's date: {today_ist}")
                    
                    if last_reset_date == today_ist:
                        print(f"    ℹ️  Same day - medications will NOT reset")
                    else:
                        print(f"    ✅ New day - medications SHOULD reset")
                except Exception as e:
                    print(f"    ❌ Error parsing date: {e}")
            else:
                print(f"    ✅ NULL - medications will reset on first call")
        
        # Check medications for each user
        print("\n\n💊 MEDICATION STATUS:")
        print("-" * 90)
        cursor.execute("SELECT id, patient_id, medication_name, is_taken, prescribed_date, taken_date FROM medications")
        meds = cursor.fetchall()
        
        for med in meds:
            print(f"\n  Medication: {med['medication_name']} (ID: {med['id']})")
            print(f"    Patient ID: {med['patient_id']}")
            print(f"    is_taken: {med['is_taken']}")
            print(f"    prescribed_date: {med['prescribed_date']}")
            print(f"    taken_date: {med['taken_date']}")
        
        # Check if there's any issue with the reset logic
        print("\n\n⚙️  RESET LOGIC ANALYSIS:")
        print("-" * 90)
        
        # For each user, check if reset SHOULD happen
        for user in users:
            user_id = user['id']
            name = user['name']
            last_reset = user['last_reset_date']
            
            should_reset = False
            reason = ""
            
            if not last_reset:
                should_reset = True
                reason = "First time (last_reset_date is NULL)"
            else:
                try:
                    stored_dt = datetime.fromisoformat(last_reset.replace('Z', '+00:00')) if 'T' in last_reset else datetime.fromisoformat(last_reset)
                    
                    if stored_dt.tzinfo is None:
                        stored_dt_utc = stored_dt.replace(tzinfo=ZoneInfo("UTC"))
                        stored_ist = stored_dt_utc.astimezone(tz_ist)
                    else:
                        stored_ist = stored_dt.astimezone(tz_ist)
                    
                    last_reset_date = stored_ist.date()
                    
                    if last_reset_date != today_ist:
                        should_reset = True
                        reason = f"New day (last: {last_reset_date}, today: {today_ist})"
                    else:
                        reason = f"Same day (no reset needed)"
                except Exception as e:
                    reason = f"Error: {e}"
            
            status = "✅ WILL RESET" if should_reset else "❌ WON'T RESET"
            print(f"\n  {name}: {status}")
            print(f"    Reason: {reason}")
        
        # Check database schema
        print("\n\n📋 DATABASE SCHEMA CHECK:")
        print("-" * 90)
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n  Users table columns:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            if col_name in ['last_reset_date', 'created_at', 'user_timezone']:
                print(f"    ✅ {col_name}: {col_type}")
        
        cursor.execute("PRAGMA table_info(medications)")
        columns = cursor.fetchall()
        print("\n  Medications table columns:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            if col_name in ['is_taken', 'prescribed_date', 'taken_date']:
                print(f"    ✅ {col_name}: {col_type}")
        
        print("\n\n📝 RECOMMENDATIONS:")
        print("-" * 90)
        
        # Check if medications marked taken have taken_date
        cursor.execute("SELECT COUNT(*) as cnt FROM medications WHERE is_taken = 1 AND taken_date IS NULL")
        count = cursor.fetchone()['cnt']
        
        if count > 0:
            print(f"  ⚠️  {count} medications marked TAKEN but have NULL taken_date")
            print(f"     → These might not reset properly")
        
        # Check if any user has never had a reset
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE last_reset_date IS NULL")
        count = cursor.fetchone()['cnt']
        
        if count > 0:
            print(f"  ℹ️  {count} users have never had medications reset")
            print(f"     → They WILL reset on next call to /my-medications")
        
        print("\n✅ Diagnostic Complete\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnose_reset_logic()
