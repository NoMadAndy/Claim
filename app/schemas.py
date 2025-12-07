from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    TRAVELLER = "traveller"
    CREATOR = "creator"
    ADMIN = "admin"


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
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


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
    
    class Config:
        from_attributes = True


# Log Schemas
class LogCreate(BaseModel):
    spot_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class LogResponse(BaseModel):
    id: int
    user_id: int
    spot_id: int
    distance: float
    is_auto: bool
    xp_gained: int
    claim_points: int
    timestamp: datetime
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    
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
