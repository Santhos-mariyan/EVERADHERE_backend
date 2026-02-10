from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.models import Reminder, Notification, Medication
from app.schemas.schemas import ReminderCreate, ReminderResponse, MessageResponse
from app.api.deps import get_current_user
from app.services import reminder_service

router = APIRouter()


@router.post("/my", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.user_type != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can create reminders")

    # validate am_pm and frequency
    if payload.am_pm.upper() not in ["AM", "PM"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="am_pm must be 'AM' or 'PM'")
    if payload.frequency.lower() not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="frequency must be daily, weekly or monthly")

    # validate medication if provided
    if getattr(payload, 'medication_id', None):
        med = db.query(Medication).filter(Medication.id == payload.medication_id, Medication.patient_id == current_user.id).first()
        if not med:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="medication_id invalid or does not belong to current patient")

    # compute next run
    next_run = reminder_service.compute_next_run(payload.time, payload.am_pm, payload.frequency.lower())

    reminder = Reminder(
        user_id=current_user.id,
        title=payload.title,
        message=payload.message,
        time=payload.time,
        am_pm=payload.am_pm.upper(),
        frequency=payload.frequency.lower(),
        medication_id=payload.medication_id if getattr(payload, 'medication_id', None) else None,
        next_run=next_run,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # schedule job
    try:
        reminder_service.schedule_reminder(reminder)
    except Exception as e:
        print("Error scheduling reminder:", e)

    return reminder


@router.get("/my", response_model=List[ReminderResponse])
def list_my_reminders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.user_type != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can list reminders")

    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).order_by(Reminder.created_at.desc()).all()
    return reminders


@router.delete("/{reminder_id}", response_model=MessageResponse)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    if reminder.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own reminders")

    reminder.is_active = False
    db.add(reminder)
    db.commit()

    # remove scheduled job if exists
    try:
        job_id = f"reminder_{reminder.id}"
        if reminder_service.scheduler.get_job(job_id):
            reminder_service.scheduler.remove_job(job_id)
    except Exception:
        pass

    return MessageResponse(message="Reminder cancelled")
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.models import Reminder, User
from app.schemas.schemas import ReminderCreate, ReminderResponse, MessageResponse
from app.api.deps import get_current_user
from app.services import reminder_service

router = APIRouter()


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(rem: ReminderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.user_type != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can create reminders")

    # basic validation
    if rem.am_pm.upper() not in ["AM", "PM"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="am_pm must be 'AM' or 'PM'")
    if rem.frequency.lower() not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="frequency must be daily, weekly or monthly")

    reminder = Reminder(
        user_id=current_user.id,
        title=rem.title,
        message=rem.message,
        time=rem.time,
        am_pm=rem.am_pm.upper(),
        frequency=rem.frequency.lower(),
        created_at=datetime.utcnow()
    )
    # compute next_run
    reminder.next_run = reminder_service.compute_next_run(reminder.time, reminder.am_pm, reminder.frequency)

    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # schedule job
    reminder_service.schedule_reminder(reminder)

    return reminder


@router.get("/my", response_model=List[ReminderResponse])
def list_my_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.user_type != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients have reminders")
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).order_by(Reminder.created_at.desc()).all()
    return reminders


@router.delete("/{reminder_id}", response_model=MessageResponse)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    if reminder.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    reminder.is_active = False
    db.add(reminder)
    db.commit()
    # remove scheduled job if exists
    job_id = f"reminder_{reminder.id}"
    try:
        reminder_service.scheduler.remove_job(job_id)
    except Exception:
        pass
    return MessageResponse(message="Reminder cancelled")
