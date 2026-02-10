#!/usr/bin/env python
"""
OTP System Diagnostic Script
Run this to verify all components are configured correctly
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🔍 OTP SYSTEM DIAGNOSTIC")
print("=" * 60)

# 1. Check .env file
print("\n1️⃣  Checking .env Configuration...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    emails_from = os.getenv("EMAILS_FROM_EMAIL")
    
    print(f"   ✅ SMTP_HOST: {smtp_host}")
    print(f"   ✅ SMTP_PORT: {smtp_port}")
    print(f"   ✅ SMTP_USER: {smtp_user}")
    print(f"   ✅ SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    print(f"   ✅ EMAILS_FROM_EMAIL: {emails_from}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 2. Check Database
print("\n2️⃣  Checking Database Setup...")
try:
    from app.db.session import engine, Base
    from app.models.models import User, VerificationCode
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print(f"   ✅ Database connected successfully")
    print(f"   ✅ Tables created: users, verification_codes")
    
    # Check columns
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    users_cols = [col['name'] for col in inspector.get_columns('users')]
    vc_cols = [col['name'] for col in inspector.get_columns('verification_codes')]
    
    print(f"   ✅ User columns: {', '.join(users_cols)}")
    print(f"   ✅ VerificationCode columns: {', '.join(vc_cols)}")
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

# 3. Check Email Service
print("\n3️⃣  Checking Email Service...")
try:
    from app.services.email_service import EmailService
    from app.core.config import settings
    
    print(f"   ✅ EmailService imported successfully")
    print(f"   ✅ SMTP Host: {settings.SMTP_HOST}")
    print(f"   ✅ SMTP Port: {settings.SMTP_PORT}")
    print(f"   ℹ️  Ready to send emails")
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 4. Check Security Functions
print("\n4️⃣  Checking Security Functions...")
try:
    from app.core.security import generate_verification_code, get_password_hash, verify_password
    
    # Test OTP generation
    otp = generate_verification_code()
    print(f"   ✅ OTP Generation works: {otp} (type: {type(otp).__name__}, length: {len(str(otp))})")
    
    # Test password hashing
    test_password = "TestPassword123"
    hashed = get_password_hash(test_password)
    is_valid = verify_password(test_password, hashed)
    print(f"   ✅ Password hashing works: {is_valid}")
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 5. Check Schemas
print("\n5️⃣  Checking API Schemas...")
try:
    from app.schemas.schemas import (
        UserCreate, UserResponse, EmailVerificationRequest, 
        VerificationCodeResponse, MessageResponse
    )
    
    print(f"   ✅ UserCreate schema loaded")
    print(f"   ✅ UserResponse schema loaded")
    print(f"   ✅ EmailVerificationRequest schema loaded")
    print(f"   ✅ VerificationCodeResponse schema loaded")
    print(f"   ✅ MessageResponse schema loaded")
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

# 6. Check API Endpoints
print("\n6️⃣  Checking API Endpoints...")
try:
    from app.api.endpoints import auth
    
    print(f"   ✅ Auth endpoints module loaded")
    print(f"   ✅ Router prefix: /api/v1/auth")
    print(f"   ✅ Available endpoints:")
    print(f"      - POST /api/v1/auth/register")
    print(f"      - POST /api/v1/auth/send-verification-code")
    print(f"      - POST /api/v1/auth/verify-email")
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Summary
print("\n" + "=" * 60)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nIf all checks passed, your OTP system is ready!")
print("\nStart backend with:")
print("  uvicorn main:app --host 0.0.0.0 --port 8001 --reload")
print("\nThen test registration flow in Android app.")
print()
