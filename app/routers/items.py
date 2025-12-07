from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ItemResponse, InventoryItemResponse, UserStats, UseItemResponse
from app.services import item_service
from app.routers.auth import get_current_user
from app.models import User, UserRole
from sqlalchemy import func

router = APIRouter(prefix="/api/items", tags=["items", "stats"])


# Items endpoints
@router.get("", response_model=List[ItemResponse])
async def get_all_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available items"""
    items = item_service.get_all_items(db)
    return items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get item by ID"""
    item = item_service.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item


# Inventory endpoints
@router.get("/inventory", response_model=List[InventoryItemResponse])
async def get_my_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's inventory"""
    inventory = item_service.get_user_inventory(db, current_user.id)
    return inventory


@router.post("/{item_id}/use", response_model=UseItemResponse)
async def use_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use/consume an item from inventory"""
    result = item_service.use_item(db, current_user.id, item_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return UseItemResponse(**result)


# Stats endpoint
@router.get("/stats", response_model=UserStats)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's game statistics"""
    from app.models import Log, Claim, Track, InventoryItem
    
    # Count logs
    total_logs = db.query(func.count(Log.id)).filter(
        Log.user_id == current_user.id
    ).scalar()
    
    # Count claimed spots
    total_spots_claimed = db.query(func.count(Claim.id)).filter(
        Claim.user_id == current_user.id,
        Claim.claim_value > 0
    ).scalar()
    
    # Count active tracks
    active_tracks = db.query(func.count(Track.id)).filter(
        Track.user_id == current_user.id,
        Track.is_active == True
    ).scalar()
    
    # Count inventory items
    inventory_count = db.query(func.sum(InventoryItem.quantity)).filter(
        InventoryItem.user_id == current_user.id
    ).scalar() or 0
    
    # Calculate XP to next level (100 XP per level)
    xp_to_next = 100 - (current_user.xp % 100)
    
    return UserStats(
        level=current_user.level,
        xp=current_user.xp,
        xp_to_next_level=xp_to_next,
        total_claim_points=current_user.total_claim_points,
        total_logs=total_logs,
        total_spots_claimed=total_spots_claimed,
        active_tracks=active_tracks,
        inventory_count=inventory_count
    )
