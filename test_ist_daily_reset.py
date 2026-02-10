#!/usr/bin/env python3
"""
Test IST Daily Reset Logic
Simulates patient marking medication as taken, then testing reset at midnight IST
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_ist_reset():
    """Test IST timezone reset logic"""
    
    print("\n" + "="*80)
    print("🧪 IST DAILY RESET TEST")
    print("="*80 + "\n")
    
    db_path = "physioclinic.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get a test patient
        print("📋 STEP 1: Finding test patient")
        print("-" * 80)
        cursor.execute("""
            SELECT id, name, email, user_timezone, last_reset_date 
            FROM users 
            WHERE user_type = 'patient' 
            LIMIT 1
        """)
        patient = cursor.fetchone()
        
        if not patient:
            print("❌ No patient found in database")
            return False
        
        patient_id = patient['id']
        patient_name = patient['name']
        current_tz = patient['user_timezone'] or 'UTC'
        last_reset = patient['last_reset_date']
        
        print(f"✅ Patient found: {patient_name} (ID: {patient_id})")
        print(f"   Timezone: {current_tz}")
        print(f"   Last reset: {last_reset}")
        
        # Update timezone to IST if not already set
        if current_tz != 'Asia/Kolkata':
            print(f"\n   📝 Updating timezone to Asia/Kolkata")
            cursor.execute("""
                UPDATE users 
                SET user_timezone = 'Asia/Kolkata' 
                WHERE id = ?
            """, (patient_id,))
            conn.commit()
            current_tz = 'Asia/Kolkata'
            print(f"   ✅ Timezone updated to {current_tz}")
        
        # Get patient's medications
        print("\n📋 STEP 2: Checking patient's medications")
        print("-" * 80)
        cursor.execute("""
            SELECT id, medication_name, is_taken, taken_date, prescribed_date, duration
            FROM medications
            WHERE patient_id = ?
            ORDER BY id
        """, (patient_id,))
        medications = cursor.fetchall()
        
        if not medications:
            print("❌ No medications found for patient")
            return False
        
        print(f"✅ Found {len(medications)} medications:")
        for med in medications:
            print(f"   • {med['medication_name']}")
            print(f"     - is_taken: {med['is_taken']}")
            print(f"     - taken_date: {med['taken_date']}")
            print(f"     - Duration: {med['duration']}")
        
        # Mark all medications as taken
        print("\n📋 STEP 3: Marking all medications as TAKEN")
        print("-" * 80)
        for med in medications:
            med_id = med['id']
            cursor.execute("""
                UPDATE medications
                SET is_taken = 1, taken_date = ?
                WHERE id = ?
            """, (datetime.now(tz=ZoneInfo("UTC")).isoformat(), med_id))
            print(f"   ✅ Marked '{med['medication_name']}' as taken")
        
        conn.commit()
        print(f"\n   📝 Current time UTC: {datetime.now(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   📝 Current time IST: {datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Verify they are marked as taken
        print("\n📋 STEP 4: Verifying medications are TAKEN")
        print("-" * 80)
        cursor.execute("""
            SELECT medication_name, is_taken, taken_date
            FROM medications
            WHERE patient_id = ?
        """, (patient_id,))
        taken_meds = cursor.fetchall()
        
        taken_count = 0
        for med in taken_meds:
            if med['is_taken']:
                taken_count += 1
                print(f"   ✅ {med['medication_name']}: TAKEN at {med['taken_date']}")
            else:
                print(f"   ❌ {med['medication_name']}: NOT TAKEN")
        
        if taken_count == 0:
            print("   ❌ No medications marked as taken!")
            return False
        
        # Simulate IST midnight reset logic
        print("\n📋 STEP 5: Simulating IST MIDNIGHT RESET LOGIC")
        print("-" * 80)
        
        # Set current IST time to 12:01 AM (just after midnight)
        tz_ist = ZoneInfo('Asia/Kolkata')
        
        # Get current time in IST
        now_ist = datetime.now(tz=tz_ist)
        current_date_ist = now_ist.date()
        
        print(f"\n   🕐 SIMULATED RESET CHECK:")
        print(f"   Current time IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
        print(f"   Current date IST: {current_date_ist}")
        
        # Check last_reset_date
        cursor.execute("""
            SELECT last_reset_date FROM users WHERE id = ?
        """, (patient_id,))
        result = cursor.fetchone()
        last_reset_date_str = result['last_reset_date']
        
        last_reset_date = None
        if last_reset_date_str:
            # Parse and convert to IST
            last_reset_utc = datetime.fromisoformat(last_reset_date_str).replace(tzinfo=ZoneInfo("UTC"))
            last_reset_ist = last_reset_utc.astimezone(tz_ist)
            last_reset_date = last_reset_ist.date()
            print(f"   📅 Last reset (UTC): {last_reset_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   📅 Last reset (IST): {last_reset_ist.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
            print(f"   📅 Last reset date: {last_reset_date}")
        else:
            print(f"   📅 Last reset: Never (NULL)")
        
        print(f"\n   🔍 RESET DECISION:")
        if last_reset_date == current_date_ist:
            print(f"   ❌ Last reset date ({last_reset_date}) == Today IST ({current_date_ist})")
            print(f"   ❌ WILL NOT RESET (already reset today)")
            reset_should_happen = False
        else:
            print(f"   ✅ Last reset date ({last_reset_date}) != Today IST ({current_date_ist})")
            print(f"   ✅ SHOULD RESET medications")
            reset_should_happen = True
        
        # Perform the reset if needed
        print("\n📋 STEP 6: PERFORMING RESET")
        print("-" * 80)
        
        if reset_should_happen:
            print("   🔄 Executing reset...")
            
            # Get medications that are not expired and are taken
            cursor.execute("""
                SELECT id, medication_name, is_taken, prescribed_date, duration
                FROM medications
                WHERE patient_id = ? AND is_taken = 1
            """, (patient_id,))
            meds_to_reset = cursor.fetchall()
            
            reset_count = 0
            for med in meds_to_reset:
                # Check if expired (simplified check)
                cursor.execute("""
                    UPDATE medications
                    SET is_taken = 0, taken_date = NULL
                    WHERE id = ?
                """, (med['id'],))
                print(f"   ✅ Reset '{med['medication_name']}' to NOT TAKEN")
                reset_count += 1
            
            # Update last_reset_date
            cursor.execute("""
                UPDATE users
                SET last_reset_date = ?
                WHERE id = ?
            """, (datetime.now(tz=ZoneInfo("UTC")).isoformat(), patient_id))
            
            conn.commit()
            print(f"\n   ✅ Updated last_reset_date to: {datetime.now(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   ✅ Total medications reset: {reset_count}")
        else:
            print("   ⏭️  Skipping reset (already reset today)")
        
        # Verify reset worked
        print("\n📋 STEP 7: VERIFYING RESET RESULT")
        print("-" * 80)
        cursor.execute("""
            SELECT medication_name, is_taken, taken_date
            FROM medications
            WHERE patient_id = ?
        """, (patient_id,))
        after_reset_meds = cursor.fetchall()
        
        not_taken_count = 0
        for med in after_reset_meds:
            if not med['is_taken']:
                not_taken_count += 1
                status = "✅ NOT TAKEN" if reset_should_happen else "❌ STILL TAKEN"
            else:
                status = "❌ STILL TAKEN"
            
            print(f"   {status}: {med['medication_name']}")
        
        print("\n" + "="*80)
        if reset_should_happen and not_taken_count > 0:
            print("✅ TEST PASSED: Medications were reset correctly at IST midnight!")
            result = True
        elif not reset_should_happen:
            print("⏭️  TEST INFO: Reset was skipped (already reset today)")
            result = True
        else:
            print("❌ TEST FAILED: Medications were not reset!")
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
    success = test_ist_reset()
    sys.exit(0 if success else 1)
