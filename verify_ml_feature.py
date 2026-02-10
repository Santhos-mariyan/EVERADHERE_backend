#!/usr/bin/env python
"""
Quick verification script for ML Recovery Prediction feature
Run this to verify all components are properly installed
"""

import sys
import os

def check_backend_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Backend Dependencies...")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'sqlalchemy': 'SQLAlchemy',
        'sklearn': 'scikit-learn',
        'scipy': 'scipy',
        'pydantic': 'Pydantic'
    }
    
    all_ok = True
    for package_name, display_name in required_packages.items():
        try:
            __import__(package_name)
            print(f"  ✅ {display_name}")
        except ImportError:
            print(f"  ❌ {display_name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_backend_files():
    """Check if all backend files are created"""
    print("\n📁 Checking Backend Files...")
    
    backend_dir = "physioclinic-backend/physioclinic-backend"
    required_files = [
        "app/services/ml_prediction_service.py",
        "app/api/endpoints/predictions.py",
        "ML_RECOVERY_PREDICTION_GUIDE.md"
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = os.path.join(backend_dir, file_path)
        if os.path.exists(full_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_ok = False
    
    return all_ok

def check_android_files():
    """Check if all Android files are created"""
    print("\n📱 Checking Android Files...")
    
    android_dir = "PhysiotherapistClinic - final FE/PhysiotherapistClinic - final FE/PhysiotherapistClinic - final FE"
    required_files = [
        "app/src/main/java/com/physioclinic/app/activities/PatientRecoveryActivity.java",
        "app/src/main/java/com/physioclinic/app/adapters/RecoveryRecommendationAdapter.java",
        "app/src/main/java/com/physioclinic/app/response/RecoveryPredictionResponse.java",
        "app/src/main/java/com/physioclinic/app/response/PatientsRecoverySummaryResponse.java",
        "app/src/main/res/layout/activity_patient_recovery.xml",
        "app/src/main/res/layout/item_recovery_recommendation.xml"
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = os.path.join(android_dir, file_path)
        if os.path.exists(full_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_ok = False
    
    return all_ok

def check_api_endpoints():
    """Check if API endpoints are registered"""
    print("\n🔌 Checking API Endpoints...")
    
    backend_dir = "physioclinic-backend/physioclinic-backend"
    main_py_path = os.path.join(backend_dir, "main.py")
    
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r') as f:
            content = f.read()
            
        checks = {
            "predictions import": "from app.api.endpoints import" in content and "predictions" in content,
            "predictions router": "app.include_router(predictions.router" in content
        }
        
        for check_name, result in checks.items():
            if result:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - NOT FOUND")
    else:
        print(f"  ❌ main.py not found")

def check_requirements():
    """Check if requirements.txt has ML packages"""
    print("\n📝 Checking Requirements...")
    
    backend_dir = "physioclinic-backend/physioclinic-backend"
    requirements_path = os.path.join(backend_dir, "requirements.txt")
    
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        packages = {
            "scikit-learn": "scikit-learn" in content,
            "scipy": "scipy" in content
        }
        
        for package_name, found in packages.items():
            if found:
                print(f"  ✅ {package_name}")
            else:
                print(f"  ❌ {package_name} - NOT IN REQUIREMENTS")
    else:
        print(f"  ❌ requirements.txt not found")

def main():
    print("=" * 60)
    print("🤖 ML Recovery Prediction Feature - Verification Script")
    print("=" * 60)
    
    results = {
        "Backend Dependencies": check_backend_dependencies(),
        "Backend Files": check_backend_files(),
        "Android Files": check_android_files(),
        "API Endpoints": check_api_endpoints(),
        "Requirements": check_requirements()
    }
    
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "⚠️  PARTIAL"
        print(f"  {status} - {check_name}")
    
    print("\n" + "=" * 60)
    if passed == total:
        print("✅ All checks passed! Ready to test the feature.")
    else:
        print("⚠️  Some checks need attention. Review above for details.")
    print("=" * 60)

if __name__ == "__main__":
    main()
