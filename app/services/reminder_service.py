from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.models import Reminder, Notification, User, VerificationCode, get_ist_now
from sqlalchemy.orm import Session
import threading
from app.services import pubsub

scheduler = BackgroundScheduler()
_scheduler_started = False


def _parse_time_12h(time_str: str, am_pm: str):
    # time_str expected as HH:MM
    hour, minute = map(int, time_str.split(":"))
    if am_pm.upper() == "PM" and hour != 12:
        hour += 12
    if am_pm.upper() == "AM" and hour == 12:
        hour = 0
    return hour, minute


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
            # naive monthly add: add 30 days
            candidate = candidate + timedelta(days=30)
    return candidate


def _send_reminder(reminder_id: int):
    # open a db session per job
    db: Session = next(get_db())
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.is_active == True).first()
        if not reminder:
            return
        user = db.query(User).filter(User.id == reminder.user_id).first()
        # create notification record
        notif = Notification(
            user_id=reminder.user_id,
            title=reminder.title,
            message=reminder.message,
            date=datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        # publish to connected clients
        try:
            pubsub.publish_sync(notif.user_id, {
                "id": notif.id,
                "title": notif.title,
                "message": notif.message,
                "date": notif.date.isoformat()
            })
        except Exception:
            pass
            # (No external push provider configured) Notification saved to DB for patient-side polling
        # reschedule next_run according to frequency
        next_run = compute_next_run(reminder.time, reminder.am_pm, reminder.frequency)
        reminder.next_run = next_run
        db.add(reminder)
        db.commit()
    finally:
        db.close()


def schedule_reminder(reminder: Reminder):
    # schedule a single job for reminder
    job_id = f"reminder_{reminder.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    run_time = reminder.next_run or compute_next_run(reminder.time, reminder.am_pm, reminder.frequency)
    scheduler.add_job(_send_reminder, 'date', run_date=run_time, args=[reminder.id], id=job_id)


def _cleanup_expired_verification_codes():
    """Clean up expired verification codes from database"""
    db: Session = next(get_db())
    try:
        current_time = get_ist_now()
        # Find expired verification codes
        expired_codes = db.query(VerificationCode).filter(
            VerificationCode.is_used == False,
            VerificationCode.expires_at < current_time
        ).all()
        
        if expired_codes:
            for code in expired_codes:
                print(f"[CLEANUP] Removing expired verification code for {code.email}")
            deleted_count = len(expired_codes)
            for code in expired_codes:
                db.delete(code)
            db.commit()
            print(f"[CLEANUP] Removed {deleted_count} expired verification codes")
        else:
            print("[CLEANUP] No expired verification codes to clean up")
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return
    scheduler.start()
    # Schedule cleanup of expired verification codes every hour
    # scheduler.add_job(_cleanup_expired_verification_codes, 'interval', hours=1, id='cleanup_expired_codes')
    # print("[SCHEDULER] Added expired verification codes cleanup job (runs every hour)")
    _scheduler_started = True


def load_and_schedule_all():
    # schedule all active reminders from DB
    db: Session = next(get_db())
    try:
        reminders = db.query(Reminder).filter(Reminder.is_active == True).all()
        for r in reminders:
            if not r.next_run:
                r.next_run = compute_next_run(r.time, r.am_pm, r.frequency)
                db.add(r)
                db.commit()
            schedule_reminder(r)
    finally:
        db.close()
*** End File