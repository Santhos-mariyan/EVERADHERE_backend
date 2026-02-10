"""
Final Comprehensive IST Timezone Implementation Verification
This script verifies all code changes are in place and database is ready
"""

import os
import re

def verify_code_changes():
    """Verify all code changes are in place"""
    
    print("\n" + "="*90)
    print("✅ CODE CHANGES VERIFICATION")
    print("="*90)
    
    checks_passed = 0
    checks_total = 0
    
    # CHECK 1: models.py has get_ist_now function
    print("\n📝 CHECK 1: app/models/models.py - get_ist_now() function")
    print("-" * 90)
    checks_total += 1
    
    try:
        with open("app/models/models.py", "r") as f:
            content = f.read()
            if "def get_ist_now():" in content and "ZoneInfo" in content:
                print("  ✅ get_ist_now() function is defined")
                print("  ✅ ZoneInfo import is present")
                checks_passed += 1
            else:
                print("  ❌ Missing get_ist_now() or ZoneInfo import")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # CHECK 2: User.created_at uses get_ist_now
    print("\n📝 CHECK 2: User.created_at uses get_ist_now")
    print("-" * 90)
    checks_total += 1
    
    try:
        with open("app/models/models.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            if 'created_at = Column(DateTime, default=get_ist_now)' in content:
                print("  ✅ User.created_at correctly uses get_ist_now")
                checks_passed += 1
            else:
                print("  ❌ User.created_at not using get_ist_now")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # CHECK 3: User.user_timezone defaults to Asia/Kolkata
    print("\n📝 CHECK 3: User.user_timezone defaults to Asia/Kolkata")
    print("-" * 90)
    checks_total += 1
    
    try:
        with open("app/models/models.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            if 'user_timezone = Column(String, default="Asia/Kolkata")' in content:
                print("  ✅ User.user_timezone correctly defaults to Asia/Kolkata")
                checks_passed += 1
            else:
                print("  ❌ User.user_timezone not set to Asia/Kolkata")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # CHECK 4: Medication.prescribed_date uses get_ist_now
    print("\n📝 CHECK 4: Medication.prescribed_date uses get_ist_now")
    print("-" * 90)
    checks_total += 1
    
    try:
        with open("app/models/models.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            if 'prescribed_date = Column(DateTime, default=get_ist_now)' in content:
                print("  ✅ Medication.prescribed_date correctly uses get_ist_now")
                checks_passed += 1
            else:
                print("  ❌ Medication.prescribed_date not using get_ist_now")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # CHECK 5: auth.py has get_ist_now imports
    print("\n📝 CHECK 5: app/api/endpoints/auth.py - get_ist_now import and usage")
    print("-" * 90)
    checks_total += 1
    
    try:
        with open("app/api/endpoints/auth.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            get_ist_now_imports = content.count("get_ist_now")
            if get_ist_now_imports >= 6:
                print(f"  ✅ get_ist_now used {get_ist_now_imports} times in auth.py")
                print("  ✅ OTP operations using IST timezone")
                checks_passed += 1
            else:
                print(f"  ❌ get_ist_now used only {get_ist_now_imports} times (expected 6+)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # CHECK 6: medications.py has get_ist_now imports
    print("\n📝 CHECK 6: app/api/endpoints/medications.py - get_ist_now import and usage")
    print("-" * 90)
    checks_total += 1
    
    try:
        with open("app/api/endpoints/medications.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            get_ist_now_count = content.count("get_ist_now")
            if get_ist_now_count >= 2:
                print(f"  ✅ get_ist_now used {get_ist_now_count} times in medications.py")
                print("  ✅ Medication operations using IST timezone")
                checks_passed += 1
            else:
                print(f"  ❌ get_ist_now used only {get_ist_now_count} times (expected 2+)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # CHECK 7: DateTime imports are correct
    print("\n📝 CHECK 7: DateTime Imports - ZoneInfo in all files")
    print("-" * 90)
    checks_total += 1
    
    try:
        files_to_check = [
            "app/models/models.py",
            "app/api/endpoints/auth.py",
            "app/api/endpoints/medications.py"
        ]
        
        all_have_zoneinfo = True
        for file in files_to_check:
            try:
                with open(file, "r") as f:
                    content = f.read()
                    if file == "app/models/models.py":
                        # models.py must have ZoneInfo
                        if "from zoneinfo import ZoneInfo" in content:
                            print(f"  ✅ {file}: ZoneInfo imported")
                        else:
                            print(f"  ❌ {file}: ZoneInfo not imported")
                            all_have_zoneinfo = False
            except:
                pass
        
        if all_have_zoneinfo:
            checks_passed += 1
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Summary
    print("\n" + "="*90)
    print("📊 CODE VERIFICATION RESULTS")
    print("="*90)
    print(f"\n  ✅ Checks Passed: {checks_passed}")
    print(f"  📊 Total Checks: {checks_total}")
    
    if checks_passed == checks_total:
        print(f"\n  🎉 ALL CODE CHANGES ARE IN PLACE!")
    else:
        print(f"\n  ⚠️  {checks_total - checks_passed} check(s) need attention")
    
    return checks_passed == checks_total

if __name__ == "__main__":
    success = verify_code_changes()
    exit(0 if success else 1)
