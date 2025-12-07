from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import LogCreate, LogResponse
from app.services import log_service, spot_service
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_data: LogCreate,
    is_auto: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a log entry (manual or auto)"""
    # Check cooldown
    if not spot_service.can_log_spot(db, current_user.id, log_data.spot_id):
        remaining = spot_service.get_cooldown_remaining(db, current_user.id, log_data.spot_id)
        minutes = remaining // 60
        seconds = remaining % 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Cooldown active: {minutes}m {seconds}s remaining"
        )
    
    # Create log
    log = log_service.create_log(db, current_user, log_data, is_auto)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot log: spot not found or too far away"
        )
    
    return log


@router.get("/me", response_model=List[LogResponse])
async def get_my_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's logs"""
    logs = log_service.get_user_logs(db, current_user.id, limit)
    return logs


@router.get("/spot/{spot_id}", response_model=List[LogResponse])
async def get_spot_logs(
    spot_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get logs for a specific spot"""
    from sqlalchemy.orm import joinedload
    from app.models import Log
    
    logs = db.query(Log).filter(
        Log.spot_id == spot_id
    ).order_by(Log.timestamp.desc()).limit(limit).all()
    
    # Manually add username and has_photo to each log
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        log_dict = LogResponse.model_validate(log)
        log_dict.username = user.username if user else "Unknown"
        log_dict.has_photo = log.photo_data is not None and len(log.photo_data) > 0
        result.append(log_dict)
    
    return result


@router.get("/{log_id}/photo")
async def get_log_photo(
    log_id: int,
    db: Session = Depends(get_db)
):
    """Get photo from a log entry (no auth required)"""
    from app.models import Log
    from fastapi.responses import StreamingResponse
    import io
    
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log or not log.photo_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Return image with correct mime type
    return StreamingResponse(
        io.BytesIO(log.photo_data),
        media_type=log.photo_mime or "image/jpeg"
    )


@router.post("/upload")
async def upload_log_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a photo for a log entry (returns base64 encoded data)"""
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Check file size (5MB limit)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 5MB)"
        )
    
    # Return binary data - frontend will include this directly with the log submission
    import base64
    return {
        "photo_data": base64.b64encode(contents).decode('utf-8'),
        "mime_type": file.content_type,
        "size": len(contents)
    }
