from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.models import VerificationCode, User
from app.core.security import generate_verification_code
from app.services.email_service import EmailService
from typing import Tuple, Optional

class OTPService:
    """Service for handling OTP generation, sending, and verification"""
    
    @staticmethod
    def generate_and_send_otp(
        email: str,
        purpose: str,
        db: Session,
        user_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Generate OTP and send via email
        
        Args:
            email: User email
            purpose: 'email_verification' or 'password_reset'
            db: Database session
            user_name: User's name (optional)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Generate OTP
            otp_code = generate_verification_code()
            
            # Delete old codes for this email and purpose
            db.query(VerificationCode).filter(
                VerificationCode.email == email,
                VerificationCode.purpose == purpose
            ).delete()
            
            # Create new verification code
            verification = VerificationCode(
                email=email,
                code=otp_code,
                purpose=purpose,
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            db.add(verification)
            db.commit()
            
            # Send OTP email
            email_sent = EmailService.send_otp_email(
                email=email,
                otp_code=otp_code,
                purpose=purpose
            )
            
            if email_sent:
                return True, f"OTP sent to {email}. Valid for 15 minutes."
            else:
                return False, "Failed to send OTP. Please try again."
                
        except Exception as e:
            db.rollback()
            return False, f"Error sending OTP: {str(e)}"
    
    @staticmethod
    def verify_otp(
        email: str,
        otp_code: str,
        purpose: str,
        db: Session
    ) -> Tuple[bool, str]:
        """
        Verify OTP code
        
        Args:
            email: User email
            otp_code: OTP code entered by user
            purpose: 'email_verification' or 'password_reset'
            db: Database session
        
        Returns:
            Tuple[bool, str]: (valid, message)
        """
        try:
            # Find verification code
            verification = db.query(VerificationCode).filter(
                VerificationCode.email == email,
                VerificationCode.code == otp_code,
                VerificationCode.purpose == purpose,
                VerificationCode.is_used == False
            ).first()
            
            if not verification:
                return False, "Invalid OTP code"
            
            # Check if code is expired
            if verification.expires_at < datetime.utcnow():
                db.delete(verification)
                db.commit()
                return False, "OTP has expired. Please request a new one."
            
            return True, "OTP verified successfully"
            
        except Exception as e:
            return False, f"Error verifying OTP: {str(e)}"
    
    @staticmethod
    def mark_otp_as_used(
        email: str,
        otp_code: str,
        purpose: str,
        db: Session
    ) -> bool:
        """
        Mark OTP as used after successful verification
        
        Args:
            email: User email
            otp_code: OTP code
            purpose: 'email_verification' or 'password_reset'
            db: Database session
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            verification = db.query(VerificationCode).filter(
                VerificationCode.email == email,
                VerificationCode.code == otp_code,
                VerificationCode.purpose == purpose,
                VerificationCode.is_used == False
            ).first()
            
            if verification:
                verification.is_used = True
                db.commit()
                return True
            return False
            
        except Exception as e:
            db.rollback()
            return False
    
    @staticmethod
    def resend_otp(
        email: str,
        purpose: str,
        db: Session
    ) -> Tuple[bool, str]:
        """
        Resend OTP to user
        
        Args:
            email: User email
            purpose: 'email_verification' or 'password_reset'
            db: Database session
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False, "User not found"
        
        # Generate and send new OTP
        return OTPService.generate_and_send_otp(
            email=email,
            purpose=purpose,
            db=db,
            user_name=user.name
        )
    
    @staticmethod
    def verify_email_with_otp(
        email: str,
        otp_code: str,
        db: Session
    ) -> Tuple[bool, str]:
        """
        Complete email verification using OTP
        
        Args:
            email: User email
            otp_code: OTP code
            db: Database session
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Verify OTP
            is_valid, message = OTPService.verify_otp(
                email=email,
                otp_code=otp_code,
                purpose="email_verification",
                db=db
            )
            
            if not is_valid:
                return False, message
            
            # Find user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False, "User not found"
            
            # Mark email as verified
            user.is_verified = True
            OTPService.mark_otp_as_used(
                email=email,
                otp_code=otp_code,
                purpose="email_verification",
                db=db
            )
            
            db.commit()
            return True, "Email verified successfully"
            
        except Exception as e:
            db.rollback()
            return False, f"Error verifying email: {str(e)}"
    
    @staticmethod
    def reset_password_with_otp(
        email: str,
        otp_code: str,
        new_password: str,
        db: Session,
        password_hasher
    ) -> Tuple[bool, str]:
        """
        Reset password using OTP
        
        Args:
            email: User email
            otp_code: OTP code
            new_password: New password (will be hashed)
            db: Database session
            password_hasher: Function to hash password
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Verify OTP
            is_valid, message = OTPService.verify_otp(
                email=email,
                otp_code=otp_code,
                purpose="password_reset",
                db=db
            )
            
            if not is_valid:
                return False, message
            
            # Find user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False, "User not found"
            
            # Update password
            user.password = password_hasher(new_password)
            OTPService.mark_otp_as_used(
                email=email,
                otp_code=otp_code,
                purpose="password_reset",
                db=db
            )
            
            db.commit()
            return True, "Password reset successfully"
            
        except Exception as e:
            db.rollback()
            return False, f"Error resetting password: {str(e)}"
