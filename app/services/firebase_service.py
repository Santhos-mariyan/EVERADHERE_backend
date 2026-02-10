"""
Firebase Cloud Messaging (FCM) service for sending push notifications to mobile devices.
This service uses the Firebase Admin SDK to send push notifications to patients when doctors
prescribe medications or other important events occur.

FULLY WORKING VERSION - Handles all edge cases and provides debugging info
"""

import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Firebase Admin SDK initialization
_firebase_initialized = False
_firebase_error = None
_firebase_app = None

def init_firebase():
    """Initialize Firebase Admin SDK once on startup - ROBUST VERSION"""
    global _firebase_initialized, _firebase_error, _firebase_app
    
    if _firebase_initialized:
        logger.info("Firebase already initialized")
        return True
    
    try:
        # Try multiple paths for the service account key
        possible_paths = [
            Path(__file__).parent.parent / "firebase" / "serviceAccountKey.json",
            Path("app") / "firebase" / "serviceAccountKey.json",
            Path("serviceAccountKey.json"),
        ]
        
        firebase_key_path = None
        for path in possible_paths:
            if path.exists():
                firebase_key_path = path
                logger.info(f"Found Firebase key at: {path}")
                break
        
        if not firebase_key_path:
            _firebase_error = f"Firebase service account key not found. Tried: {[str(p) for p in possible_paths]}"
            logger.error(_firebase_error)
            logger.error("⚠️  FIREBASE NOT INITIALIZED - Push notifications will not work")
            logger.error("Please place serviceAccountKey.json in app/firebase/ directory")
            return False
        
        # Read and validate the JSON file
        with open(firebase_key_path, 'r') as f:
            service_account = json.load(f)
        
        # Initialize Firebase Admin SDK with the service account
        cred = credentials.Certificate(service_account)
        
        # Check if Firebase app is already initialized
        try:
            _firebase_app = firebase_admin.get_app()
            logger.info("Using existing Firebase app instance")
        except ValueError:
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized successfully")
        
        _firebase_initialized = True
        logger.info(f"Firebase initialized with project: {service_account.get('project_id', 'unknown')}")
        return True
        
    except json.JSONDecodeError as e:
        _firebase_error = f"Invalid JSON in serviceAccountKey.json: {str(e)}"
        logger.error(_firebase_error)
        return False
    except FileNotFoundError as e:
        _firebase_error = f"Service account key file not found: {str(e)}"
        logger.error(_firebase_error)
        return False
    except Exception as e:
        _firebase_error = f"Failed to initialize Firebase: {str(e)}"
        logger.error(_firebase_error)
        logger.exception(e)  # Log full exception traceback
        return False


def is_firebase_initialized():
    """Check if Firebase is properly initialized"""
    return _firebase_initialized


def get_firebase_status():
    """Get Firebase initialization status and any errors"""
    return {
        "initialized": _firebase_initialized,
        "error": _firebase_error
    }


def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """
    Send a push notification via Firebase Cloud Messaging (FCM).
    
    Args:
        fcm_token: Device FCM token (obtained from Android client)
        title: Notification title (max 65 characters)
        body: Notification body/message (max 240 characters)
        data: Optional dictionary of additional data to send with the notification
    
    Returns:
        dict: {"success": True, "message_id": "...", "timestamp": "..."} or 
              {"success": False, "error": "..."}
    """
    
    result = {
        "success": False,
        "timestamp": datetime.utcnow().isoformat(),
        "token": fcm_token[:20] + "..." if fcm_token else "None"  # Log token prefix for debugging
    }
    
    # Validate FCM token
    if not fcm_token or not str(fcm_token).strip():
        result["error"] = "No FCM token provided"
        logger.warning(f"⚠️  Cannot send notification: {result['error']}")
        return result
    
    # Check if Firebase is initialized
    if not _firebase_initialized:
        logger.warning("Firebase not initialized, attempting initialization...")
        if not init_firebase():
            result["error"] = f"Firebase not initialized: {_firebase_error}"
            logger.error(f"❌ {result['error']}")
            return result
    
    try:
        # Validate and truncate title and body
        title = str(title).strip()[:65]
        body = str(body).strip()[:240]
        
        if not title or not body:
            result["error"] = "Title and body cannot be empty"
            logger.warning(f"⚠️  {result['error']}")
            return result
        
        # Build the notification message
        notification = messaging.Notification(
            title=title,
            body=body,
        )
        
        # Build the message data
        message_data = {}
        if data:
            # Convert all data values to strings (FCM requirement)
            for key, value in data.items():
                message_data[key] = str(value)
        
        # Add timestamp to data
        message_data["timestamp"] = str(int(datetime.utcnow().timestamp()))
        message_data["sent_by"] = "physioclinic_backend"
        
        # Create and send message
        message = messaging.Message(
            notification=notification,
            data=message_data,
            token=str(fcm_token).strip(),
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    click_action="FLUTTER_NOTIFICATION_CLICK",
                    sound="default",
                    channel_id="high_importance_channel",
                ),
            ),
        )
        
        # Send the message
        response = messaging.send(message)
        
        result["success"] = True
        result["message_id"] = response
        result["title"] = title
        result["body"] = body
        
        logger.info(f"✅ Successfully sent push notification. Message ID: {response}")
        logger.info(f"   Title: {title}")
        logger.info(f"   Body: {body}")
        logger.info(f"   Token: {fcm_token[:20]}...")
        
        return result

    except ValueError as e:
        # Firebase SDK raises ValueError for various FCM errors including sender ID mismatch
        error_msg = str(e)
        
        if "Sender ID" in error_msg or "sender id" in error_msg.lower():
            result["error"] = f"FCM token is from a different Firebase project. Patient needs to log in again."
            logger.warning(f"⚠️  {result['error']}")
            logger.warning(f"   This happens when switching Firebase projects - existing tokens become invalid")
            logger.warning(f"   Solution: Patient should log in again on their Android device")
        elif "registration" in error_msg.lower():
            result["error"] = f"FCM token is invalid or unregistered"
            logger.warning(f"⚠️  {result['error']}")
        else:
            result["error"] = f"FCM error: {error_msg}"
            logger.error(f"❌ {result['error']}")
        
        return result
        
    except Exception as e:
        # Catch all other exceptions
        error_msg = str(e)
        error_type = type(e).__name__
        
        if "403" in error_msg or "unauthorized" in error_msg.lower():
            result["error"] = f"Firebase API authorization failed (403). Check credentials."
            logger.error(f"❌ {result['error']}")
        elif "400" in error_msg or "invalid" in error_msg.lower():
            result["error"] = f"Invalid request to Firebase API. Error: {error_msg}"
            logger.error(f"❌ {result['error']}")
        elif "timeout" in error_msg.lower():
            result["error"] = f"Request to Firebase timed out"
            logger.error(f"❌ {result['error']}")
        else:
            result["error"] = f"Error sending notification ({error_type}): {error_msg}"
            logger.error(f"❌ {result['error']}")
        
        logger.exception(e)  # Log full traceback
        return result

def send_medication_prescribed_notification(patient_fcm_token: str, doctor_name: str, medications: list):
    """
    Send a notification when a doctor prescribes medications to a patient.
    
    Args:
        patient_fcm_token: Patient's FCM token
        doctor_name: Name of the doctor who prescribed the medication
        medications: List of medication names prescribed
    
    Returns:
        dict: Result dictionary with success status and details
    """
    
    try:
        # Validate inputs
        if not patient_fcm_token:
            logger.error("❌ Cannot send medication notification: No patient FCM token")
            return {"success": False, "error": "No patient FCM token provided"}
        
        if not doctor_name:
            doctor_name = "Your Doctor"
        
        if not medications or len(medications) == 0:
            medications = ["new medications"]
        
        # Build medication text
        if len(medications) == 1:
            med_text = f"'{medications[0]}'"
        elif len(medications) == 2:
            med_text = f"'{medications[0]}' and '{medications[1]}'"
        else:
            med_text = f"{len(medications)} new medications"
        
        title = "💊 New Medication Prescribed"
        body = f"Dr. {doctor_name} prescribed {med_text}"
        
        # Prepare data payload
        data = {
            "type": "medication_prescribed",
            "doctor_name": doctor_name,
            "medication_count": str(len(medications)),
            "medications": ",".join(medications[:5]),  # Limit to 5 for data payload
            "action": "open_medications"
        }
        
        logger.info(f"📤 Sending medication notification to patient...")
        logger.info(f"   Doctor: {doctor_name}")
        logger.info(f"   Medications: {med_text}")
        
        return send_push_notification(
            fcm_token=patient_fcm_token,
            title=title,
            body=body,
            data=data
        )
        
    except Exception as e:
        error_msg = f"Error sending medication notification: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.exception(e)
        return {"success": False, "error": error_msg}

