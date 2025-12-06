from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_X, ST_Y
from app.models import Claim, User, Spot
from app.schemas import HeatmapData, HeatmapPoint


def get_user_heatmap(db: Session, user_id: int) -> HeatmapData:
    """Get heatmap data for a specific user's claims"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return HeatmapData(user_id=user_id, username="Unknown", points=[])
    
    # Get all claims for this user with their spot locations
    claims = db.query(
        Claim,
        Spot
    ).join(
        Spot, Claim.spot_id == Spot.id
    ).filter(
        Claim.user_id == user_id,
        Claim.claim_value > 0
    ).all()
    
    points = []
    for claim, spot in claims:
        # Extract coordinates from PostGIS geometry
        lat = db.execute(func.ST_Y(spot.location)).scalar()
        lon = db.execute(func.ST_X(spot.location)).scalar()
        
        points.append(HeatmapPoint(
            latitude=lat,
            longitude=lon,
            intensity=claim.claim_value
        ))
    
    return HeatmapData(
        user_id=user.id,
        username=user.username,
        points=points
    )


def get_all_heatmaps(db: Session, limit: int = 10) -> List[HeatmapData]:
    """Get heatmap data for top users by claim points"""
    top_users = db.query(User).order_by(
        User.total_claim_points.desc()
    ).limit(limit).all()
    
    heatmaps = []
    for user in top_users:
        heatmap = get_user_heatmap(db, user.id)
        heatmaps.append(heatmap)
    
    return heatmaps


def get_spot_dominance(db: Session, spot_id: int) -> List[dict]:
    """Get dominance rankings for a specific spot"""
    claims = db.query(
        Claim,
        User
    ).join(
        User, Claim.user_id == User.id
    ).filter(
        Claim.spot_id == spot_id
    ).order_by(
        Claim.dominance.desc()
    ).all()
    
    rankings = []
    for claim, user in claims:
        rankings.append({
            "user_id": user.id,
            "username": user.username,
            "claim_value": claim.claim_value,
            "dominance": claim.dominance,
            "last_log": claim.last_log
        })
    
    return rankings
