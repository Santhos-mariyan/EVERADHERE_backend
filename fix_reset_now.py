#!/usr/bin/env python3
"""
DIRECT FIX - Reset medications in database
and update the reset date to TODAY so medications reset
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Connect to database
db_file = 'physioclinic.db'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

print("="*80)
print("MEDICATION RESET - DIRECT DATABASE FIX")
print("="*80)

# STEP 1: Get current user info
print("\nSTEP 1: Get User Information")
cursor.execute('SELECT id, name, user_timezone, last_reset_date FROM users WHERE id = 1')
user = cursor.fetchone()

if not user:
    print("❌ User not found!")
    exit(1)

user_id = user[0]
user_name = user[1]
user_tz_str = user[2] or "UTC"
last_reset = user[3]

print(f"✅ User: {user_name} (ID: {user_id})")
print(f"✅ Timezone: {user_tz_str}")
print(f"✅ Last Reset Date: {last_reset}")

# STEP 2: Get current medications
print("\nSTEP 2: Get Current Medications")
cursor.execute('''
    SELECT id, medication_name, is_taken, taken_date 
    FROM medications 
    WHERE patient_id = ?
''', (user_id,))

medications = cursor.fetchall()
taken_count = sum(1 for m in medications if m[2])

print(f"✅ Total medications: {len(medications)}")
print(f"✅ Currently TAKEN: {taken_count}")

# STEP 3: Reset medications
print("\nSTEP 3: Reset All Medications")
print("Setting is_taken=0, taken_date=NULL for all medications...")

for med in medications:
    med_id = med[0]
    med_name = med[1]
    is_taken = med[2]
    
    if is_taken:
        cursor.execute('''
            UPDATE medications 
            SET is_taken = 0, taken_date = NULL
            WHERE id = ?
        ''', (med_id,))
        print(f"  ✅ Reset: {med_name}")

print(f"\n✅ Total reset: {taken_count} medications")

# STEP 4: Update last_reset_date to TODAY
print("\nSTEP 4: Update Last Reset Date")

# Reset should be set to TODAY in UTC (so it won't trigger reset again today)
today_utc = datetime.now(tz=ZoneInfo("UTC"))
today_utc_str = today_utc.isoformat()

print(f"Setting last_reset_date to: {today_utc_str}")

cursor.execute('''
    UPDATE users
    SET last_reset_date = ?
    WHERE id = ?
''', (today_utc_str, user_id))

print("✅ Updated!")

# STEP 5: Commit changes
print("\nSTEP 5: Commit Changes")
conn.commit()
print("✅ Changes saved to database!")

# STEP 6: Verify
print("\nSTEP 6: Verification")
cursor.execute('''
    SELECT id, medication_name, is_taken, taken_date 
    FROM medications 
    WHERE patient_id = ?
''', (user_id,))

medications_after = cursor.fetchall()
taken_count_after = sum(1 for m in medications_after if m[2])

print(f"✅ Medications marked as TAKEN: {taken_count_after}")
print(f"✅ Expected: 0 (all reset)")

if taken_count_after == 0:
    print("\n✅ SUCCESS - All medications reset to NOT TAKEN!")
else:
    print(f"\n⚠️  WARNING - {taken_count_after} medications still marked as TAKEN")

conn.close()

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("""
1. Open the EverAdhere app on your device
2. Go to Medications section
3. All medications should now show as NOT TAKEN ✅

4. Mark a medication as TAKEN
5. Close and reopen app (same day)
6. It should still show as TAKEN ✓

7. Change device date to TOMORROW at 12:01 AM
8. Open app
9. All medications should reset to NOT TAKEN again ✅
""")
