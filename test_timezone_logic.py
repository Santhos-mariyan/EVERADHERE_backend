from datetime import datetime
from zoneinfo import ZoneInfo

# Current scenario from database
timezone_str = "Asia/Kolkata"
tz = ZoneInfo(timezone_str)

# Last reset from database: 2026-01-17 14:18:40.888414 (UTC)
last_reset_utc_str = "2026-01-17 14:18:40.888414"
last_reset_utc = datetime.fromisoformat(last_reset_utc_str).replace(tzinfo=ZoneInfo("UTC"))

# Convert to IST
last_reset_tz = last_reset_utc.astimezone(tz)

print("=" * 80)
print("TIMEZONE LOGIC TEST")
print("=" * 80)
print(f"Last Reset (UTC): {last_reset_utc}")
print(f"Last Reset (IST): {last_reset_tz}")
print(f"Last Reset Date (IST): {last_reset_tz.date()}")

# Current date in IST (simulating app load on Jan 17 - SAME DAY)
now_utc = datetime(2026, 1, 17, 15, 30, 0, tzinfo=ZoneInfo("UTC"))  # 15:30 UTC = 21:00 IST (same day)
now_tz = now_utc.astimezone(tz)
print(f"\nCurrent Time (UTC): {now_utc}")
print(f"Current Time (IST): {now_tz}")
print(f"Current Date (IST): {now_tz.date()}")

# Compare
should_reset = last_reset_tz.date() != now_tz.date()
print(f"\nShould Reset? {should_reset} (Dates equal: {last_reset_tz.date() == now_tz.date()})")

print("\n" + "=" * 80)
print("NOW TEST: NEXT DAY (January 18)")
print("=" * 80)

# Next day at 12:01 AM IST = 18:31 UTC (previous day)
now_utc_next = datetime(2026, 1, 18, 0, 1, 0, tzinfo=ZoneInfo("UTC"))  # 00:01 UTC on Jan 18
now_tz_next = now_utc_next.astimezone(tz)
print(f"Current Time (UTC): {now_utc_next}")
print(f"Current Time (IST): {now_tz_next}")
print(f"Current Date (IST): {now_tz_next.date()}")

# Compare
should_reset_next = last_reset_tz.date() != now_tz_next.date()
print(f"\nShould Reset? {should_reset_next} (Dates equal: {last_reset_tz.date() == now_tz_next.date()})")
print(f"Last Reset Date (IST): {last_reset_tz.date()}")
print(f"Today Date (IST): {now_tz_next.date()}")
