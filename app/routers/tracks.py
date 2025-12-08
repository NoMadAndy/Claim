from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_X, ST_Y, ST_GeomFromWKB
from app.database import get_db
from app.schemas import TrackCreate, TrackResponse, TrackPointCreate, TrackWithPoints, TrackPointResponse
from app.services import tracking_service
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.post("/", response_model=TrackResponse, status_code=status.HTTP_201_CREATED)
async def start_track(
    track_data: TrackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new track"""
    # End any existing active tracks for this user
    while True:
        active_track = tracking_service.get_active_track(db, current_user.id)
        if not active_track:
            break
        tracking_service.end_track(db, active_track.id)
        print(f"Auto-ended old track {active_track.id} for user {current_user.id}")
    
    track = tracking_service.create_track(db, current_user, track_data)
    return track


@router.post("/{track_id}/points", response_model=TrackPointResponse)
async def add_point_to_track(
    track_id: int,
    point_data: TrackPointCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a point to an active track"""
    track_point = tracking_service.add_track_point(db, track_id, point_data)
    
    if not track_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found or not active"
        )
    
    # Extract coordinates for response (cast Geography to Geometry)
    from sqlalchemy import cast
    from geoalchemy2 import Geometry
    lat = db.scalar(func.ST_Y(cast(track_point.location, Geometry)))
    lon = db.scalar(func.ST_X(cast(track_point.location, Geometry)))
    
    return TrackPointResponse(
        id=track_point.id,
        latitude=lat,
        longitude=lon,
        timestamp=track_point.timestamp,
        altitude=track_point.altitude,
        heading=track_point.heading
    )


@router.post("/{track_id}/end", response_model=TrackResponse)
async def end_track(
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End an active track"""
    track = tracking_service.end_track(db, track_id)
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    if track.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return track


@router.get("/", response_model=List[TrackResponse])
async def list_all_tracks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tracks for current user"""
    return tracking_service.get_user_tracks(db, current_user.id, active_only=False)


@router.get("/me", response_model=List[TrackResponse])
async def get_my_tracks(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's tracks"""
    tracks = tracking_service.get_user_tracks(db, current_user.id, active_only)
    return tracks


@router.get("/{track_id}", response_model=TrackWithPoints)
async def get_track_details(
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get track with all its points"""
    track = tracking_service.get_track_with_points(db, track_id)
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Convert points to response format
    points = []
    for point in track.points:
        from sqlalchemy import cast
        from geoalchemy2 import Geometry
        lat = db.scalar(func.ST_Y(cast(point.location, Geometry)))
        lon = db.scalar(func.ST_X(cast(point.location, Geometry)))
        
        points.append(TrackPointResponse(
            id=point.id,
            latitude=lat,
            longitude=lon,
            timestamp=point.timestamp,
            altitude=point.altitude,
            heading=point.heading
        ))
    
    return TrackWithPoints(
        id=track.id,
        user_id=track.user_id,
        name=track.name,
        is_active=track.is_active,
        started_at=track.started_at,
        ended_at=track.ended_at,
        distance_km=track.distance_km,
        duration_minutes=track.duration_minutes,
        points=points
    )
