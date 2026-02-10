#!/usr/bin/env python
"""Test script to verify database setup"""

import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import engine, Base
from app.models.models import User, VerificationCode

print("🔍 Testing database setup...")

try:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # List tables
    inspector = __import__('sqlalchemy').inspect(engine)
    tables = inspector.get_table_names()
    print(f"✅ Tables in database: {tables}")
    
    # Check User table columns
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    print(f"✅ User table columns: {user_columns}")
    
    # Check VerificationCode table columns
    vc_columns = [col['name'] for col in inspector.get_columns('verification_codes')]
    print(f"✅ VerificationCode table columns: {vc_columns}")
    
    print("\n✅ Database setup is correct!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
