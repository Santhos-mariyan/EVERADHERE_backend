"""
Simple IST timezone migration using direct SQLite operations
"""

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

def migrate_to_ist():
    """Convert all naive UTC datetimes to IST timezone"""
    
    db_path = "physioclinic.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*80)
        print("🔄 MIGRATING ALL DATETIME FIELDS TO IST TIMEZONE")
        print("="*80)
        
        ist = ZoneInfo("Asia/Kolkata")
        utc = ZoneInfo("UTC")
        
        # 1. Update Users table
        print("\n📋 Processing users table...")
        cursor.execute("SELECT id, name, created_at, last_reset_date, user_timezone FROM users")
        users = cursor.fetchall()
        
        for user in users:
            user_id = user['id']
            name = user['name']
            
            # Update user_timezone if not set
            if not user['user_timezone'] or user['user_timezone'] == 'UTC':
                cursor.execute("UPDATE users SET user_timezone = ? WHERE id = ?", 
                             ("Asia/Kolkata", user_id))
                print(f"  ✅ Updated timezone for {name} to Asia/Kolkata")
            
            # Update created_at
            if user['created_at']:
                try:
                    # Parse datetime and convert to IST
                    dt = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')) if 'T' in user['created_at'] else datetime.fromisoformat(user['created_at'])
                    if dt.tzinfo is None:
                        # Assume UTC if naive
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE users SET created_at = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), user_id))
                except Exception as e:
                    print(f"  ⚠️  Skipped created_at for {name}: {str(e)}")
            
            # Update last_reset_date
            if user['last_reset_date']:
                try:
                    dt = datetime.fromisoformat(user['last_reset_date'].replace('Z', '+00:00')) if 'T' in user['last_reset_date'] else datetime.fromisoformat(user['last_reset_date'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE users SET last_reset_date = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), user_id))
                except Exception as e:
                    print(f"  ⚠️  Skipped last_reset_date for {name}: {str(e)}")
        
        conn.commit()
        print(f"  ✅ {len(users)} users processed")
        
        # 2. Update Medications table
        print("\n💊 Processing medications table...")
        cursor.execute("SELECT id, medication_name, prescribed_date, taken_date FROM medications")
        meds = cursor.fetchall()
        
        for med in meds:
            med_id = med['id']
            name = med['medication_name']
            
            # Update prescribed_date
            if med['prescribed_date']:
                try:
                    dt = datetime.fromisoformat(med['prescribed_date'].replace('Z', '+00:00')) if 'T' in med['prescribed_date'] else datetime.fromisoformat(med['prescribed_date'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE medications SET prescribed_date = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), med_id))
                except Exception as e:
                    pass
            
            # Update taken_date
            if med['taken_date']:
                try:
                    dt = datetime.fromisoformat(med['taken_date'].replace('Z', '+00:00')) if 'T' in med['taken_date'] else datetime.fromisoformat(med['taken_date'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE medications SET taken_date = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), med_id))
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"  ✅ {len(meds)} medications processed")
        
        # 3. Update TestResults table
        print("\n🩺 Processing test_results table...")
        cursor.execute("SELECT id, date FROM test_results")
        results = cursor.fetchall()
        
        for result in results:
            if result['date']:
                try:
                    dt = datetime.fromisoformat(result['date'].replace('Z', '+00:00')) if 'T' in result['date'] else datetime.fromisoformat(result['date'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE test_results SET date = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), result['id']))
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"  ✅ {len(results)} test results processed")
        
        # 4. Update Videos table
        print("\n🎥 Processing videos table...")
        cursor.execute("SELECT id, upload_date FROM videos")
        videos = cursor.fetchall()
        
        for video in videos:
            if video['upload_date']:
                try:
                    dt = datetime.fromisoformat(video['upload_date'].replace('Z', '+00:00')) if 'T' in video['upload_date'] else datetime.fromisoformat(video['upload_date'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE videos SET upload_date = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), video['id']))
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"  ✅ {len(videos)} videos processed")
        
        # 5. Update Notifications table
        print("\n🔔 Processing notifications table...")
        cursor.execute("SELECT id, date FROM notifications")
        notifs = cursor.fetchall()
        
        for notif in notifs:
            if notif['date']:
                try:
                    dt = datetime.fromisoformat(notif['date'].replace('Z', '+00:00')) if 'T' in notif['date'] else datetime.fromisoformat(notif['date'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE notifications SET date = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), notif['id']))
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"  ✅ {len(notifs)} notifications processed")
        
        # 6. Update Reminders table
        print("\n⏰ Processing reminders table...")
        cursor.execute("SELECT id, created_at FROM reminders")
        reminders = cursor.fetchall()
        
        for reminder in reminders:
            if reminder['created_at']:
                try:
                    dt = datetime.fromisoformat(reminder['created_at'].replace('Z', '+00:00')) if 'T' in reminder['created_at'] else datetime.fromisoformat(reminder['created_at'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE reminders SET created_at = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), reminder['id']))
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"  ✅ {len(reminders)} reminders processed")
        
        # 7. Update VerificationCodes table
        print("\n✔️  Processing verification_codes table...")
        cursor.execute("SELECT id, email, created_at, expires_at FROM verification_codes")
        codes = cursor.fetchall()
        
        for code in codes:
            # Update created_at
            if code['created_at']:
                try:
                    dt = datetime.fromisoformat(code['created_at'].replace('Z', '+00:00')) if 'T' in code['created_at'] else datetime.fromisoformat(code['created_at'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE verification_codes SET created_at = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), code['id']))
                except Exception as e:
                    pass
            
            # Update expires_at
            if code['expires_at']:
                try:
                    dt = datetime.fromisoformat(code['expires_at'].replace('Z', '+00:00')) if 'T' in code['expires_at'] else datetime.fromisoformat(code['expires_at'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=utc)
                    ist_dt = dt.astimezone(ist)
                    cursor.execute("UPDATE verification_codes SET expires_at = ? WHERE id = ?", 
                                 (ist_dt.isoformat(), code['id']))
                except Exception as e:
                    pass
        
        conn.commit()
        print(f"  ✅ {len(codes)} verification codes processed")
        
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETE!")
        print("="*80)
        print(f"\n📊 Summary:")
        print(f"  • Users: {len(users)} processed")
        print(f"  • Medications: {len(meds)} processed")
        print(f"  • Test Results: {len(results)} processed")
        print(f"  • Videos: {len(videos)} processed")
        print(f"  • Notifications: {len(notifs)} processed")
        print(f"  • Reminders: {len(reminders)} processed")
        print(f"  • Verification Codes: {len(codes)} processed")
        print("\n✅ All datetime fields are now in IST timezone!\n")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_to_ist()
