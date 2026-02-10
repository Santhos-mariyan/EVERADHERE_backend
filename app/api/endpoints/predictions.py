"""
Patient Recovery Prediction Endpoints
====================================

API endpoints for ML-based patient recovery predictions.
Provides personalized recovery scores and recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.models.models import User, Medication, TestResult
from app.schemas.schemas import RecoveryPredictionResponse
from app.api.deps import get_current_user, get_current_doctor, get_current_patient
from app.services.ml_prediction_service import predict_patient_recovery

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/patient-recovery/{patient_id}", response_model=RecoveryPredictionResponse)
def predict_patient_recovery_score(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recovery prediction for a specific patient.
    
    Only doctors can request predictions for their patients.
    Patients can request their own predictions.
    
    Returns:
    - recovery_score: 0-100 score indicating recovery progress
    - status: EXCELLENT, GOOD, MODERATE, POOR, or CRITICAL
    - recommendations: Personalized medical recommendations
    - data_points: Input features used for prediction
    - confidence_level: HIGH, MEDIUM, or LOW based on data availability
    """
    try:
        # Get patient
        patient = db.query(User).filter(
            User.id == patient_id,
            User.user_type == "patient"
        ).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Authorization: Doctor can see all patients, patient can only see themselves
        if current_user.user_type == "patient" and current_user.id != patient_id:
            raise HTTPException(status_code=403, detail="You can only view your own recovery data")
        
        # Get patient's medications
        medications = db.query(Medication).filter(
            Medication.patient_id == patient_id
        ).all()
        
        # Get patient's test results
        test_results = db.query(TestResult).filter(
            TestResult.patient_id == patient_id
        ).all()
        
        # Get prediction
        prediction = predict_patient_recovery(
            patient_id=patient_id,
            medication_data=medications,
            test_results=test_results
        )
        
        logger.info(f"✅ Recovery prediction generated for patient {patient_id}: {prediction['status']}")
        
        return prediction
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting recovery for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating prediction: {str(e)}")


@router.get("/my-recovery", response_model=RecoveryPredictionResponse)
def get_my_recovery_prediction(
    db: Session = Depends(get_db),
    current_patient: User = Depends(get_current_patient)
):
    """
    Get recovery prediction for current patient.
    Only accessible to patients.
    
    Returns recovery score and personalized recommendations.
    """
    try:
        # Get patient's medications
        medications = db.query(Medication).filter(
            Medication.patient_id == current_patient.id
        ).all()
        
        # Get patient's test results
        test_results = db.query(TestResult).filter(
            TestResult.patient_id == current_patient.id
        ).all()
        
        # Get prediction
        prediction = predict_patient_recovery(
            patient_id=current_patient.id,
            medication_data=medications,
            test_results=test_results
        )
        
        logger.info(f"✅ Recovery prediction retrieved by patient {current_patient.id}: {prediction['status']}")
        
        return prediction
    
    except Exception as e:
        logger.error(f"Error retrieving recovery prediction for patient {current_patient.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating prediction: {str(e)}")


@router.get("/all-patients-recovery")
def get_all_patients_recovery_summary(
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """
    Get recovery predictions summary for all patients under a doctor.
    Only accessible to doctors.
    
    Returns list of patients with their recovery scores and status,
    sorted by recovery score (critical cases first).
    """
    try:
        # Get all patients with this doctor's prescriptions
        patients_with_prescriptions = db.query(User).join(
            Medication, User.id == Medication.patient_id
        ).filter(
            Medication.doctor_id == current_doctor.id,
            User.user_type == "patient"
        ).distinct().all()
        
        if not patients_with_prescriptions:
            return {
                "doctor_id": current_doctor.id,
                "patients_summary": [],
                "critical_count": 0,
                "poor_count": 0,
                "moderate_count": 0,
                "good_count": 0,
                "excellent_count": 0
            }
        
        predictions = []
        status_counts = {
            "CRITICAL": 0,
            "POOR": 0,
            "MODERATE": 0,
            "GOOD": 0,
            "EXCELLENT": 0
        }
        
        for patient in patients_with_prescriptions:
            # Get patient's medications
            medications = db.query(Medication).filter(
                Medication.patient_id == patient.id,
                Medication.doctor_id == current_doctor.id
            ).all()
            
            # Get patient's test results
            test_results = db.query(TestResult).filter(
                TestResult.patient_id == patient.id
            ).all()
            
            # Get prediction
            prediction = predict_patient_recovery(
                patient_id=patient.id,
                medication_data=medications,
                test_results=test_results
            )
            
            predictions.append({
                "patient_id": patient.id,
                "patient_name": patient.name,
                "recovery_score": prediction['recovery_score'],
                "status": prediction['status'],
                "message": prediction['message'],
                "confidence_level": prediction['confidence_level'],
                "medication_adherence": prediction['data_points']['medication_adherence']
            })
            
            status_counts[prediction['status']] += 1
        
        # Sort by recovery score (critical cases first)
        predictions.sort(key=lambda x: x['recovery_score'])
        
        logger.info(f"✅ Recovery summary generated for doctor {current_doctor.id}: "
                   f"{len(predictions)} patients analyzed")
        
        return {
            "doctor_id": current_doctor.id,
            "total_patients": len(predictions),
            "patients_summary": predictions,
            "critical_count": status_counts["CRITICAL"],
            "poor_count": status_counts["POOR"],
            "moderate_count": status_counts["MODERATE"],
            "good_count": status_counts["GOOD"],
            "excellent_count": status_counts["EXCELLENT"]
        }
    
    except Exception as e:
        logger.error(f"Error generating recovery summary for doctor {current_doctor.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
