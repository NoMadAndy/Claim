from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import HeatmapData
from app.services import claim_service
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.get("/heatmap/me", response_model=HeatmapData)
async def get_my_heatmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's claim heatmap"""
    return claim_service.get_user_heatmap(db, current_user.id)


@router.get("/heatmap/user/{user_id}", response_model=HeatmapData)
async def get_user_heatmap(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific user's claim heatmap"""
    return claim_service.get_user_heatmap(db, user_id)


@router.get("/heatmap/all", response_model=List[HeatmapData])
async def get_all_heatmaps(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get heatmaps for top users"""
    return claim_service.get_all_heatmaps(db, limit)


@router.get("/spot/{spot_id}/dominance")
async def get_spot_dominance(
    spot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dominance rankings for a spot"""
    return claim_service.get_spot_dominance(db, spot_id)
