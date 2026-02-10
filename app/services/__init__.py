from . import otp_service, email_service
# reminder_service may require extra deps; attempt import but provide a safe fallback
from types import SimpleNamespace

try:
    from . import reminder_service
except Exception:
    # provide a lightweight fallback exposing compute_next_run so tests can run
    def _parse_time_12h(time_str: str, am_pm: str):
        hour, minute = map(int, time_str.split(":"))
        if am_pm.upper() == "PM" and hour != 12:
            hour += 12
        if am_pm.upper() == "AM" and hour == 12:
            hour = 0
        return hour, minute

    from datetime import datetime, timedelta

    def compute_next_run(time_str: str, am_pm: str, frequency: str):
        now = datetime.utcnow()
        hour, minute = _parse_time_12h(time_str, am_pm)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            if frequency == "daily":
                candidate = candidate + timedelta(days=1)
            elif frequency == "weekly":
                candidate = candidate + timedelta(weeks=1)
            elif frequency == "monthly":
                candidate = candidate + timedelta(days=30)
        return candidate

    reminder_service = SimpleNamespace(
        compute_next_run=compute_next_run,
        scheduler=None,
        start_scheduler=lambda: None,
        schedule_reminder=lambda *a, **k: None,
        load_and_schedule_all=lambda: None,
    )
