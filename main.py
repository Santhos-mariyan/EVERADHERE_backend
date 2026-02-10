from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.openapi.utils import get_openapi
from pathlib import Path

from app.core.config import settings
from app.db.session import engine, Base
from app.api.endpoints import (
    auth, users, medications, test_results, videos, notifications, dashboard, predictions
)
from app.api.endpoints import reminders
from app.services import reminder_service
from app.services import firebase_service

# -------------------- DATABASE --------------------
Base.metadata.create_all(bind=engine)

# -------------------- FIREBASE --------------------
firebase_service.init_firebase()

# -------------------- APP INIT --------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PhysioClinic Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# -------------------- PROFILE IMAGE STREAMING --------------------
@app.get("/profile-images/{filename}")
async def get_profile_image(filename: str):
    """Serve profile images"""
    image_path = Path("uploaded_profile_images") / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        image_path,
        media_type="image/jpeg",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

# -------------------- VIDEO STREAMING --------------------
@app.get("/videos/{video_filename}")
async def stream_video(video_filename: str, request: Request):
    video_path = Path("uploaded_videos") / video_filename

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            video_path,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )

    range_match = range_header.replace("bytes=", "").split("-")
    start = int(range_match[0]) if range_match[0] else 0
    end = int(range_match[1]) if range_match[1] else file_size - 1

    if start >= file_size or end >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    chunk_size = end - start + 1

    def iterfile():
        with open(video_path, "rb") as video_file:
            video_file.seek(start)
            remaining = chunk_size
            while remaining:
                chunk = video_file.read(min(8192, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        iterfile(),
        status_code=206,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "video/mp4",
        },
    )

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- BASIC ROUTES --------------------
@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to PhysioClinic API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": settings.VERSION}

# -------------------- ROUTERS --------------------
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(medications.router, prefix=f"{settings.API_V1_PREFIX}/medications", tags=["Medications"])
app.include_router(test_results.router, prefix=f"{settings.API_V1_PREFIX}/test-results", tags=["Test Results"])
app.include_router(videos.router, prefix=f"{settings.API_V1_PREFIX}/videos", tags=["Videos"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["Notifications"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])
app.include_router(reminders.router, prefix=f"{settings.API_V1_PREFIX}/reminders", tags=["Reminders"])
app.include_router(predictions.router, prefix=f"{settings.API_V1_PREFIX}/predictions", tags=["ML Predictions"])

# -------------------- SWAGGER AUTH FIX --------------------
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# -------------------- STARTUP / SHUTDOWN --------------------
@app.on_event("startup")
async def startup_event():
    print(f"[STARTUP] {settings.PROJECT_NAME} v{settings.VERSION} started successfully!")
    print(f"[DOCS] API Docs: http://localhost:8001/docs")
    print(f"[DB] Database: {settings.DATABASE_URL}")
    # start reminder scheduler and load existing reminders
    try:
        reminder_service.start_scheduler()
        reminder_service.load_and_schedule_all()
        # Run initial cleanup of expired verification codes
        # from app.services.reminder_service import _cleanup_expired_verification_codes
        # _cleanup_expired_verification_codes()
        print("[SCHEDULER] Reminder scheduler started and reminders loaded")
    except Exception as e:
        print("Could not start reminder scheduler:", e)

@app.on_event("shutdown")
async def shutdown_event():
    print(f"[SHUTDOWN] {settings.PROJECT_NAME} shutting down...")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
