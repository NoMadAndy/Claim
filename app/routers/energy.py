"""
Energy monitoring API endpoints.

Provides REST API for:
- Recording energy metrics
- Retrieving energy statistics
- Managing energy settings
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User, EnergyConsumptionType
from app.schemas import (
    EnergyMetricCreate,
    EnergyMetricResponse,
    EnergySettingsUpdate,
    EnergySettingsResponse,
    EnergyStatsResponse,
    BatteryStatusResponse
)
from app.services.energy_service import EnergyService

router = APIRouter(
    prefix="/api/energy",
    tags=["energy"]
)


@router.post("/metrics", response_model=EnergyMetricResponse)
def create_energy_metric(
    metric: EnergyMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a new energy consumption metric.
    
    This endpoint allows the frontend to log energy consumption
    data for analysis and optimization.
    """
    energy_metric = EnergyService.create_energy_metric(
        db=db,
        user_id=current_user.id,
        metric_data=metric
    )
    return energy_metric


@router.get("/metrics", response_model=List[EnergyMetricResponse])
def get_energy_metrics(
    hours: int = Query(default=24, ge=1, le=168),  # 1 hour to 7 days
    consumption_type: Optional[EnergyConsumptionType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get energy consumption metrics for the current user.
    
    Args:
        hours: Number of hours to look back (default: 24, max: 168)
        consumption_type: Optional filter by consumption type
    """
    metrics = EnergyService.get_energy_metrics(
        db=db,
        user_id=current_user.id,
        hours=hours,
        consumption_type=consumption_type
    )
    return metrics


@router.post("/stats", response_model=EnergyStatsResponse)
def get_energy_stats(
    battery_status: BatteryStatusResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive energy statistics and optimization suggestions.
    
    The frontend should send current battery status to get
    accurate time estimates and suggestions.
    """
    stats = EnergyService.get_energy_stats(
        db=db,
        user_id=current_user.id,
        current_battery=battery_status.level,
        is_charging=battery_status.charging
    )
    return stats


@router.get("/settings", response_model=EnergySettingsResponse)
def get_energy_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get energy optimization settings for the current user.
    """
    settings = EnergyService.get_or_create_settings(db=db, user_id=current_user.id)
    return settings


@router.patch("/settings", response_model=EnergySettingsResponse)
def update_energy_settings(
    settings_update: EnergySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update energy optimization settings for the current user.
    
    Only provided fields will be updated.
    """
    settings = EnergyService.update_settings(
        db=db,
        user_id=current_user.id,
        settings_update=settings_update
    )
    return settings
