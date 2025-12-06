from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Item, InventoryItem, User
from app.schemas import ItemCreate


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
