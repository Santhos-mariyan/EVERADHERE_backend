from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.models import User, Medication, TestResult
from app.schemas.schemas import DoctorDashboard, PatientDashboard
from app.api.deps import get_current_user, get_current_doctor, get_current_patient

router = APIRouter()

@router.get("/doctor", response_model=DoctorDashboard)
def get_doctor_dashboard(
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """Get dashboard data for doctors"""
    
    # Get total number of patients
    total_patients = db.query(User).filter(User.user_type == "patient").count()
    
    # Get today's appointments (for now, just count of patients seen today)
    # In a real app, you'd have an Appointment model
    today = datetime.utcnow().date()
    today_appointments = db.query(Medication).filter(
        Medication.doctor_id == current_doctor.id,
        func.date(Medication.prescribed_date) == today
    ).distinct(Medication.patient_id).count()
    
    # Get active patients (unique patients this doctor has prescribed medications to)
    active_patients = db.query(func.count(func.distinct(Medication.patient_id))).filter(
        Medication.doctor_id == current_doctor.id
    ).scalar()
    
    # Get recent patients (patients with recent prescriptions)
    recent_patient_ids = db.query(Medication.patient_id).filter(
        Medication.doctor_id == current_doctor.id
    ).order_by(Medication.prescribed_date.desc()).limit(5).distinct().all()
    
    recent_patient_ids = [pid[0] for pid in recent_patient_ids]
    recent_patients = db.query(User).filter(User.id.in_(recent_patient_ids)).all()
    
    return DoctorDashboard(
        total_patients=total_patients,
        today_appointments=today_appointments,
        active_patients=active_patients or 0,
        recent_patients=recent_patients
    )

@router.get("/patient", response_model=PatientDashboard)
def get_patient_dashboard(
    db: Session = Depends(get_db),
    current_patient: User = Depends(get_current_patient)
):
    """Get dashboard data for patients with AUTOMATIC DAILY RESET
    
    AUTOMATIC RESET LOGIC:
    - Triggers when user opens app (dashboard load)
    - Checks if it's a new calendar day in user's timezone
    - If new day → Resets ALL is_taken=true medications
    - Only resets ONCE per day
    - Works in IST, EST, PST, GMT, etc.
    """
    
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    # ✅ STEP 1: AUTOMATIC DAILY RESET
    try:
        # Get user's timezone (default to UTC)
        timezone_str = current_patient.user_timezone or "UTC"
        
        # Create timezone object
        try:
            tz = ZoneInfo(timezone_str)
        except Exception as e:
            # Fallback to UTC if timezone is invalid
            tz = ZoneInfo("UTC")
        
        # Get current date in user's LOCAL timezone
        now_user_tz = datetime.now(tz=tz)
        today_date = now_user_tz.date()
        
        # Check if we need to reset (new day in user's timezone)
        should_reset = False
        
        if current_patient.last_reset_date:
            # Convert last_reset_date from UTC to user's timezone
            # Handle both UTC-aware and naive datetimes
            stored_reset = current_patient.last_reset_date
            
            if stored_reset.tzinfo is None:
                # Naive datetime - assume UTC from old system
                last_reset_utc = stored_reset.replace(tzinfo=ZoneInfo("UTC"))
                last_reset_user_tz = last_reset_utc.astimezone(tz)
            else:
                # Has timezone info, convert to user's timezone
                last_reset_user_tz = stored_reset.astimezone(tz)
            
            last_reset_date = last_reset_user_tz.date()
            
            # If dates are different, it's a new day
            if last_reset_date != today_date:
                should_reset = True
        else:
            # First time logging in, set the date
            should_reset = True
        
        # ✅ PERFORM RESET IF NEEDED
        if should_reset:
            # Get ALL medications for this patient
            medications = db.query(Medication).filter(
                Medication.patient_id == current_patient.id
            ).all()
            
            reset_count = 0
            for med in medications:
                # Reset all taken medications to not taken
                if med.is_taken:
                    med.is_taken = False
                    med.taken_date = None
                    reset_count += 1
            
            # Update last reset date (store in IST)
            current_patient.last_reset_date = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
    
    except Exception as e:
        # If reset fails, continue to dashboard (don't crash)
        pass
    
    # ✅ STEP 2: CALCULATE DASHBOARD STATS (after reset)
    
    # Calculate tree level based on taken medications (adaptive)
    total_taken = db.query(Medication).filter(
        Medication.patient_id == current_patient.id,
        Medication.is_taken == True
    ).count()
    
    # Count total medications
    total_meds = db.query(Medication).filter(
        Medication.patient_id == current_patient.id
    ).count()
    
    # Calculate tree level (adaptive: fully grown when all meds taken)
    if total_meds > 0:
        tree_level = int((total_taken / total_meds) * 10)
    else:
        tree_level = 0
    
    # Ensure max 10
    tree_level = min(tree_level, 10)
    
    # Count pending (not taken) medications
    pending_medications = db.query(Medication).filter(
        Medication.patient_id == current_patient.id,
        Medication.is_taken == False
    ).count()
    
    # Get most recent test score
    latest_test = db.query(TestResult).filter(
        TestResult.patient_id == current_patient.id
    ).order_by(TestResult.date.desc()).first()
    
    recent_test_score = latest_test.score if latest_test else None
    
    # Get recent medications (last 5)
    recent_medications = db.query(Medication).filter(
        Medication.patient_id == current_patient.id
    ).order_by(Medication.prescribed_date.desc()).limit(5).all()
    
    return PatientDashboard(
        tree_level=tree_level,
        pending_medications=pending_medications,
        recent_test_score=recent_test_score,
        recent_medications=recent_medications
    )

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get general statistics for current user"""
    
    if current_user.user_type == "doctor":
        # Doctor stats
        total_patients = db.query(User).filter(User.user_type == "patient").count()
        
        total_prescriptions = db.query(Medication).filter(
            Medication.doctor_id == current_user.id
        ).count()
        
        total_videos_uploaded = db.query(func.count()).select_from(
            db.query(User).filter(User.id == current_user.id).subquery()
        ).scalar()
        
        return {
            "user_type": "doctor",
            "total_patients": total_patients,
            "total_prescriptions": total_prescriptions,
            "total_videos_uploaded": 0  # Placeholder
        }
    
    else:
        # Patient stats
        total_medications = db.query(Medication).filter(
            Medication.patient_id == current_user.id
        ).count()
        
        medications_taken = db.query(Medication).filter(
            Medication.patient_id == current_user.id,
            Medication.is_taken == True
        ).count()
        
        total_tests = db.query(TestResult).filter(
            TestResult.patient_id == current_user.id
        ).count()
        
        # Calculate tree level (adaptive)
        if total_medications > 0:
            tree_level = int((medications_taken / total_medications) * 10)
        else:
            tree_level = 0
        tree_level = min(tree_level, 10)
        
        return {
            "user_type": "patient",
            "tree_level": tree_level,
            "total_medications": total_medications,
            "medications_taken": medications_taken,
            "total_tests": total_tests
        }
