from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.models import User, Notification
from app.schemas.schemas import NotificationCreate, NotificationResponse, MessageResponse
from app.services import pubsub
from fastapi import WebSocket, WebSocketDisconnect
from app.core.security import decode_access_token
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.websocket('/ws')
async def websocket_notifications(websocket: WebSocket):
    # expect token as query param: /api/v1/notifications/ws?token=JWT
    token = websocket.query_params.get('token')
    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    email = payload.get('sub')
    if not email:
        await websocket.close(code=1008)
        return

    # get user from DB
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
    finally:
        db.close()

    if not user:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # subscribe to user's queue
    q, _gen = pubsub.subscribe(user.id)
    try:
        while True:
            item = await q.get()
            try:
                await websocket.send_json(item)
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass

# ---------------- CREATE NOTIFICATION ----------------
@router.post("/create", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipient = db.query(User).filter(User.id == notification.user_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient user not found")

    db_notification = Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        date=datetime.utcnow()
    )

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # publish to any connected clients for this user
    try:
        pubsub.publish_sync(db_notification.user_id, {
            "id": db_notification.id,
            "title": db_notification.title,
            "message": db_notification.message,
            "date": db_notification.date.isoformat()
        })
    except Exception:
        pass

    return db_notification


# ---------------- GET MY NOTIFICATIONS ----------------
@router.get("/my-notifications", response_model=List[NotificationResponse])
def get_my_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    return query.order_by(Notification.date.desc()).offset(skip).limit(limit).all()


@router.get("/stream")
def stream_notifications(current_user: User = Depends(get_current_user)):
    """Server-sent events endpoint that streams new notifications for the current user."""

    async def event_generator():
        q, gen = pubsub.subscribe(current_user.id)
        try:
            while True:
                item = await q.get()
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            # cleanup handled in pubsub
            return

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------- MARK ONE READ ----------------
@router.put("/{notification_id}/mark-read", response_model=MessageResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    notification.is_read = True
    db.commit()

    return MessageResponse(message="Notification marked as read")


# ---------------- MARK ALL READ ----------------
@router.put("/mark-all-read", response_model=MessageResponse)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})

    db.commit()
    return MessageResponse(message="All notifications marked as read")


# ---------------- DELETE ----------------
@router.delete("/{notification_id}", response_model=MessageResponse)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(notification)
    db.commit()

    return MessageResponse(message="Notification deleted successfully")


# ---------------- UNREAD COUNT ----------------
@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return {"unread_count": count}


# ---------------- 🔥 TEST PUSH (THIS WAS MISSING) ----------------
@router.post("/test-push")
def test_push_notification(
    current_user: User = Depends(get_current_user)
):
    raise HTTPException(status_code=400, detail="Push provider not configured on server. Use streaming or polling.")
