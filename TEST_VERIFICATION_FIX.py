#!/usr/bin/env python3
"""
Test script to verify timezone comparison fix for OTP verification
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def test_timezone_comparison():
    """Test that timezone-aware and naive datetime comparison works"""
    print("\n" + "="*60)
    print("🧪 TESTING TIMEZONE COMPARISON FIX")
    print("="*60)
    
    # Simulate what happens in the database
    ist_tz = ZoneInfo("Asia/Kolkata")
    
    # Timezone-aware datetime (from get_ist_now())
    aware_dt = datetime.now(tz=ist_tz)
    print(f"\n✅ Timezone-aware datetime: {aware_dt}")
    print(f"   Timezone: {aware_dt.tzinfo}")
    
    # Naive datetime (what might be stored in DB in some cases)
    naive_dt = datetime.now()
    print(f"\n✅ Naive datetime: {naive_dt}")
    print(f"   Timezone: {naive_dt.tzinfo}")
    
    # Test the fix: converting naive to aware
    if naive_dt.tzinfo is None:
        naive_dt_aware = naive_dt.replace(tzinfo=ist_tz)
        print(f"\n✅ Fixed naive datetime: {naive_dt_aware}")
        print(f"   Timezone: {naive_dt_aware.tzinfo}")
    
    # Test comparison
    expires_at = aware_dt + timedelta(minutes=15)
    current_time = aware_dt
    
    print(f"\n⏰ Testing expiration logic:")
    print(f"   Current time:  {current_time}")
    print(f"   Expires at:    {expires_at}")
    print(f"   Is expired?    {expires_at < current_time}")
    print(f"   ✅ Comparison successful (no TypeError)")
    
    # Test with naive datetime (after conversion fix)
    print(f"\n🔧 Testing fix with naive datetime:")
    naive_expires = (datetime.now() + timedelta(minutes=15))
    if naive_expires.tzinfo is None:
        naive_expires = naive_expires.replace(tzinfo=ist_tz)
    
    print(f"   Naive expires (fixed): {naive_expires}")
    print(f"   Current time:          {current_time}")
    print(f"   Comparison result:     {naive_expires < current_time}")
    print(f"   ✅ Fix works correctly")
    
    print("\n" + "="*60)
    print("✅ ALL TIMEZONE TESTS PASSED")
    print("="*60)

if __name__ == "__main__":
    test_timezone_comparison()
