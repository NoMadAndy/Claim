from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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
    logs = log_service.get_spot_logs(db, spot_id, limit)
    return logs
