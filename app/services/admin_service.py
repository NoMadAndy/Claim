"""Admin service for managing game settings and database operations"""
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import GameSetting, User, Spot, Log, Claim, Track, Item, UserRole


# Default game settings
DEFAULT_SETTINGS = {
    "auto_log_distance": {"value": 20, "type": "int", "description": "Distance in meters for auto-logging"},
    "manual_log_distance": {"value": 100, "type": "int", "description": "Distance in meters for manual logging"},
    "log_cooldown": {"value": 300, "type": "int", "description": "Cooldown in seconds between logs at same spot"},
    "xp_per_log": {"value": 10, "type": "int", "description": "Base XP gained per log"},
    "claim_points_per_log": {"value": 5, "type": "int", "description": "Claim points gained per log"},
    "manual_log_xp": {"value": 50, "type": "int", "description": "Base XP gained per manual log"},
    "manual_log_claim_points": {"value": 25, "type": "int", "description": "Claim points gained per manual log"},
    "manual_log_bonus_xp": {"value": 25, "type": "int", "description": "Bonus XP for manual log with photo or notes"},
    "manual_log_bonus_claim_points": {"value": 10, "type": "int", "description": "Bonus claim points for manual log with photo or notes"},
    "loot_spawn_rate": {"value": 0.3, "type": "float", "description": "Probability (0-1) of loot spawning"},
    "loot_spawn_radius_min": {"value": 20, "type": "int", "description": "Minimum spawn radius in meters"},
    "loot_spawn_radius_max": {"value": 150, "type": "int", "description": "Maximum spawn radius in meters"},
    "game_enabled": {"value": True, "type": "bool", "description": "Whether the game is active"},
    "maintenance_mode": {"value": False, "type": "bool", "description": "Is server in maintenance mode?"},
    "level_xp_base": {"value": 100, "type": "int", "description": "XP required for Level 1 -> 2"},
    "level_xp_increment": {"value": 10, "type": "int", "description": "Additional XP required per next level-up (linear)"},
}


def initialize_settings(db: Session):
    """Initialize default settings if they don't exist"""
    for setting_name, setting_data in DEFAULT_SETTINGS.items():
        existing = db.query(GameSetting).filter(
            GameSetting.setting_name == setting_name
        ).first()
        
        if not existing:
            if setting_data["type"] == "bool":
                value = str(setting_data["value"]).lower()
            elif setting_data["type"] in ["int", "float"]:
                value = str(setting_data["value"])
            else:
                value = str(setting_data["value"])
            
            setting = GameSetting(
                setting_name=setting_name,
                setting_value=value,
                data_type=setting_data["type"],
                description=setting_data["description"]
            )
            db.add(setting)
    
    db.commit()


def get_setting(db: Session, setting_name: str) -> Optional[Any]:
    """Get a game setting and return typed value"""
    setting = db.query(GameSetting).filter(
        GameSetting.setting_name == setting_name
    ).first()
    
    if not setting:
        return None
    
    # Convert to proper type
    if setting.data_type == "int":
        return int(setting.setting_value)
    elif setting.data_type == "float":
        return float(setting.setting_value)
    elif setting.data_type == "bool":
        return setting.setting_value.lower() in ("true", "1", "yes")
    elif setting.data_type == "json":
        return json.loads(setting.setting_value)
    else:
        return setting.setting_value


def get_all_settings(db: Session) -> Dict[str, Dict[str, Any]]:
    """Get all settings formatted for frontend"""
    settings = db.query(GameSetting).all()
    
    result = {}
    for setting in settings:
        value = setting.setting_value
        
        # Convert to proper type
        if setting.data_type == "int":
            value = int(value)
        elif setting.data_type == "float":
            value = float(value)
        elif setting.data_type == "bool":
            value = value.lower() in ("true", "1", "yes")
        elif setting.data_type == "json":
            value = json.loads(value)
        
        result[setting.setting_name] = {
            "value": value,
            "type": setting.data_type,
            "description": setting.description
        }
    
    return result


def update_setting(db: Session, setting_name: str, new_value: Any) -> bool:
    """Update a game setting"""
    setting = db.query(GameSetting).filter(
        GameSetting.setting_name == setting_name
    ).first()
    
    if not setting:
        return False
    
    # Convert value to string based on type
    if setting.data_type == "json":
        setting.setting_value = json.dumps(new_value)
    else:
        setting.setting_value = str(new_value)
    
    db.commit()
    return True


def get_database_stats(db: Session) -> Dict[str, Any]:
    """Get comprehensive database statistics"""
    return {
        "users": {
            "total": db.query(User).count(),
            "by_role": {
                "traveller": db.query(User).filter(User.role == UserRole.TRAVELLER).count(),
                "creator": db.query(User).filter(User.role == UserRole.CREATOR).count(),
                "admin": db.query(User).filter(User.role == UserRole.ADMIN).count(),
            },
            "active": db.query(User).filter(User.is_active == True).count(),
        },
        "spots": {
            "total": db.query(Spot).count(),
            "active": db.query(Spot).filter(Spot.is_active == True).count(),
        },
        "logs": {
            "total": db.query(Log).count(),
        },
        "claims": {
            "total": db.query(Claim).count(),
            "total_points": db.query(func.sum(Claim.claim_value)).scalar() or 0,
        },
        "tracks": {
            "total": db.query(Track).count(),
            "active": db.query(Track).filter(Track.is_active == True).count(),
        },
        "items": {
            "total": db.query(Item).count(),
        },
    }


def get_users_list(db: Session, skip: int = 0, limit: int = 50, role: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of users with optional role filter"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.order_by(User.id.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value,
            "level": u.level,
            "xp": u.xp,
            "total_claim_points": u.total_claim_points,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


def get_spots_list(db: Session, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """Get list of spots"""
    spots = db.query(Spot).order_by(Spot.id.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "is_permanent": s.is_permanent,
            "is_loot": s.is_loot,
            "is_active": s.is_active,
            "loot_xp": s.loot_xp,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "creator_id": s.creator_id,
            "creator": s.creator.username if s.creator else None,
        }
        for s in spots
    ]


def get_logs_list(db: Session, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent logs"""
    logs = db.query(Log).order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user": l.user.username if l.user else "Unknown",
            "spot_id": l.spot_id,
            "spot": l.spot.name if l.spot else "Unknown",
            "xp_gained": l.xp_gained,
            "claim_points": l.claim_points,
            "is_auto": l.is_auto,
            "distance": l.distance,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        }
        for l in logs
    ]


def update_user_role(db: Session, user_id: int, new_role: str) -> bool:
    """Update user role"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    try:
        user.role = UserRole[new_role.upper()]
        db.commit()
        return True
    except (KeyError, ValueError):
        return False


def toggle_user_active(db: Session, user_id: int) -> bool:
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    user.is_active = not user.is_active
    db.commit()
    return True


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user and all related data"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True


def delete_spot(db: Session, spot_id: int) -> bool:
    """Delete a spot"""
    spot = db.query(Spot).filter(Spot.id == spot_id).first()
    if not spot:
        return False
    
    db.delete(spot)
    db.commit()
    return True


def create_spot(
    db: Session,
    name: str,
    description: str,
    latitude: float,
    longitude: float,
    spot_type: str,
    xp_reward: int = 10,
    creator_id: Optional[int] = None
) -> Optional[Spot]:
    """Create a new spot"""
    try:
        from geoalchemy2 import func as geo_func
        from sqlalchemy import text
        
        spot = Spot(
            name=name,
            description=description,
            location=text(f"ST_Point({longitude}, {latitude})"),
            spot_type=spot_type,
            xp_reward=xp_reward,
            created_by=creator_id,
        )
        db.add(spot)
        db.commit()
        db.refresh(spot)
        return spot
    except Exception as e:
        db.rollback()
        print(f"Error creating spot: {e}")
        return None


def get_player_colors(db: Session) -> List[Dict[str, Any]]:
    """Get all players with their heatmap colors"""
    users = db.query(User).filter(User.is_active == True).order_by(User.username).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "color": u.heatmap_color or "#808080",  # Default gray if no color set
        }
        for u in users
    ]


def update_player_color(db: Session, user_id: int, color: str) -> Optional[str]:
    """
    Update a player's heatmap color (admin only)
    
    Returns:
        None if successful
        "invalid_color" if color format is invalid
        "user_not_found" if user doesn't exist
    """
    import re
    
    # Validate color format (hex color #RRGGBB)
    if not color or not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return "invalid_color"
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "user_not_found"
    
    user.heatmap_color = color.upper()
    db.commit()
    return None
