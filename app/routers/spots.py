from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_X, ST_Y, ST_DistanceSphere, ST_MakePoint, ST_SetSRID, ST_GeomFromWKB
from app.database import get_db
from app.schemas import SpotCreate, SpotResponse
from app.services import spot_service
from app.routers.auth import get_current_user
from app.models import User, UserRole, Spot, Claim

router = APIRouter(prefix="/api/spots", tags=["spots"])


@router.post("/", response_model=SpotResponse, status_code=status.HTTP_201_CREATED)
async def create_spot(
    spot_data: SpotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new spot (Creator/Admin only)"""
    if current_user.role not in [UserRole.CREATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creators and admins can create spots"
        )
    
    spot = spot_service.create_spot(db, spot_data, current_user)
    
    # Extract coordinates for response (cast Geography to Geometry)
    lat = db.execute(func.ST_Y(func.ST_GeomFromWKB(spot.location))).scalar()
    lon = db.execute(func.ST_X(func.ST_GeomFromWKB(spot.location))).scalar()
    
    return SpotResponse(
        id=spot.id,
        name=spot.name,
        description=spot.description,
        latitude=lat,
        longitude=lon,
        is_permanent=spot.is_permanent,
        is_loot=spot.is_loot,
        created_at=spot.created_at,
        creator_id=spot.creator_id
    )


@router.get("/nearby", response_model=List[SpotResponse])
async def get_nearby_spots(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(1000, ge=0, le=10000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spots within radius of a location"""
    spots_with_distance = spot_service.get_spots_in_radius(db, latitude, longitude, radius)
    
    result = []
    for spot, distance in spots_with_distance:
        lat = db.execute(func.ST_Y(func.ST_GeomFromWKB(spot.location))).scalar()
        lon = db.execute(func.ST_X(func.ST_GeomFromWKB(spot.location))).scalar()
        
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


@router.get("/{spot_id}/details")
async def get_spot_details(
    spot_id: int,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed info about a spot including cooldown, my claims, distance, and dominance"""
    spot = spot_service.get_spot_by_id(db, spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spot not found"
        )
    
    # Get spot coordinates (cast Geography to Geometry)
    lat = db.execute(func.ST_Y(func.ST_GeomFromWKB(spot.location))).scalar()
    lon = db.execute(func.ST_X(func.ST_GeomFromWKB(spot.location))).scalar()
    
    # Calculate distance to spot using ST_DistanceSphere for accurate meters
    point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    distance_meters = db.execute(
        ST_DistanceSphere(spot.location, point)
    ).scalar() or 0
    
    # Get cooldown remaining
    cooldown_seconds = spot_service.get_cooldown_remaining(db, current_user.id, spot_id)
    
    # Get detailed log status (auto/manual cooldowns)
    log_status = spot_service.get_log_status(db, current_user.id, spot_id)
    
    # Get my claim value on this spot
    my_claim = db.query(Claim).filter(
        Claim.user_id == current_user.id,
        Claim.spot_id == spot_id
    ).first()
    my_claim_value = my_claim.claim_value if my_claim else 0
    
    # Get top 3 claimers (dominance)
    top_claimers = db.query(
        User.username,
        Claim.claim_value,
        Claim.dominance
    ).join(Claim, Claim.user_id == User.id).filter(
        Claim.spot_id == spot_id
    ).order_by(Claim.claim_value.desc()).limit(3).all()
    
    dominance_list = [
        {
            "username": claimer.username,
            "claim_value": float(claimer.claim_value),
            "dominance": float(claimer.dominance)
        }
        for claimer in top_claimers
    ]
    
    return {
        "spot_id": spot_id,
        "name": spot.name,
        "description": spot.description,
        "latitude": lat,
        "longitude": lon,
        "distance_meters": float(distance_meters),
        "cooldown_seconds": cooldown_seconds,
        "my_claim_value": float(my_claim_value),
        "top_claimers": dominance_list,
        "is_loot": spot.is_loot,
        "loot_xp": spot.loot_xp,
        "loot_expires_at": spot.loot_expires_at,
        "can_auto_log": log_status["can_auto_log"],
        "auto_cooldown_remaining": log_status["auto_cooldown_remaining"],
        "can_manual_log": log_status["can_manual_log"],
        "manual_cooldown_remaining": log_status["manual_cooldown_remaining"],
        "last_log_type": log_status["last_log_type"]
    }


@router.get("/{spot_id}", response_model=SpotResponse)
async def get_spot(
    spot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spot by ID"""
    spot = spot_service.get_spot_by_id(db, spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spot not found"
        )
    
    lat = db.execute(func.ST_Y(func.ST_GeomFromWKB(spot.location))).scalar()
    lon = db.execute(func.ST_X(func.ST_GeomFromWKB(spot.location))).scalar()
    
    return SpotResponse(
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
    )


@router.delete("/{spot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spot(
    spot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a spot (Admin only or creator)"""
    spot = spot_service.get_spot_by_id(db, spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spot not found"
        )
    
    if current_user.role != UserRole.ADMIN and spot.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this spot"
        )
    
    spot_service.delete_spot(db, spot_id)
    return None
