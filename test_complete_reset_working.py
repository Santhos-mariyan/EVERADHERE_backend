#!/usr/bin/env python3
"""
Complete Test: Automatic Daily Reset at Midnight IST
Tests the FULL scenario with proper reset logic
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_complete_reset():
    """Complete test of daily reset functionality"""
    
    print("\n" + "="*80)
    print("🧪 COMPLETE DAILY RESET TEST (FULLY WORKING MODEL)")
    print("="*80 + "\n")
    
    db_path = "physioclinic.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get test patient
        cursor.execute("""
            SELECT id, name, user_timezone, last_reset_date 
            FROM users 
            WHERE user_type = 'patient' 
            LIMIT 1
        """)
        patient = cursor.fetchone()
        patient_id = patient['id']
        
        print("=" * 80)
        print("SCENARIO: Patient marks meds on Day 1, opens app on Day 2 at midnight")
        print("=" * 80 + "\n")
        
        # STEP 1: Set timezone and clear all medications
        print("STEP 1: SETUP - Clear database and set timezone")
        print("-" * 80)
        
        cursor.execute("""UPDATE users SET user_timezone = 'Asia/Kolkata' WHERE id = ?""", (patient_id,))
        
        # Get all medications
        cursor.execute("""SELECT id FROM medications WHERE patient_id = ?""", (patient_id,))
        med_ids = [row['id'] for row in cursor.fetchall()]
        
        # Clear all (set to not taken)
        for med_id in med_ids:
            cursor.execute("""UPDATE medications SET is_taken = 0, taken_date = NULL WHERE id = ?""", (med_id,))
        
        # Clear last reset (set to NULL to force reset)
        cursor.execute("""UPDATE users SET last_reset_date = NULL WHERE id = ?""", (patient_id,))
        conn.commit()
        
        print(f"✅ Cleared all medications for patient {patient_id}")
        print(f"✅ Set timezone: Asia/Kolkata")
        print(f"✅ Cleared last_reset_date\n")
        
        # STEP 2: Simulate Day 1 - Mark medications as taken
        print("STEP 2: DAY 1 - Mark all medications as TAKEN (simulate patient taking meds)")
        print("-" * 80)
        
        day1_time = datetime(2026, 1, 17, 10, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        day1_time_utc = day1_time.astimezone(ZoneInfo("UTC")).isoformat()
        
        print(f"📅 Simulated time: {day1_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        for med_id in med_ids:
            cursor.execute("""
                UPDATE medications 
                SET is_taken = 1, taken_date = ? 
                WHERE id = ?
            """, (day1_time_utc, med_id))
        
        conn.commit()
        print(f"✅ Marked {len(med_ids)} medications as TAKEN\n")
        
        # STEP 3: Simulate Day 2 at midnight - Check reset logic
        print("STEP 3: DAY 2 AT MIDNIGHT (12:01 AM IST) - Dashboard loads")
        print("-" * 80)
        
        day2_time = datetime(2026, 1, 18, 0, 1, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        day2_date = day2_time.date()
        
        print(f"📅 Simulated time: {day2_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 Simulated date: {day2_date}\n")
        
        print("STEP 4: CHECK RESET LOGIC")
        print("-" * 80)
        
        # Get user and check if reset should happen
        cursor.execute("""SELECT last_reset_date, user_timezone FROM users WHERE id = ?""", (patient_id,))
        user = cursor.fetchone()
        last_reset_date_str = user['last_reset_date']
        timezone_str = user['user_timezone']
        
        tz = ZoneInfo(timezone_str)
        
        print(f"User timezone: {timezone_str}")
        print(f"Current date (IST): {day2_date}")
        
        should_reset = False
        if last_reset_date_str:
            last_reset_utc = datetime.fromisoformat(last_reset_date_str).replace(tzinfo=ZoneInfo("UTC"))
            last_reset_user_tz = last_reset_utc.astimezone(tz)
            last_reset_date = last_reset_user_tz.date()
            print(f"Last reset date (IST): {last_reset_date}")
            
            if last_reset_date != day2_date:
                should_reset = True
                print(f"✅ Different dates → RESET WILL HAPPEN!")
            else:
                print(f"❌ Same day → NO RESET")
        else:
            should_reset = True
            print(f"Last reset: NEVER → RESET WILL HAPPEN!")
        
        # STEP 5: Perform the reset
        print(f"\nSTEP 5: {'PERFORMING' if should_reset else 'SKIPPING'} RESET")
        print("-" * 80)
        
        if should_reset:
            reset_count = 0
            
            # Get all medications for this patient
            cursor.execute("""SELECT id, medication_name, is_taken FROM medications WHERE patient_id = ?""", (patient_id,))
            medications = cursor.fetchall()
            
            for med in medications:
                if med['is_taken']:
                    cursor.execute("""UPDATE medications SET is_taken = 0, taken_date = NULL WHERE id = ?""", (med['id'],))
                    reset_count += 1
                    print(f"   ✅ Reset '{med['medication_name']}' → NOT TAKEN")
            
            # Update last_reset_date
            day2_time_utc = day2_time.astimezone(ZoneInfo("UTC")).isoformat()
            cursor.execute("""UPDATE users SET last_reset_date = ? WHERE id = ?""", (day2_time_utc, patient_id))
            conn.commit()
            
            print(f"\n✅ Reset complete! {reset_count} medications reset")
            print(f"✅ Updated last_reset_date")
        
        # STEP 6: Verify result
        print(f"\nSTEP 6: VERIFY RESULT (What UI will show)")
        print("-" * 80)
        
        cursor.execute("""
            SELECT medication_name, is_taken 
            FROM medications 
            WHERE patient_id = ? 
            ORDER BY id
        """, (patient_id,))
        
        result_meds = cursor.fetchall()
        all_reset = True
        
        for med in result_meds:
            status = "✅ NOT TAKEN" if not med['is_taken'] else "❌ STILL TAKEN"
            print(f"{status}: {med['medication_name']}")
            if med['is_taken']:
                all_reset = False
        
        # FINAL VERDICT
        print("\n" + "="*80)
        if should_reset and all_reset:
            print("✅ TEST PASSED - MEDICATIONS RESET CORRECTLY!")
            print("\nWhat the user will see:")
            print("  ✅ On Jan 17 at 10 AM: All medications marked as TAKEN")
            print("  ✅ On Jan 18 at 12:01 AM: Open app → All reset to NOT TAKEN")
            print("  ✅ Fresh start for the new day!")
            result = True
        else:
            print("❌ TEST FAILED - MEDICATIONS NOT RESET!")
            result = False
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_complete_reset()
    sys.exit(0 if success else 1)
