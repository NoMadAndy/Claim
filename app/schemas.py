from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    TRAVELLER = "traveller"
    CREATOR = "creator"
    ADMIN = "admin"


class SpotType(str, Enum):
    """Types of spots with different XP and claim conditions"""
    STANDARD = "standard"
    CHURCH = "church"
    SIGHT = "sight"
    SPORTS_FACILITY = "sports_facility"
    PLAYGROUND = "playground"
    MONUMENT = "monument"
    MUSEUM = "museum"
    CASTLE = "castle"
    PARK = "park"
    VIEWPOINT = "viewpoint"
    HISTORIC = "historic"
    CULTURAL = "cultural"
    RELIGIOUS = "religious"
    TOWNHALL = "townhall"
    MARKET = "market"
    FOUNTAIN = "fountain"
    STATUE = "statue"


class ItemType(str, Enum):
    CONSUMABLE = "consumable"
    TOOL = "tool"
    SKILL_BOOST = "skill_boost"


class Rarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    role: UserRole
    level: int
    xp: int
    total_claim_points: int
    heatmap_color: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# User Settings Schemas
class UserSettingsUpdate(BaseModel):
    selected_map_layer: Optional[str] = None
    sounds_enabled: Optional[bool] = None
    sound_volume: Optional[float] = None
    compass_enabled: Optional[bool] = None
    heatmap_visible: Optional[bool] = None
    territory_visible: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    selected_map_layer: str = "osm"
    sounds_enabled: bool = True
    sound_volume: float = 0.3
    compass_enabled: bool = False
    heatmap_visible: bool = False
    territory_visible: bool = True
    
    class Config:
        from_attributes = True


# Location Schema
class LocationPoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


# Spot Schemas
class SpotBase(BaseModel):
    name: str
    description: Optional[str] = None


class SpotCreate(SpotBase):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    spot_type: Optional[SpotType] = SpotType.STANDARD
    xp_multiplier: Optional[float] = 1.0
    claim_multiplier: Optional[float] = 1.0
    icon_name: Optional[str] = None


class SpotResponse(SpotBase):
    id: int
    latitude: float
    longitude: float
    is_permanent: bool
    is_loot: bool
    created_at: datetime
    creator_id: Optional[int] = None
    loot_expires_at: Optional[datetime] = None
    loot_xp: Optional[int] = None
    cooldown_status: Optional[str] = None  # "ready", "partial", "cooldown" for non-loot spots
    dominant_player_color: Optional[str] = None  # Hex color of the player with most dominance
    dominant_player_name: Optional[str] = None  # Username of the player with most dominance
    spot_type: Optional[SpotType] = SpotType.STANDARD
    xp_multiplier: Optional[float] = 1.0
    claim_multiplier: Optional[float] = 1.0
    icon_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Log Schemas
class LogCreate(BaseModel):
    spot_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_auto: bool = False  # Whether this is an auto-log
    notes: Optional[str] = None
    photo_data: Optional[str] = None  # Base64 encoded binary data
    photo_mime: Optional[str] = None  # MIME type


class LogResponse(BaseModel):
    id: int
    user_id: int
    spot_id: int
    distance: float
    is_auto: bool
    xp_gained: int
    claim_points: int
    xp_multiplier_applied: Optional[float] = None
    claim_multiplier_applied: Optional[float] = None
    range_bonus_m_applied: Optional[float] = None
    timestamp: datetime
    notes: Optional[str] = None
    has_photo: bool = False  # Just indicate if photo exists, don't return binary data
    username: str = ""  # Username from User table
    
    class Config:
        from_attributes = True


# Claim Schemas
class ClaimResponse(BaseModel):
    id: int
    user_id: int
    spot_id: int
    claim_value: float
    dominance: float
    last_log: datetime
    
    class Config:
        from_attributes = True


# Track Schemas
class TrackPointCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None


class TrackPointResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    timestamp: datetime
    altitude: Optional[float] = None
    heading: Optional[float] = None
    
    class Config:
        from_attributes = True


class TrackCreate(BaseModel):
    name: Optional[str] = None


class TrackResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    is_active: bool
    started_at: datetime
    ended_at: Optional[datetime] = None
    distance_km: float
    duration_minutes: int
    
    class Config:
        from_attributes = True


class TrackWithPoints(TrackResponse):
    points: List[TrackPointResponse] = []


# Item Schemas
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    item_type: str
    rarity: str


class ItemCreate(ItemBase):
    xp_boost: float = 0.0
    claim_boost: float = 0.0
    range_boost: float = 0.0


class ItemResponse(ItemBase):
    id: int
    xp_boost: float
    claim_boost: float
    range_boost: float
    icon_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# Inventory Schemas
class InventoryItemResponse(BaseModel):
    id: int
    user_id: int
    item: ItemResponse
    quantity: int
    acquired_at: datetime
    
    class Config:
        from_attributes = True


class UseItemResponse(BaseModel):
    success: bool
    error: str = None
    item_id: int = None
    item_name: str = None
    effects: dict = None
    remaining: int = 0


# WebSocket Event Schemas
class WSEvent(BaseModel):
    event_type: str
    data: dict


class WSPositionUpdate(BaseModel):
    user_id: int
    username: str
    latitude: float
    longitude: float
    heading: Optional[float] = None
    timestamp: datetime


class WSLogEvent(BaseModel):
    log_id: int
    user_id: int
    username: str
    spot_name: str
    xp_gained: int
    claim_points: int
    is_auto: bool


class WSLootEvent(BaseModel):
    spot_id: int
    latitude: float
    longitude: float
    xp: int
    item: Optional[ItemResponse] = None
    expires_at: datetime


class WSClaimUpdate(BaseModel):
    spot_id: int
    user_id: int
    username: str
    claim_value: float
    dominance: float


# Heatmap Schemas
class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    intensity: float


class HeatmapData(BaseModel):
    user_id: int
    username: str
    color: Optional[str] = None
    points: List[HeatmapPoint]


# Stats Schemas
class UserStats(BaseModel):
    level: int
    xp: int
    xp_to_next_level: int
    total_claim_points: int
    total_logs: int
    total_spots_claimed: int
    active_tracks: int
    inventory_count: int


# Energy Monitoring Schemas
class EnergyConsumptionType(str, Enum):
    GPS = "gps"
    NETWORK = "network"
    WEBSOCKET = "websocket"
    TRACKING = "tracking"
    SENSORS = "sensors"
    UI = "ui"
    OTHER = "other"


class EnergyMetricCreate(BaseModel):
    consumption_type: EnergyConsumptionType
    battery_level: Optional[float] = None
    is_charging: bool = False
    activity_duration_seconds: Optional[float] = None
    gps_updates_count: int = 0
    network_requests_count: int = 0
    websocket_messages_count: int = 0
    estimated_battery_drain: Optional[float] = None


class EnergyMetricResponse(BaseModel):
    id: int
    user_id: int
    consumption_type: EnergyConsumptionType
    battery_level: Optional[float]
    is_charging: bool
    activity_duration_seconds: Optional[float]
    gps_updates_count: int
    network_requests_count: int
    websocket_messages_count: int
    estimated_battery_drain: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


class EnergySettingsUpdate(BaseModel):
    energy_saving_enabled: Optional[bool] = None
    auto_enable_at_battery: Optional[float] = None
    gps_update_interval_normal: Optional[int] = None
    gps_update_interval_saving: Optional[int] = None
    batch_network_requests: Optional[bool] = None
    reduce_heatmap_updates: Optional[bool] = None
    reduce_tracking_accuracy: Optional[bool] = None
    notify_battery_level: Optional[bool] = None
    notify_optimization_tips: Optional[bool] = None


class EnergySettingsResponse(BaseModel):
    id: int
    user_id: int
    energy_saving_enabled: bool
    auto_enable_at_battery: float
    gps_update_interval_normal: int
    gps_update_interval_saving: int
    batch_network_requests: bool
    reduce_heatmap_updates: bool
    reduce_tracking_accuracy: bool
    notify_battery_level: bool
    notify_optimization_tips: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class EnergyStatsResponse(BaseModel):
    """Energy statistics and analysis"""
    current_battery_level: Optional[float] = None
    is_charging: bool = False
    estimated_time_remaining_hours: Optional[float] = None
    average_battery_drain_per_hour: Optional[float] = None
    top_consumers: List[dict]  # List of {type, percentage, count}
    optimization_suggestions: List[str]
    energy_saving_enabled: bool


class BatteryStatusResponse(BaseModel):
    """Current battery status from device"""
    level: Optional[float] = None  # 0-100
    charging: bool = False
    discharge_time: Optional[float] = None  # seconds
    charge_time: Optional[float] = None  # seconds
