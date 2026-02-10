from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "PhysioClinic API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./physioclinic.db"
    
    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "demo@physioclinic.com"
    SMTP_PASSWORD: str = "demo-password"
    EMAILS_FROM_EMAIL: str = "noreply@physioclinic.com"
    EMAILS_FROM_NAME: str = "PhysioClinic"
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_FOLDER: str = "./uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create upload folder if it doesn't exist
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
