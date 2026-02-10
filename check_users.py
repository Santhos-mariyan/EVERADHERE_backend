"""
Check database users
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from app.db.session import SessionLocal
from app.models.models import User

db = SessionLocal()
users = db.query(User).all()

print("\n===== USERS IN DATABASE =====")
print(f"Total users: {len(users)}\n")

for user in users:
    print(f"ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Name: {user.name}")
    print(f"User Type: {user.user_type}")
    print(f"Password: {user.password[:10]}..." if user.password else "NO password")
    print(f"FCM Token: {user.fcm_token[:30] + '...' if user.fcm_token else 'NONE (need to login on Android)'}")
    print("---")

db.close()
print("\nUse these credentials to login on your Android device!")
