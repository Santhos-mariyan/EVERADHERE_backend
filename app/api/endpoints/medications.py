from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.db.session import get_db
from app.models.models import User, Medication, Notification, get_ist_now
from app.schemas.schemas import (
    MedicationCreate, MedicationResponse, MedicationListCreate,
    MessageResponse, TreeLevelResponse
)
from app.api.deps import get_current_user, get_current_doctor
from app.services import firebase_service
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== UTILITY FUNCTIONS ====================

def parse_duration(duration_str: str) -> timedelta:
    """
    Parse duration string and convert to timedelta.
    Supports: "2 days", "1 week", "3 months", "2 years", etc.
    """
    if not duration_str:
        return timedelta(days=0)
    
    # Extract number and unit using regex
    match = re.match(r'(\d+)\s*([a-zA-Z]+)', duration_str.strip())
    if not match:
        return timedelta(days=0)
    
    quantity = int(match.group(1))
    unit = match.group(2).lower()
    
    if unit.startswith('day'):
        return timedelta(days=quantity)
    elif unit.startswith('week'):
        return timedelta(weeks=quantity)
    elif unit.startswith('month'):
        return timedelta(days=quantity * 30)  # Approximate
    elif unit.startswith('year'):
        return timedelta(days=quantity * 365)  # Approximate
    else:
        return timedelta(days=0)


def is_medication_expired(prescribed_date: datetime, duration_str: str) -> bool:
    """
    Check if a medication has expired based on prescribed date and duration.
    """
    if not prescribed_date or not duration_str:
        return False
    
    duration = parse_duration(duration_str)
    expiration_date = prescribed_date + duration
    
    return datetime.utcnow() > expiration_date


@router.post("/prescribe", response_model=List[MedicationResponse], status_code=status.HTTP_201_CREATED)
def prescribe_medications(
    medication_list: MedicationListCreate,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """Prescribe medications to a patient (Doctor only) - FULLY WORKING VERSION"""
    
    logger.info(f"📋 Doctor {current_doctor.name} (ID: {current_doctor.id}) prescribing medications to patient {medication_list.patient_id}")
    
    # Verify patient exists
    patient = db.query(User).filter(
        User.id == medication_list.patient_id,
        User.user_type == "patient"
    ).first()
    
    if not patient:
        logger.error(f"❌ Patient {medication_list.patient_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    logger.info(f"✅ Patient found: {patient.name} (FCM Token: {patient.fcm_token[:20] if patient.fcm_token else 'NOT SET'}...)")
    
    # Verify doctor has a name
    doctor_name = current_doctor.name or "Your Doctor"
    
    created_medications = []
    medication_names = []
    
    try:
        # Add all medications to database
        for med in medication_list.medications:
            logger.info(f"   📌 Adding medication: {med.medication_name} ({med.dosage})")
            
            db_medication = Medication(
                patient_id=medication_list.patient_id,
                doctor_id=current_doctor.id,
                medication_name=med.medication_name,
                dosage=med.dosage,
                frequency=med.frequency,
                duration=med.duration,
                instructions=med.instructions,
                prescribed_date=datetime.utcnow()
            )
            db.add(db_medication)
            created_medications.append(db_medication)
            medication_names.append(med.medication_name)
        
        # Create notification for patient (saved to DB)
        notification = Notification(
            user_id=medication_list.patient_id,
            title="New Medication Prescribed",
            message=f"Dr. {doctor_name} has prescribed {len(medication_names)} medication(s) for you.",
            date=datetime.utcnow()
        )
        db.add(notification)
        
        # Commit the transaction to make objects persistent
        db.commit()
        
        logger.info(f"✅ Medications saved to database: {medication_names}")
        
        # Refresh medications to get IDs (after commit, objects are persistent)
        for med in created_medications:
            db.refresh(med)
        
        # THEN SEND FCM NOTIFICATION (Non-blocking)
        if patient.fcm_token:
            logger.info(f"📤 Attempting to send FCM notification...")
            logger.info(f"   Patient FCM Token: {patient.fcm_token[:30]}...")
            logger.info(f"   Doctor Name: {doctor_name}")
            logger.info(f"   Medications: {medication_names}")
            
            notification_result = firebase_service.send_medication_prescribed_notification(
                patient_fcm_token=patient.fcm_token,
                doctor_name=doctor_name,
                medications=medication_names
            )
            
            if notification_result.get("success"):
                logger.info(f"✅ FCM Notification sent successfully!")
                logger.info(f"   Message ID: {notification_result.get('message_id')}")
                logger.info(f"   Title: {notification_result.get('title')}")
                logger.info(f"   Body: {notification_result.get('body')}")
            else:
                logger.warning(f"⚠️  FCM Notification failed (but medications were saved)")
                logger.warning(f"   Error: {notification_result.get('error')}")
        else:
            logger.warning(f"⚠️  Patient has no FCM token - notification not sent")
            logger.warning(f"   Patient {patient.name} needs to log in on their mobile device first")
        
        return created_medications
        
    except Exception as e:
        logger.error(f"❌ Error prescribing medications: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error prescribing medications: {str(e)}"
        )


@router.get("/patient/{patient_id}", response_model=List[MedicationResponse])
def get_patient_medications(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all medications for a patient"""
    
    # Allow if user is the patient or a doctor
    if current_user.user_type == "patient" and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own medications"
        )
    
    medications = db.query(Medication).filter(
        Medication.patient_id == patient_id
    ).order_by(Medication.prescribed_date.desc()).all()
    
    return medications


@router.get("/my-medications", response_model=List[MedicationResponse])
def get_my_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get medications for current patient with AUTOMATIC DAILY RESET
    
    AUTOMATIC RESET ON EACH CALL:
    - Resets at midnight IST (00:00 IST)
    - If new day → resets all is_taken=true medications
    - Returns fresh medication list
    - Everything in IST timezone only
    """
    
    if current_user.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access their medications"
        )
    
    # ✅ AUTOMATIC DAILY RESET LOGIC (IST ONLY - NO UTC)
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # Use IST timezone only (no UTC conversion)
        tz_ist = ZoneInfo("Asia/Kolkata")
        
        # Get current time in IST
        now_ist = datetime.now(tz=tz_ist)
        today_date_ist = now_ist.date()
        
        logger.info(f"[RESET CHECK] Current IST: {now_ist}")
        logger.info(f"[RESET CHECK] Today's date: {today_date_ist}")
        
        # Check if we need to reset (new day in IST)
        should_reset = False
        
        if current_user.last_reset_date:
            # Get stored datetime
            stored_reset = current_user.last_reset_date
            logger.info(f"[RESET CHECK] Stored datetime: {stored_reset}")
            logger.info(f"[RESET CHECK] Stored tzinfo: {stored_reset.tzinfo}")
            
            # Convert datetime to IST - handle both UTC-aware and naive datetimes
            if stored_reset.tzinfo is None:
                # Naive datetime - assume UTC from old system
                logger.info(f"[RESET CHECK] Naive datetime - treating as UTC")
                stored_reset_utc = stored_reset.replace(tzinfo=ZoneInfo("UTC"))
                last_reset_ist = stored_reset_utc.astimezone(tz_ist)
            else:
                # Has timezone info, convert to IST
                last_reset_ist = stored_reset.astimezone(tz_ist)
            
            last_reset_date_ist = last_reset_ist.date()
            
            logger.info(f"[RESET CHECK] Last reset date (IST): {last_reset_date_ist}")
            logger.info(f"[RESET CHECK] Comparing: {last_reset_date_ist} vs {today_date_ist}")
            
            # If dates are different, it's a new day
            if last_reset_date_ist != today_date_ist:
                should_reset = True
                logger.info(f"[RESET CHECK] ✅ NEW DAY - Will reset medications!")
            else:
                logger.info(f"[RESET CHECK] Same day - Skip reset")
        else:
            # First time, always reset
            should_reset = True
            logger.info(f"[RESET CHECK] ✅ FIRST TIME - Will reset medications!")
        
        # ✅ PERFORM RESET IF NEW DAY
        if should_reset:
            # Get ALL medications for this patient
            all_medications = db.query(Medication).filter(
                Medication.patient_id == current_user.id
            ).all()
            
            reset_count = 0
            for med in all_medications:
                # Reset all taken medications to not taken
                if med.is_taken:
                    med.is_taken = False
                    med.taken_date = None
                    reset_count += 1
                    logger.info(f"  [RESET] {med.medication_name} → NOT TAKEN")
            
            # Update last reset date (store as proper datetime with IST timezone)
            current_user.last_reset_date = now_ist
            reset_time_str = now_ist.strftime("%I:%M %p IST")
            logger.info(f"[SUCCESS] Reset {reset_count} medications! Last reset: {reset_time_str}")
        else:
            logger.info(f"[SKIP RESET] Same day, no reset needed")
    
    except Exception as e:
        # If reset fails, log but continue (don't crash endpoint)
        logger.error(f"[ERROR] Reset logic failed: {str(e)}")
    
    # ✅ RETURN FRESH MEDICATIONS (after reset)
    medications = db.query(Medication).filter(
        Medication.patient_id == current_user.id
    ).order_by(Medication.prescribed_date.desc()).all()
    
    return medications


@router.get("/all-by-doctor")
def get_all_medications_by_doctor(
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """Get all medications prescribed by the current doctor with patient names"""
    
    try:
        # Get all medications prescribed by this doctor
        medications = db.query(Medication).filter(
            Medication.doctor_id == current_doctor.id
        ).order_by(Medication.prescribed_date.desc()).all()
        
        result = []
        for med in medications:
            # Get patient details
            patient = db.query(User).filter(User.id == med.patient_id).first()
            
            # Calculate if medication is active (prescribed within last 30 days)
            from datetime import datetime, timedelta
            is_active = True
            if med.prescribed_date:
                days_old = (datetime.utcnow() - med.prescribed_date).days
                is_active = days_old <= 30
            
            result.append({
                "id": med.id,
                "patient_id": med.patient_id,
                "patient_name": patient.name if patient else "Unknown",
                "medication_name": med.medication_name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "duration": med.duration,
                "instructions": med.instructions if med.instructions else "",
                "prescribed_date": med.prescribed_date.isoformat() if med.prescribed_date else None,
                "is_taken": getattr(med, 'is_taken', False),  # Safe way to get is_taken
                "is_active": is_active  # Calculated, not from database
            })
        
        return result
        
    except Exception as e:
        print(f"Error in get_all_medications_by_doctor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching medications: {str(e)}"
        )

@router.put("/{medication_id}/mark-taken", response_model=MessageResponse)
def mark_medication_taken(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark medication as taken (Patient only)"""
    
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )
    
    # Verify patient owns this medication
    if medication.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own medications as taken"
        )
    
    # Allow updating even if already marked as taken
    medication.is_taken = True
    medication.taken_date = get_ist_now()
    
    return MessageResponse(message="Medication marked as taken successfully")


@router.put("/{medication_id}/mark-not-taken", response_model=MessageResponse)
def mark_medication_not_taken(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark medication as not taken (Patient only)"""
    
    logger.info(f"🔵 Mark-not-taken called for medication {medication_id} by user {current_user.id}")
    
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    
    if not medication:
        logger.error(f"❌ Medication {medication_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medication {medication_id} not found"
        )
    
    logger.info(f"✅ Found medication: {medication.medication_name}, patient_id={medication.patient_id}")
    
    # Verify patient owns this medication
    if medication.patient_id != current_user.id:
        logger.error(f"❌ Ownership check failed: med.patient_id={medication.patient_id}, user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own medications"
        )
    
    logger.info(f"✅ Ownership verified")
    
    # Allow marking as not taken even if already false (idempotent)
    medication.is_taken = False
    medication.taken_date = None
    
    logger.info(f"Medication marked as not taken successfully")
    
    return MessageResponse(message="Medication marked as not taken successfully")


@router.post("/reset-daily", response_model=MessageResponse)
def reset_daily_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset 'taken' status for medications at the start of a new day.
    Works with any timezone (IST, EST, UTC, etc.).
    
    TIMEZONE-AWARE LOGIC:
    - Uses user's local timezone (stored in user_timezone field)
    - Default: UTC if no timezone set
    - Resets at 12:00 AM in user's local time
    - Only resets once per calendar day (user's local time)
    - Resets ALL is_taken=true medications
    """
    
    if current_user.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can reset daily medications"
        )
    
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    
    # Get user's timezone (default to UTC if not set)
    timezone_str = current_user.user_timezone or "UTC"
    
    try:
        tz = ZoneInfo(timezone_str)
    except Exception as e:
        logger.warning(f"⚠️  Invalid timezone '{timezone_str}', defaulting to UTC: {str(e)}")
        tz = ZoneInfo("UTC")
    
    # Get current time in user's timezone
    now_user_tz = datetime.now(tz=tz)
    today_date = now_user_tz.date()
    
    logger.info(f"🔵 Daily reset called for patient {current_user.id}")
    logger.info(f"   Timezone: {timezone_str}")
    logger.info(f"   Local time: {now_user_tz}")
    logger.info(f"   Local date: {today_date}")
    
    # Check if reset has already been done today (in user's local timezone)
    if current_user.last_reset_date:
        # Convert last_reset_date to user's timezone for comparison
        # Handle both UTC-aware and naive datetimes
        stored_reset = current_user.last_reset_date
        
        if stored_reset.tzinfo is None:
            # Naive datetime - assume UTC from old system
            last_reset_utc = stored_reset.replace(tzinfo=ZoneInfo("UTC"))
            last_reset_user_tz = last_reset_utc.astimezone(tz)
        else:
            # Has timezone info, convert to user's timezone
            last_reset_user_tz = stored_reset.astimezone(tz)
        
        last_reset_date = last_reset_user_tz.date()
        
        logger.info(f"📅 Last reset was on {last_reset_date}, today is {today_date}")
        
        if last_reset_date == today_date:
            # Already reset today (in user's timezone), don't reset again
            logger.info(f"✅ Already reset today, skipping duplicate reset")
            return MessageResponse(message="Already reset today, no medications to reset")
    
    # Get all medications for this patient
    medications = db.query(Medication).filter(
        Medication.patient_id == current_user.id
    ).all()
    
    logger.info(f"📋 Found {len(medications)} total medications for patient")
    
    reset_count = 0
    
    for med in medications:
        # Only reset if medication hasn't expired
        if not is_medication_expired(med.prescribed_date, med.duration):
            # Reset ALL is_taken=true medications (clean slate for new day)
            if med.is_taken:
                med.is_taken = False
                med.taken_date = None
                reset_count += 1
                logger.info(f"✅ Reset {med.medication_name}")
        else:
            logger.debug(f"⏰ Skipped {med.medication_name} (medication has expired)")
    
    # Update the last reset date (store in IST - NOT UTC)
    current_user.last_reset_date = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
    
    logger.info(f"🔄 Daily reset completed: {reset_count} medications reset for patient {current_user.id}")
    return MessageResponse(message=f"Reset {reset_count} medications for new day")


@router.get("/tree-level", response_model=TreeLevelResponse)
def get_tree_level(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get patient's tree level based on medications taken"""
    
    if current_user.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients have tree levels"
        )
    
    # Count medications taken
    total_taken = db.query(Medication).filter(
        Medication.patient_id == current_user.id,
        Medication.is_taken == True
    ).count()
    
    # Count total medications
    total_meds = db.query(Medication).filter(
        Medication.patient_id == current_user.id
    ).count()
    
    # Calculate tree level (adaptive: fully grown when all meds taken)
    if total_meds > 0:
        tree_level = int((total_taken / total_meds) * 10)
    else:
        tree_level = 0
    
    # Ensure max 10
    tree_level = min(tree_level, 10)
    
    return TreeLevelResponse(
        tree_level=tree_level,
        total_taken=total_taken,
        max_level=10
    )


@router.delete("/{medication_id}", response_model=MessageResponse)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """Delete a medication (Doctor only)"""
    
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )
    
    # Only the prescribing doctor can delete
    if medication.doctor_id != current_doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete medications you prescribed"
        )
    
    db.delete(medication)
    
    return MessageResponse(message="Medication deleted successfully")


@router.post("/cleanup-expired")
def cleanup_expired_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """
    Clean up expired medications for the current patient.
    This endpoint can be called periodically or when the patient views their medications.
    """
    if current_user.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can cleanup their medications"
        )
    
    try:
        # Get all medications for this patient
        medications = db.query(Medication).filter(
            Medication.patient_id == current_user.id
        ).all()
        
        expired_count = 0
        for med in medications:
            if is_medication_expired(med.prescribed_date, med.duration):
                logger.info(f"🗑️ Deleting expired medication: {med.medication_name} (ID: {med.id})")
                db.delete(med)
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"✅ Cleaned up {expired_count} expired medications for patient {current_user.name}")
            return MessageResponse(message=f"Removed {expired_count} expired medication(s)")
        else:
            return MessageResponse(message="No expired medications found")
    
    except Exception as e:
        logger.error(f"❌ Error cleaning up expired medications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cleaning up expired medications"
        )
