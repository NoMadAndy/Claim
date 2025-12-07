from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_MakePoint
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from app.models import Log, Spot, User, Claim
from app.schemas import LogCreate
from app.config import settings
import pytz

# CET timezone
CET = pytz.timezone('Europe/Berlin')

def get_current_cet():
    """Get current time in CET timezone (naive datetime for DB compatibility)"""
    return datetime.now(CET).replace(tzinfo=None)
from app.services.auth_service import update_user_xp


def create_log(
    db: Session,
    user: User,
    log_data: LogCreate,
    is_auto: bool = False
) -> Optional[Log]:
    """Create a log entry for a spot visit"""
    # Get spot
    spot = db.query(Spot).filter(Spot.id == log_data.spot_id).first()
    if not spot:
        return None
    
    # Calculate distance using PostGIS
    user_point = ST_SetSRID(ST_MakePoint(log_data.longitude, log_data.latitude), 4326)
    distance = db.query(
        ST_Distance(
            spot.location,
            user_point
        )
    ).scalar()
    
    # Check distance constraints
    max_distance = settings.AUTO_LOG_DISTANCE if is_auto else settings.MANUAL_LOG_DISTANCE
    if distance > max_distance:
        return None
    
    # Calculate rewards - manual logs get more reward
    if is_auto:
        xp_gained = 10
        claim_points = 5
    else:
        # Manual logs with photos/notes get bonus
        xp_gained = 50  # 5x auto log
        claim_points = 25  # 5x auto log
        if log_data.photo_data or log_data.notes:
            xp_gained += 25  # +25 bonus for photo or notes
            claim_points += 10
    
    # Create log
    log_point = f'POINT({log_data.longitude} {log_data.latitude})'
    
    # Process photo if provided (convert base64 to binary)
    photo_data = None
    photo_mime = None
    if log_data.photo_data and log_data.photo_mime:
        import base64
        try:
            photo_data = base64.b64decode(log_data.photo_data)
            photo_mime = log_data.photo_mime
        except Exception:
            pass  # Ignore photo errors, log without it
    
    log = Log(
        user_id=user.id,
        spot_id=spot.id,
        location=WKTElement(log_point, srid=4326),
        distance=distance,
        is_auto=is_auto,
        xp_gained=xp_gained,
        claim_points=claim_points,
        notes=log_data.notes,
        photo_data=photo_data,
        photo_mime=photo_mime
    )
    
    db.add(log)
    
    # Update user XP
    update_user_xp(db, user, xp_gained)
    
    # Update or create claim
    update_claim(db, user.id, spot.id, claim_points)
    
    db.commit()
    db.refresh(log)
    return log


def get_user_logs(db: Session, user_id: int, limit: int = 50) -> List[Log]:
    """Get recent logs for a user"""
    return db.query(Log).filter(
        Log.user_id == user_id
    ).order_by(Log.timestamp.desc()).limit(limit).all()


def get_spot_logs(db: Session, spot_id: int, limit: int = 50) -> List[Log]:
    """Get recent logs for a spot"""
    return db.query(Log).filter(
        Log.spot_id == spot_id
    ).order_by(Log.timestamp.desc()).limit(limit).all()


def update_claim(db: Session, user_id: int, spot_id: int, points: int):
    """Update or create claim for user at spot"""
    claim = db.query(Claim).filter(
        Claim.user_id == user_id,
        Claim.spot_id == spot_id
    ).first()
    
    if claim:
        claim.claim_value += points
        claim.dominance += points * 0.1
        claim.last_log = get_current_cet()
    else:
        claim = Claim(
            user_id=user_id,
            spot_id=spot_id,
            claim_value=points,
            dominance=points * 0.1,
            last_log=get_current_cet()
        )
        db.add(claim)
    
    db.commit()


def apply_claim_decay(db: Session):
    """Apply time-based decay to all claims"""
    claims = db.query(Claim).all()
    now = get_current_cet()
    
    for claim in claims:
        hours_since_decay = (now - claim.last_decay).total_seconds() / 3600
        decay_amount = hours_since_decay * settings.CLAIM_DECAY_RATE
        
        claim.claim_value = max(0, claim.claim_value - decay_amount)
        claim.dominance = max(0, claim.dominance - decay_amount * 0.1)
        claim.last_decay = now
    
    db.commit()
