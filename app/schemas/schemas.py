from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

# ==================== User Schemas ====================

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=1, le=150)
    gender: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., min_length=5)  # Changed from EmailStr for more flexibility
    location: str = Field(..., min_length=1, max_length=100)
    user_type: str  # 'doctor' or 'patient'
    contact_number: Optional[str] = None  # User's contact number
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('user_type')
    @classmethod
    def validate_user_type(cls, v):
        if v.lower() not in ['doctor', 'patient']:
            raise ValueError('user_type must be "doctor" or "patient"')
        return v.lower()

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    contact_number: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_verified: bool
    created_at: datetime
    profile_image: Optional[str] = None
    contact_number: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_type: str
    email: str
    name: str

# ==================== Medication Schemas ====================

class MedicationBase(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None

class MedicationCreate(MedicationBase):
    patient_id: int

class MedicationResponse(MedicationBase):
    id: int
    patient_id: int
    doctor_id: int
    is_taken: bool
    prescribed_date: datetime
    taken_date: Optional[datetime] = None  # When the medication was marked as taken
    
    class Config:
        from_attributes = True

class MedicationListCreate(BaseModel):
    patient_id: int
    medications: List[MedicationBase]

# ==================== Test Result Schemas ====================

class TestResultBase(BaseModel):
    test_name: str
    score: int
    notes: Optional[str] = None

class TestResultCreate(TestResultBase):
    patient_id: Optional[int] = None

class TestResultResponse(TestResultBase):
    id: int
    patient_id: int
    date: datetime
    patient_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# ==================== Video Schemas ====================

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    uploaded_by: int
    upload_date: datetime
    
    class Config:
        from_attributes = True

# ==================== Notification Schemas ====================

class NotificationBase(BaseModel):
    title: str
    message: str

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    date: datetime
    
    class Config:
        from_attributes = True


# ==================== Reminder Schemas ====================
class ReminderBase(BaseModel):
    title: str
    message: str
    time: str  # 12-hour HH:MM
    am_pm: str  # 'AM' or 'PM'
    frequency: str  # 'daily'|'weekly'|'monthly'
    medication_id: Optional[int] = None

class ReminderCreate(ReminderBase):
    pass

class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    medication_id: Optional[int] = None
    next_run: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== Verification Schemas ====================

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class VerificationCodeResponse(BaseModel):
    code: str
    message: str

# ==================== Dashboard Schemas ====================

class DoctorDashboard(BaseModel):
    total_patients: int
    today_appointments: int
    active_patients: int
    recent_patients: List[UserResponse]

class PatientDashboard(BaseModel):
    tree_level: int
    pending_medications: int
    recent_test_score: Optional[int]
    recent_medications: List[MedicationResponse]

# ==================== Generic Response ====================

class MessageResponse(BaseModel):
    message: str
    success: bool = True
    image_url: str = None  # Optional image URL for profile image uploads

class TreeLevelResponse(BaseModel):
    tree_level: int
    total_taken: int
    max_level: int = 10

# ==================== FCM Token Schema ====================
class FCMTokenRequest(BaseModel):
    fcm_token: str

# ==================== ML Prediction Schemas ====================

class RecoveryRecommendation(BaseModel):
    priority: str  # HIGH, MEDIUM, LOW
    category: str  # Medication Adherence, Treatment Plan, Recovery Trend, General
    recommendation: str
    impact: str

class FeatureImportance(BaseModel):
    medication_adherence: float
    avg_test_score: float
    test_score_trend: float
    days_in_treatment: float
    medication_count: float

class DataPoints(BaseModel):
    medication_adherence: float
    avg_test_score: float
    test_score_trend: float
    days_in_treatment: int
    medication_count: int

class RecoveryPredictionResponse(BaseModel):
    patient_id: int
    recovery_score: float
    score_percentage: str  # e.g., "85.3%"
    status: str  # EXCELLENT, GOOD, MODERATE, POOR, CRITICAL
    message: str
    confidence_level: str  # HIGH, MEDIUM, LOW
    recommendations: List[RecoveryRecommendation]
    data_points: DataPoints
    feature_importance: FeatureImportance
    predicted_at: datetime
    
    class Config:
        from_attributes = True