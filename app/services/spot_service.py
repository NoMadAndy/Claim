from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakePoint, ST_SetSRID
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from app.models import Spot, User, Log, Claim
from app.schemas import SpotCreate
from app.config import settings


def create_spot(db: Session, spot_data: SpotCreate, creator: User) -> Spot:
    """Create a new permanent spot"""
    point = f'POINT({spot_data.longitude} {spot_data.latitude})'
    
    spot = Spot(
        name=spot_data.name,
        description=spot_data.description,
        location=WKTElement(point, srid=4326),
        is_permanent=True,
        is_loot=False,
        creator_id=creator.id
    )
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot


def get_spots_in_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000
) -> List[Tuple[Spot, float]]:
    """Get all spots within radius of a point, with distances"""
    point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    
    # Query spots within radius
    spots = db.query(
        Spot,
        ST_Distance(Spot.location, point).label('distance')
    ).filter(
        ST_DWithin(Spot.location, point, radius_meters)
    ).filter(
        Spot.is_permanent == True
    ).all()
    
    return spots


def can_log_spot(db: Session, user_id: int, spot_id: int) -> bool:
    """
    Check if user can log this spot (per-spot cooldown).
    
    Each player has a separate 5-minute cooldown per spot.
    Example: Player A has cooldown on Spot 1, but Player B can log Spot 1 immediately.
    """
    cooldown_time = datetime.utcnow() - timedelta(seconds=settings.LOG_COOLDOWN)
    
    # Check if this specific user logged this specific spot recently
    last_log = db.query(Log).filter(
        and_(
            Log.user_id == user_id,  # This user
            Log.spot_id == spot_id,  # This specific spot
            Log.timestamp > cooldown_time  # Within cooldown window
        )
    ).first()
    
    return last_log is None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using PostGIS"""
    # This is a placeholder - actual calculation done in DB
    return 0.0


def get_spot_by_id(db: Session, spot_id: int) -> Optional[Spot]:
    """Get spot by ID"""
    return db.query(Spot).filter(Spot.id == spot_id).first()


def delete_spot(db: Session, spot_id: int) -> bool:
    """Delete a spot"""
    spot = get_spot_by_id(db, spot_id)
    if spot:
        db.delete(spot)
        db.commit()
        return True
    return False


def create_loot_spot(
    db: Session,
    latitude: float,
    longitude: float,
    owner_id: int,
    xp: int = 50,
    item_id: Optional[int] = None
) -> Spot:
    """Create a loot spot for a specific player"""
    point = f'POINT({longitude} {latitude})'
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    spot = Spot(
        name=f"Loot Spot",
        description="Temporary loot spot",
        location=WKTElement(point, srid=4326),
        is_permanent=False,
        is_loot=True,
        owner_id=owner_id,
        loot_expires_at=expires_at,
        loot_xp=xp,
        loot_item_id=item_id
    )
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot


def cleanup_expired_loot(db: Session) -> int:
    """Remove expired loot spots"""
    now = datetime.utcnow()
    result = db.query(Spot).filter(
        and_(
            Spot.is_loot == True,
            Spot.loot_expires_at < now
        )
    ).delete()
    db.commit()
    return result
