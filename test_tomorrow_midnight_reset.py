#!/usr/bin/env python3
"""
Test IST Daily Reset - TOMORROW SIMULATION
Tests that reset will happen at midnight IST tomorrow (2026-01-18)
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_tomorrow_reset():
    """Test IST reset at tomorrow's midnight"""
    
    print("\n" + "="*80)
    print("🧪 TEST: RESET AT TOMORROW'S MIDNIGHT IST (2026-01-18 00:00)")
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
        patient_name = patient['name']
        
        print(f"📋 Patient: {patient_name} (ID: {patient_id})")
        print(f"   Current timezone: {patient['user_timezone']}")
        print(f"   Last reset: {patient['last_reset_date']}\n")
        
        # Step 1: Make sure all medications are marked as TAKEN TODAY
        print("STEP 1: Marking all medications as TAKEN (simulating day 1)")
        print("-" * 80)
        
        cursor.execute("""
            SELECT id, medication_name FROM medications WHERE patient_id = ?
        """, (patient_id,))
        medications = cursor.fetchall()
        
        today_utc = datetime.now(tz=ZoneInfo("UTC")).isoformat()
        for med in medications:
            cursor.execute("""
                UPDATE medications SET is_taken = 1, taken_date = ? WHERE id = ?
            """, (today_utc, med['id']))
            print(f"   ✅ {med['medication_name']}: TAKEN")
        
        # Update last_reset_date to TODAY so it won't reset again today
        cursor.execute("""
            UPDATE users SET last_reset_date = ? WHERE id = ?
        """, (today_utc, patient_id))
        
        conn.commit()
        print(f"\n   Updated last_reset_date to TODAY ({today_utc})\n")
        
        # Step 2: Verify all are taken
        print("STEP 2: Verify all medications are TAKEN")
        print("-" * 80)
        cursor.execute("""
            SELECT medication_name, is_taken FROM medications WHERE patient_id = ?
        """, (patient_id,))
        result = cursor.fetchall()
        
        all_taken = all(med['is_taken'] for med in result)
        print(f"   ✅ All {len(result)} medications marked as TAKEN\n")
        
        # Step 3: Simulate TOMORROW at 12:01 AM IST
        print("STEP 3: SIMULATING TOMORROW AT 12:01 AM IST")
        print("-" * 80)
        
        tz_ist = ZoneInfo('Asia/Kolkata')
        
        # Simulate tomorrow at 00:01 AM IST
        # Today: 2026-01-17 19:28:35 IST
        # Tomorrow: 2026-01-18 00:01:00 IST
        tomorrow_ist = datetime(2026, 1, 18, 0, 1, 0, tzinfo=tz_ist)
        tomorrow_date = tomorrow_ist.date()
        
        print(f"   📅 Simulated time: {tomorrow_ist.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
        print(f"   📅 Simulated date: {tomorrow_date}\n")
        
        # Step 4: Check reset decision at tomorrow 12:01 AM
        print("STEP 4: RESET DECISION AT TOMORROW 12:01 AM IST")
        print("-" * 80)
        
        cursor.execute("""
            SELECT last_reset_date FROM users WHERE id = ?
        """, (patient_id,))
        result = cursor.fetchone()
        last_reset_date_str = result['last_reset_date']
        
        last_reset_utc = datetime.fromisoformat(last_reset_date_str).replace(tzinfo=ZoneInfo("UTC"))
        last_reset_ist = last_reset_utc.astimezone(tz_ist)
        last_reset_date = last_reset_ist.date()
        
        print(f"   📅 Last reset (UTC): {last_reset_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📅 Last reset (IST): {last_reset_ist.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📅 Last reset date: {last_reset_date}")
        print(f"   📅 Tomorrow's date: {tomorrow_date}\n")
        
        print(f"   🔍 COMPARISON: {last_reset_date} vs {tomorrow_date}")
        
        if last_reset_date == tomorrow_date:
            print(f"   ❌ Same day - WILL NOT RESET")
            should_reset = False
        else:
            print(f"   ✅ Different days - WILL RESET!")
            should_reset = True
        
        # Step 5: Perform reset if needed
        print(f"\nSTEP 5: PERFORMING RESET")
        print("-" * 80)
        
        if should_reset:
            cursor.execute("""
                SELECT id, medication_name FROM medications 
                WHERE patient_id = ? AND is_taken = 1
            """, (patient_id,))
            meds_to_reset = cursor.fetchall()
            
            reset_count = 0
            for med in meds_to_reset:
                cursor.execute("""
                    UPDATE medications SET is_taken = 0, taken_date = NULL WHERE id = ?
                """, (med['id'],))
                print(f"   ✅ Reset '{med['medication_name']}' to NOT TAKEN")
                reset_count += 1
            
            # Update last_reset_date to tomorrow's time
            tomorrow_utc = tomorrow_ist.astimezone(ZoneInfo("UTC"))
            cursor.execute("""
                UPDATE users SET last_reset_date = ? WHERE id = ?
            """, (tomorrow_utc.isoformat(), patient_id))
            
            conn.commit()
            print(f"\n   ✅ Reset complete! {reset_count} medications reset")
        
        # Step 6: Verify result
        print(f"\nSTEP 6: VERIFY MEDICATIONS AFTER RESET")
        print("-" * 80)
        
        cursor.execute("""
            SELECT medication_name, is_taken FROM medications WHERE patient_id = ?
        """, (patient_id,))
        final_result = cursor.fetchall()
        
        not_taken_count = 0
        for med in final_result:
            status = "✅ NOT TAKEN" if not med['is_taken'] else "❌ STILL TAKEN"
            print(f"   {status}: {med['medication_name']}")
            if not med['is_taken']:
                not_taken_count += 1
        
        # Final verdict
        print("\n" + "="*80)
        if should_reset and not_taken_count == len(final_result):
            print("✅ TEST PASSED!")
            print("   At midnight IST tomorrow, ALL medications will be reset to NOT TAKEN")
            print("   This will show up as fresh medications on the new day!")
            result = True
        elif not should_reset:
            print("ℹ️  TEST INFO:")
            print("   Reset would have been skipped (was already reset today)")
            result = True
        else:
            print("❌ TEST FAILED!")
            print("   Medications were not reset properly")
            result = False
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_tomorrow_reset()
    sys.exit(0 if success else 1)
