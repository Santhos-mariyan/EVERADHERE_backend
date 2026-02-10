from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from zoneinfo import ZoneInfo
from app.db.session import Base

# Helper function to get current IST time
def get_ist_now():
    """Returns current time in IST timezone"""
    return datetime.now(tz=ZoneInfo("Asia/Kolkata"))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    location = Column(String, nullable=False)
    user_type = Column(String, nullable=False)  # 'doctor' or 'patient'
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_ist_now)
    fcm_token = Column(String, nullable=True)  # Firebase Cloud Messaging token for push notifications
    profile_image = Column(String, nullable=True)  # Profile image file path
    contact_number = Column(Text, nullable=True)  # User's contact number
    last_reset_date = Column(DateTime, nullable=True)  # Last time medications were reset (tracks daily reset)
    user_timezone = Column(String, default="Asia/Kolkata")  # User's timezone (IST by default)


    # Relationships
    prescribed_medications = relationship(
        "Medication",
        foreign_keys="Medication.doctor_id",
        back_populates="doctor",
        lazy="select",
        cascade="all, delete-orphan"
    )
    received_medications = relationship(
        "Medication",
        foreign_keys="Medication.patient_id",
        back_populates="patient",
        lazy="select",
        cascade="all, delete-orphan"
    )
    test_results = relationship(
        "TestResult",
        back_populates="patient",
        lazy="select",
        cascade="all, delete-orphan"
    )
    uploaded_videos = relationship(
        "Video",
        back_populates="uploader",
        lazy="select",
        cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan"
    )


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    instructions = Column(Text)
    is_taken = Column(Boolean, default=False)
    prescribed_date = Column(DateTime, default=get_ist_now)
    taken_date = Column(DateTime, nullable=True)  # When the medication was marked as taken

    # Relationships
    patient = relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="received_medications"
    )
    doctor = relationship(
        "User",
        foreign_keys=[doctor_id],
        back_populates="prescribed_medications"
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_name = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    notes = Column(Text)
    date = Column(DateTime, default=get_ist_now)

    # Relationships
    patient = relationship(
        "User",
        back_populates="test_results"
    )


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_date = Column(DateTime, default=get_ist_now)

    # Relationships
    uploader = relationship(
        "User",
        back_populates="uploaded_videos"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    date = Column(DateTime, default=get_ist_now)

    # Relationships
    user = relationship(
        "User",
        back_populates="notifications"
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    time = Column(String, nullable=False)  # stored as 12-hour string like "08:30"
    am_pm = Column(String, nullable=False)  # 'AM' or 'PM'
    frequency = Column(String, nullable=False)  # 'daily', 'weekly', 'monthly'
    next_run = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_ist_now)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)

    user = relationship("User")


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    purpose = Column(String, nullable=False)  # 'email_verification' or 'password_reset'
    created_at = Column(DateTime, default=get_ist_now)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    data = Column(Text, nullable=True)  # JSON data for pending registrations
