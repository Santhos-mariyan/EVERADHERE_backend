from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.session import get_db
from app.models.models import User, TestResult
from app.schemas.schemas import (
    TestResultCreate, TestResultResponse, MessageResponse
)
from app.api.deps import get_current_user


router = APIRouter()


@router.post("/submit", response_model=TestResultResponse, status_code=status.HTTP_201_CREATED)
def submit_test_result(
    test_result: TestResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a test result (Patient submits their own)"""
    
    # If patient_id not provided, use current user (must be patient)
    patient_id = test_result.patient_id if test_result.patient_id else current_user.id
    
    # Verify patient exists
    patient = db.query(User).filter(
        User.id == patient_id,
        User.user_type == "patient"
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # If current user is patient, can only submit for themselves
    if current_user.user_type == "patient" and patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own test results"
        )
    
    db_test_result = TestResult(
        patient_id=patient_id,
        test_name=test_result.test_name,
        score=test_result.score,
        notes=test_result.notes,
        date=datetime.utcnow()
    )
    
    db.add(db_test_result)
    db.commit()
    db.refresh(db_test_result)
    
    return db_test_result


@router.get("/all", response_model=List[TestResultResponse])
def get_all_test_results(
    test_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all test results from all patients (for doctors only)"""
    
    # Only doctors can access all test results
    if current_user.user_type != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access all test results"
        )
    
    # Join with User table to get patient names
    query = db.query(TestResult).join(User, TestResult.patient_id == User.id)
    
    # Optional filter by test name
    if test_name:
        query = query.filter(TestResult.test_name == test_name)
    
    # Get results ordered by most recent first
    results = query.order_by(TestResult.date.desc()).offset(skip).limit(limit).all()
    
    # Add patient name to each result
    response_results = []
    for result in results:
        response_results.append({
            "id": result.id,
            "patient_id": result.patient_id,
            "test_name": result.test_name,
            "score": result.score,
            "notes": result.notes,
            "date": result.date,
            "patient_name": result.patient.name
        })
    
    return response_results


@router.get("/patient/{patient_id}", response_model=List[TestResultResponse])
def get_patient_test_results(
    patient_id: int,
    test_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all test results for a patient, optionally filtered by test name"""
    
    # Allow if user is the patient or a doctor
    if current_user.user_type == "patient" and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own test results"
        )
    
    query = db.query(TestResult).filter(TestResult.patient_id == patient_id)
    
    if test_name:
        query = query.filter(TestResult.test_name == test_name)
    
    results = query.order_by(TestResult.date.desc()).all()
    
    return results


@router.get("/my-results", response_model=List[TestResultResponse])
def get_my_test_results(
    test_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get test results for current patient"""
    
    if current_user.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access their test results"
        )
    
    query = db.query(TestResult).filter(TestResult.patient_id == current_user.id)
    
    if test_name:
        query = query.filter(TestResult.test_name == test_name)
    
    results = query.order_by(TestResult.date.desc()).all()
    
    return results


@router.get("/latest/{patient_id}", response_model=Optional[TestResultResponse])
def get_latest_test_result(
    patient_id: int,
    test_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the most recent test result for a patient"""
    
    # Allow if user is the patient or a doctor
    if current_user.user_type == "patient" and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own test results"
        )
    
    query = db.query(TestResult).filter(TestResult.patient_id == patient_id)
    
    if test_name:
        query = query.filter(TestResult.test_name == test_name)
    
    result = query.order_by(TestResult.date.desc()).first()
    
    return result


@router.get("/{result_id}", response_model=TestResultResponse)
def get_test_result_by_id(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific test result by ID"""
    
    result = db.query(TestResult).filter(TestResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test result not found"
        )
    
    # Allow if user is the patient or a doctor
    if current_user.user_type == "patient" and current_user.id != result.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own test results"
        )
    
    return result


@router.delete("/{result_id}", response_model=MessageResponse)
def delete_test_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a test result"""
    
    result = db.query(TestResult).filter(TestResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test result not found"
        )
    
    # Only the patient or a doctor can delete
    if current_user.user_type == "patient" and current_user.id != result.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own test results"
        )
    
    db.delete(result)
    db.commit()
    
    return MessageResponse(message="Test result deleted successfully")
