from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Item, InventoryItem, User
from app.schemas import ItemCreate
from app.services import buff_service


def create_item(db: Session, item_data: ItemCreate) -> Item:
    """Create a new item"""
    item = Item(
        name=item_data.name,
        description=item_data.description,
        item_type=item_data.item_type,
        rarity=item_data.rarity,
        xp_boost=item_data.xp_boost,
        claim_boost=item_data.claim_boost,
        range_boost=item_data.range_boost
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def add_to_inventory(db: Session, user_id: int, item_id: int, quantity: int = 1) -> InventoryItem:
    """Add an item to user's inventory"""
    # Check if user already has this item
    inventory_item = db.query(InventoryItem).filter(
        InventoryItem.user_id == user_id,
        InventoryItem.item_id == item_id
    ).first()
    
    if inventory_item:
        inventory_item.quantity += quantity
    else:
        inventory_item = InventoryItem(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity
        )
        db.add(inventory_item)
    
    db.commit()
    db.refresh(inventory_item)
    return inventory_item


def get_user_inventory(db: Session, user_id: int) -> List[InventoryItem]:
    """Get all items in user's inventory"""
    return db.query(InventoryItem).filter(
        InventoryItem.user_id == user_id
    ).all()


def remove_from_inventory(db: Session, user_id: int, item_id: int, quantity: int = 1) -> bool:
    """Remove an item from inventory"""
    inventory_item = db.query(InventoryItem).filter(
        InventoryItem.user_id == user_id,
        InventoryItem.item_id == item_id
    ).first()
    
    if not inventory_item or inventory_item.quantity < quantity:
        return False
    
    inventory_item.quantity -= quantity
    
    if inventory_item.quantity <= 0:
        db.delete(inventory_item)
    
    db.commit()
    return True


def get_all_items(db: Session) -> List[Item]:
    """Get all available items"""
    return db.query(Item).all()


def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    """Get item by ID"""
    return db.query(Item).filter(Item.id == item_id).first()


def use_item(db: Session, user_id: int, item_id: int) -> dict:
    """
    Use/consume an item from inventory.
    Returns dict with effects applied.
    """
    inventory_item = db.query(InventoryItem).filter(
        InventoryItem.user_id == user_id,
        InventoryItem.item_id == item_id
    ).first()
    
    if not inventory_item or inventory_item.quantity <= 0:
        return {"success": False, "error": "Item not in inventory"}
    
    item = inventory_item.item

    # Determine buff duration (seconds). No DB schema for duration yet, so keep mapping in code.
    duration_seconds = 0
    name = (item.name or "").strip().lower()
    if name == "xp boost":
        duration_seconds = 3600
    elif name == "mega xp boost":
        duration_seconds = 1800
    elif name == "range extender":
        duration_seconds = 3600
    elif name == "claim amplifier":
        duration_seconds = 3600
    else:
        # Default: if it has an effect, give it 1h so it visibly works.
        if (item.xp_boost or 0) != 0 or (item.claim_boost or 0) != 0 or (item.range_boost or 0) != 0:
            duration_seconds = 3600
    
    # Apply effects (now persisted as temporary buffs)
    effects = {
        "xp_boost": item.xp_boost,
        "claim_boost": item.claim_boost,
        "range_boost": item.range_boost
    }

    # Persist buff so it affects subsequent actions (logs / loot)
    created_buff = None
    if duration_seconds > 0 and (
        (item.xp_boost or 0) != 0 or (item.claim_boost or 0) != 0 or (item.range_boost or 0) != 0
    ):
        created_buff = buff_service.create_buff_from_item_effects(
            db,
            user_id=user_id,
            xp_boost=item.xp_boost,
            claim_boost=item.claim_boost,
            range_boost=item.range_boost,
            duration_seconds=duration_seconds,
        )
        effects["expires_at"] = created_buff.expires_at.isoformat() if created_buff.expires_at else None
    
    # Decrease quantity
    inventory_item.quantity -= 1
    if inventory_item.quantity <= 0:
        db.delete(inventory_item)
    
    db.commit()
    
    return {
        "success": True,
        "item_id": item.id,
        "item_name": item.name,
        "effects": effects,
        "remaining": inventory_item.quantity if inventory_item.quantity > 0 else 0
    }


def initialize_default_items(db: Session):
    """Create default items for the game"""
    default_items = [
        {
            "name": "XP Boost",
            "description": "Increases XP gain by 50% for 1 hour",
            "item_type": "consumable",
            "rarity": "common",
            "xp_boost": 0.5,
            "icon_url": "⭐"
        },
        {
            "name": "Mega XP Boost",
            "description": "Doubles XP gain for 30 minutes",
            "item_type": "consumable",
            "rarity": "rare",
            "xp_boost": 1.0,
            "icon_url": "🌟"
        },
        {
            "name": "Range Extender",
            "description": "Increases log range by 50m",
            "item_type": "consumable",
            "rarity": "rare",
            "range_boost": 50.0,
            "icon_url": "📡"
        },
        {
            "name": "Claim Amplifier",
            "description": "Increases claim points by 100%",
            "item_type": "consumable",
            "rarity": "epic",
            "claim_boost": 1.0,
            "icon_url": "💎"
        },
        {
            "name": "Lucky Charm",
            "description": "Increases loot spawn rate",
            "item_type": "passive",
            "rarity": "legendary",
            "icon_url": "🍀"
        },
        {
            "name": "Health Potion",
            "description": "Restores energy (future feature)",
            "item_type": "consumable",
            "rarity": "common",
            "icon_url": "🧪"
        }
    ]
    
    for item_data in default_items:
        # Check if item already exists
        existing = db.query(Item).filter(Item.name == item_data["name"]).first()
        if not existing:
            item = Item(**item_data)
            db.add(item)
    
    db.commit()
    print(f"Initialized {len(default_items)} default items")
