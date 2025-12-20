from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.functions import ST_MakeLine, ST_SetSRID, ST_MakePoint, ST_Length
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from app.models import Track, TrackPoint, User
from app.schemas import TrackCreate, TrackPointCreate


def create_track(db: Session, user: User, track_data: TrackCreate) -> Track:
    """Create a new track for a user"""
    track = Track(
        user_id=user.id,
        name=track_data.name or f"Track {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        is_active=True,
        started_at=datetime.utcnow()
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    return track


def add_track_point(
    db: Session,
    track_id: int,
    point_data: TrackPointCreate
) -> Optional[TrackPoint]:
    """Add a point to an active track"""
    track = db.query(Track).filter(
        Track.id == track_id,
        Track.is_active == True
    ).first()
    
    if not track:
        return None
    
    point_wkt = f'POINT({point_data.longitude} {point_data.latitude})'
    track_point = TrackPoint(
        track_id=track_id,
        location=WKTElement(point_wkt, srid=4326),
        altitude=point_data.altitude,
        accuracy=point_data.accuracy,
        heading=point_data.heading,
        speed=point_data.speed
    )
    
    db.add(track_point)
    db.commit()
    db.refresh(track_point)
    
    # Update track path and stats
    update_track_stats(db, track)
    
    return track_point


def end_track(db: Session, track_id: int) -> Optional[Track]:
    """End an active track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        return None
    
    track.is_active = False
    track.ended_at = datetime.utcnow()
    
    # Calculate final duration
    duration = track.ended_at - track.started_at
    track.duration_minutes = int(duration.total_seconds() / 60)
    
    db.commit()
    db.refresh(track)
    return track


def update_track_stats(db: Session, track: Track):
    """Update track statistics (distance, etc.)"""
    # Get all points for this track
    points = db.query(TrackPoint).filter(
        TrackPoint.track_id == track.id
    ).order_by(TrackPoint.timestamp).all()
    
    if len(points) < 2:
        return
    
    # Build LineString from points (cast Geography to Geometry)
    coords = []
    for p in points:
        coord = db.execute(
            text("SELECT ST_X(location::geometry), ST_Y(location::geometry) FROM track_points WHERE id = :id"), 
            {"id": p.id}
        ).fetchone()
        if coord:
            lon, lat = coord
            coords.append(f'{lon} {lat}')
    linestring_wkt = f'LINESTRING({", ".join(coords)})'
    
    track.path = WKTElement(linestring_wkt, srid=4326)
    
    # Calculate distance in km using PostGIS
    distance_meters = db.query(
        ST_Length(track.path)
    ).scalar()
    
    if distance_meters:
        track.distance_km = distance_meters / 1000.0
    
    db.commit()


def get_user_tracks(db: Session, user_id: int, active_only: bool = False) -> List[Track]:
    """Get tracks for a user"""
    query = db.query(Track).filter(Track.user_id == user_id)
    
    if active_only:
        query = query.filter(Track.is_active == True)
    
    return query.order_by(Track.started_at.desc()).all()


def get_active_track(db: Session, user_id: int) -> Optional[Track]:
    """Get user's currently active track"""
    return db.query(Track).filter(
        Track.user_id == user_id,
        Track.is_active == True
    ).first()


def get_track_with_points(db: Session, track_id: int) -> Optional[Track]:
    """Get a track with all its points"""
    return db.query(Track).filter(Track.id == track_id).first()
