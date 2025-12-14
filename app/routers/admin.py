"""Admin panel routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserResponse
from app.routers.auth import get_current_user
from app.models import User, UserRole
from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


def check_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to check if user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/settings")
async def get_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Get all game settings"""
    # Initialize settings if needed
    admin_service.initialize_settings(db)
    settings = admin_service.get_all_settings(db)
    return {"settings": settings}


@router.put("/settings/{setting_name}")
async def update_setting(
    setting_name: str,
    value: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Update a game setting"""
    success = admin_service.update_setting(db, setting_name, value.get("value"))
    if not success:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"success": True, "setting": setting_name}


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Get database statistics"""
    stats = admin_service.get_database_stats(db)
    return stats


@router.get("/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: str = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Get list of users"""
    users = admin_service.get_users_list(db, skip, limit, role)
    return {"users": users, "total": len(users)}


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Update user role"""
    success = admin_service.update_user_role(db, user_id, new_role.get("role"))
    if not success:
        raise HTTPException(status_code=404, detail="User not found or invalid role")
    return {"success": True}


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Toggle user active status"""
    success = admin_service.toggle_user_active(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Delete a user"""
    success = admin_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}


@router.get("/spots")
async def get_spots(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Get list of spots"""
    spots = admin_service.get_spots_list(db, skip, limit)
    return {"spots": spots}


@router.delete("/spots/{spot_id}")
async def delete_spot(
    spot_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Delete a spot"""
    success = admin_service.delete_spot(db, spot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Spot not found")
    return {"success": True}


@router.post("/spots")
async def create_spot(
    spot_data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Create a new spot"""
    spot = admin_service.create_spot(
        db,
        name=spot_data.get("name"),
        description=spot_data.get("description", ""),
        latitude=spot_data.get("latitude"),
        longitude=spot_data.get("longitude"),
        spot_type=spot_data.get("spot_type", "permanent"),
        xp_reward=spot_data.get("xp_reward", 10),
        creator_id=admin.id
    )
    if not spot:
        raise HTTPException(status_code=400, detail="Failed to create spot")
    return {"success": True, "spot_id": spot.id}


@router.get("/logs")
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Get recent logs"""
    logs = admin_service.get_logs_list(db, skip, limit)
    return {"logs": logs}


@router.get("/player-colors")
async def get_player_colors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all players with their colors (available to all authenticated users)"""
    players = admin_service.get_player_colors(db)
    return {"players": players}


@router.put("/player-colors/{user_id}")
async def update_player_color(
    user_id: int,
    color_data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin)
):
    """Update a player's color (admin only)"""
    error = admin_service.update_player_color(db, user_id, color_data.get("color"))
    if error == "invalid_color":
        raise HTTPException(status_code=400, detail="Invalid color format. Use hex format #RRGGBB")
    elif error == "user_not_found":
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}
