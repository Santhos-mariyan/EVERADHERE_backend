from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.db.session import get_db
from app.models.models import User, VerificationCode, get_ist_now
from app.schemas.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    EmailVerificationRequest, PasswordResetRequest, PasswordResetConfirm,
    VerificationCodeResponse, MessageResponse
)
from app.core.security import (
    get_password_hash, verify_password, create_access_token, generate_verification_code
)
from app.services.email_service import EmailService

router = APIRouter()

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (doctor or patient) and send OTP verification code"""
    
    try:
        print(f"\n{'='*60}")
        print(f"📝 REGISTRATION REQUEST")
        print(f"{'='*60}")
        print(f"Email: {user.email}")
        print(f"Name: {user.name}")
        print(f"User Type: {user.user_type}")
        print(f"Contact Number: '{user.contact_number}' (type: {type(user.contact_number).__name__})")
        
        # Restrict to only one doctor registration (robust)
        if user.user_type.lower() == "doctor":
            # Check if any verified doctor already exists
            existing_doctor = db.query(User).filter(User.user_type == "doctor", User.is_verified == True).first()
            if existing_doctor:
                print(f"❌ Doctor already registered: {existing_doctor.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A doctor account already exists. Only one doctor can be registered."
                )
            # Clean up expired pending doctor registrations
            import json
            pending_doctor_codes = db.query(VerificationCode).filter(
                VerificationCode.purpose == "email_verification",
                VerificationCode.is_used == False,
                VerificationCode.data != None
            ).all()
            for v in pending_doctor_codes:
                try:
                    data = json.loads(v.data)
                    if data.get("user_type", "").lower() == "doctor":
                        expires_at = v.expires_at
                        if expires_at.tzinfo is None:
                            expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                        if expires_at < get_ist_now():
                            print(f"✅ Expired pending doctor registration found, deleting...")
                            db.delete(v)
                            db.commit()
                except Exception:
                    continue
            # Check if any valid (not expired) pending doctor registration exists
            valid_pending_doctor = db.query(VerificationCode).filter(
                VerificationCode.purpose == "email_verification",
                VerificationCode.is_used == False,
                VerificationCode.data != None
            ).all()
            for v in valid_pending_doctor:
                try:
                    data = json.loads(v.data)
                    if data.get("user_type", "").lower() == "doctor":
                        expires_at = v.expires_at
                        if expires_at.tzinfo is None:
                            expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                        if expires_at >= get_ist_now():
                            print(f"❌ Pending doctor registration already exists: {v.email}")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="A doctor registration is already in progress. Only one doctor can be registered."
                            )
                except Exception:
                    continue
        # Check if user already exists (by email)
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            print(f"❌ Email already registered: {user.email}")
            if user.user_type.lower() == "doctor":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A doctor account already exists. Only one doctor can be registered."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        # Check if there's already a pending registration for this email
        existing_pending = db.query(VerificationCode).filter(
            VerificationCode.email == user.email,
            VerificationCode.purpose == "email_verification",
            VerificationCode.is_used == False
        ).first()
        if existing_pending:
            # Check if the existing pending registration has expired
            expires_at = existing_pending.expires_at
            if expires_at.tzinfo is None:
                # If naive, make it aware with IST timezone
                expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            if expires_at < get_ist_now():
                # Expired, delete it and proceed with new registration
                print(f"✅ Previous pending registration expired, deleting and proceeding...")
                db.delete(existing_pending)
                db.commit()
            else:
                # Still valid, block registration
                print(f"❌ Pending registration already exists for: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration already in progress. Please check your email for the verification code."
                )
        
        print(f"✅ Starting registration process...")
        hashed_password = get_password_hash(user.password)
        
        # Handle contact_number - ensure it's not the string "None"
        contact = user.contact_number
        if contact == "None" or contact == "" or contact is None:
            contact = None
        
        print(f"✅ Contact after processing: '{contact}' (type: {type(contact).__name__})")
        
        # Prepare user data for storage
        import json
        user_data = {
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "email": user.email,
            "password": hashed_password,
            "location": user.location,
            "user_type": user.user_type,
            "contact_number": contact
        }
        
        # Generate verification code (OTP)
        print(f"✅ Generating OTP...")
        otp_code = generate_verification_code()
        print(f"✅ OTP Generated: {otp_code}")
        
        # Delete any old pending registrations for this email
        deleted_count = db.query(VerificationCode).filter(
            VerificationCode.email == user.email,
            VerificationCode.purpose == "email_verification"
        ).delete()
        if deleted_count > 0:
            print(f"✅ Deleted {deleted_count} old pending registrations")
        
        verification = VerificationCode(
            email=user.email,
            code=otp_code,
            purpose="email_verification",
            expires_at=get_ist_now() + timedelta(minutes=15),
            data=json.dumps(user_data)
        )
        db.add(verification)
        db.commit()
        print(f"✅ Registration data stored temporarily")
        
        # Send OTP email
        print(f"📧 Sending OTP email to {user.email}...")
        email_result = EmailService.send_otp_email(
            email=user.email,
            otp_code=otp_code,
            purpose="email_verification"
        )
        
        if email_result:
            print(f"✅ Email sent successfully!")
        else:
            print(f"⚠️ Warning: Email sending may have failed, but registration stored. Code: {otp_code}")
        
        print(f"{'='*60}")
        print(f"✅ REGISTRATION INITIATED - AWAITING VERIFICATION")
        print(f"{'='*60}\n")
        
        return MessageResponse(message=f"Registration initiated. Please check your email for the verification code. Valid for 15 minutes.")
    
    except HTTPException as http_ex:
        print(f"❌ HTTP Exception: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/send-verification-code", response_model=VerificationCodeResponse)
def send_verification_code(email: str, db: Session = Depends(get_db)):
    """Send or resend verification OTP code to email"""
    
    print(f"\n{'='*60}")
    print(f"📨 RESEND OTP REQUEST")
    print(f"{'='*60}")
    print(f"Email: {email}")
    
    # Check if user is already verified
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user and existing_user.is_verified:
        print(f"❌ User already verified: {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Look for pending registration
    pending_registration = db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.purpose == "email_verification",
        VerificationCode.is_used == False
    ).first()
    
    if not pending_registration or not pending_registration.data:
        print(f"❌ No pending registration found for: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending registration found. Please register first."
        )
    
    print(f"✅ Pending registration found")
    
    # Generate new verification code (OTP)
    otp_code = generate_verification_code()
    print(f"✅ New OTP Generated: {otp_code}")
    
    # Delete old codes for this email
    deleted_count = db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.purpose == "email_verification"
    ).delete()
    print(f"✅ Deleted {deleted_count} old OTP codes")
    
    # Create new verification code with the same data
    verification = VerificationCode(
        email=email,
        code=otp_code,
        purpose="email_verification",
        expires_at=get_ist_now() + timedelta(minutes=15),
        data=pending_registration.data  # Keep the same registration data
    )
    db.add(verification)
    db.commit()
    print(f"✅ New OTP saved to database")
    
    # Send OTP email
    print(f"📧 Sending OTP email...")
    email_sent = EmailService.send_otp_email(
        email=email,
        otp_code=otp_code,
        purpose="email_verification"
    )
    
    print(f"{'='*60}\n")
    
    if email_sent:
        return VerificationCodeResponse(
            code="",
            message=f"Verification OTP sent to {email}. Valid for 15 minutes."
        )
    else:
        print(f"❌ Failed to send verification email to {email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code. Please try again later."
        )

@router.post("/verify-email", response_model=MessageResponse)
def verify_email(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Verify user email with code and complete registration"""
    
    print(f"\n{'='*60}")
    print(f"✔️  EMAIL VERIFICATION REQUEST")
    print(f"{'='*60}")
    print(f"Email: {request.email}")
    print(f"Code: {request.code}")
    
    # Find verification code
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.code == request.code,
        VerificationCode.purpose == "email_verification",
        VerificationCode.is_used == False
    ).first()
    
    if not verification:
        print(f"❌ Verification code not found or already used")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    print(f"✅ Verification code found")
    
    # Check if code is expired
    # Handle timezone-aware/naive datetime comparison
    expires_at = verification.expires_at
    if expires_at.tzinfo is None:
        # If naive, make it aware with IST timezone
        expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    
    if expires_at < get_ist_now():
        print(f"❌ Verification code expired")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    
    print(f"✅ Code is not expired")
    
    # Check if user data exists in verification record
    if not verification.data:
        print(f"❌ No registration data found in verification record")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration data not found. Please register again."
        )
    try:
        import json
        user_data = json.loads(verification.data)
        print(f"✅ Registration data loaded")
    except json.JSONDecodeError:
        print(f"❌ Invalid registration data format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid registration data. Please register again."
        )
    # Enforce only one doctor registration (robust)
    if user_data.get("user_type", "").lower() == "doctor":
        # Check if any verified doctor already exists
        existing_doctor = db.query(User).filter(User.user_type == "doctor", User.is_verified == True).first()
        if existing_doctor:
            print(f"❌ Doctor already registered: {existing_doctor.email}")
            verification.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A doctor account already exists. Only one doctor can be registered."
            )
        # Clean up expired pending doctor registrations (other than this one)
        import json
        pending_doctor_codes = db.query(VerificationCode).filter(
            VerificationCode.purpose == "email_verification",
            VerificationCode.is_used == False,
            VerificationCode.data != None,
            VerificationCode.email != request.email
        ).all()
        for v in pending_doctor_codes:
            try:
                data = json.loads(v.data)
                if data.get("user_type", "").lower() == "doctor":
                    expires_at = v.expires_at
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                    if expires_at < get_ist_now():
                        print(f"✅ Expired pending doctor registration found, deleting...")
                        db.delete(v)
                        db.commit()
            except Exception:
                continue
        # Check if any valid (not expired) pending doctor registration exists (other than this one)
        valid_pending_doctor = db.query(VerificationCode).filter(
            VerificationCode.purpose == "email_verification",
            VerificationCode.is_used == False,
            VerificationCode.data != None,
            VerificationCode.email != request.email
        ).all()
        for v in valid_pending_doctor:
            try:
                data = json.loads(v.data)
                if data.get("user_type", "").lower() == "doctor":
                    expires_at = v.expires_at
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                    if expires_at >= get_ist_now():
                        print(f"❌ Another pending doctor registration exists: {v.email}")
                        verification.is_used = True
                        db.commit()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A doctor registration is already in progress. Only one doctor can be registered."
                        )
            except Exception:
                continue
    # Check if user already exists (in case of race condition)
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        print(f"❌ User already exists")
        verification.is_used = True
        db.commit()
        # Always show the doctor message if this is a doctor registration
        if user_data.get("user_type", "").lower() == "doctor":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A doctor account already exists. Only one doctor can be registered."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    # Create the user
    print(f"✅ Creating verified user...")
    db_user = User(
        name=user_data["name"],
        age=user_data["age"],
        gender=user_data["gender"],
        email=user_data["email"],
        password=user_data["password"],
        location=user_data["location"],
        user_type=user_data["user_type"],
        contact_number=user_data["contact_number"],
        is_verified=True
    )
    db.add(db_user)
    verification.is_used = True
    db.commit()
    db.refresh(db_user)
    print(f"✅ User created with ID: {db_user.id}")
    print(f"✅ User marked as verified")
    print(f"{'='*60}\n")
    return MessageResponse(message="Email verified successfully. Registration complete!")

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": user.user_type}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        user_type=user.user_type,
        email=user.email,
        name=user.name
    )

@router.post("/forgot-password", response_model=VerificationCodeResponse)
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send password reset OTP code to email"""
    
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate reset code (OTP)
    otp_code = generate_verification_code()
    
    # Delete old reset codes for this email
    db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.purpose == "password_reset"
    ).delete()
    
    # Create new reset code
    verification = VerificationCode(
        email=request.email,
        code=otp_code,
        purpose="password_reset",
        expires_at=get_ist_now() + timedelta(minutes=15)
    )
    db.add(verification)
    db.commit()
    
    # Send password reset OTP email
    email_sent = EmailService.send_otp_email(
        email=request.email,
        otp_code=otp_code,
        purpose="password_reset"
    )
    
    return VerificationCodeResponse(
        code=otp_code if not email_sent else "",
        message=f"Password reset OTP sent to {request.email}. Valid for 15 minutes." if email_sent else "Failed to send reset code. Please try again."
    )

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password with verification code"""
    
    # Find verification code
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.code == request.code,
        VerificationCode.purpose == "password_reset",
        VerificationCode.is_used == False
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # Check if code is expired
    # Handle timezone-aware/naive datetime comparison
    expires_at = verification.expires_at
    if expires_at.tzinfo is None:
        # If naive, make it aware with IST timezone
        expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    
    if expires_at < get_ist_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired"
        )
    
    # Update password
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password = get_password_hash(request.new_password)
    verification.is_used = True
    
    db.commit()
    
    return MessageResponse(message="Password reset successfully")
