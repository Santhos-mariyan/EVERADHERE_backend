from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil
from pathlib import Path
from app.db.session import get_db
from app.models.models import User, Video
from app.schemas.schemas import VideoResponse, MessageResponse
from app.api.deps import get_current_user, get_current_doctor


router = APIRouter()

# Create upload directory
UPLOAD_DIR = Path("uploaded_videos")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """Upload a new video file (Doctor only)"""
    
    # Validate file type
    if not video_file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video files are allowed"
        )
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(video_file.filename)[1]
    unique_filename = f"{timestamp}_{video_file.filename}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video: {str(e)}"
        )
    
    # Create video URL (relative path for serving)
    video_url = f"/videos/{unique_filename}"
    
    # Save to database
    db_video = Video(
        title=title,
        description=description,
        url=video_url,
        uploaded_by=current_doctor.id,
        upload_date=datetime.utcnow()
    )
    
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    return db_video


@router.get("/all", response_model=List[VideoResponse])
def get_all_videos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all videos"""
    
    videos = db.query(Video).order_by(
        Video.upload_date.desc()
    ).offset(skip).limit(limit).all()
    
    return videos


@router.get("/{video_id}", response_model=VideoResponse)
def get_video_by_id(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific video by ID"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    return video


@router.delete("/{video_id}", response_model=MessageResponse)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    """Delete a video (Doctor who uploaded only)"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Only the uploader can delete
    if video.uploaded_by != current_doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete videos you uploaded"
        )
    
    # Delete physical file
    try:
        file_path = UPLOAD_DIR / os.path.basename(video.url)
        if file_path.exists():
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    db.delete(video)
    db.commit()
    
    return MessageResponse(message="Video deleted successfully")


@router.get("/doctor/{doctor_id}", response_model=List[VideoResponse])
def get_videos_by_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all videos uploaded by a specific doctor"""
    
    videos = db.query(Video).filter(
        Video.uploaded_by == doctor_id
    ).order_by(Video.upload_date.desc()).all()
    
    return videos
