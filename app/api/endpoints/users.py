from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import (
    UserResponse,
    UserUpdate,
    MessageResponse,
    FCMTokenRequest,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current logged-in user's profile"""
    
    print(f"\n{'='*60}")
    print(f"📋 GET PROFILE REQUEST")
    print(f"{'='*60}")
    print(f"User: {current_user.name} (ID: {current_user.id})")
    print(f"Contact in DB: '{current_user.contact_number}' (type: {type(current_user.contact_number).__name__})")
    
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    
    print(f"\n{'='*60}")
    print(f"📝 PROFILE UPDATE REQUEST")
    print(f"{'='*60}")
    print(f"Contact Number received: '{user_update.contact_number}' (type: {type(user_update.contact_number).__name__})")

    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.age is not None:
        current_user.age = user_update.age
    if user_update.gender is not None:
        current_user.gender = user_update.gender
    if user_update.location is not None:
        current_user.location = user_update.location
    if user_update.contact_number is not None:
        # Handle contact_number - ensure it's not the string "None"
        contact = user_update.contact_number
        if contact == "None" or contact == "":
            contact = None
        
        print(f"✅ Updating contact_number to: '{contact}'")
        current_user.contact_number = contact

    db.commit()
    db.refresh(current_user)
    
    print(f"✅ Profile updated, saved contact: '{current_user.contact_number}'")

    return current_user


@router.get("/patients/all", response_model=List[UserResponse])
def get_all_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all patients (only for doctors)"""

    if current_user.user_type != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access patient list"
        )

    patients = db.query(User).filter(User.user_type == "patient").all()
    return patients


@router.delete("/me", response_model=MessageResponse)
def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete current user account"""

    db.delete(current_user)
    db.commit()

    return MessageResponse(message="Account deleted successfully")


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user by ID (only doctors can delete patients)"""
    
    # Only doctors can delete users
    if current_user.user_type != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can delete users"
        )
    
    # Get the user to delete
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Can only delete patients
    if user_to_delete.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete patient accounts"
        )
    
    try:
        # Delete any profile image if it exists
        if user_to_delete.profile_image:
            from pathlib import Path
            image_path = Path("uploaded_profile_images") / user_to_delete.profile_image
            if image_path.exists():
                image_path.unlink()
        
        db.delete(user_to_delete)
        db.commit()
        
        return MessageResponse(message=f"Patient {user_to_delete.name} and their account have been deleted successfully")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )


# ==================== 🔔 FCM TOKEN (NEW & REQUIRED) ====================

@router.post("/fcm-token", response_model=MessageResponse)
def save_fcm_token(
    fcm_request: FCMTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save or update the FCM (Firebase Cloud Messaging) token for the current user.
    This token is used to send push notifications to the patient's mobile device.
    The Android app should call this endpoint after receiving the FCM token from Firebase.
    
    FULLY WORKING VERSION - Includes detailed logging
    """
    
    if not fcm_request.fcm_token or not fcm_request.fcm_token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FCM token cannot be empty"
        )
    
    try:
        from app.services import firebase_service
        import logging
        
        logger = logging.getLogger(__name__)
        fcm_token = fcm_request.fcm_token.strip()
        
        logger.info(f"📱 Saving FCM token for user: {current_user.name} (ID: {current_user.id}, Type: {current_user.user_type})")
        logger.info(f"   Token: {fcm_token[:40]}...")
        
        # Check Firebase status
        firebase_status = firebase_service.get_firebase_status()
        if firebase_status.get("error"):
            logger.warning(f"⚠️  Firebase not ready: {firebase_status.get('error')}")
        else:
            logger.info(f"✅ Firebase is ready for push notifications")
        
        current_user.fcm_token = fcm_token
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"✅ FCM token saved successfully for {current_user.name}")
        
        return MessageResponse(
            message=f"FCM token saved successfully. Push notifications enabled for {current_user.name}."
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to save FCM token: {str(e)}")
        logger.exception(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save FCM token: {str(e)}"
        )


@router.get("/fcm-status")
def get_fcm_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get FCM (Firebase Cloud Messaging) status for debugging.
    Shows if Firebase is initialized and current user's FCM token status.
    """
    from app.services import firebase_service
    import logging
    
    logger = logging.getLogger(__name__)
    
    firebase_status = firebase_service.get_firebase_status()
    
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "type": current_user.user_type,
            "fcm_token": current_user.fcm_token[:40] + "..." if current_user.fcm_token else None,
            "has_fcm_token": bool(current_user.fcm_token)
        },
        "firebase": {
            "initialized": firebase_status.get("initialized"),
            "error": firebase_status.get("error")
        },
        "message": "✅ Ready for push notifications" if (firebase_status.get("initialized") and current_user.fcm_token) else "⚠️  Push notifications not available"
    }


@router.post("/test-notification")
def test_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a test push notification to the current user's device.
    Useful for debugging and verifying FCM setup.
    """
    from app.services import firebase_service
    import logging
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"🧪 Test notification requested by {current_user.name} (ID: {current_user.id})")
    
    if not current_user.fcm_token:
        logger.warning(f"⚠️  {current_user.name} has no FCM token saved")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No FCM token saved for your account. Please log in on your mobile device first."
        )
    
    # Send test notification
    result = firebase_service.send_push_notification(
        fcm_token=current_user.fcm_token,
        title="🧪 Test Notification",
        body=f"Hello {current_user.name}! This is a test notification from PhysioClinic.",
        data={
            "type": "test",
            "user_id": str(current_user.id),
            "timestamp": str(int(__import__('time').time()))
        }
    )
    
    if result.get("success"):
        logger.info(f"✅ Test notification sent successfully to {current_user.name}")
        return {
            "success": True,
            "message": "Test notification sent successfully!",
            "message_id": result.get("message_id")
        }
    else:
        logger.error(f"❌ Test notification failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {result.get('error')}"
        )


# ==================== 📷 PROFILE IMAGE ENDPOINTS ====================

@router.post("/me/profile-image", response_model=MessageResponse)
def upload_profile_image(
    profile_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a profile image for the current user.
    Accepts JPEG and PNG images.
    """
    import os
    import shutil
    from pathlib import Path
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if profile_image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are allowed"
        )
    
    # Validate file size (max 5MB)
    max_file_size = 5 * 1024 * 1024  # 5MB
    content = profile_image.file.read()
    if len(content) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )
    
    try:
        # Create profile images directory
        upload_dir = Path("uploaded_profile_images")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Delete old profile image if exists
        if current_user.profile_image:
            old_image_path = Path(current_user.profile_image)
            if old_image_path.exists():
                old_image_path.unlink()
                logger.info(f"Deleted old profile image: {current_user.profile_image}")
        
        # Save new image with user_id as filename
        file_extension = profile_image.filename.split(".")[-1]
        filename = f"user_{current_user.id}.{file_extension}"
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Update user's profile_image field with ONLY the filename (not the full path)
        current_user.profile_image = filename
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"✅ Profile image uploaded for user {current_user.name} (ID: {current_user.id})")
        
        # Return the image URL so app can display it
        image_url = f"http://192.168.137.1:8001/profile-images/{filename}"
        return MessageResponse(
            message="Profile image uploaded successfully",
            image_url=image_url
        )
        
    except Exception as e:
        logger.error(f"❌ Error uploading profile image: {str(e)}")
        logger.exception(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading profile image: {str(e)}"
        )


@router.delete("/me/profile-image", response_model=MessageResponse)
def delete_profile_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete the profile image for the current user.
    """
    from pathlib import Path
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        if current_user.profile_image:
            image_path = Path(current_user.profile_image)
            if image_path.exists():
                image_path.unlink()
                logger.info(f"Deleted profile image: {current_user.profile_image}")
            
            current_user.profile_image = None
            db.commit()
            db.refresh(current_user)
            
            logger.info(f"✅ Profile image deleted for user {current_user.name} (ID: {current_user.id})")
            return MessageResponse(message="Profile image deleted successfully")
        else:
            return MessageResponse(message="No profile image to delete")
            
    except Exception as e:
        logger.error(f"❌ Error deleting profile image: {str(e)}")
        logger.exception(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting profile image: {str(e)}"
        )

