from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.services import loot_service
from app.routers.auth import get_current_user
from app.schemas import SpotResponse
from app.models import User
from pydantic import BaseModel


router = APIRouter(prefix="/api/loot", tags=["loot"])


class SpawnLootRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = 500


class CollectLootRequest(BaseModel):
    loot_spot_id: int
    latitude: float
    longitude: float


class LootReward(BaseModel):
    xp: int
    items: List[dict]


class CollectLootResponse(BaseModel):
    success: bool
    error: str = None
    rewards: LootReward = None
    level_up: bool = False
    new_level: int = None
    total_xp: int = 0


@router.post("/spawn", response_model=List[SpotResponse])
async def spawn_loot(
    request: SpawnLootRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Spawn loot spots around user's current position"""
    spots = loot_service.spawn_loot_spots_for_user(
        db,
        current_user.id,
        request.latitude,
        request.longitude,
        request.radius_meters
    )
    
    # Extract coordinates from PostGIS POINT
    result = []
    for spot in spots:
        lat = db.execute(func.ST_Y(spot.location)).scalar()
        lon = db.execute(func.ST_X(spot.location)).scalar()
        
        result.append(SpotResponse(
            id=spot.id,
            name=spot.name,
            description=spot.description,
            latitude=lat,
            longitude=lon,
            is_permanent=spot.is_permanent,
            is_loot=spot.is_loot,
            created_at=spot.created_at,
            creator_id=spot.creator_id,
            loot_expires_at=spot.loot_expires_at,
            loot_xp=spot.loot_xp
        ))
    
    return result


@router.post("/collect", response_model=CollectLootResponse)
async def collect_loot(
    request: CollectLootRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Collect a loot spot"""
    result = loot_service.collect_loot(
        db,
        current_user.id,
        request.loot_spot_id,
        request.latitude,
        request.longitude
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return CollectLootResponse(**result)


@router.get("/active", response_model=List[SpotResponse])
async def get_active_loot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active loot spots for current user"""
    spots = loot_service.get_active_loot_spots(db, current_user.id)
    
    # Extract coordinates from PostGIS POINT
    result = []
    for spot in spots:
        lat = db.execute(func.ST_Y(spot.location)).scalar()
        lon = db.execute(func.ST_X(spot.location)).scalar()
        
        result.append(SpotResponse(
            id=spot.id,
            name=spot.name,
            description=spot.description,
            latitude=lat,
            longitude=lon,
            is_permanent=spot.is_permanent,
            is_loot=spot.is_loot,
            created_at=spot.created_at,
            creator_id=spot.creator_id,
            loot_expires_at=spot.loot_expires_at,
            loot_xp=spot.loot_xp
        ))
    
    return result


@router.post("/cleanup")
async def cleanup_expired(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cleanup expired loot spots for current user"""
    count = loot_service.cleanup_expired_loot_for_user(db, current_user.id)
    return {"removed": count}
