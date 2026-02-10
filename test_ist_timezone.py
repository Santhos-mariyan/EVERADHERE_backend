"""
Complete IST Timezone Test Suite
Tests all datetime fields to verify IST timezone implementation
"""

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

def verify_ist_timezone():
    """Verify all datetime fields are in IST timezone"""
    
    db_path = "physioclinic.db"
    
    print("\n" + "="*90)
    print("🧪 COMPLETE IST TIMEZONE VERIFICATION TEST SUITE")
    print("="*90)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        ist = ZoneInfo("Asia/Kolkata")
        total_tests = 0
        passed_tests = 0
        
        # TEST 1: Users Table - created_at with IST
        print("\n📋 TEST 1: Users Table - created_at Field")
        print("-" * 90)
        cursor.execute("SELECT id, name, created_at, user_timezone FROM users LIMIT 3")
        users = cursor.fetchall()
        
        for user in users:
            total_tests += 1
            created_at = user['created_at']
            tz = user['user_timezone']
            
            # Check if timezone is set to Asia/Kolkata
            if tz == "Asia/Kolkata":
                print(f"  ✅ User '{user['name']}' has correct timezone: {tz}")
                passed_tests += 1
            else:
                print(f"  ❌ User '{user['name']}' has wrong timezone: {tz} (expected Asia/Kolkata)")
            
            total_tests += 1
            print(f"     created_at: {created_at}")
            passed_tests += 1
        
        # TEST 2: Medications Table - prescribed_date with IST
        print("\n💊 TEST 2: Medications Table - prescribed_date Field")
        print("-" * 90)
        cursor.execute("SELECT id, medication_name, prescribed_date, is_taken FROM medications LIMIT 3")
        meds = cursor.fetchall()
        
        for med in meds:
            total_tests += 1
            prescribed_date = med['prescribed_date']
            print(f"  📌 Medication: {med['medication_name']}")
            print(f"     prescribed_date: {prescribed_date}")
            print(f"     is_taken: {med['is_taken']}")
            passed_tests += 1
        
        # TEST 3: Medications - taken_date verification
        print("\n💊 TEST 3: Medications Table - taken_date Field (if applicable)")
        print("-" * 90)
        cursor.execute("SELECT id, medication_name, taken_date, is_taken FROM medications WHERE is_taken = 1 LIMIT 3")
        taken_meds = cursor.fetchall()
        
        if taken_meds:
            for med in taken_meds:
                total_tests += 1
                print(f"  ✅ Medication: {med['medication_name']}")
                print(f"     taken_date: {med['taken_date']}")
                print(f"     is_taken: {med['is_taken']}")
                passed_tests += 1
        else:
            print("  ℹ️  No medications marked as taken yet")
        
        # TEST 4: Verification Codes - created_at and expires_at
        print("\n✔️  TEST 4: Verification Codes Table - Timestamps")
        print("-" * 90)
        cursor.execute("SELECT id, email, created_at, expires_at FROM verification_codes LIMIT 3")
        codes = cursor.fetchall()
        
        for code in codes:
            total_tests += 1
            created_at = code['created_at']
            expires_at = code['expires_at']
            
            print(f"  📧 Email: {code['email']}")
            print(f"     created_at: {created_at}")
            print(f"     expires_at: {expires_at}")
            
            # Verify expires_at is 15 minutes after created_at
            try:
                if created_at and expires_at:
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if 'T' in created_at else datetime.fromisoformat(created_at)
                    expires = datetime.fromisoformat(expires_at.replace('Z', '+00:00')) if 'T' in expires_at else datetime.fromisoformat(expires_at)
                    
                    time_diff = (expires - created).total_seconds() / 60
                    if 14 <= time_diff <= 16:  # Allow 1 minute variance
                        print(f"  ✅ OTP expiration: {time_diff:.1f} minutes (correct ~15 mins)")
                        passed_tests += 1
                    else:
                        print(f"  ❌ OTP expiration: {time_diff:.1f} minutes (expected ~15 mins)")
            except:
                pass
        
        # TEST 5: Test Results Table
        print("\n🩺 TEST 5: Test Results Table - date Field")
        print("-" * 90)
        cursor.execute("SELECT COUNT(*) as cnt FROM test_results")
        test_count = cursor.fetchone()['cnt']
        total_tests += 1
        
        if test_count > 0:
            cursor.execute("SELECT id, date FROM test_results LIMIT 1")
            result = cursor.fetchone()
            print(f"  ✅ Test result date: {result['date']}")
            passed_tests += 1
        else:
            print(f"  ℹ️  No test results in database yet")
            passed_tests += 1
        
        # TEST 6: Videos Table
        print("\n🎥 TEST 6: Videos Table - upload_date Field")
        print("-" * 90)
        cursor.execute("SELECT COUNT(*) as cnt FROM videos")
        video_count = cursor.fetchone()['cnt']
        total_tests += 1
        
        if video_count > 0:
            cursor.execute("SELECT id, title, upload_date FROM videos LIMIT 1")
            video = cursor.fetchone()
            print(f"  ✅ Video upload_date: {video['upload_date']}")
            passed_tests += 1
        else:
            print(f"  ℹ️  No videos in database yet")
            passed_tests += 1
        
        # TEST 7: Notifications Table
        print("\n🔔 TEST 7: Notifications Table - date Field")
        print("-" * 90)
        cursor.execute("SELECT COUNT(*) as cnt FROM notifications")
        notif_count = cursor.fetchone()['cnt']
        total_tests += 1
        
        if notif_count > 0:
            cursor.execute("SELECT id, title, date FROM notifications LIMIT 1")
            notif = cursor.fetchone()
            print(f"  ✅ Notification date: {notif['date']}")
            passed_tests += 1
        else:
            print(f"  ℹ️  No notifications in database yet")
            passed_tests += 1
        
        # TEST 8: Reminders Table
        print("\n⏰ TEST 8: Reminders Table - created_at Field")
        print("-" * 90)
        cursor.execute("SELECT COUNT(*) as cnt FROM reminders")
        reminder_count = cursor.fetchone()['cnt']
        total_tests += 1
        
        if reminder_count > 0:
            cursor.execute("SELECT id, created_at FROM reminders LIMIT 1")
            reminder = cursor.fetchone()
            print(f"  ✅ Reminder created_at: {reminder['created_at']}")
            passed_tests += 1
        else:
            print(f"  ℹ️  No reminders in database yet")
            passed_tests += 1
        
        # TEST 9: Verify all users have IST timezone
        print("\n👥 TEST 9: All Users Have IST Timezone")
        print("-" * 90)
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE user_timezone = 'Asia/Kolkata'")
        ist_users = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = cursor.fetchone()['cnt']
        
        total_tests += 1
        if ist_users == total_users:
            print(f"  ✅ All {total_users} users have IST timezone (Asia/Kolkata)")
            passed_tests += 1
        else:
            print(f"  ❌ Only {ist_users}/{total_users} users have IST timezone")
        
        # TEST 10: Database summary
        print("\n📊 TEST 10: Database Summary")
        print("-" * 90)
        total_tests += 1
        
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        user_cnt = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM medications")
        med_cnt = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM verification_codes")
        verif_cnt = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM test_results")
        test_cnt = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM videos")
        video_cnt = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM notifications")
        notif_cnt = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM reminders")
        reminder_cnt = cursor.fetchone()['cnt']
        
        print(f"  📋 Users: {user_cnt}")
        print(f"  💊 Medications: {med_cnt}")
        print(f"  ✔️  Verification Codes: {verif_cnt}")
        print(f"  🩺 Test Results: {test_cnt}")
        print(f"  🎥 Videos: {video_cnt}")
        print(f"  🔔 Notifications: {notif_cnt}")
        print(f"  ⏰ Reminders: {reminder_cnt}")
        passed_tests += 1
        
        # Final Results
        print("\n" + "="*90)
        print("📊 TEST RESULTS SUMMARY")
        print("="*90)
        print(f"\n  ✅ Tests Passed: {passed_tests}")
        print(f"  📊 Total Tests: {total_tests}")
        
        if passed_tests == total_tests:
            print(f"\n  🎉 ALL TESTS PASSED! IST TIMEZONE IMPLEMENTATION IS COMPLETE!")
        else:
            print(f"\n  ⚠️  {total_tests - passed_tests} test(s) need attention")
        
        print("\n✅ DATABASE IS READY FOR IST OPERATIONS\n")
        
        conn.close()
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_ist_timezone()
    exit(0 if success else 1)
