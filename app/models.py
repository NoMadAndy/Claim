from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    TRAVELLER = "traveller"
    CREATOR = "creator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.TRAVELLER, nullable=False)
    
    # Game Stats
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    total_claim_points = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    logs = relationship("Log", back_populates="user", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="user", cascade="all, delete-orphan")
    tracks = relationship("Track", back_populates="user", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="user", cascade="all, delete-orphan")
    created_spots = relationship("Spot", back_populates="creator", foreign_keys="Spot.creator_id")


class Spot(Base):
    __tablename__ = "spots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    
    # Spot Type
    is_permanent = Column(Boolean, default=True)
    is_loot = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For loot spots
    
    # Creator Info
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Loot specific
    loot_expires_at = Column(DateTime, nullable=True)
    loot_xp = Column(Integer, default=0)
    loot_item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    logs = relationship("Log", back_populates="spot", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="spot", cascade="all, delete-orphan")
    creator = relationship("User", back_populates="created_spots", foreign_keys=[creator_id])
    loot_item = relationship("Item", foreign_keys=[loot_item_id])


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    spot_id = Column(Integer, ForeignKey("spots.id"), nullable=False)
    
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    distance = Column(Float)  # Distance to spot in meters
    
    # Log Type
    is_auto = Column(Boolean, default=False)
    
    # Rewards
    xp_gained = Column(Integer, default=0)
    claim_points = Column(Integer, default=0)
    
    # Optional photo and notes
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="logs")
    spot = relationship("Spot", back_populates="logs")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    spot_id = Column(Integer, ForeignKey("spots.id"), nullable=False)
    
    # Claim values
    claim_value = Column(Float, default=0.0)
    dominance = Column(Float, default=0.0)
    
    last_log = Column(DateTime, default=datetime.utcnow)
    last_decay = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="claims")
    spot = relationship("Spot", back_populates="claims")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Track as LineString
    path = Column(Geography(geometry_type='LINESTRING', srid=4326), nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Stats
    distance_km = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="tracks")
    points = relationship("TrackPoint", back_populates="track", cascade="all, delete-orphan")


class TrackPoint(Base):
    __tablename__ = "track_points"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Optional metadata
    altitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    
    # Relationships
    track = relationship("Track", back_populates="points")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    item_type = Column(String(50))  # consumable, tool, skill_boost, etc.
    rarity = Column(String(20), default="common")  # common, rare, epic, legendary
    
    # Effects
    xp_boost = Column(Float, default=0.0)
    claim_boost = Column(Float, default=0.0)
    range_boost = Column(Float, default=0.0)
    
    icon_url = Column(String(500), nullable=True)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="item", cascade="all, delete-orphan")


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="inventory")
    item = relationship("Item", back_populates="inventory_items")


# Create tables function
def init_db():
    """Initialize database with PostGIS extension and create all tables"""
    from sqlalchemy import text
    from app.database import engine
    
    # Enable PostGIS extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
