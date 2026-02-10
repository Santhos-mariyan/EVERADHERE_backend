#!/usr/bin/env python3
"""
Clean up corrupted ML model files and rebuild fresh
Run this when you get: "X has 5 features, but StandardScaler is expecting 4 features"
"""

import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def cleanup_ml_models():
    """Delete corrupted model files to force rebuild"""
    
    models_dir = Path("ml_models")
    
    if not models_dir.exists():
        logger.info("✅ ml_models directory doesn't exist - no cleanup needed")
        return True
    
    files_to_delete = [
        models_dir / "recovery_model.pkl",
        models_dir / "recovery_scaler.pkl"
    ]
    
    success = True
    for file_path in files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️  Deleted: {file_path}")
            else:
                logger.info(f"⏭️  Not found: {file_path}")
        except Exception as e:
            logger.error(f"❌ Failed to delete {file_path}: {e}")
            success = False
    
    # Try to remove empty directory
    try:
        if models_dir.exists() and not any(models_dir.iterdir()):
            models_dir.rmdir()
            logger.info(f"🗑️  Deleted empty directory: {models_dir}")
    except:
        pass  # Directory not empty or permission issue
    
    return success

if __name__ == "__main__":
    logger.info("🧹 Cleaning up corrupted ML models...")
    logger.info("This will force the model to rebuild with correct 5 features\n")
    
    if cleanup_ml_models():
        logger.info("\n✅ Cleanup completed successfully!")
        logger.info("👉 Next: Restart the backend server (python main.py)")
        logger.info("👉 The model will auto-rebuild with 5 features")
    else:
        logger.error("\n⚠️  Cleanup had some issues. Check the messages above.")
