from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_MakePoint, ST_DistanceSphere
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from app.models import Log, Spot, User, Claim, GameSetting
from app.schemas import LogCreate
from app.config import settings
import pytz
from app.services import buff_service

# CET timezone
CET = pytz.timezone('Europe/Berlin')

def get_current_cet():
    """Get current time in CET timezone (naive datetime for DB compatibility)"""
    return datetime.now(CET).replace(tzinfo=None)
from app.services.auth_service import update_user_xp


def _repeat_multiplier(seconds_since_last_spot_log: Optional[float]) -> float:
    """Diminishing returns per spot (no hard cap)."""
    if seconds_since_last_spot_log is None:
        return 1.0
    if seconds_since_last_spot_log < 10 * 60:
        return 0.15
    if seconds_since_last_spot_log < 60 * 60:
        return 0.45
    if seconds_since_last_spot_log < 24 * 60 * 60:
        return 0.75
    return 1.0


def _novelty_multiplier(seconds_since_last_spot_log: Optional[float]) -> float:
    """Rewards returning after a longer time; first-time counts as very novel."""
    if seconds_since_last_spot_log is None:
        return 1.6
    if seconds_since_last_spot_log >= 7 * 24 * 60 * 60:
        return 1.6
    if seconds_since_last_spot_log >= 24 * 60 * 60:
        return 1.25
    return 1.0


def _movement_bonus_xp(distance_m: Optional[float]) -> int:
    """Small additive XP bonus for moving between logs."""
    if distance_m is None:
        return 0
    try:
        d = float(distance_m)
    except Exception:
        return 0
    if d < 0:
        return 0
    bonus = int(round(d / 120.0))
    if bonus < 0:
        return 0
    if bonus > 18:
        return 18
    return bonus

def get_game_setting(db: Session, setting_name: str, default_value: float) -> float:
    """Get a game setting from database with fallback to default"""
    setting = db.query(GameSetting).filter(
        GameSetting.setting_name == setting_name
    ).first()
    
    if not setting:
        return default_value
    
    try:
        if setting.data_type == "int":
            return float(int(setting.setting_value))
        elif setting.data_type == "float":
            return float(setting.setting_value)
        else:
            return float(setting.setting_value)
    except (ValueError, TypeError):
        return default_value

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
    
    # Calculate distance using PostGIS ST_DistanceSphere (returns meters)
    user_point = ST_SetSRID(ST_MakePoint(log_data.longitude, log_data.latitude), 4326)
    distance = db.query(
        ST_DistanceSphere(
            spot.location,
            user_point
        )
    ).scalar()
    
    # Active buffs (XP/Claim multipliers, optional range bonus)
    modifiers = buff_service.get_active_modifiers(db, user.id)

    # Check distance constraints - get from database with fallback to config defaults
    auto_log_distance = get_game_setting(db, "auto_log_distance", settings.AUTO_LOG_DISTANCE)
    manual_log_distance = get_game_setting(db, "manual_log_distance", settings.MANUAL_LOG_DISTANCE)
    # Range buffs apply to manual logs only (auto-log stays tight at default radius)
    max_distance = auto_log_distance if is_auto else (manual_log_distance + modifiers.range_bonus_m)
    if distance > max_distance:
        return None
    
    # Calculate rewards - manual logs get more reward
    auto_base_xp = int(get_game_setting(db, "xp_per_log", 10))
    auto_claim_points = int(get_game_setting(db, "claim_points_per_log", 5))

    manual_base_xp = int(get_game_setting(db, "manual_log_xp", 50))
    manual_claim_points = int(get_game_setting(db, "manual_log_claim_points", 25))
    manual_bonus_xp = int(get_game_setting(db, "manual_log_bonus_xp", 25))
    manual_bonus_claim_points = int(get_game_setting(db, "manual_log_bonus_claim_points", 10))

    if is_auto:
        base_xp = auto_base_xp
        claim_points = auto_claim_points
    else:
        # Manual logs with photos/notes get bonus
        base_xp = manual_base_xp
        claim_points = manual_claim_points
        if log_data.photo_data or log_data.notes:
            base_xp += manual_bonus_xp
            claim_points += manual_bonus_claim_points

    # --- RPG XP improvements: novelty + diminishing returns + movement bonus (applies to auto & manual) ---
    now = get_current_cet()
    last_spot_log = (
        db.query(Log)
        .filter(Log.user_id == user.id, Log.spot_id == spot.id)
        .order_by(Log.timestamp.desc())
        .first()
    )
    seconds_since_last_spot_log: Optional[float] = None
    if last_spot_log and getattr(last_spot_log, 'timestamp', None):
        try:
            seconds_since_last_spot_log = float((now - last_spot_log.timestamp).total_seconds())
        except Exception:
            seconds_since_last_spot_log = None

    novelty = _novelty_multiplier(seconds_since_last_spot_log)
    repeat = _repeat_multiplier(seconds_since_last_spot_log)

    last_user_log = (
        db.query(Log)
        .filter(Log.user_id == user.id)
        .order_by(Log.timestamp.desc())
        .first()
    )

    move_dist_m: Optional[float] = None
    if last_user_log and getattr(last_user_log, 'location', None) is not None:
        try:
            move_dist_m = db.query(ST_DistanceSphere(last_user_log.location, user_point)).scalar()
        except Exception:
            move_dist_m = None
    move_bonus = _movement_bonus_xp(move_dist_m)

    xp_gained = int(round(float(base_xp) * float(novelty) * float(repeat))) + int(move_bonus)

    # Apply active buff multipliers
    try:
        xp_gained = int(round(float(xp_gained) * float(modifiers.xp_multiplier)))
    except Exception:
        pass
    try:
        claim_points = int(round(float(claim_points) * float(modifiers.claim_multiplier)))
    except Exception:
        pass
    
    # Apply spot type multipliers (after buff multipliers)
    try:
        xp_gained = int(round(float(xp_gained) * float(spot.xp_multiplier)))
    except Exception:
        pass
    try:
        claim_points = int(round(float(claim_points) * float(spot.claim_multiplier)))
    except Exception:
        pass
    
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

    # Attach applied buff info (transient, for API response)
    try:
        log.xp_multiplier_applied = float(modifiers.xp_multiplier or 1.0)
    except Exception:
        log.xp_multiplier_applied = 1.0
    try:
        log.claim_multiplier_applied = float(modifiers.claim_multiplier or 1.0)
    except Exception:
        log.claim_multiplier_applied = 1.0
    try:
        log.range_bonus_m_applied = float(modifiers.range_bonus_m or 0.0)
    except Exception:
        log.range_bonus_m_applied = 0.0
    
    db.add(log)
    
    # Update user XP
    update_user_xp(db, user, xp_gained)

    # Track total claim points for rankings
    try:
        user.total_claim_points = int(user.total_claim_points or 0) + int(claim_points or 0)
    except Exception:
        pass
    
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
