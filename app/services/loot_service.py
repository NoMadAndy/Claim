from sqlalchemy.orm import Session
from sqlalchemy import and_, text, func
from datetime import datetime, timedelta
from geoalchemy2.elements import WKTElement
from app.models import Spot, User, Item, InventoryItem, get_cet_now
from app.config import settings
import random
import math
from typing import List, Optional


def get_current_cet():
    """Get current CET time as naive datetime (for DB compatibility)"""
    return get_cet_now()


def spawn_loot_spots_for_user(db: Session, user_id: int, latitude: float, longitude: float, radius_meters: int = 500) -> List[Spot]:
    """
    Spawn loot spots around user's current position.
    Returns list of newly spawned loot spots.
    """
    from app.ws.connection_manager import manager
    import asyncio
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # Check if user already has active loot spots nearby
    current_time = get_current_cet()
    existing_loot = db.query(Spot).filter(
        and_(
            Spot.owner_id == user_id,
            Spot.is_loot == True,
            Spot.loot_expires_at > current_time
        )
    ).all()
    
    # Limit to max 5 active loot spots per user
    if len(existing_loot) >= 5:
        return []
    
    # Spawn only 1 loot spot randomly around user
    num_spots = 1
    spawned_spots = []
    
    for _ in range(num_spots):
        # Random offset within radius (50-300m around player)
        angle = random.uniform(0, 2 * math.pi)  # Random angle in radians
        distance = random.uniform(50, min(300, radius_meters))
        
        # Calculate offset lat/lng using proper trigonometry
        # 1 degree latitude = ~111,000 meters
        # 1 degree longitude = ~111,000 * cos(latitude) meters
        lat_offset = (distance * math.cos(angle)) / 111000
        lng_offset = (distance * math.sin(angle)) / (111000 * math.cos(math.radians(latitude)))
        
        loot_lat = latitude + lat_offset
        loot_lng = longitude + lng_offset
        
        # Random loot contents
        loot_xp = random.randint(10, 50)
        expires_at = current_time + timedelta(minutes=random.randint(5, 15))
        
        # Optionally spawn with item (30% chance)
        loot_item_id = None
        item_name = None
        if random.random() < 0.3:
            items = db.query(Item).all()
            if items:
                item = random.choice(items)
                loot_item_id = item.id
                item_name = item.name
        
        # Create loot spot
        point = f'POINT({loot_lng} {loot_lat})'
        loot_spot = Spot(
            name=f"Loot ({loot_xp} XP)",
            description="Mysterious loot appeared!",
            location=WKTElement(point, srid=4326),
            is_permanent=False,
            is_loot=True,
            owner_id=user_id,
            loot_expires_at=expires_at,
            loot_xp=loot_xp,
            loot_item_id=loot_item_id,
            created_at=current_time
        )
        
        db.add(loot_spot)
        db.flush()  # Get the ID but don't commit yet
        
        # Store for WebSocket notification after commit
        spawned_spots.append({
            'spot': loot_spot,
            'lat': loot_lat,
            'lng': loot_lng,
            'item_name': item_name
        })
    
    db.commit()
    
    # Refresh and send WebSocket notifications
    result_spots = []
    for spot_data in spawned_spots:
        spot = spot_data['spot']
        db.refresh(spot)
        result_spots.append(spot)
    # Refresh and send WebSocket notifications
    result_spots = []
    for spot_data in spawned_spots:
        spot = spot_data['spot']
        db.refresh(spot)
        result_spots.append(spot)
        
        # Send WebSocket notification
        try:
            asyncio.create_task(
                manager.send_loot_spawn(
                    user_id=user_id,
                    spot_id=spot.id,
                    latitude=spot_data['lat'],
                    longitude=spot_data['lng'],
                    xp=spot.loot_xp,
                    item_name=spot_data['item_name'],
                    expires_at=spot.loot_expires_at.isoformat() if spot.loot_expires_at else None
                )
            )
        except:
            pass  # WebSocket notification is not critical
    
    return result_spots


def collect_loot(db: Session, user_id: int, loot_spot_id: int, user_lat: float, user_lng: float) -> dict:
    """
    Collect a loot spot if user is close enough and it's still valid.
    First-come-first-serve: Any user can collect any loot spot.
    Returns dict with rewards.
    """
    loot_spot = db.query(Spot).filter(
        and_(
            Spot.id == loot_spot_id,
            Spot.is_loot == True
        )
    ).first()
    
    if not loot_spot:
        return {"success": False, "error": "Loot spot not found or already collected"}
    
    # Check if expired
    current_time = get_current_cet()
    if loot_spot.loot_expires_at and loot_spot.loot_expires_at < current_time:
        # Delete expired loot
        db.delete(loot_spot)
        db.commit()
        return {"success": False, "error": "Loot expired"}
    
    # Check distance
    distance_query = text("""
        SELECT ST_Distance(
            ST_GeographyFromText(:user_location),
            location
        ) as distance
        FROM spots
        WHERE id = :spot_id
    """)
    
    result = db.execute(distance_query, {
        "user_location": f"SRID=4326;POINT({user_lng} {user_lat})",
        "spot_id": loot_spot_id
    }).fetchone()
    
    distance = result[0] if result else None
    
    if distance is None or distance > settings.MANUAL_LOG_DISTANCE:
        return {"success": False, "error": f"Too far away (distance: {distance:.0f}m, max: {settings.MANUAL_LOG_DISTANCE}m)"}
    
    # Collect rewards
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "User not found"}
    
    rewards = {
        "xp": loot_spot.loot_xp or 0,
        "items": []
    }
    
    # Add XP
    user.xp += rewards["xp"]
    
    # Check for level up
    level_up = False
    xp_for_next_level = 100 + (user.level - 1) * 50
    if user.xp >= xp_for_next_level:
        user.level += 1
        level_up = True
    
    # Add item to inventory if present
    if loot_spot.loot_item_id:
        item = db.query(Item).filter(Item.id == loot_spot.loot_item_id).first()
        if item:
            # Check if user already has this item
            inventory_item = db.query(InventoryItem).filter(
                and_(
                    InventoryItem.user_id == user_id,
                    InventoryItem.item_id == item.id
                )
            ).first()
            
            if inventory_item:
                inventory_item.quantity += 1
            else:
                inventory_item = InventoryItem(
                    user_id=user_id,
                    item_id=item.id,
                    quantity=1,
                    acquired_at=current_time
                )
                db.add(inventory_item)
            
            rewards["items"].append({
                "id": item.id,
                "name": item.name,
                "rarity": item.rarity
            })
    
    # Delete loot spot after collection
    db.delete(loot_spot)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "rewards": rewards,
        "level_up": level_up,
        "new_level": user.level if level_up else None,
        "total_xp": user.xp
    }


def cleanup_expired_loot(db: Session):
    """Remove all expired loot spots"""
    current_time = get_current_cet()
    expired_loot = db.query(Spot).filter(
        and_(
            Spot.is_loot == True,
            Spot.loot_expires_at < current_time
        )
    ).all()
    
    for loot in expired_loot:
        db.delete(loot)
    
    db.commit()
    return len(expired_loot)


def cleanup_expired_loot_for_user(db: Session, user_id: int):
    """Remove expired loot spots for a specific user"""
    current_time = get_current_cet()
    expired_loot = db.query(Spot).filter(
        and_(
            Spot.owner_id == user_id,
            Spot.is_loot == True,
            Spot.loot_expires_at < current_time
        )
    ).all()
    
    for loot in expired_loot:
        db.delete(loot)
    
    db.commit()
    return len(expired_loot)


def get_active_loot_for_user(db: Session, user_id: int) -> List[Spot]:
    """Get all active (non-expired) loot spots for a user"""
    current_time = get_current_cet()
    return db.query(Spot).filter(
        and_(
            Spot.owner_id == user_id,
            Spot.is_loot == True,
            Spot.loot_expires_at > current_time
        )
    ).all()
