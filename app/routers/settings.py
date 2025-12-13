from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserSettingsUpdate, UserSettingsResponse
from app.routers.auth import get_current_user
from app.models import User, UserSettings, get_cet_now

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's settings"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        # Create default settings if they don't exist
        settings = UserSettings(
            user_id=current_user.id,
            selected_map_layer="osm",
            sounds_enabled=True,
            sound_volume=0.3,
            compass_enabled=False,
            heatmap_visible=False,
            territory_visible=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return UserSettingsResponse(
        selected_map_layer=settings.selected_map_layer,
        sounds_enabled=settings.sounds_enabled,
        sound_volume=settings.sound_volume,
        compass_enabled=settings.compass_enabled,
        heatmap_visible=settings.heatmap_visible,
        territory_visible=settings.territory_visible
    )


@router.put("/", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        # Create new settings
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    settings.updated_at = get_cet_now()
    db.commit()
    db.refresh(settings)
    
    return UserSettingsResponse(
        selected_map_layer=settings.selected_map_layer,
        sounds_enabled=settings.sounds_enabled,
        sound_volume=settings.sound_volume,
        compass_enabled=settings.compass_enabled,
        heatmap_visible=settings.heatmap_visible,
        territory_visible=settings.territory_visible
    )
