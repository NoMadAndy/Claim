from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakePoint, ST_SetSRID
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from app.models import Spot, User, Log, Claim, SpotType
from app.schemas import SpotCreate
from app.config import settings
import pytz

# CET timezone
CET = pytz.timezone('Europe/Berlin')

def get_current_cet():
    """Get current time in CET timezone (naive datetime for DB compatibility)"""
    return datetime.now(CET).replace(tzinfo=None)


def create_spot(db: Session, spot_data: SpotCreate, creator: User) -> Spot:
    """Create a new permanent spot"""
    from app.spot_types_config import get_spot_config
    
    point = f'POINT({spot_data.longitude} {spot_data.latitude})'
    
    # Get configuration for spot type if provided
    spot_type = spot_data.spot_type or SpotType.STANDARD
    config = get_spot_config(spot_type)
    
    # Use provided multipliers or defaults from config
    xp_multiplier = spot_data.xp_multiplier if spot_data.xp_multiplier is not None else config["xp_multiplier"]
    claim_multiplier = spot_data.claim_multiplier if spot_data.claim_multiplier is not None else config["claim_multiplier"]
    icon_name = spot_data.icon_name or config["icon"]
    
    spot = Spot(
        name=spot_data.name,
        description=spot_data.description,
        location=WKTElement(point, srid=4326),
        is_permanent=True,
        is_loot=False,
        creator_id=creator.id,
        spot_type=spot_type,
        xp_multiplier=xp_multiplier,
        claim_multiplier=claim_multiplier,
        icon_name=icon_name
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
    from app.models import get_cet_now
    point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    current_time = get_cet_now()
    
    # Query spots within radius (permanent spots OR active loot)
    spots = db.query(
        Spot,
        ST_Distance(Spot.location, point).label('distance')
    ).filter(
        ST_DWithin(Spot.location, point, radius_meters)
    ).filter(
        # Either permanent spot OR active loot (not expired)
        (Spot.is_permanent == True) | 
        ((Spot.is_loot == True) & (Spot.loot_expires_at > current_time))
    ).all()
    
    return spots


def get_cooldown_remaining(db: Session, user_id: int, spot_id: int) -> int:
    """
    Get remaining cooldown time in seconds for a user on a specific spot.
    Returns 0 if no cooldown is active.
    """
    current_time = get_current_cet()
    cooldown_time = current_time - timedelta(seconds=settings.LOG_COOLDOWN)
    
    last_log = db.query(Log).filter(
        and_(
            Log.user_id == user_id,
            Log.spot_id == spot_id,
            Log.timestamp > cooldown_time
        )
    ).first()
    
    if not last_log:
        return 0
    
    # Calculate remaining cooldown
    elapsed = (current_time - last_log.timestamp).total_seconds()
    remaining = max(0, settings.LOG_COOLDOWN - int(elapsed))
    
    # Debug logging
    print(f"[COOLDOWN DEBUG] Current CET: {current_time}, Last log: {last_log.timestamp}, Elapsed: {elapsed}s, Remaining: {remaining}s")
    
    return remaining


def can_log_spot(db: Session, user_id: int, spot_id: int, is_auto: bool = False) -> bool:
    """
    Check if user can log this spot (per-spot cooldown).
    
    - Auto logs: blocked by recent MANUAL logs AND recent AUTO logs (both prevent next auto log)
    - Manual logs: blocked by recent MANUAL logs (their own cooldown)
    
    This means: 
    - Manual log → blocks both auto and manual logs for 5 min
    - Auto log → blocks only auto logs for 5 min, manual still possible
    """
    if is_auto:
        # Auto logs: blocked by recent MANUAL logs OR recent AUTO logs
        last_manual_log = db.query(Log).filter(
            and_(
                Log.user_id == user_id,
                Log.spot_id == spot_id,
                Log.is_auto == False,
                Log.timestamp > get_current_cet() - timedelta(seconds=settings.LOG_COOLDOWN)
            )
        ).first()
        
        last_auto_log = db.query(Log).filter(
            and_(
                Log.user_id == user_id,
                Log.spot_id == spot_id,
                Log.is_auto == True,
                Log.timestamp > get_current_cet() - timedelta(seconds=settings.LOG_COOLDOWN)
            )
        ).first()
        
        # Can log if no recent manual AND no recent auto log
        return last_manual_log is None and last_auto_log is None
    else:
        # Manual logs: blocked by recent MANUAL logs (their own cooldown)
        last_manual_log = db.query(Log).filter(
            and_(
                Log.user_id == user_id,
                Log.spot_id == spot_id,
                Log.is_auto == False,
                Log.timestamp > get_current_cet() - timedelta(seconds=settings.LOG_COOLDOWN)
            )
        ).first()
        return last_manual_log is None


def get_log_status(db: Session, user_id: int, spot_id: int) -> dict:
    """
    Get detailed cooldown status for both auto and manual logs.
    
    Returns:
    {
        "can_auto_log": bool,
        "auto_cooldown_remaining": int (seconds, 0 if ready),
        "can_manual_log": bool,
        "manual_cooldown_remaining": int (seconds, 0 if ready),
        "last_log_type": "auto" | "manual" | None
    }
    """
    # Check for recent manual log
    last_manual_log = db.query(Log).filter(
        and_(
            Log.user_id == user_id,
            Log.spot_id == spot_id,
            Log.is_auto == False,
            Log.timestamp > get_current_cet() - timedelta(seconds=settings.LOG_COOLDOWN)
        )
    ).order_by(Log.timestamp.desc()).first()
    
    # Check for recent auto log
    last_auto_log = db.query(Log).filter(
        and_(
            Log.user_id == user_id,
            Log.spot_id == spot_id,
            Log.is_auto == True,
            Log.timestamp > get_current_cet() - timedelta(seconds=settings.LOG_COOLDOWN)
        )
    ).order_by(Log.timestamp.desc()).first()
    
    # Determine last log type
    last_log_type = None
    if last_manual_log and (not last_auto_log or last_manual_log.timestamp > last_auto_log.timestamp):
        last_log_type = "manual"
    elif last_auto_log:
        last_log_type = "auto"
    
    # Calculate auto log cooldown (blocked by manual log OR recent auto log)
    auto_cooldown = 0
    can_auto_log = True
    
    # Check manual log cooldown (blocks auto logs)
    if last_manual_log:
        elapsed = (get_current_cet() - last_manual_log.timestamp).total_seconds()
        auto_cooldown = max(0, int(settings.LOG_COOLDOWN - elapsed))
    
    # Also check auto log cooldown (blocks auto logs)
    if last_auto_log:
        elapsed = (get_current_cet() - last_auto_log.timestamp).total_seconds()
        auto_cooldown_from_auto = max(0, int(settings.LOG_COOLDOWN - elapsed))
        auto_cooldown = max(auto_cooldown, auto_cooldown_from_auto)
    
    can_auto_log = (auto_cooldown == 0)
    
    # Calculate manual log cooldown (blocked by manual log)
    manual_cooldown = 0
    can_manual_log = True
    if last_manual_log:
        elapsed = (get_current_cet() - last_manual_log.timestamp).total_seconds()
        manual_cooldown = max(0, int(settings.LOG_COOLDOWN - elapsed))
        can_manual_log = (manual_cooldown == 0)
    
    return {
        "can_auto_log": can_auto_log,
        "auto_cooldown_remaining": auto_cooldown,
        "can_manual_log": can_manual_log,
        "manual_cooldown_remaining": manual_cooldown,
        "last_log_type": last_log_type
    }


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
    expires_at = get_current_cet() + timedelta(hours=1)
    
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
    now = get_current_cet()
    result = db.query(Spot).filter(
        and_(
            Spot.is_loot == True,
            Spot.loot_expires_at < now
        )
    ).delete()
    db.commit()
    return result
